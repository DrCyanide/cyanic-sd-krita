from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QBuffer, QIODevice, QByteArray
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import CollapsibleWidget, CyanicWidget

class MaskWidget(CyanicWidget):
    MAX_HEIGHT = 100
    def __init__(self, settings_controller:SettingsController, api:SDAPI, size_dict:dict):
        super().__init__(settings_controller, api)
        self.size_dict = size_dict
        self.variables = {
            'inpaint_mask_blur': 4,
            'inpaint_mask_mode': 0,
            'inpaint_mask_content': 1,
            'inpaint_area': 0,
            'inpaint_padding': 32,
            'inpaint_mask_auto_update': True,
            'inpaint_mask_above_results': False,
            'inpaint_mask_hide_while_gen': True,
        }
        self.selection_mode = 'canvas'
        self.mask_uuid = None
        self.mask = None
        self.image = None
        
        self.init_ui()
        self.set_widget_values()

    def set_widget_values(self):
        self.auto_update_mask_cb.setChecked(self.variables['inpaint_mask_auto_update'])
        self.mask_above_results_cb.setChecked(self.variables['inpaint_mask_above_results'])
        self.hide_mask_cb.setChecked(self.variables['inpaint_mask_hide_while_gen'])
        self.blur_box.setValue(self.variables['inpaint_mask_blur'])
        self.mask_mode_select.setCurrentIndex(self.variables['inpaint_mask_mode'])
        self.mask_content_select.setCurrentIndex(self.variables['inpaint_mask_content'])
        self.inpaint_select.setCurrentIndex(self.variables['inpaint_area'])
        self.padding_box.setValue(self.variables['inpaint_padding'])

    def handle_hidden(self):
        self.auto_update_mask_cb.setHidden(self.settings_controller.get('hide_ui_inpaint_auto_update'))
        self.mask_above_results_cb.setHidden(self.settings_controller.get('hide_ui_inpaint_mask_above_results'))
        self.hide_mask_cb.setHidden(self.settings_controller.get('hide_ui_inpaint_hide_mask'))

    def load_server_data(self):
        pass

    def init_ui(self):
        # Making the combined Mask + Image box uses a lot of the same code that ImageInWidget uses.
        self.preview_list = QListWidget()
        self.preview_list.setSelectionMode(QAbstractItemView.NoSelection)
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

        # Mask QoL settings
        mask_settings = QWidget()
        mask_settings.setLayout(QFormLayout())
        mask_settings.layout().setContentsMargins(0,0,0,0)
        # Update Mask before Generating
        self.auto_update_mask_cb = QCheckBox('Update mask before generating')
        self.auto_update_mask_cb.setToolTip('Will remember the last layer used as a mask and use the current state of that layer whenever the "Generate" button is clicked')
        # self.auto_update_mask_cb.setChecked(self.variables['inpaint_mask_auto_update'])
        self.auto_update_mask_cb.stateChanged.connect(lambda: self._update_variable('inpaint_mask_auto_update', self.auto_update_mask_cb.isChecked()))
        mask_settings.layout().addWidget(self.auto_update_mask_cb)

        # Add Results below Mask
        self.mask_above_results_cb = QCheckBox('Mask above results')
        self.mask_above_results_cb.setToolTip('Will insert the results as a new layer below the mask')
        # self.mask_above_results_cb.setChecked(self.variables['inpaint_mask_above_results'])
        self.mask_above_results_cb.stateChanged.connect(lambda: self._update_variable('inpaint_mask_above_results', self.mask_above_results_cb.isChecked()))
        mask_settings.layout().addWidget(self.mask_above_results_cb)

        # Hide mask on generation
        self.hide_mask_cb = QCheckBox('Hide mask when generating')
        self.hide_mask_cb.setToolTip('Turns off mask visibility so that you can see the results faster')
        # self.hide_mask_cb.setChecked(self.variables['inpaint_mask_hide_while_gen'])
        self.hide_mask_cb.stateChanged.connect(lambda: self._update_variable('inpaint_mask_hide_while_gen', self.hide_mask_cb.isChecked()))
        mask_settings.layout().addWidget(self.hide_mask_cb)
        
        # # The `not <setting>` is a bit confusing, but it makes for an easier time understanding the final layout
        # mask_settings_shown = sum([not self.settings_controller.get('hide_ui_inpaint_auto_update'), not self.settings_controller.get('hide_ui_inpaint_mask_above_results'), not self.settings_controller.get('hide_ui_inpaint_hide_mask')])
        # if mask_settings_shown == 1:
        #     self.layout().addWidget(mask_settings)
        # elif mask_settings_shown > 1:
        #     ms_cw = CollapsibleWidget('Mask Settings', mask_settings)
        #     self.layout().addWidget(ms_cw)
        # # else, nothing to add
        mask_settings_collapse = CollapsibleWidget('Mask Settings', mask_settings)
        self.layout().addWidget(mask_settings_collapse)

        form = QWidget()
        form.setLayout(QFormLayout())
        form.layout().setContentsMargins(0,0,0,0)

        # mask blur
        self.blur_box = QSpinBox()
        self.blur_box.wheelEvent = lambda event : None
        self.blur_box.setMinimum(0)
        self.blur_box.setMaximum(64)
        # self.blur_box.setValue(self.variables['inpaint_mask_blur'])
        self.blur_box.valueChanged.connect(lambda: self._update_variable('inpaint_mask_blur', self.blur_box.value()))
        form.layout().addRow('Mask Blur', self.blur_box)

        # mask mode = inpainting_mask_invert (0 = inpaint masked, 1 = inpaint not masked)
        mask_mode_options = [
            'Inpaint masked',
            'Inpaint not masked',
        ]
        self.mask_mode_select = QComboBox()
        self.mask_mode_select.wheelEvent = lambda event : None
        self.mask_mode_select.addItems(mask_mode_options)
        self.mask_mode_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        # self.mask_mode_select.setCurrentIndex(self.variables['inpaint_mask_mode'])
        self.mask_mode_select.currentIndexChanged.connect(lambda: self._update_variable('inpaint_mask_mode', self.mask_mode_select.currentIndex()))
        form.layout().addRow('Mask Mode', self.mask_mode_select)

        # mask content = inpainting_fill (0 = fill, 1 = original, 2 = latent noise, 3 = latent nothing)
        mask_content_options = [
            'Fill',
            'Original',
            'Latent Noise',
            'Latent Nothing',
        ]
        self.mask_content_select = QComboBox()
        self.mask_content_select.wheelEvent = lambda event : None
        self.mask_content_select.addItems(mask_content_options)
        self.mask_content_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        # self.mask_content_select.setCurrentIndex(self.variables['inpaint_mask_content'])
        self.mask_content_select.currentIndexChanged.connect(lambda: self._update_variable('inpaint_mask_content', self.mask_content_select.currentIndex()))
        form.layout().addRow('Masked Content', self.mask_content_select)

        # Inpaint Area = inpaint_full_res (0 = whole picture, 1 = only masked)
        inpaint_area_options = [
            'Whole Picture',
            'Only Masked',
        ]
        self.inpaint_select = QComboBox()
        self.inpaint_select.wheelEvent = lambda event : None
        self.inpaint_select.addItems(inpaint_area_options)
        self.inpaint_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        # self.inpaint_select.setCurrentIndex(self.variables['inpaint_area'])
        self.inpaint_select.currentIndexChanged.connect(lambda: self._update_variable('inpaint_area', self.inpaint_select.currentIndex()))
        form.layout().addRow('Inpaint Area', self.inpaint_select)

        # Only masked padding, pixels (inpaint_full_res_padding)
        self.padding_box = QSpinBox()
        self.padding_box.wheelEvent = lambda event : None
        self.padding_box.setMinimum(0)
        self.padding_box.setMaximum(64)
        # self.padding_box.setValue(self.variables['inpaint_padding'])
        self.padding_box.valueChanged.connect(lambda: self._update_variable('inpaint_padding', self.padding_box.value()))
        form.layout().addRow('Only masked padding', self.padding_box)

        # self.layout().addWidget(form)
        cw = CollapsibleWidget('Inpaint Settings', form)
        self.layout().addWidget(cw)

    def update_size_dict(self, mode='canvas'):
        kc = KritaController()
        if mode == 'selection':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = kc.get_selection_bounds()
        if mode == 'layer':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = kc.get_layer_bounds()
        if mode == 'canvas':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = kc.get_canvas_bounds()

    def update_preview_icons(self):
        self.preview_list.clear()
        icon = QIcon(QPixmap.fromImage(self.image))
        self.preview_list.addItem(QListWidgetItem(icon, 'Image'))
        mask_icon = QIcon(QPixmap.fromImage(self.mask))
        self.preview_list.addItem(QListWidgetItem(mask_icon, 'Mask'))

    def update_mask_only(self, mode='canvas'):
        kc = KritaController()
        self.update_size_dict(mode)
        self.mask, _ = kc.get_mask_and_image(mode)
        self.update_preview_icons()
        

    def get_mask_and_img(self, mode='canvas'):
        self.selection_mode = mode
        self.update_size_dict(mode)
        kc = KritaController()

        try:
            self.mask_uuid = kc.get_active_layer_uuid()
            self.mask, self.image = kc.get_mask_and_image(mode)
            self.update_preview_icons()
        except Exception as e:
            raise Exception('Cyanic SD - Error updating mask: %s' % e)


    def get_generation_data(self):
        kc = KritaController()
        data = {
            'mask_blur': self.variables['inpaint_mask_blur'],
            'inpainting_mask_invert': self.variables['inpaint_mask_mode'],
            'inpainting_fill': self.variables['inpaint_mask_content'],
            'inpaint_full_res': self.variables['inpaint_area'],
            'inpaint_full_res_padding': self.variables['inpaint_padding'], # IDK what this actually does
        }
        self.save_settings()

        if self.variables['inpaint_mask_auto_update'] and self.mask_uuid is not None:
            # Auto-update the mask
            kc.set_layer_uuid_as_active(self.mask_uuid)
            if self.selection_mode is 'selection':
                s_x, s_y, s_w, s_h = kc.get_selection_bounds()
                if s_w == 0 and s_h == 0:
                    # The selection was cleared, fallback to using the canvas instead
                    self.selection_mode = 'canvas'
                    self.get_mask_and_img(mode=self.selection_mode)
            # self.get_mask_and_img(mode=self.selection_mode)
            self.update_mask_only(mode=self.selection_mode)


        if self.image is None:
            s_x, s_y, s_w, s_h = kc.get_selection_bounds()
            if s_w > 0 and s_h > 0:
                self.get_mask_and_img(mode="selection")
            else:
                self.get_mask_and_img(mode="canvas")

        if self.image is not None:
            data['inpaint_img'] = kc.qimage_to_b64_str(self.image)
        if self.mask is not None:
            data['mask_img'] = kc.qimage_to_b64_str(self.mask)

        if self.variables['inpaint_mask_above_results']:
            # This data will be intercepted by the Generate widget
            data['CYANIC'] = {
                'results_below_layer_uuid': self.mask_uuid 
            }
        if self.variables['inpaint_mask_hide_while_gen']:
            layer = kc.get_layer_from_uuid(self.mask_uuid)
            kc.set_layer_visible(layer, False)
        return data