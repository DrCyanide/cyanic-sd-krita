from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
import os
import json
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController


class ExtraNetworksManageDialog(QDialog):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None):
        super().__init__()
        self.setWindowTitle('Extra Networks - Import')
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close

        self.default_save_path = os.path.join(os.path.expanduser('~'), 'Cyanic-SD-Customizations.json') # Gets the user's root directory

        self.changed = False

        self.setLayout(QHBoxLayout())
        # self.layout().setContentsMargins(0,0,0,0)

        self.init_ui()

    def init_ui(self):
        # Text
        text_panel = QWidget()
        text_panel.setLayout(QVBoxLayout())

        text = [
            "* Import and Export custom settings, such as default weight, activation text, notes, etc.",
            "* Exported settings can be imported to Cyanic SD plugins on other computers.",
            "* Importing from a server requires Cyanic SD be installed on that computer.",
            "* To change an individual Lora or Hypernetwork, right click on it and select 'Customize'."
        ]
        disclaimer = QLabel('\n'.join(text))
        disclaimer.setWordWrap(True)
        text_panel.layout().addWidget(disclaimer)

        self.status_label = QLabel('')
        self.status_label.setWordWrap(True)
        self.status_label.setHidden(True)
        text_panel.layout().addWidget(self.status_label)

        self.layout().addWidget(text_panel)

        # Buttons
        button_panel = QWidget()
        button_panel.setLayout(QVBoxLayout())

        self.import_server_btn = QPushButton('Import from Server')
        self.import_server_btn.setIcon(Krita.instance().icon('document-import'))
        self.import_server_btn.setToolTip('If Krita is on the same computer that Stable Diffusion is being run, grab the custom data straight from Stable Diffusion')
        self.import_server_btn.clicked.connect(lambda: self.import_server())
        button_panel.layout().addWidget(self.import_server_btn)

        local_host = 'localhost' in self.api.host or '127.0.0.1' in self.api.host
        if not local_host:
            self.import_server_btn.setDisabled(True)

        self.import_external_btn = QPushButton('Import from File')
        self.import_external_btn.setIcon(Krita.instance().icon('document-import'))
        self.import_external_btn.setToolTip('Import custom data file that was exported from Cyanic SD Krita')
        self.import_external_btn.clicked.connect(lambda: self.import_file())
        button_panel.layout().addWidget(self.import_external_btn)

        self.export_external_btn = QPushButton('Export to File')
        self.export_external_btn.setIcon(Krita.instance().icon('document-export'))
        self.export_external_btn.setToolTip('Export custom data file for use on another computer')
        self.export_external_btn.clicked.connect(lambda: self.export_file())
        button_panel.layout().addWidget(self.export_external_btn)

        button_panel.layout().addWidget(QLabel('')) # As a spacer

        self.delete_settings_btn = QPushButton('Delete custom data')
        self.delete_settings_btn.setIcon(Krita.instance().icon('deletelayer'))
        self.delete_settings_btn.setToolTip('Delete the saved default weights, activation text, SD Model version, etc. info from Cyanic SD')
        self.delete_settings_btn.clicked.connect(lambda: self.delete_data())
        button_panel.layout().addWidget(self.delete_settings_btn)

        self.layout().addWidget(button_panel)

    def closeEvent(self, event):
        if self.on_close is not None and self.changed:
            self.on_close()

    def show(self):
        self.clear_status_label()
        super().show()

    def clear_status_label(self):
        self.status_label.setText('')
        self.status_label.setHidden(True)

    def set_status_label(self, text):
        self.status_label.setText(text)
        self.status_label.setHidden(False)

    def import_server(self):
        self.clear_status_label()
        self.import_server_btn.setText('Importing...')
        self.import_server_btn.setDisabled(True)
        # Get the paths to check.
        dirs = []
        loras = self.api.get_loras()
        if loras is not None and len(loras) > 0:
            dirs.extend(set(map(lambda x: os.path.split(x['path'])[0], loras)))

        hypernetworks = self.api.get_hypernetworks()
        if hypernetworks is not None and len(hypernetworks) > 0:
            dirs.extend(set(map(lambda x: os.path.split(x['path'])[0], hypernetworks)))

        self.settings_controller.load_local_server_extra_network_settings(dirs)

        self.changed = True
        self.set_status_label('Imported settings from server')
        self.import_server_btn.setText('Import from Server')
        self.import_server_btn.setDisabled(False)

    def import_file(self):
        self.clear_status_label()
        filename, _ = QFileDialog.getOpenFileName(self, 'Export customizations', self.default_save_path, 'JSON (*.json)')
        if filename and os.path.exists(filename):
            custom_settings = {}
            with open(filename, 'r') as file:
                custom_settings = json.load(file)
            self.settings_controller.save_extra_network_settings(custom_settings)
            self.changed = True
            self.set_status_label('Imported settings from file')

    def export_file(self):
        self.clear_status_label()
        data = self.settings_controller.get_extra_network_settings()
        filename, _ = QFileDialog.getSaveFileName(self, 'Export customizations', self.default_save_path, 'JSON (*.json)')
        if filename:
            with open(filename, 'w') as file:
                file.write(json.dumps(data, indent=4))
            self.status_label.setText('Exported settings to "%s"' % filename)

    def delete_data(self):
        self.clear_status_label()
        self.settings_controller.delete_extra_network_data()
        self.set_status_label('Deleted saved customizations')