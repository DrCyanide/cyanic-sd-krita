from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QBuffer, QIODevice, QByteArray
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import CollapsibleWidget

class MaskWidget(QWidget):
    MAX_HEIGHT = 100
    def __init__(self, settings_controller:SettingsController, api:SDAPI, size_dict:dict):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.size_dict = size_dict
        self.kc = KritaController()
        # self.setLayout(QFormLayout())
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        # self.variables = {
        #     'mask_blur': 4,
        #     'mask_mode': 0,
        #     'masked_content': 1,
        #     'inpaint_area': 0,
        #     'mask_padding': 32,
        # }
        self.mask = None
        self.image = None

        # Making the combined Mask + Image box uses a lot of the same code that ImageInWidget uses.
        self.preview_list = QListWidget()
        self.preview_list.setFixedHeight(MaskWidget.MAX_HEIGHT)
        self.preview_list.setFlow(QListView.Flow.LeftToRight)
        self.preview_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.preview_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview_list.setViewMode(QListWidget.IconMode)
        self.preview_list.setIconSize(QSize(MaskWidget.MAX_HEIGHT, MaskWidget.MAX_HEIGHT))
        self.layout().addWidget(self.preview_list)
        
        button_row = QWidget()
        button_row.setLayout(QHBoxLayout())
        button_row.layout().setContentsMargins(0,0,0,0)

        use_selection = QPushButton('Use Selection')
        use_selection.clicked.connect(lambda: self.get_mask_and_img('selection'))
        button_row.layout().addWidget(use_selection)

        use_active = QPushButton('Use Layer')
        use_active.clicked.connect(lambda: self.get_mask_and_img('layer'))
        button_row.layout().addWidget(use_active)

        use_canvas = QPushButton('Use Canvas')
        use_canvas.clicked.connect(lambda: self.get_mask_and_img('canvas'))
        button_row.layout().addWidget(use_canvas)

        self.layout().addWidget(button_row)


        form = QWidget()
        form.setLayout(QFormLayout())
        form.layout().setContentsMargins(0,0,0,0)

        # mask blur
        blur_box = QSpinBox()
        blur_box.setMinimum(0)
        blur_box.setMaximum(64)
        # blur_box.setValue(self.variables['mask_blur'])
        # blur_box.valueChanged.connect(lambda: self.update_variable('mask_blur', blur_box.value()))
        blur_box.setValue(self.settings_controller.get('inpaint.mask_blur'))
        blur_box.valueChanged.connect(lambda: self.settings_controller.set('inpaint.mask_blur', blur_box.value()))
        form.layout().addRow('Mask Blur', blur_box)

        # mask mode = inpainting_mask_invert (0 = inpaint masked, 1 = inpaint not masked)
        mask_mode_options = [
            'Inpaint masked',
            'Inpaint not masked',
        ]
        mask_mode_select = QComboBox()
        mask_mode_select.addItems(mask_mode_options)
        mask_mode_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        # mask_mode_select.setCurrentIndex(self.variables['mask_mode'])
        # mask_mode_select.currentIndexChanged.connect(lambda: self.update_variable('mask_mode', mask_mode_select.currentIndex()))
        mask_mode_select.setCurrentIndex(self.settings_controller.get('inpaint.mask_mode'))
        mask_mode_select.currentIndexChanged.connect(lambda: self.settings_controller.set('inpaint.mask_mode', mask_mode_select.currentIndex()))
        form.layout().addRow('Mask Mode', mask_mode_select)

        # mask content = inpainting_fill (0 = fill, 1 = original, 2 = latent noise, 3 = latent nothing)
        mask_content_options = [
            'Fill',
            'Original',
            'Latent Noise',
            'Latent Nothing',
        ]
        mask_content_select = QComboBox()
        mask_content_select.addItems(mask_content_options)
        mask_content_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        # mask_content_select.setCurrentIndex(self.variables['masked_content'])
        # mask_content_select.currentIndexChanged.connect(lambda: self.update_variable('masked_content', mask_content_select.currentIndex()))
        mask_content_select.setCurrentIndex(self.settings_controller.get('inpaint.masked_content'))
        mask_content_select.currentIndexChanged.connect(lambda: self.settings_controller.set('inpaint.masked_content', mask_content_select.currentIndex()))
        form.layout().addRow('Masked Content', mask_content_select)

        # Inpaint Area = inpaint_full_res (0 = whole picture, 1 = only masked)
        inpaint_area_options = [
            'Whole Picture',
            'Only Masked',
        ]
        inpaint_select = QComboBox()
        inpaint_select.addItems(inpaint_area_options)
        inpaint_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        # inpaint_select.setCurrentIndex(self.variables['inpaint_area'])
        # inpaint_select.currentIndexChanged.connect(lambda: self.update_variable('inpaint_area', inpaint_select.currentIndex()))
        inpaint_select.setCurrentIndex(self.settings_controller.get('inpaint.inpaint_area'))
        inpaint_select.currentIndexChanged.connect(lambda: self.settings_controller.set('inpaint.inpaint_area', inpaint_select.currentIndex()))
        form.layout().addRow('Inpaint Area', inpaint_select)

        # Only masked padding, pixels (inpaint_full_res_padding)
        padding_box = QSpinBox()
        padding_box.setMinimum(0)
        padding_box.setMaximum(64)
        # padding_box.setValue(self.variables['mask_padding'])
        # padding_box.valueChanged.connect(lambda: self.update_variable('mask_padding', padding_box.value()))
        padding_box.setValue(self.settings_controller.get('inpaint.padding'))
        padding_box.valueChanged.connect(lambda: self.settings_controller.set('inpaint.padding', padding_box.value()))
        form.layout().addRow('Only masked padding', padding_box)

        # self.layout().addWidget(form)

        cw = CollapsibleWidget('Inpaint Settings', form)
        self.layout().addWidget(cw)


    # def update_variable(self, key, value):
    #     self.variables[key] = value

    def get_mask_and_img(self, mode='canvas'):
        if mode == 'selection':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_selection_bounds()
        if mode == 'layer':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_layer_bounds()
        if mode == 'canvas':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_canvas_bounds()

        self.mask, self.image = self.kc.get_mask_and_image(mode)
        self.preview_list.clear()
        icon = QIcon(QPixmap.fromImage(self.image))
        self.preview_list.addItem(QListWidgetItem(icon, 'Image'))
        mask_icon = QIcon(QPixmap.fromImage(self.mask))
        self.preview_list.addItem(QListWidgetItem(mask_icon, 'Mask'))

    def get_generation_data(self):
        # data = {
        #     'mask_blur': self.variables['mask_blur'],
        #     'inpainting_mask_invert': self.variables['mask_mode'],
        #     'inpainting_fill': self.variables['masked_content'],
        #     'inpaint_full_res': self.variables['inpaint_area'],
        #     'inpaint_full_res_padding': self.variables['mask_padding'], # IDK what this actually does
        # }
        data = {
            'mask_blur': self.settings_controller.get('inpaint.mask_blur'),
            'inpainting_mask_invert': self.settings_controller.get('inpaint.mask_mode'),
            'inpainting_fill': self.settings_controller.get('inpaint.masked_content'),
            'inpaint_full_res': self.settings_controller.get('inpaint.inpaint_area'),
            'inpaint_full_res_padding': self.settings_controller.get('inpaint.padding'), # IDK what this actually does
        }
        self.settings_controller.save()
        if self.image is not None:
            data['inpaint_img'] = self.kc.qimage_to_b64_str(self.image)
        if self.mask is not None:
            data['mask_img'] = self.kc.qimage_to_b64_str(self.mask)
        return data