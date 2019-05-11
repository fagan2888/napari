from qtpy.QtCore import QCoreApplication, Qt, QSize
from qtpy.QtWidgets import QWidget, QSlider, QVBoxLayout, QSplitter
from qtpy.QtGui import QCursor, QPixmap
from ...._vispy.scene import SceneCanvas
from vispy.scene import PanZoomCamera

from ..._dims.view import QtDims
from ..._layers.view import QtLayers
from ....resources import resources_dir
from .controls import QtControls
from .buttons import QtLayersButtons

class QtViewer(QSplitter):

    def __init__(self, viewer):
        super().__init__()

        QCoreApplication.setAttribute(
            Qt.AA_UseStyleSheetPropagationInWidgetStyles, True
        )

        self.viewer = viewer
        self.viewer._qtviewer = self

        self.canvas = SceneCanvas(keys=None, vsync=True)
        self.canvas.native.setMinimumSize(QSize(100, 100))

        self.canvas.connect(self.on_mouse_move)
        self.canvas.connect(self.on_mouse_press)
        self.canvas.connect(self.on_mouse_release)
        self.canvas.connect(self.on_key_press)
        self.canvas.connect(self.on_key_release)

        self.view = self.canvas.central_widget.add_view()
        # Set 2D camera (the camera will scale to the contents in the scene)
        self.view.camera = PanZoomCamera(aspect=1)
        # flip y-axis to have correct aligment
        self.view.camera.flip = (0, 1, 0)
        self.view.camera.set_range()

        self.view.camera.viewbox_key_event = viewbox_key_event

        center = QWidget()
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(15, 20, 15, 10)
        center_layout.addWidget(self.canvas.native)
        self.dims = QtDims(self.viewer.dims)
        center_layout.addWidget(self.dims)
        center.setLayout(center_layout)

        # Add controls, center, and layerlist
        self.control_panel = QtControls(viewer)
        self.addWidget(self.control_panel)
        self.addWidget(center)

        right = QWidget()
        right_layout = QVBoxLayout()
        self.layers = QtLayers(self.viewer.layers)
        right_layout.addWidget(self.layers)
        self.buttons = QtLayersButtons(viewer)
        right_layout.addWidget(self.buttons)
        right.setLayout(right_layout)
        right.setMinimumSize(QSize(308, 250))

        self.addWidget(right)

        self._cursors = {
                'disabled': QCursor(
                    QPixmap(':/icons/cursor/cursor_disabled.png')
                    .scaled(20, 20)),
                'cross': Qt.CrossCursor,
                'forbidden': Qt.ForbiddenCursor,
                'pointing': Qt.PointingHandCursor,
                'standard': QCursor()
            }

    def set_cursor(self, cursor, size=10):
        if cursor == 'square':
            if size < 10 or size > 300:
                q_cursor = self._cursors['cross']
            else:
                q_cursor = QCursor(QPixmap(':/icons/cursor/cursor_square.png')
                                   .scaledToHeight(size))
        else:
            q_cursor = self._cursors[cursor]
        self.canvas.native.setCursor(q_cursor)

    def on_mouse_move(self, event):
        """Called whenever mouse moves over canvas.
        """
        layer = self.viewer._top
        if layer is not None:
            layer.on_mouse_move(event)

    def on_mouse_press(self, event):
        """Called whenever mouse pressed in canvas.
        """
        layer = self.viewer._top
        if layer is not None:
            layer.on_mouse_press(event)

    def on_mouse_release(self, event):
        """Called whenever mouse released in canvas.
        """
        layer = self.viewer._top
        if layer is not None:
            layer.on_mouse_release(event)

    def on_key_press(self, event):
        """Called whenever key pressed in canvas.
        """
        if (event.text in self.viewer.key_bindings and not
                event.native.isAutoRepeat()):
            self.viewer.key_bindings[event.text](self.viewer)
            return

        layer = self.viewer._top
        if layer is not None:
            layer.on_key_press(event)

    def on_key_release(self, event):
        """Called whenever key released in canvas.
        """
        layer = self.viewer._top
        if layer is not None:
            layer.on_key_release(event)


def viewbox_key_event(event):
    """ViewBox key event handler
    Parameters
    ----------
    event : instance of Event
        The event.
    """
    return
