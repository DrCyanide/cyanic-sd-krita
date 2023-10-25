from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CollapsibleWidget

class PromptWidget(QWidget):
    NUM_LINES = 4
    def __init__(self, settings_controller:SettingsController, api:SDAPI, mode:str):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.mode = mode.lower() # txt2img / img2img / inpaint / adetailer
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.style_name_list = QListWidget()

        self.draw_ui()

    def draw_ui(self):
        self.prompt_text_edit = QPlainTextEdit()
        self.prompt_text_edit.setPlaceholderText('Prompt')
        self.prompt_text_edit.setFixedHeight(self.prompt_text_edit.fontMetrics().lineSpacing() * PromptWidget.NUM_LINES)
        self.prompt_text_edit.setToolTip('Prompt')
        self.layout().addWidget(self.prompt_text_edit)

        self.negative_prompt_text_edit = QPlainTextEdit()
        self.negative_prompt_text_edit.setPlaceholderText('Negative prompt')
        self.negative_prompt_text_edit.setFixedHeight(self.negative_prompt_text_edit.fontMetrics().lineSpacing() * PromptWidget.NUM_LINES)
        self.negative_prompt_text_edit.setToolTip('Negative Prompt')
        if not self.settings_controller.get('hide_ui.negative_prompt'):
            self.layout().addWidget(self.negative_prompt_text_edit)

        if not self.settings_controller.get('hide_ui.styles'):
            self.layout().addWidget(self.styles_control())
        # self.layout().addWidget(self.network_control()) # TODO: But adding Networks is laborous. 

        self.load_prompt()

    def get_generation_data(self):
        data = {
            'prompt': self.prompt_text_edit.toPlainText(),
            'negative_prompt': self.negative_prompt_text_edit.toPlainText(),
        }
        style_names = self.get_selected_style_names()
        if len(style_names) > 0:
            data['styles'] = style_names
        return data

    def styles_control(self):
        style_form = QWidget()
        style_form.setLayout(QVBoxLayout())
        style_names = self.api.get_style_names()
        self.style_name_list = QListWidget()
        # self.style_name_list.setAlternatingRowColors(True)
        for name in style_names:
            item = QListWidgetItem(name, self.style_name_list)
            item.setBackground( QColor('#222222') )
            item.setCheckState(Qt.Unchecked)
        style_form.layout().addWidget(self.style_name_list)
        
        add_to_prompt = QPushButton()
        add_to_prompt.setText('Add to Prompt')
        add_to_prompt.clicked.connect(self.apply_styles)
        
        style_form.layout().addWidget(add_to_prompt)
        return CollapsibleWidget('Styles', style_form)
    
    def network_control(self):
        # Want a drop down to select between Lora, Textual Inversion, Hypernetwork, etc.
        # ... that might have to be another file
        return CollapsibleWidget('Networks', QLabel('Networks'))

    def get_selected_style_names(self):
        items = []
        for index in range(self.style_name_list.count()):
            if self.style_name_list.item(index).checkState() == Qt.Checked:
                items.append(self.style_name_list.item(index).text())
        return items

    def apply_styles(self):
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


    def load_prompt(self):
        if self.settings_controller.has_key('prompts.save_prompts') and not self.settings_controller.get('prompts.save_prompts'):
            return # The user doesn't want their prompts saved/loaded
        try:
            excluded = self.settings_controller.get('prompts.exclude_sharing')
            if self.settings_controller.has_key('prompts.share_prompts') and self.settings_controller.get('prompts.share_prompts') and self.mode not in excluded:
                # Restore shared prompts
                self.prompt_text_edit.setPlainText(self.settings_controller.get('prompts.shared_prompt'))
                self.negative_prompt_text_edit.setPlainText(self.settings_controller.get('prompts.shared_negative_prompt'))
            else:
                # Restore mode's prompts
                self.prompt_text_edit.setPlainText(self.settings_controller.get('prompts.%s_prompt' % self.mode))
                self.negative_prompt_text_edit.setPlainText(self.settings_controller.get('prompts.%s_negative_prompt' % self.mode))
            self.update()
        except:
            # Honestly don't care what the issue was, the result is empty prompt fields - which is the desired default
            pass

    def save_prompt(self):
        if self.settings_controller.has_key('prompts.save_prompts') and not self.settings_controller.get('prompts.save_prompts'):
            return # The user doesn't want their prompts saved/loaded    
        
        prompt = self.prompt_text_edit.toPlainText()
        negative_prompt = self.negative_prompt_text_edit.toPlainText()

        excluded = self.settings_controller.get('prompts.exclude_sharing')
        if self.settings_controller.has_key('prompts.share_prompts') and self.settings_controller.get('prompts.share_prompts') and self.mode not in excluded:
            self.settings_controller.set('prompts.shared_prompt', prompt)
            self.settings_controller.set('prompts.shared_negative_prompt', negative_prompt)
        else:
            self.settings_controller.set('prompts.%s_prompt' % self.mode, prompt)
            self.settings_controller.set('prompts.%s_negative_prompt' % self.mode, negative_prompt)

        self.settings_controller.save()