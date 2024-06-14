from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController
from ..widgets import CyanicWidget, LabeledSlider

class DenoiseWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, include_start=False, include_end=False):
        super().__init__(settings_controller, None, QHBoxLayout)
        self.variables = {
            'denoising_strength': 0.7,
        }
        self.init_ui()
        self.set_widget_values()

    def init_ui(self):
        self.layout().addWidget(QLabel('Denoising Strength'))
        self.slider = LabeledSlider(0, 100, self.variables['denoising_strength'], as_percent=True)
        self.layout().addWidget(self.slider)

    def set_widget_values(self):
        self.slider.set_value(self.variables['denoising_strength'])

    def load_server_data(self):
        # Get the server's default denoise?
        pass

    def update_variables(self):
        self.variables['denoising_strength'] = self.slider.value()

    def save_settings(self):
        self.update_variables()
        super().save_settings()

    def get_generation_data(self):
        self.update_variables()
        data = self.variables
        self.save_settings()
        # self.settings_controller.save()
        return data
