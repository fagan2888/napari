import warnings

import numpy as np
from vispy.color import Colormap as VispyColormap
from vispy.scene.node import Node

from .image import Image as ImageNode
from .vispy_base_layer import VispyBaseLayer
from .volume import Volume as VolumeNode

texture_dtypes = [
    np.dtype(np.int8),
    np.dtype(np.uint8),
    np.dtype(np.int16),
    np.dtype(np.uint16),
    np.dtype(np.float32),
]


class ImageLayerNode:
    def __init__(self, custom_node: Node = None):
        self._custom_node = custom_node
        self._image_node = ImageNode(None, method='auto')
        self._volume_node = VolumeNode(np.zeros((1, 1, 1)), clim=[0, 1])

    def get_node(self, ndisplay: int) -> Node:

        # Return custom node if we have one.
        if self._custom_node is not None:
            return self._custom_node

        # Return Image or Volume node based on 2D or 3D.
        if ndisplay == 2:
            return self._image_node
        return self._volume_node


class VispyImageLayer(VispyBaseLayer):
    def __init__(self, layer, node=None):

        # Use custom node from caller, or our standard image/volume nodes.
        self._layer_node = ImageLayerNode(node)

        # Default to 2D (image) node.
        super().__init__(layer, self._layer_node.get_node(2))

        self._array_like = True

        self.layer.events.rendering.connect(self._on_rendering_change)
        self.layer.events.interpolation.connect(self._on_interpolation_change)
        self.layer.events.colormap.connect(self._on_colormap_change)
        self.layer.events.contrast_limits.connect(
            self._on_contrast_limits_change
        )
        self.layer.events.gamma.connect(self._on_gamma_change)
        self.layer.events.iso_threshold.connect(self._on_iso_threshold_change)
        self.layer.events.attenuation.connect(self._on_attenuation_change)

        self._on_display_change()
        self._on_data_change()

    def _on_display_change(self, data=None):

        parent = self.node.parent
        self.node.parent = None

        self.node = self._layer_node.get_node(self.layer._dims.ndisplay)

        if data is None:
            data = np.zeros((1,) * self.layer._dims.ndisplay)

        if self.layer._empty:
            self.node.visible = False
        else:
            self.node.visible = self.layer.visible

        if self.layer.loaded:
            self.node.set_data(data)

        self.node.parent = parent
        self.node.order = self.order
        self.reset()

    def _data_astype(self, data, dtype):
        """Broken out as a separate function so we can time with perfmon."""
        return data.astype(dtype)

    def _on_data_change(self, event=None):
        if not self.layer.loaded:
            # Do nothing if we are not yet loaded. Calling astype below could
            # be very expensive. Lets not do it until our data has been loaded.
            return

        self._set_node_data(self.node, self.layer._data_view)

    def _set_node_data(self, node, data):
        """Our self.layer._data_view has been updated, update our node.
        """

        dtype = np.dtype(data.dtype)
        if dtype not in texture_dtypes:
            try:
                dtype = dict(
                    i=np.int16, f=np.float32, u=np.uint16, b=np.uint8
                )[dtype.kind]
            except KeyError:  # not an int or float
                raise TypeError(
                    f'type {dtype} not allowed for texture; must be one of {set(texture_dtypes)}'  # noqa: E501
                )
            data = self._data_astype(data, dtype)

        if self.layer._dims.ndisplay == 3 and self.layer._dims.ndim == 2:
            data = np.expand_dims(data, axis=0)

        # Check if data exceeds MAX_TEXTURE_SIZE and downsample
        if (
            self.MAX_TEXTURE_SIZE_2D is not None
            and self.layer._dims.ndisplay == 2
        ):
            data = self.downsample_texture(data, self.MAX_TEXTURE_SIZE_2D)
        elif (
            self.MAX_TEXTURE_SIZE_3D is not None
            and self.layer._dims.ndisplay == 3
        ):
            data = self.downsample_texture(data, self.MAX_TEXTURE_SIZE_3D)

        # Check if ndisplay has changed current node type needs updating
        if (
            self.layer._dims.ndisplay == 3 and not isinstance(node, VolumeNode)
        ) or (
            self.layer._dims.ndisplay == 2 and not isinstance(node, ImageNode)
        ):
            self._on_display_change(data)
        else:
            node.set_data(data)

        if self.layer._empty:
            node.visible = False
        else:
            node.visible = self.layer.visible

        # Call to update order of translation values with new dims:
        self._on_matrix_change()
        node.update()

    def _on_interpolation_change(self, event=None):
        self.node.interpolation = self.layer.interpolation

    def _on_rendering_change(self, event=None):
        if isinstance(self.node, VolumeNode):
            self.node.method = self.layer.rendering
            self._on_attenuation_change()
            self._on_iso_threshold_change()

    def _on_colormap_change(self, event=None):
        self.node.cmap = VispyColormap(*self.layer.colormap)

    def _on_contrast_limits_change(self, event=None):
        self.node.clim = self.layer.contrast_limits

    def _on_gamma_change(self, event=None):
        if len(self.node.shared_program.frag._set_items) > 0:
            self.node.gamma = self.layer.gamma

    def _on_iso_threshold_change(self, event=None):
        if isinstance(self.node, VolumeNode):
            self.node.threshold = self.layer.iso_threshold

    def _on_attenuation_change(self, event=None):
        if isinstance(self.node, VolumeNode):
            self.node.attenuation = self.layer.attenuation

    def reset(self, event=None):
        self._reset_base()
        self._on_interpolation_change()
        self._on_colormap_change()
        self._on_contrast_limits_change()
        self._on_gamma_change()
        self._on_rendering_change()

    def downsample_texture(self, data, MAX_TEXTURE_SIZE):
        """Downsample data based on maximum allowed texture size.

        Parameters
        ----------
        data : array
            Data to be downsampled if needed.
        MAX_TEXTURE_SIZE : int
            Maximum allowed texture size.

        Returns
        -------
        data : array
            Data that now fits inside texture.
        """
        if np.any(np.greater(data.shape, MAX_TEXTURE_SIZE)):
            if self.layer.multiscale:
                raise ValueError(
                    f"Shape of individual tiles in multiscale {data.shape} "
                    f"cannot exceed GL_MAX_TEXTURE_SIZE "
                    f"{MAX_TEXTURE_SIZE}. Rendering is currently in "
                    f"{self.layer._dims.ndisplay}D mode."
                )
            warnings.warn(
                f"data shape {data.shape} exceeds GL_MAX_TEXTURE_SIZE "
                f"{MAX_TEXTURE_SIZE} in at least one axis and "
                f"will be downsampled. Rendering is currently in "
                f"{self.layer._dims.ndisplay}D mode."
            )
            downsample = np.ceil(
                np.divide(data.shape, MAX_TEXTURE_SIZE)
            ).astype(int)
            scale = np.ones(self.layer.ndim)
            for i, d in enumerate(self.layer._dims.displayed):
                scale[d] = downsample[i]
            self.layer._transforms['tile2data'].scale = scale
            self._on_matrix_change()
            slices = tuple(slice(None, None, ds) for ds in downsample)
            data = data[slices]
        return data
