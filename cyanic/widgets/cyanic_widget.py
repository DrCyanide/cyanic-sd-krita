from abc import ABC, ABCMeta, abstractmethod
from PyQt5.QtWidgets import QWidget

class CyanicWidget(QWidget):
    @abstractmethod
    def init_ui(self):
        pass

    @abstractmethod
    def on_server_update(self):
        pass

    @abstractmethod
    def on_settings_update(self):
        pass

    @abstractmethod
    def get_generation_data(self):
        pass

    @abstractmethod
    def save_settings(self):
        pass
    