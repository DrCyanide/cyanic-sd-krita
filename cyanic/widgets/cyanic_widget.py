from abc import ABC, ABCMeta, abstractmethod
from PyQt5.QtWidgets import QWidget

class CyanicWidget(QWidget):
    @abstractmethod
    def init_ui(self):
        # Create the UI elements
        pass

    @abstractmethod
    def on_server_update(self):
        # Refresh UI elements that depend on SD server settings (models, vaes, etc)
        pass

    @abstractmethod
    def on_settings_update(self):
        # Refresh UI elements that depend on settings saved to file (prompt history, selected images, selected models, etc)
        pass

    @abstractmethod
    def get_generation_data(self):
        # Return a formatted dict with data used to generate images.
        pass

    @abstractmethod
    def save_settings(self):
        # Write widget settings to settings_controller
        pass
    