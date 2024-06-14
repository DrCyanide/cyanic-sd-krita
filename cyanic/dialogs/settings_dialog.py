from PyQt5.QtWidgets import *
from ..pages import SettingsPage, SimplifyPage, PromptSettingsPage
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController

class SettingsDialog(QDialog):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, on_close=None):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.on_close = on_close

        self.setLayout(QVBoxLayout())

        self.tabs = QTabWidget()
        self.settings_page = SettingsPage(self.settings_controller, self.api)
        self.prompt_settings_page = PromptSettingsPage(self.settings_controller, self.api)
        self.simplify_page = SimplifyPage(self.settings_controller, self.api)
        # Default Settings?

        self.pages = [
            self.settings_page,
            self.prompt_settings_page,
            self.simplify_page,
        ]

        self.init_ui()

    def init_ui(self):
        self.layout().addWidget(self.tabs)
        self.tabs.addTab(self.settings_page, 'Server')

        # Set prompt history length + initial prompt + clean prompts on new docs
        self.tabs.addTab(self.prompt_settings_page, 'Prompts')

        # Simplify is way too long to not have a scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.simplify_page)
        scroll.setWidgetResizable(True)
        self.tabs.addTab(scroll, 'Simplify')

    def load_all_settings(self):
        for page in self.pages:
            page.load_all_settings()

    def load_server_data(self):
        for page in self.pages:
            page.load_server_data()

    def load_settings(self):
        for page in self.pages:
            page.load_settings()

    def closeEvent(self, event):
        for page in self.pages:
            page.save_settings()
        if self.on_close is not None:
            self.on_close()

        