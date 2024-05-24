from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CollapsibleWidget, CyanicWidget

class PromptWidget(CyanicWidget):
    NUM_LINES = 4
    def __init__(self, settings_controller:SettingsController, api:SDAPI, mode:str):
        super().__init__(settings_controller, api)
        self.mode = mode.lower() # txt2img / img2img / inpaint / adetailer1 / adetailer2
        self.variables = {
            'prompt_history_max': 15, # Default value that can be overwritten by settings
            'prompt_share': False,
            'prompt_share_excludes': [],
            'prompts_txt_shared': [],
            'prompts_txt_shared_negative': [],
            'prompts_txt_%s' % self.mode : [],
            'prompts_txt_%s_negative' % self.mode : [],
        }
        self.server_const = {
            'styles': [],
            'lora_names': [],
            'hypernetwork_names': [],
            'embedding_names': [],
        }
        self.extra_network_types = {
            # UI Name : server_const key
            'Loras': 'lora_names',
            'Hypernetworks': 'hypernetwork_names',
            'Textual Inversions': 'embedding_names',
        }
        self.active_prompt_variable = 'prompts_txt_%s' % self.mode
        self.active_prompt_negative_variable = 'prompts_txt_%s_negative' % self.mode 
        self.prompt_history_index = 0
        self.init_ui()
        self.load_server_data()
        self.load_settings()

    def init_ui(self):
        # Prompt History
        self.prompt_history_row = QWidget()
        self.prompt_history_row.setLayout(QHBoxLayout())
        self.prompt_history_row.layout().setContentsMargins(0,0,0,0)

        self.prompt_history_prev_btn = QPushButton('Prev')
        self.prompt_history_prev_btn.setToolTip('Load a more recent used prompt')
        self.prompt_history_prev_btn.clicked.connect(self.load_prev_prompt)

        self.prompt_history_next_btn = QPushButton('Next')
        self.prompt_history_next_btn.setToolTip('Load older recently used prompt')
        self.prompt_history_next_btn.clicked.connect(self.load_next_prompt)

        self.prompt_history_label = QLabel()
        self.prompt_history_label.setAlignment(Qt.AlignCenter)
        self.update_history_label()

        self.prompt_history_row.layout().addWidget(self.prompt_history_prev_btn)
        self.prompt_history_row.layout().addWidget(self.prompt_history_label)
        self.prompt_history_row.layout().addWidget(self.prompt_history_next_btn)

        self.layout().addWidget(self.prompt_history_row)

        # Prompt
        self.prompt_text_edit = QPlainTextEdit()
        self.prompt_text_edit.setFixedHeight(self.prompt_text_edit.fontMetrics().lineSpacing() * PromptWidget.NUM_LINES)
        self.prompt_text_edit.setToolTip('Prompt')
        self.prompt_text_edit.setPlaceholderText('Prompt')
        self.prompt_text_edit.setTabChangesFocus(True)
        
        self.layout().addWidget(self.prompt_text_edit)

        # Negative Prompt
        self.negative_prompt_text_edit = QPlainTextEdit()
        self.negative_prompt_text_edit.setFixedHeight(self.negative_prompt_text_edit.fontMetrics().lineSpacing() * PromptWidget.NUM_LINES)
        self.negative_prompt_text_edit.setToolTip('Negative Prompt')
        self.negative_prompt_text_edit.setPlaceholderText('Negative Prompt')
        self.negative_prompt_text_edit.setTabChangesFocus(True)
        
        self.layout().addWidget(self.negative_prompt_text_edit)

        # Styles
        self.style_panel = QWidget()
        self.style_panel.setLayout(QVBoxLayout())
        self.style_panel.layout().setContentsMargins(0,0,0,0)
        
        self.style_name_list = QListWidget()
        self.style_panel.layout().addWidget(self.style_name_list)

        self.style_append_to_prompt_btn = QPushButton('Add style text to prompt')
        self.style_append_to_prompt_btn.clicked.connect(self.styles_to_prompt)
        self.style_append_to_prompt_btn.setToolTip('Optional. Will append the prompt/negative prompt to the existing prompt.')
        self.style_panel.layout().addWidget(self.style_append_to_prompt_btn)

        self.style_collapse = CollapsibleWidget('Styles', self.style_panel)
        self.layout().addWidget(self.style_collapse)

        # Extra Networks
        self.extra_network_panel = QWidget()
        self.extra_network_panel.setLayout(QVBoxLayout())
        self.extra_network_panel.layout().setContentsMargins(0,0,0,0)

        # TODO: Add a label that explains autocomplete functionality (where typing in '<' in the prompt triggers a suggestion)

        # Select Lora/Hypernetwork/Embedding
        self.extra_network_box = QComboBox()
        self.extra_network_box.wheelEvent = lambda event : None # Disable scrollwheel interactions
        self.extra_network_box.activated.connect(lambda: self.change_extra_network_list(self.extra_network_box.currentText()))
        self.extra_network_box.addItems(list(self.extra_network_types.keys()))
        self.extra_network_panel.layout().addWidget(self.extra_network_box)

        # List of items
        self.extra_network_item_list = QListWidget()
        self.extra_network_item_list.itemPressed.connect(self.add_extra_network_to_prompt)
        self.extra_network_panel.layout().addWidget(self.extra_network_item_list)

        self.extra_network_collapse = CollapsibleWidget('Extra Networks', self.extra_network_panel)
        self.layout().addWidget(self.extra_network_collapse)

        self.handle_hidden()

    def handle_hidden(self):
        # Hide widgets that settings specify shouldn't show up. Must be called in init_ui() and on load_settings()
        self.negative_prompt_text_edit.setHidden(self.settings_controller.get('hide_ui_negative_prompt'))
        self.style_collapse.setHidden(self.settings_controller.get('hide_ui_styles'))
        self.extra_network_collapse.setHidden(self.settings_controller.get('hide_ui_extra_networks'))

    def load_server_data(self):
        self.server_const['styles'] = self.api.get_styles()
        self.server_const['lora_names'] = self.api.get_lora_names()
        self.server_const['hypernetwork_names'] = self.api.get_hypernetwork_names()
        self.server_const['embedding_names'] = self.api.get_embedding_names()
        self.load_styles_and_extra_networks()

    def load_settings(self):
        self.variables['prompt_history_max'] = self.settings_controller.get('prompt_history_max', self.variables['prompt_history_max'])
        self.variables['prompt_share'] = self.settings_controller.get('prompt_share', self.variables['prompt_share'])
        self.variables['prompt_share_excludes'] = self.settings_controller.get('prompt_share_excludes', [])
        self.variables['prompts_txt_shared'] = self.settings_controller.get('prompts_txt_shared', [])
        self.variables['prompts_txt_shared_negative'] = self.settings_controller.get('prompts_txt_shared_negative', [])
        self.variables['prompts_txt_%s' % self.mode] = self.settings_controller.get('prompts_txt_%s' % self.mode, [])
        self.variables['prompts_txt_%s_negative' % self.mode] = self.settings_controller.get('prompts_txt_%s_negative' % self.mode, [])
        # Reset the prompt_history_index
        self.prompt_history_index = 0
        self.load_prompt_edits()
        self.handle_hidden()

    def save_settings(self):
        prompt = self.prompt_text_edit.toPlainText()
        negative_prompt = self.negative_prompt_text_edit.toPlainText()

        active_prompt_history = self.variables[self.active_prompt_variable]
        active_negative_prompt_history = self.variables['%s_negative' % self.active_prompt_variable]

        # Check if this prompt/negative prompt combo is in the history
        for i in range(0, len(active_prompt_history)):
            if active_prompt_history[i] == prompt and active_negative_prompt_history[i] == negative_prompt:
                # Prompt combination was already in the history, remove it from the old index so it can be added at the front
                active_prompt_history.pop(i)
                active_negative_prompt_history.pop(i)
                break
        
        # Insert at the beginning
        active_prompt_history.insert(0, prompt)
        active_negative_prompt_history.insert(0, negative_prompt)
        
        if len(active_prompt_history) > self.variables['prompt_history_max']:
            # Too many items, trim the history down
            active_prompt_history = active_prompt_history[0:self.variables['prompt_history_max']]
            active_negative_prompt_history = active_negative_prompt_history[0:self.variables['prompt_history_max']]
        
        # Move the prompt_history_index back to the start
        self.prompt_history_index = 0

        # TODO: Save selected styles

    def get_generation_data(self):
        self.save_settings()
        data = {
            'prompt': self.prompt_text_edit.toPlainText(),
            'negative_prompt': self.negative_prompt_text_edit.toPlainText(),
        }
        # Styles can have their own section, but this doesn't work great for 
        style_names = self.get_selected_style_names()
        if len(style_names) > 0:
            data['styles'] = style_names
        return data

    # -----------------------
    # Widget specific methods
    # -----------------------

    def load_prev_prompt(self):
        if self.prompt_history_index > 0:
            self.prompt_history_index -= 1
        self.load_prompt_edits()
    
    def load_next_prompt(self):
        prompt_history_length = len(self.variables[self.active_prompt_variable])
        if self.prompt_history_index < prompt_history_length - 1:
            self.prompt_history_index += 1
        self.load_prompt_edits()

    def load_prompt_edits(self):
        self.update_history_label()
        active_prompt_history = self.variables[self.active_prompt_variable]
        active_negative_prompt_history = self.variables['%s_negative' % self.active_prompt_variable]
        if self.prompt_history_index >= 0 and self.prompt_history_index < len(active_prompt_history):
            self.prompt_text_edit.setPlainText(active_prompt_history[self.prompt_history_index])
            self.negative_prompt_text_edit.setPlainText(active_negative_prompt_history[self.prompt_history_index])
        else:
            # current_prompt_index is out of bounds?
            self.clear_prompt_edits()

    def clear_prompt_edits(self):
        self.prompt_text_edit.setPlainText('')
        self.negative_prompt_text_edit.setPlainText('')

    def update_history_label(self):
        prompt_history_length = len(self.variables[self.active_prompt_variable])
        if prompt_history_length > 0:
            self.prompt_history_label.setText('%s/%s' % (self.prompt_history_index + 1, prompt_history_length))
            self.prompt_history_label.setToolTip('Which prompt in the history is selected. 1 is most recent, %s is oldest' % prompt_history_length)
        else:
            self.prompt_history_label.setText('0/0')
            self.prompt_history_label.setToolTip('Which prompt in the history is selected. No prompt history is currently available.')

    def load_styles_and_extra_networks(self):
        self.style_name_list.clear()
        if len(self.server_const['styles']) > 0:
            style_names = list(map(lambda x: x['name'], self.server_const['styles']))
            for name in style_names:
                item = QListWidgetItem(name, self.style_name_list)
                item.setCheckState(Qt.Unchecked)
                item.setBackground( QColor('#222222') )
        
        # Load loras/hypernetworks/embeddings
        self.change_extra_network_list(self.extra_network_box.currentText())

    def change_extra_network_list(self, list_type=None):
        if list_type is None:
            list_type = self.extra_network_box.currentText()
        self.extra_network_item_list.clear()
        names_list = self.server_const[self.extra_network_types[list_type]]
        self.extra_network_item_list.addItems(names_list)

    def get_selected_style_names(self):
        items = []
        for index in range(self.style_name_list.count()):
            if self.style_name_list.item(index).checkState() == Qt.Checked:
                items.append(self.style_name_list.item(index).text())
        return items

    def styles_to_prompt(self):
        # Get the selected items text
        items = self.get_selected_style_names()
        
        # Get the prompt text from the API
        prompt_additions, negative_prompt_additions = self.api.get_style_prompts(items)
        existing_prompt = self.prompt_text_edit.toPlainText()
        existing_negative_prompt = self.negative_prompt_text_edit.toPlainText()
        
        # Combine that with the existing text
        final_prompt = '%s, %s' % (existing_prompt, prompt_additions) if len(existing_prompt) > 0 else prompt_additions
        final_negative_prompt = '%s, %s' % (existing_negative_prompt, negative_prompt_additions) if len(existing_negative_prompt) > 0 else negative_prompt_additions
        
        # Set that prompt text
        self.prompt_text_edit.setPlainText(final_prompt)
        self.negative_prompt_text_edit.setPlainText(final_negative_prompt)

        # Clear the selected prompts
        for index in range(self.style_name_list.count()):
            self.style_name_list.item(index).setCheckState(Qt.Unchecked)

    def add_extra_network_to_prompt(self, item):
        extra_network_name = item.text()
        extra_network_type = self.extra_network_types[self.extra_network_box.currentText()].split('_names')[0]
        existing_prompt = self.prompt_text_edit.toPlainText()
        self.prompt_text_edit.setPlainText('%s <%s:%s:1.0>' % (existing_prompt, extra_network_type, extra_network_name))
