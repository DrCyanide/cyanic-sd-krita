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
        self.variables = {
            'mask_blur': self.settings_controller.get('inpaint.mask_blur'),
            'mask_mode': self.settings_controller.get('inpaint.mask_mode'),
            'masked_content': self.settings_controller.get('inpaint.masked_content'),
            'inpaint_area': self.settings_controller.get('inpaint.inpaint_area'),
            'mask_padding': self.settings_controller.get('inpaint.padding'),
            'auto_update_mask': self.settings_controller.get('inpaint.auto_update_mask'),
            'results_below_mask': self.settings_controller.get('inpaint.results_below_mask'),
            'hide_mask_on_gen': self.settings_controller.get('inpaint.hide_mask_on_gen'),
        }
        self.selection_mode = 'canvas'
        self.mask_uuid = None
        self.mask = None
        self.image = None
        
        self.draw_ui()

    def draw_ui(self):
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

        # Mask QoL settings
        mask_settings = QWidget()
        mask_settings.setLayout(QFormLayout())
        mask_settings.layout().setContentsMargins(0,0,0,0)
        # Update Mask before Generating
        auto_update_mask_cb = QCheckBox('Update mask before generating')
        auto_update_mask_cb.setToolTip('Will remember the last layer used as a mask and use the current state of that layer whenever the "Generate" button is clicked')
        auto_update_mask_cb.setChecked(self.variables['auto_update_mask'])
        auto_update_mask_cb.stateChanged.connect(lambda: self._update_variable('auto_update_mask', auto_update_mask_cb.isChecked()))
        if not self.settings_controller.get('hide_ui.inpaint_auto_update'):
            mask_settings.layout().addWidget(auto_update_mask_cb)

        # Add Results below Mask
        results_below_mask_cb = QCheckBox('Results below mask')
        results_below_mask_cb.setToolTip('Will insert the results as a new layer below the mask')
        results_below_mask_cb.setChecked(self.variables['results_below_mask'])
        results_below_mask_cb.stateChanged.connect(lambda: self._update_variable('results_below_mask', results_below_mask_cb.isChecked()))
        if not self.settings_controller.get('hide_ui.inpaint_below_mask'):
            mask_settings.layout().addWidget(results_below_mask_cb)

        # Hide mask on generation
        hide_mask_cb = QCheckBox('Hide mask when generating')
        hide_mask_cb.setToolTip('Turns off mask visibility so that you can see the results faster')
        hide_mask_cb.setChecked(self.variables['hide_mask_on_gen'])
        hide_mask_cb.stateChanged.connect(lambda: self._update_variable('hide_mask_on_gen', hide_mask_cb.isChecked()))
        if not self.settings_controller.get('hide_ui.inpaint_hide_mask'):
            mask_settings.layout().addWidget(hide_mask_cb)
        
        # The `not <setting>` is a bit confusing, but it makes for an easier time understanding the final layout
        mask_settings_shown = sum([not self.settings_controller.get('hide_ui.inpaint_auto_update'), not self.settings_controller.get('hide_ui.inpaint_below_mask'), not self.settings_controller.get('hide_ui.inpaint_hide_mask')])
        if mask_settings_shown == 1:
            self.layout().addWidget(mask_settings)
        elif mask_settings_shown > 1:
            ms_cw = CollapsibleWidget('Mask Settings', mask_settings)
            self.layout().addWidget(ms_cw)
        # else, nothing to add

        form = QWidget()
        form.setLayout(QFormLayout())
        form.layout().setContentsMargins(0,0,0,0)

        # mask blur
        blur_box = QSpinBox()
        blur_box.setMinimum(0)
        blur_box.setMaximum(64)
        blur_box.setValue(self.variables['mask_blur'])
        blur_box.valueChanged.connect(lambda: self._update_variable('mask_blur', blur_box.value()))
        # blur_box.setValue(self.settings_controller.get('inpaint.mask_blur'))
        # blur_box.valueChanged.connect(lambda: self.settings_controller.set('inpaint.mask_blur', blur_box.value()))
        form.layout().addRow('Mask Blur', blur_box)

        # mask mode = inpainting_mask_invert (0 = inpaint masked, 1 = inpaint not masked)
        mask_mode_options = [
            'Inpaint masked',
            'Inpaint not masked',
        ]
        mask_mode_select = QComboBox()
        mask_mode_select.addItems(mask_mode_options)
        mask_mode_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        mask_mode_select.setCurrentIndex(self.variables['mask_mode'])
        mask_mode_select.currentIndexChanged.connect(lambda: self._update_variable('mask_mode', mask_mode_select.currentIndex()))
        # mask_mode_select.setCurrentIndex(self.settings_controller.get('inpaint.mask_mode'))
        # mask_mode_select.currentIndexChanged.connect(lambda: self.settings_controller.set('inpaint.mask_mode', mask_mode_select.currentIndex()))
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
        mask_content_select.setCurrentIndex(self.variables['masked_content'])
        mask_content_select.currentIndexChanged.connect(lambda: self._update_variable('masked_content', mask_content_select.currentIndex()))
        # mask_content_select.setCurrentIndex(self.settings_controller.get('inpaint.masked_content'))
        # mask_content_select.currentIndexChanged.connect(lambda: self.settings_controller.set('inpaint.masked_content', mask_content_select.currentIndex()))
        form.layout().addRow('Masked Content', mask_content_select)

        # Inpaint Area = inpaint_full_res (0 = whole picture, 1 = only masked)
        inpaint_area_options = [
            'Whole Picture',
            'Only Masked',
        ]
        inpaint_select = QComboBox()
        inpaint_select.addItems(inpaint_area_options)
        inpaint_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        inpaint_select.setCurrentIndex(self.variables['inpaint_area'])
        inpaint_select.currentIndexChanged.connect(lambda: self._update_variable('inpaint_area', inpaint_select.currentIndex()))
        # inpaint_select.setCurrentIndex(self.settings_controller.get('inpaint.inpaint_area'))
        # inpaint_select.currentIndexChanged.connect(lambda: self.settings_controller.set('inpaint.inpaint_area', inpaint_select.currentIndex()))
        form.layout().addRow('Inpaint Area', inpaint_select)

        # Only masked padding, pixels (inpaint_full_res_padding)
        padding_box = QSpinBox()
        padding_box.setMinimum(0)
        padding_box.setMaximum(64)
        padding_box.setValue(self.variables['mask_padding'])
        padding_box.valueChanged.connect(lambda: self._update_variable('mask_padding', padding_box.value()))
        # padding_box.setValue(self.settings_controller.get('inpaint.padding'))
        # padding_box.valueChanged.connect(lambda: self.settings_controller.set('inpaint.padding', padding_box.value()))
        form.layout().addRow('Only masked padding', padding_box)

        # self.layout().addWidget(form)
        cw = CollapsibleWidget('Inpaint Settings', form)
        self.layout().addWidget(cw)


    def _update_variable(self, key, value):
        self.variables[key] = value

    def update_size_dict(self, mode='canvas'):
        if mode == 'selection':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_selection_bounds()
        if mode == 'layer':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_layer_bounds()
        if mode == 'canvas':
            self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'] = self.kc.get_canvas_bounds()

    def update_preview_icons(self):
        self.preview_list.clear()
        icon = QIcon(QPixmap.fromImage(self.image))
        self.preview_list.addItem(QListWidgetItem(icon, 'Image'))
        mask_icon = QIcon(QPixmap.fromImage(self.mask))
        self.preview_list.addItem(QListWidgetItem(mask_icon, 'Mask'))

    def update_mask_only(self, mode='canvas'):
        self.update_size_dict(mode)
        self.mask, _ = self.kc.get_mask_and_image(mode)
        self.update_preview_icons()
        

    def get_mask_and_img(self, mode='canvas'):
        self.selection_mode = mode
        self.update_size_dict(mode)

        self.mask_uuid = self.kc.get_active_layer_uuid()
        self.mask, self.image = self.kc.get_mask_and_image(mode)
        self.update_preview_icons()

    def save_settings(self):
        self.settings_controller.set('inpaint.mask_blur', self.variables['mask_blur'])
        self.settings_controller.set('inpaint.mask_mode', self.variables['mask_mode'])
        self.settings_controller.set('inpaint.masked_content', self.variables['masked_content'])
        self.settings_controller.set('inpaint.inpaint_area', self.variables['inpaint_area'])
        self.settings_controller.set('inpaint.padding', self.variables['mask_padding'])
        self.settings_controller.set('inpaint.auto_update_mask', self.variables['auto_update_mask'])
        self.settings_controller.set('inpaint.results_below_mask', self.variables['results_below_mask'])
        self.settings_controller.set('inpaint.hide_mask_on_gen', self.variables['hide_mask_on_gen'])
        self.settings_controller.save()

    def get_generation_data(self):
        data = {
            'mask_blur': self.variables['mask_blur'],
            'inpainting_mask_invert': self.variables['mask_mode'],
            'inpainting_fill': self.variables['masked_content'],
            'inpaint_full_res': self.variables['inpaint_area'],
            'inpaint_full_res_padding': self.variables['mask_padding'], # IDK what this actually does
        }
        # data = {
        #     'mask_blur': self.settings_controller.get('inpaint.mask_blur'),
        #     'inpainting_mask_invert': self.settings_controller.get('inpaint.mask_mode'),
        #     'inpainting_fill': self.settings_controller.get('inpaint.masked_content'),
        #     'inpaint_full_res': self.settings_controller.get('inpaint.inpaint_area'),
        #     'inpaint_full_res_padding': self.settings_controller.get('inpaint.padding'), # IDK what this actually does
        # }
        self.save_settings()

        if self.variables['auto_update_mask'] and self.mask_uuid is not None:
            # Auto-update the mask
            self.kc.set_layer_uuid_as_active(self.mask_uuid)
            if self.selection_mode is 'selection':
                s_x, s_y, s_w, s_h = self.kc.get_selection_bounds()
                if s_w == 0 and s_h == 0:
                    # The selection was cleared, fallback to using the canvas instead
                    self.selection_mode = 'canvas'
                    self.get_mask_and_img(mode=self.selection_mode)
            # self.get_mask_and_img(mode=self.selection_mode)
            self.update_mask_only(mode=self.selection_mode)


        if self.image is None:
            s_x, s_y, s_w, s_h = self.kc.get_selection_bounds()
            if s_w > 0 and s_h > 0:
                self.get_mask_and_img(mode="selection")
            else:
                self.get_mask_and_img(mode="canvas")

        if self.image is not None:
            data['inpaint_img'] = self.kc.qimage_to_b64_str(self.image)
        if self.mask is not None:
            data['mask_img'] = self.kc.qimage_to_b64_str(self.mask)

        if self.variables['results_below_mask']:
            # This data will be intercepted by the Generate widget
            data['CYANIC'] = {
                'results_below_layer_uuid': self.mask_uuid 
            }
        if self.variables['hide_mask_on_gen']:
            layer = self.kc.get_layer_from_uuid(self.mask_uuid)
            self.kc.set_layer_visible(layer, False)
        return data