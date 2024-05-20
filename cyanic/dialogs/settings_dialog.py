from PyQt5.QtWidgets import *
from ..pages import SettingsPage, SimplifyPage
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController

class SettingsDialog(QDialog):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api

        self.setLayout(QVBoxLayout())

        self.tabs = QTabWidget()
        self.setting_page = SettingsPage(self.settings_controller, self.api)
        self.simplify_page = SimplifyPage(self.settings_controller, self.api)

        self.draw_ui()

    def draw_ui(self):
        self.layout().addWidget(self.tabs)
        self.tabs.addTab(self.setting_page, 'Server')

        # Simplify is way too long to not have a scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.simplify_page)
        scroll.setWidgetResizable(True)
        self.tabs.addTab(scroll, 'Simplify')

        # Set prompt history length + initial prompt + clean prompts on new docs

        