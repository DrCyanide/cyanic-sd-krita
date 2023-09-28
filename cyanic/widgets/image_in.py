from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QBuffer, QIODevice, QByteArray
import base64
from ..krita_controller import KritaController
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController

# Select an image
class ImageInWidget(QWidget):
    MAX_HEIGHT = 100
    def __init__(self, settings_controller:SettingsController, api:SDAPI, mode):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.mode = mode # `mode` should be whatever the key get_generation_data() should use to return the image
        self.kc = KritaController()
        self.image:QImage = None
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self.preview_list = QListWidget()
        self.preview_list.setFixedHeight(ImageInWidget.MAX_HEIGHT)
        self.preview_list.setFlow(QListView.Flow.LeftToRight)
        self.preview_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.preview_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_list.setViewMode(QListWidget.IconMode)
        self.preview_list.setIconSize(QSize(ImageInWidget.MAX_HEIGHT, ImageInWidget.MAX_HEIGHT))
        self.clear_previews()

        self.layout().addWidget(self.preview_list)
        
        button_row = QWidget()
        button_row.setLayout(QHBoxLayout())
        button_row.layout().setContentsMargins(0,0,0,0)

        clear_btn = QPushButton('Clear')
        clear_btn.clicked.connect(self.clear_previews)
        button_row.layout().addWidget(clear_btn)

        use_active = QPushButton('Use Layer')
        use_active.clicked.connect(self.get_layer_img)
        button_row.layout().addWidget(use_active)

        use_canvas = QPushButton('Use Canvas')
        use_canvas.clicked.connect(self.get_canvas_img)
        button_row.layout().addWidget(use_canvas)

        self.layout().addWidget(button_row)

    def clear_previews(self):
        self.preview_list.clear()
        self.preview_list.addItem(QListWidgetItem(QIcon(), 'No Image Selected'))
        self.image = None

    def get_layer_img(self):
        # name = self.kc.get_active_layer_name()
        self.preview_list.clear()
        name = ''
        self.image = self.kc.get_selected_layer_img()
        icon = QIcon(QPixmap.fromImage(self.image))
        self.preview_list.addItem(QListWidgetItem(icon, name))

    def get_canvas_img(self):
        # name = self.kc.get_active_layer_name()
        self.preview_list.clear()
        name = ''
        self.image = self.kc.get_canvas_img()
        icon = QIcon(QPixmap.fromImage(self.image))
        self.preview_list.addItem(QListWidgetItem(icon, name))

    def qimage_to_b64_str(self, image:QImage):
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, 'PNG')
        b64_data = ba.toBase64().data()
        return b64_data.decode()

    def get_generation_data(self):
        data = {}
        data[self.mode] = self.qimage_to_b64_str(self.image)
        return data