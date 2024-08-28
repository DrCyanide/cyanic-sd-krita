from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
import re
import os
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import LabeledSlider


class ExtraNetworksEditDialog(QDialog):
    DESCRIPTION_LINES = 4
    def __init__(self, settings_controller:SettingsController, api:SDAPI, extra_network_type:str, extra_network_name:str, show_thumbnail=False):
        super().__init__()
        self.setWindowTitle('Custom Settings - %s' % extra_network_name)
        self.settings_controller = settings_controller
        self.api = api
        self.extra_network_type = extra_network_type
        self.extra_network_name = extra_network_name
        self.show_thumbnail = show_thumbnail
        self.extra_network_settings = {} 
        self.allowed_versions = SettingsController.SD_MODEL_VERSIONS[1:]
        self.setLayout(QVBoxLayout())

        self.init_ui()
        self.set_widget_values()

    def init_ui(self):
        # Icon

        # Name
        label = QLabel(self.extra_network_name)
        self.layout().addWidget(label)
        # Alias too?

        body = QWidget()
        body.setLayout(QFormLayout())
        body.layout().setContentsMargins(0,0,0,0)

        # Description
        self.description_text_edit = QPlainTextEdit()
        self.description_text_edit.setFixedHeight(self.description_text_edit.fontMetrics().lineSpacing() * ExtraNetworksEditDialog.DESCRIPTION_LINES)
        # self.layout().addWidget(self.description_text_edit)
        body.layout().addRow('Description', self.description_text_edit)

        # SD Version
        self.model_filter_box = QComboBox()
        self.model_filter_box.wheelEvent = lambda event : None
        self.model_filter_box.setToolTip('SD Model version')
        self.model_filter_box.addItems(SettingsController.SD_MODEL_VERSIONS)
        # self.layout().addWidget(self.model_filter_box)
        body.layout().addRow('SD Version', self.model_filter_box)

        # Prefered Weight ("0 to disable")
        self.weight_slider = LabeledSlider(min=0, max=2, value=0.0, as_percent=False, step_size=0.01)
        # self.layout().addWidget(self.weight_slider)
        body.layout().addRow('Weight', self.weight_slider)

        # Activation Text
        self.activation_text_edit = QTextEdit()
        self.activation_text_edit.setFixedHeight(self.activation_text_edit.fontMetrics().lineSpacing() * ExtraNetworksEditDialog.DESCRIPTION_LINES)
        # self.layout().addWidget(self.activation_text_edit)
        body.layout().addRow('Prompt', self.activation_text_edit)

        # Negative Prompt
        self.negative_text_edit = QTextEdit()
        self.negative_text_edit.setFixedHeight(self.negative_text_edit.fontMetrics().lineSpacing() * ExtraNetworksEditDialog.DESCRIPTION_LINES)
        # self.layout().addWidget(self.negative_text_edit)
        body.layout().addRow('Negative Prompt', self.negative_text_edit)

        # Notes
        self.note_text_edit = QPlainTextEdit()
        self.note_text_edit.setFixedHeight(self.note_text_edit.fontMetrics().lineSpacing() * ExtraNetworksEditDialog.DESCRIPTION_LINES)
        # self.layout().addWidget(self.note_text_edit)
        body.layout().addRow('Notes', self.note_text_edit)

        self.layout().addWidget(body)
        # Save
        self.save_btn = QPushButton('Save')
        self.save_btn.setIcon(Krita.instance().icon('document-save'))
        self.save_btn.clicked.connect(self.save_settings)
        self.layout().addWidget(self.save_btn)


    def set_widget_values(self):
        # Load settings
        self.extra_network_settings = self.settings_controller.get_extra_network_data(self.extra_network_type, self.extra_network_name)
        
        # Description
        self.description_text_edit.setPlainText(self.extra_network_settings['description'])

        # Version
        matched_version = list(filter(lambda version: version.lower() == self.extra_network_settings['sd version'].lower(), SettingsController.SD_MODEL_VERSIONS))
        if len(matched_version) == 0:
            self.model_filter_box.setCurrentText(SettingsController.SD_MODEL_VERSIONS[-1]) # Unknown should always be last
        else:
            self.model_filter_box.setCurrentText(matched_version[0])

        # Weight
        self.weight_slider.set_value(self.extra_network_settings['preferred weight'])

        # Activation text
        self.activation_text_edit.setText(self.extra_network_settings['activation text'])

        # Negative text
        self.negative_text_edit.setText(self.extra_network_settings['negative text'])

        # Notes
        self.note_text_edit.setPlainText(self.extra_network_settings['notes'])

    def save_settings(self):
        self.extra_network_settings['description'] = self.description_text_edit.toPlainText()
        self.extra_network_settings['sd version'] = self.model_filter_box.currentText()
        self.extra_network_settings['preferred weight'] = self.weight_slider.value()
        self.extra_network_settings['activation text'] = self.activation_text_edit.toPlainText()
        self.extra_network_settings['negative text'] = self.negative_text_edit.toPlainText()
        self.extra_network_settings['notes'] = self.note_text_edit.toPlainText()
        
        self.settings_controller.set_extra_network_data_from_dict(self.extra_network_type, self.extra_network_name, self.extra_network_settings)
        # self.settings_controller.save_extra_network_settings() # Saving happens automatically.
        

        