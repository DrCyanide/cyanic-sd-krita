from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import PromptWidget, SeedWidget, CollapsibleWidget, ModelsWidget, GenerateWidget, ImageInWidget, DenoiseWidget, ExtensionWidget

class Img2ImgPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.kc = KritaController()
        self.is_generating = False
        self.setLayout(QVBoxLayout())

        self.img_in = ImageInWidget(self.settings_controller, self.api, 'img2img_img')
        self.layout().addWidget(self.img_in)

        self.denoise_widget = DenoiseWidget(self.settings_controller)
        self.layout().addWidget(self.denoise_widget)

        self.model_widget = ModelsWidget(self.settings_controller, self.api)
        self.layout().addWidget(self.model_widget)

        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'img2img')
        self.layout().addWidget(self.prompt_widget)

        self.seed_widget = SeedWidget()
        seed_collapsed = CollapsibleWidget('Seed Details', self.seed_widget)
        self.layout().addWidget(seed_collapsed)

        self.extension_widget = ExtensionWidget(self.settings_controller, self.api)
        extension_collapsed = CollapsibleWidget('Extensions', self.extension_widget)
        self.layout().addWidget(extension_collapsed)

        self.generate_widget = GenerateWidget(self.settings_controller, self.api, [self.img_in, self.denoise_widget, self.model_widget, self.prompt_widget, self.seed_widget, self.extension_widget], 'img2img')
        self.layout().addWidget(self.generate_widget)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def update(self):
        super().update()
