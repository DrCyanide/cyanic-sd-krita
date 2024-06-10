from PyQt5.QtWidgets import *
from ..widgets import CollapsibleWidget, CyanicWidget
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..extension_widgets import *

class ExtensionWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.server_supported = {
            'controlnet': False, 
            'adetailer': False,
        }
        self.init_ui()
        self.set_widget_values()
        
    def load_server_data(self):
        self.server_supported['controlnet'] = self.api.script_installed('controlnet')
        self.server_supported['adetailer'] = self.api.script_installed('adetailer')

    def set_widget_values(self):
        pass

    def init_ui(self):
        self.controlnet_widget = ControlNetExtension(self.settings_controller, self.api)
        self.controlnet_collapse = CollapsibleWidget('ControlNet', self.controlnet_widget)
        self.layout().addWidget(self.controlnet_collapse)    

        self.adetailer_widget = ADetailerExtension(self.settings_controller, self.api)
        self.adetailer_collapse = CollapsibleWidget('ADetailer', self.adetailer_widget)
        self.layout().addWidget(self.adetailer_collapse)

        # Feel free to add more extensions

    def handle_hidden(self):
        self.controlnet_collapse.setHidden(self.server_supported['controlnet'] and not 'controlnet' in self.settings_controller.get('hide_ui_hidden_extensions'))
        self.adetailer_collapse.setHidden(self.server_supported['adetailer'] and not 'adetailer' in self.settings_controller.get('hide_ui_hidden_extensions'))

    def get_generation_data(self):
        data = {}
        # Go through each widget get their data
        if self.server_supported['controlnet']:
            if not 'alwayson_scripts' in data.keys():
                data['alwayson_scripts'] = {}
            data['alwayson_scripts'].update(self.controlnet_widget.get_generation_data())

        if self.server_supported['adetailer']:
            if not 'alwayson_scripts' in data.keys():
                data['alwayson_scripts'] = {}
            data['alwayson_scripts'].update(self.adetailer_widget.get_generation_data())
        return data

    def save_settings(self):
        if self.server_supported['controlnet']:
            self.controlnet_widget.save_settings()

        if self.server_supported['adetailer']:
            self.adetailer_widget.save_settings()