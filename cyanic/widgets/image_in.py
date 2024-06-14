from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QBuffer, QIODevice, QByteArray
import base64
from ..krita_controller import KritaController
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CyanicWidget

# Select an image
class ImageInWidget(CyanicWidget):
    MAX_HEIGHT = 100
    def __init__(self, settings_controller:SettingsController, api:SDAPI, key:str, size_dict:dict={"x":0,"y":0,"w":0,"h":0}, hide_refresh=True):
        super().__init__(settings_controller, api)
        self.key = key # `key` should be whatever the key get_generation_data() should use to return the image
        # Example 'img2img' returns {'img2img': {...}}
        # self.size_dict = size_dict
        self.hide_refresh = hide_refresh
        self.selection_mode = 'canvas'
        # self.image:QImage = None

        self.img_ref_key = 'img_ref_%s' % self.key
        self.img_ref_coords_key = 'img_ref_%s_coords' % self.key

        self.variables = {
            self.img_ref_key: None, # QImage
            self.img_ref_coords_key: size_dict, 
        }

        self.init_ui()
        self.set_widget_values()

    # Replaces the old self.image?
    @property
    def image(self):
        return self.variables[self.img_ref_key]

    @image.setter
    def image(self, value:QImage):
        self.variables[self.img_ref_key] = value


    def load_settings(self):
        super().load_settings()

    def load_server_data(self):
        pass

    def set_widget_values(self):
        if self.variables[self.img_ref_key] is None:
            self.clear_previews()
        else:
            self.update_preview_icons()

    def init_ui(self):
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
        # self.image = None
        self.variables[self.img_ref_key] = None

    def set_ref_coords(self, x, y, w, h):
        self.variables[self.img_ref_coords_key]['x'] = x
        self.variables[self.img_ref_coords_key]['y'] = y
        self.variables[self.img_ref_coords_key]['w'] = w
        self.variables[self.img_ref_coords_key]['h'] = h

    def get_selection_img(self):
        kc = KritaController()
        self.selection_mode = 'selection'
        # self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = kc.get_selection_bounds()
        self.set_ref_coords(*kc.get_selection_bounds())
        self.get_img()

    def get_layer_img(self):
        kc = KritaController()
        self.selection_mode = 'layer'
        # self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = kc.get_layer_bounds()
        self.set_ref_coords(*kc.get_layer_bounds())
        self.get_img()

    def get_canvas_img(self):
        kc = KritaController()
        self.selection_mode = 'canvas'
        # self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = kc.get_canvas_bounds()
        self.set_ref_coords(*kc.get_canvas_bounds())
        self.get_img()

    def get_img(self, selection_mode=None):
        kc = KritaController()
        if selection_mode is None:
            selection_mode = self.selection_mode

        if selection_mode is 'selection':
            self.image = kc.get_selection_img()
        elif selection_mode is 'layer':
            self.image = kc.get_selected_layer_img()
        else:
            self.image = kc.get_canvas_img()
        
        self.update_preview_icons()

    def update_preview_icons(self):
        self.preview_list.clear()
        name = ''
        if self.image is not None:
            if type(self.image) == str:
                self.image = QImage(self.image)
            icon = QIcon(QPixmap.fromImage(self.image))
            self.preview_list.addItem(QListWidgetItem(icon, name))

    def load_settings(self):
        super().load_settings()
        self.update_preview_icons()
        # Update selected area to match? Might cause confusion going back and forth either way.
        # I'm going to leave it turned off for now.
        # kc = KritaController()
        # coords = self.variables[self.img_ref_coords_key]
        # kc.set_selection(coords['x'], coords['y'], coords['w'], coords['h'])

    def get_generation_data(self):
        data = {}
        kc = KritaController()

        if self.refresh_before_gen_cb.isChecked():
            clear_selection = False
            # Should selection_mode == 'selection' repeat the previous selection? Or just use the current?
            if self.selection_mode is 'selection':
                x, y, w, h = kc.get_selection_bounds()
                if w == 0 and h == 0:
                    # The selection was cleared, reset the previous selection before refreshing the image
                    clear_selection = True
                    coords = self.variables[self.img_ref_coords_key]
                    # kc.set_selection(self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'])
                    kc.set_selection(coords['x'], coords['y'], coords['w'], coords['h'])

            self.get_img() # Refresh self.img

            if clear_selection:
                kc.set_selection(0,0,0,0)


        if self.image is None: # Default to the canvas
            s_x, s_y, s_w, s_h = kc.get_selection_bounds()
            if s_w > 0 and s_h > 0:
                self.get_selection_img()
            else:
                self.get_canvas_img()

        if self.image is not None:
            data[self.key] = kc.qimage_to_b64_str(self.image)
        else:
            data[self.key] = None # Keeps things from crashing, even if it's not very useful.
        return data