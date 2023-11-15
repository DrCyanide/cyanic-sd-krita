from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..krita_controller import KritaController
from ..settings_controller import SettingsController

class CFGWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.kc = KritaController()
        self.api = api
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {
            'cfg': self.settings_controller.get('defaults.cfg_scale'),
        }
        self.draw_ui()

    def draw_ui(self):
        self.layout().addWidget(QLabel('CFG Scale'))

        cfg_entry = QDoubleSpinBox()
        cfg_entry.setMinimum(0.0)
        cfg_entry.setMaximum(30.0)
        cfg_entry.setValue(self.variables['cfg'])
        cfg_entry.setSingleStep(0.1)
        cfg_entry.valueChanged.connect(lambda: self._update_variable('cfg', cfg_entry.value()))
        self.layout().addWidget(cfg_entry)

    def _update_variable(self, key, value):
        self.variables[key] = value

    def save_settings(self):
        self.settings_controller.set('defaults.cfg_scale', self.variables['cfg'])
        self.settings_controller.save()
    
    def get_generation_data(self):
        data = {
            'cfg_scale': self.variables['cfg']
        }
        self.save_settings()
        return data