from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController

class DenoiseWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, include_start=False, include_end=False):
        super().__init__()
        self.settings_controller = settings_controller
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        denoise_row = QWidget()
        denoise_row.setLayout(QHBoxLayout())
        denoise_row.layout().setContentsMargins(0,0,0,0)
        denoise_row.layout().addWidget(QLabel('Denoise Strength'))

        # Denoise label
        default_noise = self.settings_controller.get('defaults.denoise_strength')
        self.denoise_percent = QLabel('%s%%' % int(default_noise * 100))

        # Denoise Strength
        self.denoise_slider = QSlider(Qt.Horizontal)
        self.denoise_slider.setTickInterval(10)
        self.denoise_slider.setTickPosition(QSlider.TicksAbove)
        self.denoise_slider.setMinimum(0)
        self.denoise_slider.setMaximum(100)
        self.denoise_slider.setValue(int(default_noise * 100))
        self.denoise_slider.valueChanged.connect(lambda: self.denoise_percent.setText('%s%%' % self.denoise_slider.value()))

        denoise_row.layout().addWidget(self.denoise_slider)

        denoise_row.layout().addWidget(self.denoise_percent)
        self.layout().addWidget(denoise_row)

    def save_settings(self):
        denoise = self.denoise_slider.value() / 100
        self.settings_controller.set('defaults.denoise_strength', denoise)

    def get_generation_data(self):
        denoise = self.denoise_slider.value() / 100
        data = {
            'denoising_strength': denoise
        }
        self.save_settings()
        self.settings_controller.save()
        return data
