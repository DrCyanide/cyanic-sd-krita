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
    def __init__(self, settings_controller:SettingsController, api:SDAPI, key:str, size_dict:dict={"x":0,"y":0,"w":0,"h":0}, hide_refresh=True):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.key = key # `key` should be whatever the key get_generation_data() should use to return the image
        self.size_dict = size_dict
        self.hide_refresh = hide_refresh
        self.selection_mode = 'canvas'
        self.kc = KritaController()
        self.image:QImage = None
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.draw_ui()

    def draw_ui(self):
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

        # clear_btn = QPushButton('Clear')
        # clear_btn.clicked.connect(self.clear_previews)
        # button_row.layout().addWidget(clear_btn)
        use_selection = QPushButton('Use Selection')
        use_selection.clicked.connect(self.get_selection_img)
        button_row.layout().addWidget(use_selection)

        use_active = QPushButton('Use Layer')
        use_active.clicked.connect(self.get_layer_img)
        button_row.layout().addWidget(use_active)

        use_canvas = QPushButton('Use Canvas')
        use_canvas.clicked.connect(self.get_canvas_img)
        button_row.layout().addWidget(use_canvas)

        self.layout().addWidget(button_row)

        self.refresh_before_gen_cb = QCheckBox('Refresh image before generating')
        self.refresh_before_gen_cb.setToolTip("If checked, it'll act like you clicked the 'Use Selection'/'Use Layer'/'Use Canvas' button again right before clicking 'Generate'. Defaults to 'Use Canvas'")
        # Set default value? 
        if not self.hide_refresh:
            self.layout().addWidget(self.refresh_before_gen_cb)

    def clear_previews(self):
        self.preview_list.clear()
        self.preview_list.addItem(QListWidgetItem(QIcon(), 'No Image Selected'))
        self.image = None


    def get_selection_img(self):
        self.selection_mode = 'selection'
        self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_selection_bounds()
        self.get_img()

    def get_layer_img(self):
        self.selection_mode = 'layer'
        self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_layer_bounds()
        self.get_img()

    def get_canvas_img(self):
        self.selection_mode = 'canvas'
        self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_canvas_bounds()
        self.get_img()

    def get_img(self, selection_mode=None):
        if selection_mode is None:
            selection_mode = self.selection_mode
        self.preview_list.clear()
        name = ''

        if selection_mode is 'selection':
            self.image = self.kc.get_selection_img()
        elif selection_mode is 'layer':
            self.image = self.kc.get_selected_layer_img()
        else:
            self.image = self.kc.get_canvas_img()
        icon = QIcon(QPixmap.fromImage(self.image))
        self.preview_list.addItem(QListWidgetItem(icon, name))


    def get_generation_data(self):
        data = {}

        if self.refresh_before_gen_cb.isChecked():
            clear_selection = False
            # Should selection_mode == 'selection' repeat the previous selection? Or just use the current?
            if self.selection_mode is 'selection':
                x, y, w, h = self.kc.get_selection_bounds()
                if w == 0 and h == 0:
                    # The selection was cleared, reset the previous selection before refreshing the image
                    clear_selection = True
                    self.kc.set_selection(self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'])

            self.get_img() # Refresh self.img

            if clear_selection:
                self.kc.set_selection(0,0,0,0)


        if self.image is None: # Default to the canvas
            s_x, s_y, s_w, s_h = self.kc.get_selection_bounds()
            if s_w > 0 and s_h > 0:
                self.get_selection_img()
            else:
                self.get_canvas_img()

        if self.image is not None:
            data[self.key] = self.kc.qimage_to_b64_str(self.image)
        else:
            data[self.key] = None # Keeps things from crashing, even if it's not very useful.
        return data