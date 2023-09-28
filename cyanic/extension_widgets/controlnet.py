from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController

class ControlNetExtension(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.cnapi = ControlNetAPI(self.api)
        self.setLayout(QVBoxLayout())

    def display(self):
        server_supported = self.api.script_installed('controlnet')
        if not server_supported:
            error = QLabel('Host "%s" does not have ControlNet installed' % self.api.host)
            self.layout().addWidget(error)
            return

        # Else... everything...
        # Tabs for the units
        # KritaController select layer, get as a QImage
        # Enable button
        # PixelPerfect, Low VRAM, "allow preview"
        # ControlType
        # Preprocessor / Run Preprocessor
        # Model
        # Control Weight
        # Start/End Control Step
        # Control Mode (Balanced)
        # Resize Mode (Crop and Resize)



class ControlNetAPI():
    def __init__(self, api:SDAPI):
        self.api = api
        self.models = []
        self.module_list = []
        self.module_details = {}
        self.control_types = {}
        self.settings = {}

    def get_version(self):
        return self.api.get('/controlnet/version')
    
    def get_models(self):
        self.models = self.api.get('/controlnet/model_list?update=true')
        # return self.models 
    
    def get_modules(self):
        results = self.api.get('/controlnet/module_list')
        self.module_list = results['module_list']
        self.module_details = results['module_details']

    def get_control_types(self):
        self.control_types = self.api.get('/controlnet/control_types')['control_types']

    def get_settings(self):
        self.settings = self.api.get('/controlnet/settings')

    # def detect(self, images):