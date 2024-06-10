from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import *
from . import CyanicPage

class InpaintPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.size_dict = {"x":0,"y":0,"w":0,"h":0}
        self.soft_inpaint_installed = False
        self.init_ui()

    def init_ui(self):
        self.mask_widget = MaskWidget(self.settings_controller, self.api, self.size_dict)
        self.cyanic_widgets.append(self.mask_widget)
        self.layout().addWidget(self.mask_widget)

        # This is an alwayson script, added in A1111 v1.8
        self.soft_inpaint_widget = SoftInpaintWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.soft_inpaint_widget)
        self.layout().addWidget(self.soft_inpaint_widget)

        self.color_correction = ColorCorrectionWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.color_correction)
        self.layout().addWidget(self.color_correction)

        self.denoise_widget = DenoiseWidget(self.settings_controller)
        self.cyanic_widgets.append(self.denoise_widget)
        self.layout().addWidget(self.denoise_widget)

        self.model_widget = ModelsWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.model_widget)
        self.layout().addWidget(self.model_widget)

        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'inpaint')
        self.cyanic_widgets.append(self.prompt_widget)
        self.layout().addWidget(self.prompt_widget)

        self.batch_widget = BatchWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.batch_widget)
        self.layout().addWidget(self.batch_widget)

        self.cfg_widget = CFGWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.cfg_widget)
        self.layout().addWidget(self.cfg_widget)

        self.seed_widget = SeedWidget(self.settings_controller)
        self.seed_collapsed = CollapsibleWidget('Seed Details', self.seed_widget)
        self.cyanic_widgets.append(self.seed_widget)
        self.layout().addWidget(self.seed_collapsed)

        self.extension_widget = ExtensionWidget(self.settings_controller, self.api)
        self.extension_collapsed = CollapsibleWidget('Extensions', self.extension_widget)
        self.cyanic_widgets.append(self.extension_widget)
        self.layout().addWidget(self.extension_collapsed)

        self.generate_widget = GenerateWidget(self.settings_controller, self.api, self.cyanic_widgets, 'inpaint', self.size_dict)
        self.layout().addWidget(self.generate_widget)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def handle_hidden(self):
        self.include_soft_inpaint = self.api.script_installed('soft inpainting')
        self.soft_inpaint_widget.setHidden(self.soft_inpaint_installed or self.settings_controller.get('hide_ui_soft_inpaint'))
        self.color_correction.setHidden(self.settings_controller.get('hide_ui_color_correction'))
        self.denoise_widget.setHidden(self.settings_controller.get('hide_ui_denoise'))
        self.batch_widget.setHidden(self.settings_controller.get('hide_ui_batch'))
        self.cfg_widget.setHidden(self.settings_controller.get('hide_ui_cfg'))
        self.seed_collapsed.setHidden(self.settings_controller.get('hide_ui_seed'))
        self.extension_collapsed.setHidden(self.settings_controller.get('hide_ui_extensions'))


    def update(self):
        super().update()
