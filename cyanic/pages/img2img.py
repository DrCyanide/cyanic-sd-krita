from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import *

class Img2ImgPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.kc = KritaController()
        self.size_dict = {"x":0,"y":0,"w":0,"h":0}
        self.setLayout(QVBoxLayout())

        self.img_in = ImageInWidget(self.settings_controller, self.api, 'img2img_img', self.size_dict)
        self.layout().addWidget(self.img_in)

        self.color_correction = ColorCorrectionWidget(self.settings_controller, self.api)
        if not self.settings_controller.get('hide_ui_color_correction'):
            self.layout().addWidget(self.color_correction)

        self.denoise_widget = DenoiseWidget(self.settings_controller)
        if not self.settings_controller.get('hide_ui_denoise'):
            self.layout().addWidget(self.denoise_widget)

        self.model_widget = ModelsWidget(self.settings_controller, self.api)
        self.layout().addWidget(self.model_widget)

        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'img2img')
        self.layout().addWidget(self.prompt_widget)

        self.batch_widget = BatchWidget(self.settings_controller, self.api)
        if not self.settings_controller.get('hide_ui_batch'):
            self.layout().addWidget(self.batch_widget)

        self.cfg_widget = CFGWidget(self.settings_controller, self.api)
        if not self.settings_controller.get('hide_ui_cfg'):
            self.layout().addWidget(self.cfg_widget)

        self.seed_widget = SeedWidget(self.settings_controller)
        seed_collapsed = CollapsibleWidget('Seed Details', self.seed_widget)
        if not self.settings_controller.get('hide_ui_seed'):
            self.layout().addWidget(seed_collapsed)

        self.extension_widget = ExtensionWidget(self.settings_controller, self.api)
        extension_collapsed = CollapsibleWidget('Extensions', self.extension_widget)
        if not self.settings_controller.get('hide_ui_extensions'):
            self.layout().addWidget(extension_collapsed)

        if not self.settings_controller.get('hide_ui_interrogate_img2img'):
            self.interrogate_model_widget = InterrogateModelWidget(self.settings_controller, self.api, self.size_dict, True)
            if not self.settings_controller.get('hide_ui_interrogate_model'):
                self.layout().addWidget(self.interrogate_model_widget)

            self.interrogate_widget = InterrogateWidget(self.settings_controller, self.api, self.interrogate_model_widget, self.prompt_widget, self.img_in, self.size_dict)
            self.layout().addWidget(self.interrogate_widget)
        
        self.generate_widget = GenerateWidget(self.settings_controller, self.api, [self.img_in, self.color_correction, self.denoise_widget, self.model_widget, self.prompt_widget, self.batch_widget, self.cfg_widget, self.seed_widget, self.extension_widget], 'img2img', self.size_dict)
        self.layout().addWidget(self.generate_widget)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def update(self):
        super().update()
