from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CyanicWidget

class CFGWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api, QHBoxLayout)
        self.variables = {
            'cfg': 7
        }
        self.init_ui()
        self.set_widget_values()

    def load_server_data(self):
        pass

    def set_widget_values(self):
        self.cfg_entry.setValue(self.variables['cfg'])

    def init_ui(self):
        self.layout().addWidget(QLabel('CFG Scale'))

        self.cfg_entry = QDoubleSpinBox()
        self.cfg_entry.wheelEvent = lambda event : None
        self.cfg_entry.setMinimum(0.0)
        self.cfg_entry.setMaximum(30.0)
        # self.cfg_entry.setValue(self.variables['cfg'])
        self.cfg_entry.setSingleStep(0.1)
        self.cfg_entry.valueChanged.connect(lambda: self._update_variable('cfg', self.cfg_entry.value()))
        self.layout().addWidget(self.cfg_entry)

    def _update_variable(self, key, value):
        self.variables[key] = round(value, 2)

    def save_settings(self):
        self.settings_controller.set('cfg', self.variables['cfg'])
        # self.settings_controller.save()
    
    def get_generation_data(self):
        data = {
            'cfg_scale': self.variables['cfg']
        }
        self.save_settings()
        return data