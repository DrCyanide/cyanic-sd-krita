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
    MAX_HEIGHT = 150
    MAX_WIDTH = 150
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
        self.unknown_icon = self.raw_img_to_qpixmap(self.settings_controller.get_unknown_thumbnail())
        self.setLayout(QVBoxLayout())

        self.init_ui()
        self.set_widget_values()

    def init_ui(self):
        # Icon
        self.icon = self.unknown_icon
        self.icon_label = QLabel()
        self.icon_label.setPixmap(self.icon)
        self.icon_label.setMaximumHeight(ExtraNetworksEditDialog.MAX_HEIGHT)
        self.icon_label.setMaximumWidth(ExtraNetworksEditDialog.MAX_WIDTH)
        self.layout().addWidget(self.icon_label) 

        # Name
        label = QLabel(self.extra_network_name)
        self.layout().addWidget(label)
        # Alias too? Some aliases are meaningfully different

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
        self.model_filter_box.addItems(self.allowed_versions) # Removes 'All'
        # self.layout().addWidget(self.model_filter_box)
        body.layout().addRow('SD Version', self.model_filter_box)

        # Prefered Weight ("0 to disable")
        self.weight_slider = LabeledSlider(min=0, max=2, value=0.0, as_percent=False, step_size=0.01)
        self.weight_slider.setToolTip('What weight the %s should be loaded with (the default 0 will be converted to 1.0)' % self.extra_network_type)
        # self.layout().addWidget(self.weight_slider)
        body.layout().addRow('Weight', self.weight_slider)

        # Activation Text
        self.activation_text_edit = QTextEdit()
        self.activation_text_edit.setFixedHeight(self.activation_text_edit.fontMetrics().lineSpacing() * ExtraNetworksEditDialog.DESCRIPTION_LINES)
        self.activation_text_edit.setToolTip('Text that will be added to the prompt when this %s is used' % self.extra_network_type)
        # self.layout().addWidget(self.activation_text_edit)
        body.layout().addRow('Prompt', self.activation_text_edit)

        # Negative Prompt
        self.negative_text_edit = QTextEdit()
        self.negative_text_edit.setFixedHeight(self.negative_text_edit.fontMetrics().lineSpacing() * ExtraNetworksEditDialog.DESCRIPTION_LINES)
        self.activation_text_edit.setToolTip('Text that will be added to the negative prompt when this %s is used' % self.extra_network_type)
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

    def raw_img_to_qpixmap(self, raw_img):
        ba = QByteArray(raw_img)
        qimage = QImage()
        qimage.loadFromData(ba)
        pixmap = QPixmap.fromImage(qimage)
        # pixmap.scaledToHeight(ExtraNetworksEditDialog.MAX_HEIGHT)
        # pixmap.scaledToWidth(ExtraNetworksEditDialog.MAX_WIDTH)
        pixmap = pixmap.scaled(ExtraNetworksEditDialog.MAX_WIDTH, ExtraNetworksEditDialog.MAX_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap


    def set_thumbnail(self):
        if not self.show_thumbnail:
            # If you're not showing thumbnails in the other UI, don't show it here.
            self.icon = self.unknown_icon
            return

        cached_thumbnail = self.settings_controller.get_cached_thumbnail(self.extra_network_type, self.extra_network_name)
        if cached_thumbnail is not None:
            self.icon = self.raw_img_to_qpixmap(cached_thumbnail)
        else:
            # If the thumbnail existed on the server, it would've been cached. No need to search for it.
            self.icon = self.unknown_icon
        self.icon_label.setPixmap(self.icon)
       

    def set_widget_values(self):
        # Set icon
        self.set_thumbnail()

        # Load settings
        self.extra_network_settings = self.settings_controller.get_extra_network_data(self.extra_network_type, self.extra_network_name)
        has_override = 'kra_override' in self.extra_network_settings

        # Description
        description = ''
        if has_override and 'description' in self.extra_network_settings['kra_override']:
            description = self.extra_network_settings['kra_override']['description']
        else:
            description = self.extra_network_settings[self.api.host]['description']
        self.description_text_edit.setPlainText(description)

        # Version
        self.model_filter_box.setCurrentText(SettingsController.SD_MODEL_VERSIONS[-1]) # Unknown should always be last
        sd_version = 'unknown'
        if has_override and 'sd version' in self.extra_network_settings['kra_override']:
            sd_version = self.extra_network_settings['kra_override']['sd version'].lower()
        else:
            sd_version = self.extra_network_settings[self.api.host]['sd version'].lower()
        matched_version = list(filter(lambda version: version.lower() == sd_version, SettingsController.SD_MODEL_VERSIONS))
        if len(matched_version) > 0:
            self.model_filter_box.setCurrentText(matched_version[0])

        # Weight
        weight = 1.0
        if has_override and 'preferred weight' in self.extra_network_settings['kra_override']:
            weight = self.extra_network_settings['kra_override']['preferred weight']
        else:
            weight = self.extra_network_settings[self.api.host]['preferred weight']
        self.weight_slider.set_value(weight)

        # Activation text
        activation_text = ''
        if has_override and 'activation text' in self.extra_network_settings['kra_override']:
            activation_text = self.extra_network_settings['kra_override']['activation text']
        else:
            activation_text = self.extra_network_settings[self.api.host]['activation text']
        self.activation_text_edit.setText(activation_text)

        # Negative text
        negative_text = ''
        if has_override and 'negative text' in self.extra_network_settings['kra_override']:
            activation_text = self.extra_network_settings['kra_override']['negative text']
        else:
            activation_text = self.extra_network_settings[self.api.host]['negative text']
        self.negative_text_edit.setText(negative_text)

        # Notes
        notes = ''
        if has_override and 'notes' in self.extra_network_settings['kra_override']:
            notes = self.extra_network_settings['kra_override']['notes']
        else:
            notes = self.extra_network_settings[self.api.host]['notes']
        self.note_text_edit.setPlainText(notes)

        # Debugging
        # self.note_text_edit.setPlainText('%s' % self.extra_network_settings)

    def save_settings(self):
        edited_data = {
            'description': self.description_text_edit.toPlainText(),
            'sd version': self.model_filter_box.currentText(),
            'preferred weight': self.weight_slider.value(),
            'activation text': self.activation_text_edit.toPlainText(),
            'negative text': self.negative_text_edit.toPlainText(),
            'notes':self.note_text_edit.toPlainText(),
        }

        for key in edited_data.keys():
            if self.extra_network_settings[self.api.host][key] != edited_data[key]:
                # Override
                if not has_override:
                    self.extra_network_settings['kra_override'] = {}
                    has_override = True
                self.extra_network_settings['kra_override'][key] = edited_data[key]
        
        self.settings_controller.set_extra_network_data_from_dict(self.extra_network_type, self.extra_network_name, self.extra_network_settings)
        # Saving happens in set_extra_network_data_from_dict
        
    def show(self):
        super().show()
        self.set_widget_values()