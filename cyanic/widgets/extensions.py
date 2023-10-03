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

        self.controlnet_widget = ControlNetExtension(self.settings_controller, self.api)
        controlnet_collapse = CollapsibleWidget('ControlNet', self.controlnet_widget)
        self.layout().addWidget(controlnet_collapse)

    def get_generation_data(self):
        data = {}
        # Go through each widget get their data
        data.update(self.controlnet_widget.get_generation_data())
        return data
