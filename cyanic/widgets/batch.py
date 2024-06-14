from PyQt5.QtWidgets import *

from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CyanicWidget

class BatchWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api, QHBoxLayout)
        self.variables = {
            'batch_count': 1,
            'batch_size': 1,
        }
        self.init_ui()

    def load_server_data(self):
        pass

    def set_widget_values(self):
        self.count_spin.setValue(self.variables['batch_count'])
        self.size_spin.setValue(self.variables['batch_size'])

    def init_ui(self):
        self.count_spin = QSpinBox()
        self.count_spin.wheelEvent = lambda event : None
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(16)
        self.count_spin.setValue(self.variables['batch_count'])
        self.count_spin.valueChanged.connect(lambda: self._update_variable('batch_count', self.count_spin.value()))

        self.size_spin = QSpinBox()
        self.size_spin.wheelEvent = lambda event : None
        self.size_spin.setMinimum(1)
        self.size_spin.setMaximum(8)
        self.size_spin.setValue(self.variables['batch_size'])
        self.size_spin.valueChanged.connect(lambda: self._update_variable('batch_size', self.size_spin.value()))

        self.layout().addWidget(QLabel('Batch Count'))
        self.layout().addWidget(self.count_spin)
        self.layout().addWidget(QLabel('Batch Size'))
        self.layout().addWidget(self.size_spin)

    def _update_variable(self, key, value):
        self.variables[key] = value

    def save_settings(self):
        self.settings_controller.set('batch_count', self.variables['batch_count'])
        self.settings_controller.set('batch_size', self.variables['batch_size'])
        self.settings_controller.save()

    def get_generation_data(self):
        data = {
            'batch_count': self.variables['batch_count'],
            'batch_size': self.variables['batch_size'], # n_iter in the API
        }
        self.save_settings()
        return data