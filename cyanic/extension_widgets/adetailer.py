from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from enum import Enum
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import PromptWidget, CollapsibleWidget, CyanicWidget

class ADetailerExtension(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.units = []
        self.enabled = False
        self.server_supported = False
        
        self.models = [ # Assuming these are standard with the install... there's no API to check what's available
            'face_yolov8n.pt',
            'face_yolov8s.pt',
            'hand_yolov8n.pt',
            'person_yolov8n-seg.pt',
            'person_yolov8s-seg.pt',
            'mediapipe_face_full',
            'mediapipe_face_short',
            'mediapipe_face_mesh',
            'mediapipe_face_mesh_eyes_only',
        ]
        
        self.init_ui()


    
    def init_ui(self):
        # server_supported = self.api.script_installed('adetailer')
        # if not server_supported:
        #     error = QLabel('Host "%s" does not have ADetailer installed' % self.api.host)
        #     website = QLabel('Get it from https://github.com/Bing-su/adetailer')
        #     self.layout().addWidget(error)
        #     self.layout().addWidget(website)
        #     return

        # Checkbox to Enable
        self.enable_cb = QCheckBox('Enable')
        self.enable_cb.stateChanged.connect(lambda: self.set_enabled(self.enable_cb.isChecked()))
        self.layout().addWidget(self.enable_cb)

        # Model Select
        self.model_select = QComboBox()
        self.model_select.wheelEvent = lambda event : None
        self.model_select.addItems(self.models)
        self.model_select.setCurrentText(self.models[0])
        self.model_select.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.model_select.setMaxVisibleItems(5) # Suppose to limit the number of visible options
        self.model_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.layout().addWidget(self.model_select)


        # Prompts
        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'adetailer')
        self.layout().addWidget(self.prompt_widget)

        # ... a ton of settings I never use...
        # A few more need to be added though
        # Although there is a use steps option that might make it work as a post-processing...

    def load_server_data(self):
        pass

    def set_enabled(self, value):
        self.enabled = value

    def get_generation_data(self):
        # https://github.com/Bing-su/adetailer/wiki/API
        if not self.enabled:
            return {}
        
        prompt_data = self.prompt_widget.get_generation_data()
        data = { # Whatever is requesting this data will have to add the `alwayson_scripts`, otherwise multiple extensions will delete each other
            'ADetailer': {
                'args': [
                    True, # Enabled... and technically optionall
                    {
                        'ad_model': self.model_select.currentText(),
                        'ad_prompt': prompt_data['prompt'],
                        'ad_negative_prompt': prompt_data['negative_prompt'],
                        # Many more args I'm skipping and using the defaults for
                    }
                    # Could add more tabs, just add their args down here in the same way
                ]
            }
        }
        self.prompt_widget.save_settings()
        return data
