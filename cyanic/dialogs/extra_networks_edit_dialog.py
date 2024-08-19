from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt, QByteArray
import re
import os
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController


class ExtraNetworksEditDialog(QDialog):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, extra_network_type:str, extra_network_name:str):
        super().__init__()
        self.setWindowTitle('Custom Settings - %s' % extra_network_name)
        self.settings_controller = settings_controller
        self.api = api
        self.extra_network_type = extra_network_type
        self.extra_network_name = extra_network_name

        self.init_ui()

    def init_ui(self):
        pass