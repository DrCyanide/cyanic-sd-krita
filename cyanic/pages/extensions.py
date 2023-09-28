from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CollapsibleWidget
from ..extension_widgets import *
from inspect import getmembers, ismethod

class ExtensionsPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.setLayout(QVBoxLayout())

        # Get the Always On extensions, and see if they have a matching widget
        self.layout().addWidget(QLabel('Extensions'))

        # self.layout().addWidget(CollapsibleWidget('ControlNet', extension_widgets.ControlNetExtension(self.settings_controller, self.api)))
        self.layout().addWidget(CollapsibleWidget('Collapse', QLabel('Something hidden')))
        # for w in dir(extension_widgets)
        # p = getmembers(extension_widgets, ismethod)
        
        # self.layout().addWidget(QLabel(p))

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top
