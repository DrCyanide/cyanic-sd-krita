
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController

class ColorCorrectionWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, include_start=False, include_end=False):
        super().__init__()
        self.settings_controller = settings_controller
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.color_correct = self.settings_controller.get('color_correction')

        # Match Image Colors
        match_colors = QCheckBox('Match Image Colors')
        match_colors.setChecked(self.settings_controller.get('color_match'))
        match_colors.toggled.connect(lambda: self.update_match_colors(match_colors.isChecked()))
        self.layout().addWidget(match_colors)

    def update_match_colors(self, match):
        self.color_correct = match

    def save_settings(self):
        self.settings_controller.set('color_match', self.color_correct)

    def get_generation_data(self):
        data = {
            'color_correction': self.color_correct,
        }
        self.save_settings()
        self.settings_controller.save()
        return data