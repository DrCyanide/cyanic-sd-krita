
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController
from ..sdapi_v1 import SDAPI
from ..widgets import CyanicWidget

class ColorCorrectionWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, include_start=False, include_end=False):
        super().__init__(settings_controller, api)
        self.variables = {
            'color_correction': False,
        }
        self.init_ui()
        self.set_widget_values()

    def init_ui(self):
        # self.color_correct = self.settings_controller.get('color_correction')

        # Match Image Colors
        self.match_colors = QCheckBox('Match Image Colors')
        # self.match_colors.setChecked(self.settings_controller.get('color_match'))
        self.match_colors.toggled.connect(lambda: self._update_variable('color_correction', self.match_colors.isChecked()))
        self.layout().addWidget(self.match_colors)

    def set_widget_values(self):
        self.match_colors.setChecked(self.settings_controller.get('color_match'))

    # def save_settings(self):
        # self.settings_controller.set('color_match', self.color_correct) # Was this a typo?

    def load_server_data(self):
        pass

    def get_generation_data(self):
        # data = {
        #     'color_correction': self.color_correct,
        # }
        data = self.variables
        self.save_settings()
        # self.settings_controller.save()
        return data