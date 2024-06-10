from PyQt5.QtWidgets import *

from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController

class SDConnectionWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.testing_connection = False
        self.kc = KritaController()

        self.setLayout(QFormLayout())
        self.init_ui()
    

    def init_ui(self):
        self.host_addr = QLineEdit(self.settings_controller.get('host'))
        self.host_addr.setPlaceholderText(self.api.DEFAULT_HOST)
        self.host_addr.returnPressed.connect(self.handle_connect_btn_click)
        self.layout().addRow('Host', self.host_addr)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.handle_connect_btn_click)
        self.layout().addWidget(self.connect_btn)

        self.connect_label = QLabel('No SD connection')
        if self.api.connected:
            self.connect_label.setText('SD connected')
        self.layout().addWidget(self.connect_label) 


    def handle_connect_btn_click(self):
        self.test_connection()
        self.update()


    def test_connection(self):
        # NOTE: this crashes instantly if KritaController is a local variable. Must use in the self.kc format
        self.kc.run_as_thread(lambda: self.threadable_run(), lambda: self.threadable_return()) 

    def threadable_run(self):
        self.testing_connection = True
        self.connect_btn.setText('Connecting')
        self.connect_btn.setDisabled(True)
        self.connect_label.setText('Attempting connection...')
        new_host = self.host_addr.text()
        self.api.test_connection(new_host, switch_if_success=True)

    def threadable_return(self):
        self.testing_connection = False
        self.connect_btn.setText('Connect')
        self.connect_btn.setDisabled(False)

        if self.api.connected:
            self.connect_label.setText('SD connected')
            # Has to be called from here. SDAPI should finish updating itself before threadable_return() is called
            self.api.on_connection_change() 
        else:
            self.connect_label.setText('No SD connection')