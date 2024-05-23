from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import *
from . import CyanicPage

class Txt2ImgPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)

    def init_ui(self):
        self.model_widget = ModelsWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.model_widget)
        self.layout().addWidget(self.model_widget)
        
        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'txt2img')
        self.cyanic_widgets.append(self.prompt_widget)
        self.layout().addWidget(self.prompt_widget)

        self.batch_widget = BatchWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.batch_widget)
        self.layout().addWidget(self.batch_widget)

        self.cfg_widget = CFGWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.cfg_widget)
        self.layout().addWidget(self.cfg_widget)

        self.seed_widget = SeedWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.seed_widget)
        self.seed_collapse = CollapsibleWidget('Seed Details', self.seed_widget)
        self.layout().addWidget(self.seed_collapse)

        self.hires_widget = HiResFixWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.hires_widget)
        self.hires_collapse = CollapsibleWidget('Hires Fix', self.hires_widget)
        self.layout().addWidget(self.hires_collapse)

        self.extension_widget = ExtensionWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.extension_widget)
        self.extension_collapse = CollapsibleWidget('Extensions', self.extension_widget)
        self.layout().addWidget(self.extension_collapse)

        self.generate_widget = GenerateWidget(self.settings_controller, self.api, self.cyanic_widgets, 'txt2img')
        self.layout().addWidget(self.generate_widget)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top
        self.handle_hidden()

    def handle_hidden(self):
        self.batch_widget.setHidden(self.settings_controller.get('hide_ui_batch'))
        self.cfg_widget.setHidden(self.settings_controller.get('hide_ui_cfg'))
        self.seed_collapse.setHidden(self.settings_controller.get('hide_ui_seed'))
        self.hires_collapse.setHidden(self.settings_controller.get('hide_ui_hires_fix'))
        self.extension_collapse.setHidden(self.settings_controller.get('hide_ui_extensions'))
