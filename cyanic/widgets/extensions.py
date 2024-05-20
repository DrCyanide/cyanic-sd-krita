from PyQt5.QtWidgets import *
from ..widgets import CollapsibleWidget
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..extension_widgets import *

class ExtensionWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.setLayout(QVBoxLayout())
        # self.layout().setContentsMargins(0,0,0,0)
        self.server_supported = {
            'controlnet': self.api.script_installed('controlnet'),
            'adetailer': self.api.script_installed('adetailer'),
        }
        
        
        self.controlnet_widget = ControlNetExtension(self.settings_controller, self.api)
        controlnet_collapse = CollapsibleWidget('ControlNet', self.controlnet_widget)
        if self.server_supported['controlnet'] and not 'controlnet' in self.settings_controller.get('hide_ui_hidden_extensions'):
            self.layout().addWidget(controlnet_collapse)

        self.adetailer_widget = ADetailerExtension(self.settings_controller, self.api)
        adetailer_collapse = CollapsibleWidget('ADetailer', self.adetailer_widget)
        if self.server_supported['adetailer'] and not 'adetailer' in self.settings_controller.get('hide_ui_hidden_extensions'):
            self.layout().addWidget(adetailer_collapse)

        # TODO: Add some message about no supported extensions

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
