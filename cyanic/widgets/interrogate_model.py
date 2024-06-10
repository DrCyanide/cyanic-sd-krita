import select
from PyQt5.QtWidgets import *
from krita import QTimer
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from . import CyanicWidget

# Interrogate was originally designed by tectin0 - https://github.com/DrCyanide/cyanic-sd-krita/pull/29
class InterrogateModelWidget(CyanicWidget):
    def __init__(
        self,
        settings_controller: SettingsController,
        api: SDAPI,
        size_dict: dict,
        hide_prompt_mode: bool = False,
    ):
        super().__init__(settings_controller, api)
        self.size_dict = size_dict
        self.hide_prompt_mode = hide_prompt_mode

        self.variables = {
            "interrogate_model": "clip",
            "interrogate_prompt_mode": "img2img",  # txt2img / img2img / inpaint / adetailer
        }

        # TODO: clip download can fail very easily -> then the button just does nothing and the user has no idea why | check if the model was downloaded successfully?
        self.models = ["clip"]

        self.init_ui()
        self.set_widget_values()

    def load_server_data(self):
        self.models = ['clip']
        # check if deepdanbooru is installed
        # TODO: add info that deepdanbooru is not installed but could be used?
        if "deepbooru_sort_alpha" in self.api.default_settings.keys() and self.api.default_settings["deepbooru_sort_alpha"]:
            self.models.append("deepdanbooru")
        else:
            # Deepdanbooru not installed, so have to go back to Clip
            self.variables['interrogate_prompt_mode'] = 'clip'

    def set_widget_values(self):
        self.model_box.setCurrentText(self.variables["interrogate_model"])
        self.prompt_mode_box.setCurrentText(self.variables["interrogate_prompt_mode"])


    def init_ui(self):
        select_form = QWidget()
        select_form.setLayout(QFormLayout())
        select_form.layout().setContentsMargins(0, 0, 0, 0)

        self.model_box = QComboBox()
        self.model_box.addItems(self.models)
        # self.model_box.setCurrentText(self.variables["interrogate_model"])
        self.model_box.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.model_box.setMaxVisibleItems(10)
        self.model_box.currentTextChanged.connect(
            lambda: self._update_variables("interrogate_model", self.model_box.currentText())
        )
        self.model_box.setToolTip("Interrogate Model")

        select_form.layout().addRow("Model", self.model_box)

        # TODO: maybe move prompt mode to own widget? InterrogateSettingsWidget?
        # might be more useful if there are more settings for the interrogate widget
        self.prompt_mode_box = QComboBox()
        self.prompt_mode_box.addItems(
            ["txt2img", "img2img", "inpaint", "adetailer"]
        )
        # self.prompt_mode_box.setCurrentText(self.variables["interrogate_prompt_mode"])
        self.prompt_mode_box.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.prompt_mode_box.setMaxVisibleItems(10)
        self.prompt_mode_box.currentTextChanged.connect(
            lambda: self._update_variables(
                "interrogate_prompt_mode", self.prompt_mode_box.currentText()
            )
        )
        self.prompt_mode_box.setToolTip(
            "Interrogate Prompt Mode (sync prompt with txt2img / img2img / inpaint / adetailer)"
        )
        if not self.hide_prompt_mode:
            select_form.layout().addRow("Prompt Mode", self.prompt_mode_box)

        self.layout().addWidget(select_form)

    def get_model(self):
        return self.variables["interrogate_model"]

    def get_prompt_mode(self):
        return self.variables["interrogate_prompt_mode"]

    def _update_variables(self, key, value):
        self.variables[key] = value
        # TODO: idk if that is a good place to save the settings
        self.save_settings()

    def handle_hidden(self):
        #self.settings_controller.get("hide_ui_interrogate_model") # This should be handled in the parent object
        pass 

    # Default CyanicWidget version should handle this
    # def save_settings(self):
    #     self.settings_controller.set("interrogate_model", self.variables["interrogate_model"])
    #     self.settings_controller.set(
    #         "interrogate_prompt_mode", self.variables["interrogate_prompt_mode"]
    #     )
    #     self.settings_controller.save()

    # Not needed, since interrogation operates separately from the generation
    def get_generation_data(self):
        return {}