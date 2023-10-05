from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from enum import Enum
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import PromptWidget, CollapsibleWidget

class ADetailerExtension(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.units = []

        server_supported = self.api.script_installed('adetailer')
        if not server_supported:
            error = QLabel('Host "%s" does not have ADetailer installed' % self.api.host)
            website = QLabel('Get it from https://github.com/Bing-su/adetailer')
            self.layout().addWidget(error)
            self.layout().addWidget(website)
            return

        # Checkbox to Enable
        self.enable_cb = QCheckBox('Enable')
        self.layout().addWidget(self.enable_cb)

        # Model Select
        models = [ # Assuming these are standard with the install... there's no API to check what's available
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
        self.model_select = QComboBox()
        self.model_select.addItems(models)
        self.model_select.setCurrentText(models[0])
        self.model_select.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.model_select.setMaxVisibleItems(5) # Suppose to limit the number of visible options
        self.model_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.layout().addWidget(self.model_select)


        # Prompts
        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'ad_')
        self.layout().addWidget(self.prompt_widget)

        # ... a ton of settings I honestly never used.
        # Although there is a use steps option that might make it work as a post-processing...

    def get_generation_data(self):
        # https://github.com/Bing-su/adetailer/wiki/API
        if not self.enable_cb.isChecked():
            return {}
        prompt_data = self.prompt_widget.get_generation_data()
        data = {
            'alwayson_scripts': {
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
        }
        return data
