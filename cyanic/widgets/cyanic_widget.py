# from abc import ABC, ABCMeta, abstractmethod
# Couldn't figure out a solution to "the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all it's bases"
# So I went with a suggestion from https://stackoverflow.com/questions/4382945/abstract-methods-in-python instead
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class CyanicWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, layout=None):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        if layout:
            self.setLayout(layout())
        else:
            self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {}

    def init_ui(self):
        # Create the UI elements
        raise NotImplementedError('init_ui() not implemented for this widget')

    def handle_hidden(self):
        # Hide widgets that settings specify shouldn't show up. Must be called in init_ui() and on load_settings()
        pass

    def load_all_settings(self):
        # Pull in all the settings
        self.load_server_data()
        self.load_settings()

    def load_server_data(self):
        # Refresh UI elements that depend on SD server settings (models, vaes, etc)
        raise NotImplementedError('load_server_data() not implemented for this widget')

    def load_settings(self):
        # Refresh UI elements that depend on settings saved to file (prompt history, selected images, selected models, etc)
        raise NotImplementedError('load_settings() not implemented for this widget')

    def save_settings(self):
        # Write widget settings to settings_controller
        raise NotImplementedError('save_settings() not implemented for this widget')

    def get_generation_data(self):
        # Return a formatted dict with data used to generate images.
        raise NotImplementedError('get_generation_data() not implemented for this widget')
    
    