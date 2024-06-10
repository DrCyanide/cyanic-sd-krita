from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class CyanicPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api

        self.cyanic_widgets = [] # Widgets that implement CyanicWidget, and should be notified of settings/server changes

        self.setLayout(QVBoxLayout())
        # self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def init_ui(self):
        # Initialize cyanic_widgets
        raise NotImplementedError('init_ui() not implemented for this page')

    def handle_hidden(self):
        # Hide widgets that settings specify shouldn't show up. Must be called in init_ui() and on load_settings()
        pass

    def load_all_settings(self):
        for widget in self.cyanic_widgets:
            widget.load_all_settings()

    def load_server_data(self):
        for widget in self.cyanic_widgets:
            widget.load_server_data()
    
    def load_settings(self):
        for widget in self.cyanic_widgets:
            widget.load_settings()
        self.handle_hidden()

    def save_settings(self):
        for widget in self.cyanic_widgets:
            widget.save_settings();
    