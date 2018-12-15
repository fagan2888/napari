from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QSlider, QVBoxLayout, QSplitter
from vispy.scene import SceneCanvas, PanZoomCamera

class QtViewer(QSplitter):
    def __init__(self, viewer):
        super().__init__()

        self.canvas = SceneCanvas(keys=None, vsync=True)

        self.view = self.canvas.central_widget.add_view()
        # Set 2D camera (the camera will scale to the contents in the scene)
        self.view.camera = PanZoomCamera(aspect=1)
        # flip y-axis to have correct aligment
        self.view.camera.flip = (0, 1, 0)
        self.view.camera.set_range()

        center = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas.native)
        layout.addWidget(viewer.dimensions._qt)
        center.setLayout(layout)

        # Add vertical sliders, center, and layerlist
        viewer.controlBars._qt.setMinimumSize(QSize(40, 40))
        self.addWidget(viewer.controlBars._qt)
        viewer.dimensions._qt.setMinimumSize(QSize(100, 100))
        self.addWidget(center)
        viewer.layers._qt.setMinimumSize(QSize(250, 250))
        self.addWidget(viewer.layers._qt)

        viewer.dimensions._qt.setFixedHeight(0)
