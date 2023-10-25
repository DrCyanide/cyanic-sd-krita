from PyQt5.QtWidgets import *

from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController

class BatchWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {
            'batch_count': self.settings_controller.get('batch.count'),
            'batch_size': self.settings_controller.get('batch.size'),
        }

        self.draw_ui()

    def draw_ui(self):
        count_spin = QSpinBox()
        count_spin.setMinimum(1)
        count_spin.setMaximum(16)
        count_spin.setValue(self.variables['batch_count'])
        count_spin.valueChanged.connect(lambda: self._update_variable('batch_count', count_spin.value()))

        size_spin = QSpinBox()
        size_spin.setMinimum(1)
        size_spin.setMaximum(8)
        size_spin.setValue(self.variables['batch_size'])
        count_spin.valueChanged.connect(lambda: self._update_variable('batch_size', size_spin.value()))

        self.layout().addWidget(QLabel('Batch Count'))
        self.layout().addWidget(count_spin)
        self.layout().addWidget(QLabel('Batch Size'))
        self.layout().addWidget(size_spin)

    def _update_variable(self, key, value):
        self.variables[key] = value

    def save_settings(self):
        self.settings_controller.set('batch.count', self.variables['batch_count'])
        self.settings_controller.set('batch.size', self.variables['batch_size'])

    def get_generation_data(self):
        data = {
            'batch_count': self.variables['batch_count'],
            'batch_size': self.variables['batch_size'], # n_iter in the API
        }
        self.save_settings()
        return data