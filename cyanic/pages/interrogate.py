from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from . import CyanicPage
from ..widgets import (
    InterrogateWidget,
    InterrogateModelWidget,
    ImageInWidget,
    PromptWidget,
)

# Interrogate was originally designed by tectin0 - https://github.com/DrCyanide/cyanic-sd-krita/pull/29
class InterrogatePage(CyanicPage):
    def __init__(self, settings_controller: SettingsController, api: SDAPI):
        super().__init__(settings_controller, api)
        self.size_dict = {"x": 0, "y": 0, "w": 0, "h": 0}
        self.prompt_mode = "img2img" # Probably not necessary
        self.init_ui()
  
    def load_settings(self):
        self.prompt_mode = self.settings_controller.get("interrogate_prompt_mode")
        super().load_settings()

    def init_ui(self):
        self.img_in = ImageInWidget(
            # self.settings_controller, self.api, "img2img_img", self.size_dict
            self.settings_controller, self.api, "img2img_img", "img2img", self.size_dict
        )
        self.cyanic_widgets.append(self.img_in)
        self.layout().addWidget(self.img_in)

        self.prompt_widget = PromptWidget(
            self.settings_controller,
            self.api,
            self.prompt_mode,
        )
        self.cyanic_widgets.append(self.prompt_widget)
        self.layout().addWidget(self.prompt_widget)

        self.interrogate_model_widget = InterrogateModelWidget(
            self.settings_controller, self.api, self.size_dict
        )
        self.cyanic_widgets.append(self.interrogate_model_widget)
        self.layout().addWidget(self.interrogate_model_widget)

        self.interrogate_widget = InterrogateWidget(
            self.settings_controller,
            self.api,
            self.interrogate_model_widget,
            self.prompt_widget,
            self.img_in,
        )
        self.layout().addWidget(self.interrogate_widget)

        # TODO: add a setting to decide if the interrogated text should replace, append or prepend the current prompt

        self.layout().addStretch()  # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def update(self):
        super().update()
