from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import *
from . import CyanicPage

class Img2ImgPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.size_dict = {"x":0,"y":0,"w":0,"h":0}
        self.init_ui()
        self.load_all_settings()
        self.handle_hidden()

    def init_ui(self):
        # self.img_in = ImageInWidget(self.settings_controller, self.api, 'img2img_img', self.size_dict)
        self.img_in = ImageInWidget(self.settings_controller, self.api, 'img2img_img', 'img2img', self.size_dict)
        self.cyanic_widgets.append(self.img_in)
        self.layout().addWidget(self.img_in)

        self.color_correction = ColorCorrectionWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.color_correction)
        self.layout().addWidget(self.color_correction)

        self.denoise_widget = DenoiseWidget(self.settings_controller)
        self.cyanic_widgets.append(self.denoise_widget)
        self.layout().addWidget(self.denoise_widget)

        self.model_widget = ModelsWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.model_widget)
        self.layout().addWidget(self.model_widget)

        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'img2img')
        self.cyanic_widgets.append(self.prompt_widget)
        self.layout().addWidget(self.prompt_widget)

        self.batch_widget = BatchWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.batch_widget)
        self.layout().addWidget(self.batch_widget)

        self.cfg_widget = CFGWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.cfg_widget)
        self.layout().addWidget(self.cfg_widget)

        self.seed_widget = SeedWidget(self.settings_controller)
        self.cyanic_widgets.append(self.seed_widget)
        self.seed_collapsed = CollapsibleWidget('Seed Details', self.seed_widget)
        self.layout().addWidget(self.seed_collapsed)

        self.extension_widget = ExtensionWidget(self.settings_controller, self.api)
        self.cyanic_widgets.append(self.extension_widget)
        self.extension_collapsed = CollapsibleWidget('Extensions', self.extension_widget)
        self.layout().addWidget(self.extension_collapsed)

        # Interrogate was originally designed by tectin0 - https://github.com/DrCyanide/cyanic-sd-krita/pull/29
        # They don't contribute to get_generation_data(), but they do need to sync with API and Settings changes
        self.interrogate_model_widget = InterrogateModelWidget(self.settings_controller, self.api, self.size_dict, True)
        self.cyanic_widgets.append(self.interrogate_model_widget)
        self.layout().addWidget(self.interrogate_model_widget)

        self.interrogate_widget = InterrogateWidget(self.settings_controller, self.api, self.interrogate_model_widget, self.prompt_widget, self.img_in, self.size_dict)
        self.cyanic_widgets.append(self.interrogate_widget)
        self.layout().addWidget(self.interrogate_widget)

        self.generate_widget = GenerateWidget(self.settings_controller, self.api, self.cyanic_widgets, 'img2img', self.size_dict)
        self.layout().addWidget(self.generate_widget)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def handle_hidden(self):
        self.color_correction.setHidden(self.settings_controller.get('hide_ui_color_correction'))
        self.denoise_widget.setHidden(self.settings_controller.get('hide_ui_denoise'))
        self.batch_widget.setHidden(self.settings_controller.get('hide_ui_batch'))
        self.cfg_widget.setHidden(self.settings_controller.get('hide_ui_cfg'))
        self.seed_collapsed.setHidden(self.settings_controller.get('hide_ui_seed'))
        self.extension_collapsed.setHidden(self.settings_controller.get('hide_ui_extensions'))

        if self.settings_controller.get('hide_ui_interrogate_img2img'):
            self.interrogate_model_widget.setHidden(True)
            self.interrogate_widget.setHidden(True)
        else:
            self.interrogate_model_widget.setHidden('hide_ui_interrogate_model')
            self.interrogate_widget.setHidden(False)


    def update(self):
        super().update()
