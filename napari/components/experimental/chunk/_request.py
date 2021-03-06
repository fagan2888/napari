"""ChunkKey and ChunkRequest classes.
"""
import contextlib
import logging
from typing import NamedTuple, Optional, Tuple

import numpy as np

from ....layers.base.base import Layer
from ....types import ArrayLike, Dict
from ....utils.perf import PerfEvent, block_timer
from ._utils import get_data_id

LOGGER = logging.getLogger("napari.async")

# We convert slices to tuple for hashing.
SliceTuple = Tuple[Optional[int], Optional[int], Optional[int]]


def _flatten(indices) -> tuple:
    """Return a flat tuple of integers to represent the indices.

    Slice objects are not hashable, so we convert them.
    """
    result = []
    for x in indices:
        if isinstance(x, slice):
            result.extend([x.start, x.stop, x.step])
        else:
            result.append(x)
    return tuple(result)


class LayerKey(NamedTuple):
    """The key for a layer and its important properties.

    Attributes
    ----------
    layer_id : int
        The id of the layer making the request.
    data_id : int
        The id of the data in the layer.
    data_level : int
        The level in the data (for multi-scale).
    indices : Tuple[Optional[slice], ...]
        The indices of the slice.
    """

    layer_id: int
    data_id: int
    data_level: int
    indices: Tuple[Optional[slice], ...]

    def _get_hash_values(self):
        return (
            self.layer_id,
            self.data_id,
            self.data_level,
            _flatten(self.indices),
        )


class ChunkKey:
    """The key for one single ChunkRequest.

    Parameters
    ----------
    layer : Layer
        The layer which is loading the chunk.
    indices : Indices
        The indices of the layer we are loading.

    Attributes
    ----------
    layer_key : LayerKey
        The layer specific parts of the key.
    key : Tuple
        The combined key, everything hashed together.
    """

    def __init__(self, layer: Layer, indices: Tuple[Optional[slice], ...]):
        self.layer_key = LayerKey(
            id(layer), get_data_id(layer), layer._data_level, indices
        )

        self.key = hash(self._get_hash_values())

    def _get_hash_values(self):
        return self.layer_key._get_hash_values()

    def __str__(self):
        layer_key = self.layer_key
        return (
            f"layer_id={layer_key.layer_id} data_id={layer_key.data_id} "
            f"data_level={layer_key.data_level} indices={layer_key.indices}"
        )

    def __eq__(self, other):
        return self.key == other.key


class ChunkRequest:
    """A request asking the ChunkLoader to load one or more arrays.

    Parameters
    ----------
    key : ChunkKey
        The key of the request.
    chunks : Dict[str, ArrayLike]
        The chunk arrays we need to load.

    Attributes
    ----------
    key : ChunkKey
        The key of the request.
    chunks : Dict[str, ArrayLike]
        The chunk arrays we need to load.
    timers : Dict[str, PerfEvent]
        Timing information about chunk load time.
    """

    def __init__(self, key: ChunkKey, chunks: Dict[str, ArrayLike]):
        # Make sure chunks dict is what we expect.
        for chunk_key, array in chunks.items():
            assert isinstance(chunk_key, str)
            assert array is not None

        self.key = key
        self.chunks = chunks

        self.timers: Dict[str, PerfEvent] = {}

    @property
    def data_id(self) -> int:
        return self.key.layer_key.data_id

    @property
    def num_chunks(self) -> int:
        """Return the number of chunks in this request."""
        return len(self.chunks)

    @property
    def num_bytes(self) -> int:
        """Return the number of bytes that were loaded."""
        return sum(array.nbytes for array in self.chunks.values())

    @property
    def in_memory(self) -> bool:
        """Return True if all chunks are ndarrays."""
        return all(isinstance(x, np.ndarray) for x in self.chunks.values())

    @contextlib.contextmanager
    def chunk_timer(self, name):
        """Time a block of code and save the PerfEvent in self.timers.

        We want to time our loads whether perfmon is enabled or not, since
        the auto-async feature needs to work in all cases.

        Parameters
        ----------
        name : str
            The name of the timer.

        Yields
        ------
        PerfEvent
            The timing event for the block.
        """
        with block_timer(name) as event:
            yield event
        self.timers[name] = event

    def load_chunks(self):
        """Load all of our chunks now in this thread.

        We time the overall load with the special name "load_chunks" and then
        we time each chunk as it loads, using it's array name as the key.
        """
        with self.chunk_timer("ChunkRequest.load_chunks"):
            for key, array in self.chunks.items():
                with self.chunk_timer(key):
                    loaded_array = np.asarray(array)
                    self.chunks[key] = loaded_array

    def transpose_chunks(self, order: tuple) -> None:
        """Transpose all our chunks.

        Parameters
        ----------
        order
            Transpose the chunks into this order.
        """
        for key, array in self.chunks.items():
            self.chunks[key] = array.transpose(order)

    @property
    def image(self) -> Optional[ArrayLike]:
        """The image chunk or None.

        Returns
        -------
        Optional[ArrayLike]
            The image chunk or None if we don't have one.
        """
        return self.chunks.get('image')

    @property
    def thumbnail_source(self):
        """The chunk to use as the thumbnail_source or None.

        Returns
        -------
        Optional[ArrayLike]
            The thumbnail_source chunk or None if we don't have one.
        """
        try:
            return self.chunks['thumbnail_source']
        except KeyError:
            # No thumbnail_source so return the image instead. For single-scale
            # we use the image as the thumbnail_source.
            return self.chunks.get('image')
