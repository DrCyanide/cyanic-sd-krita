from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController


class ExtraNetworksImportDialog(QDialog):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None):
        super().__init__()
        self.setWindowTitle('Extra Networks - Import')
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self.init_ui()

    def init_ui(self):
        self.import_server_btn = QPushButton('Import from Server')
        self.import_server_btn.setToolTip('If Krita is on the same computer that Stable Diffusion is being run, grab the custom data straight from Stable Diffusion')
        self.layout().addWidget(self.import_server_btn)

        local_host = 'localhost' in self.api.host or '127.0.0.1' in self.api.host
        if not local_host:
            self.import_server_btn.setDisabled(True)

        self.import_external_btn = QPushButton('Import from File')
        self.import_external_btn.setToolTip('Import custome data file that was exported from Cyanic SD Krita')
        self.layout().addWidget(self.import_external_btn)

    def closeEvent(self):
        if self.on_close is not None:
            self.on_close()

    def import_server(self):
        pass

    def import_file(self):
        pass