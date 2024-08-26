from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
import os
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController


class ExtraNetworksManageDialog(QDialog):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None):
        super().__init__()
        self.setWindowTitle('Extra Networks - Import')
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close

        self.changed = False

        self.setLayout(QVBoxLayout())
        # self.layout().setContentsMargins(0,0,0,0)

        self.init_ui()

    def init_ui(self):
        self.import_server_btn = QPushButton('Import from Server')
        self.import_server_btn.setToolTip('If Krita is on the same computer that Stable Diffusion is being run, grab the custom data straight from Stable Diffusion')
        self.import_server_btn.clicked.connect(lambda: self.import_server())
        self.layout().addWidget(self.import_server_btn)

        local_host = 'localhost' in self.api.host or '127.0.0.1' in self.api.host
        if not local_host:
            self.import_server_btn.setDisabled(True)

        self.import_external_btn = QPushButton('Import from File')
        self.import_external_btn.setIcon(Krita.instance().icon('document-import'))
        self.import_external_btn.setToolTip('Import custom data file that was exported from Cyanic SD Krita')
        self.import_external_btn.clicked.connect(lambda: self.import_file())
        self.layout().addWidget(self.import_external_btn)

        self.export_external_btn = QPushButton('Export to File')
        self.export_external_btn.setIcon(Krita.instance().icon('document-export'))
        self.export_external_btn.setToolTip('Export custom data file for use on another computer')
        self.export_external_btn.clicked.connect(lambda: self.export_file())
        self.layout().addWidget(self.export_external_btn)

    def closeEvent(self, event):
        if self.on_close is not None and self.changed:
            self.on_close()

    def import_server(self):
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
        self.import_server_btn.setText('Imported')

    def import_file(self):
        self.changed = True
        pass

    def export_file(self):
        pass