from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import PromptWidget, SeedWidget, CollapsibleWidget, ModelsWidget, GenerateWidget, ExtensionWidget

class Txt2ImgPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.kc = KritaController()
        self.is_generating = False
        self.setLayout(QVBoxLayout())

        self.model_widget = ModelsWidget(self.settings_controller, self.api)
        self.layout().addWidget(self.model_widget)

        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'txt2img')
        self.layout().addWidget(self.prompt_widget)

        
        self.seed_widget = SeedWidget()
        seed_collapsed = CollapsibleWidget('Seed Details', self.seed_widget)
        self.layout().addWidget(seed_collapsed)

        self.extension_widget = ExtensionWidget(self.settings_controller, self.api)
        extension_collapsed = CollapsibleWidget('Extensions', self.extension_widget)
        self.layout().addWidget(extension_collapsed)

        self.generate_widget = GenerateWidget(self.settings_controller, self.api, [self.model_widget, self.prompt_widget, self.seed_widget, self.extension_widget], 'txt2img')
        self.layout().addWidget(self.generate_widget)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def update(self):
        super().update()
