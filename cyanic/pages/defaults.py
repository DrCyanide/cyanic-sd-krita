from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import *
from . import CyanicPage

class DefaultsPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.variables = {
            # These are variables that can't be updated by importing their component widget
            # 'inpaint_mask_auto_update': self.settings_controller.get('inpaint_mask_auto_update'),
            # 'inpaint_mask_above_results': self.settings_controller.get('inpaint_mask_above_results'),
            # 'mask_hide_while_gen': self.settings_controller.get('inpaint_mask_hide_while_gen'),
            'inpaint_mask_auto_update': False,
            'inpaint_mask_above_results': True,
            'inpaint_mask_hide_while_gen': True,
        }
        self.server_supported = {
            'controlnet': self.api.script_installed('controlnet'),
            'adetailer': self.api.script_installed('adetailer'),
        }
        self.init_ui()

    def init_ui(self):
        # Models
        model_settings = QGroupBox('Model')
        model_settings.setLayout(QVBoxLayout())
        self.model_widget = ModelsWidget(self.settings_controller, self.api, ignore_hidden=True)
        self.cyanic_widgets.append(self.model_widget)
        model_settings.layout().addWidget(self.model_widget)
        self.layout().addWidget(model_settings)
        
        # Hires Fix
        hires_fix_settings = QGroupBox('Hires Fix')
        hires_fix_settings.setLayout(QVBoxLayout())
        self.hires_fix_widget = HiResFixWidget(self.settings_controller, self.api, ignore_hidden=True)
        self.cyanic_widgets.append(self.hires_fix_widget)
        hires_fix_settings.layout().addWidget(self.hires_fix_widget)
        self.layout().addWidget(hires_fix_settings)

        # CFG
        cfg_settings = QGroupBox('CFG Scale')
        cfg_settings.setLayout(QVBoxLayout())
        self.cfg_widget = CFGWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.cfg_widget)
        cfg_settings.layout().addWidget(self.cfg_widget)
        self.layout().addWidget(cfg_settings)

        # Img2Img and Inpainting
        img2img_settings = QGroupBox('Img2Img and Inpainting')
        img2img_settings.setLayout(QVBoxLayout())
        self.denoise_widget = DenoiseWidget(self.settings_controller)
        self.cyanic_widgets.append(self.denoise_widget)
        img2img_settings.layout().addWidget(self.denoise_widget)
        self.color_correction = ColorCorrectionWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.color_correction)
        img2img_settings.layout().addWidget(self.color_correction)
        self.layout().addWidget(img2img_settings)

        # Inpaint Only settings
        inpaint_settings = QGroupBox('Inpainting')
        inpaint_settings.setLayout(QVBoxLayout())
        # TODO: add Mask Blur, Mask Mode, Masked Content, Inpaint Area
            # Update Mask before Generating
        self.mask_auto_update_cb = QCheckBox('Update mask before generating')
        self.mask_auto_update_cb.setToolTip('Will remember the last layer used as a mask and use the current state of that layer whenever the "Generate" button is clicked')
        self.mask_auto_update_cb.setChecked(self.variables['inpaint_mask_auto_update'])
        self.mask_auto_update_cb.stateChanged.connect(lambda: self._update_variable('inpaint_mask_auto_update', self.mask_auto_update_cb.isChecked()))
        inpaint_settings.layout().addWidget(self.mask_auto_update_cb)
            # Add Results below Mask
        self.mask_above_results_cb = QCheckBox('Mask above results')
        self.mask_above_results_cb.setToolTip('Will insert the results as a new layer below the mask')
        self.mask_above_results_cb.setChecked(self.variables['inpaint_mask_above_results'])
        self.mask_above_results_cb.stateChanged.connect(lambda: self._update_variable('inpaint_mask_above_results', self.mask_above_results_cb.isChecked()))
        inpaint_settings.layout().addWidget(self.mask_above_results_cb)
            # Hide mask on generation
        self.hide_mask_cb = QCheckBox('Hide mask when generating')
        self.hide_mask_cb.setToolTip('Turns off mask visibility so that you can see the results faster')
        self.hide_mask_cb.setChecked(self.variables['inpaint_mask_hide_while_gen'])
        self.hide_mask_cb.stateChanged.connect(lambda: self._update_variable('inpaint_mask_hide_while_gen', self.hide_mask_cb.isChecked()))
        inpaint_settings.layout().addWidget(self.hide_mask_cb)
            # Soft Inpaint
        soft_inpaint_settings = QGroupBox('Soft Inpaint Settings')
        soft_inpaint_settings.setLayout(QVBoxLayout())
        self.soft_inpaint = SoftInpaintWidget(self.settings_controller, self.api, settings_only=True)
        soft_inpaint_settings.layout().addWidget(self.soft_inpaint)
        inpaint_settings.layout().addWidget(soft_inpaint_settings)

        self.layout().addWidget(inpaint_settings)

        # Batch
        batch_settings = QGroupBox('Batch')
        batch_settings.setLayout(QVBoxLayout())
        self.batch_widget = BatchWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.batch_widget)
        batch_settings.layout().addWidget(self.batch_widget)
        self.layout().addWidget(batch_settings)

        # Seed
        seed_settings = QGroupBox('Seed')
        seed_settings.setLayout(QVBoxLayout())
        self.seed_widget = SeedWidget(self.settings_controller)
        self.cyanic_widgets.append(self.seed_widget)
        seed_settings.layout().addWidget(self.seed_widget)
        self.layout().addWidget(seed_settings)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def _update_variable(self, key, value):
        self.variables[key] = value

    def set_widget_values(self):
        # For variables that don't have a dedicated widget
        self.mask_auto_update_cb.setChecked(self.variables['inpaint_mask_auto_update'])
        self.mask_above_results_cb.setChecked(self.variables['inpaint_mask_above_results'])
        self.hide_mask_cb.setChecked(self.variables['inpaint_mask_hide_while_gen'])

    def load_all_settings(self):
        super().load_all_settings()
        self.load_settings()

    def load_settings(self):
        super().load_settings()
        for widget in self.cyanic_widgets:
            widget.load_settings()
        for key in self.variables:
            self.variables[key] = self.settings_controller.get(key)
        self.set_widget_values()

    def save_settings(self):
        super().save_settings()
        for key in self.variables:
            self.settings_controller.set(key, self.variables[key])