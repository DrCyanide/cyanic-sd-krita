from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import (
    InterrogateWidget,
    InterrogateModelWidget,
    ImageInWidget,
    PromptWidget,
)


class InterrogatePage(QWidget):
    def __init__(self, settings_controller: SettingsController, api: SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.kc = KritaController()
        self.size_dict = {"x": 0, "y": 0, "w": 0, "h": 0}
        self.setLayout(QVBoxLayout())

        self.img_in = ImageInWidget(
            self.settings_controller, self.api, "img2img_img", self.size_dict
        )
        self.layout().addWidget(self.img_in)

        prompt_mode = self.settings_controller.get("interrogate.prompt_mode")

        # TODO: probably not necessary?
        if not prompt_mode:
            prompt_mode = "img2img"
            self.settings_controller.set("interrogate.prompt_mode", prompt_mode)

        self.prompt_widget = PromptWidget(
            self.settings_controller,
            self.api,
            prompt_mode,
        )
        self.layout().addWidget(self.prompt_widget)

        self.interrogate_model_widget = InterrogateModelWidget(
            self.settings_controller, self.api, self.size_dict
        )
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
