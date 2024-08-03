from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController
from ..widgets import CyanicWidget, LabeledSlider

class DenoiseWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, include_start=False, include_end=False, settings_key='denoising_strength', default_value=0.7):
        super().__init__(settings_controller, None, QHBoxLayout)

        self.key = settings_key
        self.variables = {}
        self.variables[self.key] = default_value
        self.init_ui()
        self.set_widget_values()

    def init_ui(self):
        self.layout().addWidget(QLabel('Denoising Strength'))
        self.slider = LabeledSlider(0, 100, self.variables[self.key], as_percent=True)
        self.layout().addWidget(self.slider)

    def set_widget_values(self):
        self.slider.set_value(self.variables[self.key])

    def load_server_data(self):
        # Get the server's default denoise?
        pass

    def update_variables(self):
        self.variables[self.key] = self.slider.value()

    def get_value(self):
        self.update_variables()
        return self.variables[self.key]

    def save_settings(self):
        self.update_variables()
        super().save_settings()

    def get_generation_data(self):
        self.update_variables()
        data = self.variables
        self.save_settings()
        # self.settings_controller.save()
        return data
