from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from . import CyanicPage
from ..widgets import PromptWidget

class PromptSettingsPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.variables = {
            'new_doc_prompt_mode': 'empty',
            'prompt_initial': '',
            'prompt_negative_initial': '',
            'prompt_history_max': 10,
            'prompt_share': True,
            'prompt_share_includes': [],
        }
        self.shared_prompt_btns = []
        self.log = {}
        self.init_ui()
        self.handle_hidden()

    def load_settings(self):
        # No widgets, so just do it manually
        for key in self.variables.keys():
            self.variables[key] = self.settings_controller.get(key)

        self.set_widget_values()

    def save_settings(self):
        # No widgets, so just do it manually
        data = self.prompt_widget.get_generation_data()
        self.variables['prompt_initial'] = data['prompt']
        self.variables['prompt_negative_initial'] = data['negative_prompt']

        shared = []
        for btn in self.shared_prompt_btns:
            label = btn.text().lower()
            # Was getting an odd bug where the values would be "&txt2img" or "i&mg2img"
            label = label.replace('&', '')
            if btn.isChecked():
                shared.append(label)

        self.variables['prompt_share_includes'] = shared

        for key in self.variables.keys():
            self.settings_controller.set(key, self.variables[key])

    def load_log(self):
        self.log = self.api.read_log()

    def init_ui(self):
        # Radio Button
        #   New documents start without a prompt
        #   New documents uses last opened documents prompts
        #   New documents use this initial prompt (show prompt widget)'
        self.radio_group = QButtonGroup()
        self.radio_group.setExclusive(True)
        self.radio_group.buttonClicked.connect(self.clicked_radio_btn)
        
        self.radio_btn_empty = QRadioButton("New docs start without prompt")
        self.radio_group.addButton(self.radio_btn_empty)
        self.layout().addWidget(self.radio_btn_empty)

        self.radio_btn_last_doc = QRadioButton("New docs use last opened doc's prompt")
        self.radio_group.addButton(self.radio_btn_last_doc)
        self.layout().addWidget(self.radio_btn_last_doc)

        self.radio_btn_init_prompt = QRadioButton("New docs use an initial prompt")
        self.radio_group.addButton(self.radio_btn_init_prompt)
        self.layout().addWidget(self.radio_btn_init_prompt)
        
        self.set_clicked_radio_btn(self.variables['new_doc_prompt_mode'])

        # PromptWidget
        self.layout().addWidget(QLabel('Initial Prompt'))
        self.prompt_widget = PromptWidget(self.settings_controller, self.api, 'initial', prompts_only=True)
        self.layout().addWidget(self.prompt_widget)

        # Prompt history length
        self.max_history_length = QSpinBox()
        self.max_history_length.setToolTip("How many prompts should be saved in the .kra file")
        self.max_history_length.setRange(0, 50)
        self.max_history_length.setValue(self.variables['prompt_history_max'])
        self.max_history_length.valueChanged.connect(self.updated_max_history)
        self.layout().addWidget(QLabel('Maximum Prompt History'))
        self.layout().addWidget(self.max_history_length)
        
        # Clear file prompt history
        self.clear_history_btn = QPushButton('Clear Saved Prompt History')
        self.clear_history_btn.clicked.connect(self.clear_prompt_history)
        self.layout().addWidget(self.clear_history_btn)

        # Prompt sharing 
        self.prompt_sharing = QCheckBox('Prompt Sharing')
        self.prompt_sharing.setToolTip('Share prompts between Txt2Img, Img2Img, etc')
        self.prompt_sharing.setChecked(self.variables['prompt_share'])
        self.prompt_sharing.clicked.connect(self.update_prompt_sharing)
        self.layout().addWidget(self.prompt_sharing)

        # Sharing Inclusions
        self.share_inclusions = QGroupBox('Shared Prompts')
        self.share_inclusions.setLayout(QVBoxLayout())

        self.include_txt2img = QCheckBox('Txt2Img')
        self.include_txt2img.setChecked('txt2img' in self.variables['prompt_share_includes'])
        # self.include_txt2img.toggled.connect(lambda: self.update_share_includes('txt2img', self.include_txt2img.isChecked()))
        self.shared_prompt_btns.append(self.include_txt2img)
        self.share_inclusions.layout().addWidget(self.include_txt2img)

        self.include_img2img = QCheckBox('Img2Img')
        self.include_img2img.setChecked('img2img' in self.variables['prompt_share_includes'])
        # self.include_img2img.toggled.connect(lambda: self.update_share_includes('img2img', self.include_img2img.isChecked()))
        self.shared_prompt_btns.append(self.include_img2img)
        self.share_inclusions.layout().addWidget(self.include_img2img)

        self.include_inpaint = QCheckBox('Inpaint')
        self.include_inpaint.setChecked('inpaint' in self.variables['prompt_share_includes'])
        # self.include_inpaint.toggled.connect(lambda: self.update_share_includes('inpaint', self.include_inpaint.isChecked()))
        self.shared_prompt_btns.append(self.include_inpaint)
        self.share_inclusions.layout().addWidget(self.include_inpaint)

        self.layout().addWidget(self.share_inclusions)

        self.layout().addStretch()


    def set_clicked_radio_btn(self, key):
        if key == 'empty':
            self.radio_btn_empty.click()
        elif key == 'last':
            self.radio_btn_last_doc.click()
        elif key == 'initial':
            self.radio_btn_init_prompt.click()
        else:
            # Nothing selected, defaulting to empty
            self.radio_btn_empty.click()

    def set_widget_values(self):
        self.set_clicked_radio_btn(self.variables['new_doc_prompt_mode'])

        self.max_history_length.setValue(self.variables['prompt_history_max'])

        for btn in self.shared_prompt_btns:
            label = btn.text().lower()
            # Was getting an odd bug where the values would be "&txt2img" or "i&mg2img"
            label = label.replace('&', '')
            btn.setChecked(label in self.variables['prompt_share_includes'])

        self.prompt_widget.set_prompt(self.variables['prompt_initial'], self.variables['prompt_negative_initial'])

    def clicked_radio_btn(self, btn_clicked):
        if btn_clicked == self.radio_btn_empty:
            self.variables['new_doc_prompt_mode'] = 'empty'
        elif btn_clicked == self.radio_btn_last_doc:
            self.variables['new_doc_prompt_mode'] = 'last'
        elif btn_clicked == self.radio_btn_init_prompt:
            self.variables['new_doc_prompt_mode'] = 'initial'
        else:
            # Unknown button?
            self.variables['new_doc_prompt_mode'] = 'empty'

    def clear_prompt_history(self):
        self.settings_controller.clear_file_prompt_history()
        # TODO: Trigger a reload of everything's settings

    def update_share_includes(self, mode:str, active:bool):
        # if active and not self.variables['prompt_share_includes'].index(mode) > -1:
        if active and mode not in self.variables['prompt_share_includes']:
            self.variables['prompt_share_includes'].append(mode)
        
        # if not active and self.variables['prompt_share_includes'].index(mode) > -1:
        if not active and mode in self.variables['prompt_share_includes']:
            self.variables['prompt_share_includes'].remove(mode)
            
    def updated_max_history(self):
        self.variables['prompt_history_max'] = self.max_history_length.value()
    
    def update_prompt_sharing(self):
        self.variables['prompt_share'] = self.prompt_sharing.isChecked()
        self.share_inclusions.setDisabled(not self.variables['prompt_share'])

    