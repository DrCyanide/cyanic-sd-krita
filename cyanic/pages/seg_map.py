from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
import json
import os

# https://docs.google.com/spreadsheets/d/1se8YEtb2detS7OuPE86fXGyD269pMycAWe2mtKUj2W8/edit#gid=0
class SegmentationMapPage(QWidget):
    def __init__(self, settings_controller:SettingsController):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.settings_controller = settings_controller
        self.kc = KritaController()
        self.seg_map = {}
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))
        self.map_path = os.path.join(self.plugin_dir, '..', 'extras', 'seg_map.json')
        self.icon_size = 24
        self.update_user_colors()
        self.load_seg_map_json()
        self.draw_ui()

    def load_seg_map_json(self):
        try:
            with open(self.map_path, 'r') as file_in:
                self.seg_map = json.loads(file_in.read())
        except Exception as e:
            raise Exception('Cyanic SD - Error loading segmap: %s' % e)

    def draw_ui(self):
        description = QLabel("ControlNet's Segmentation Map uses different colors to represent different types of objects. Here's an easy way to access those colors.")
        description.setWordWrap(True)
        self.layout().addWidget(description)

        # Primary / Secondary colors, and their descriptions
        primary_pixmap = QPixmap(self.icon_size, self.icon_size)
        primary_pixmap.fill(QColor(self.foreground))
        # primary_icon = QIcon(primary_pixmap)
        primary_icon = QLabel()
        primary_icon.setPixmap(primary_pixmap)
        self.layout().addWidget(primary_icon)

        secondary_pixmap = QPixmap(self.icon_size, self.icon_size)
        secondary_pixmap.fill(QColor(self.background))
        # secondary_icon = QIcon(secondary_pixmap)
        secondary_icon = QLabel()
        secondary_icon.setPixmap(secondary_pixmap)
        self.layout().addWidget(secondary_icon)

        # Search bar
        search_bar = QPlainTextEdit()
        self.layout().addWidget(search_bar)

        # List of potential results that match
        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def update(self):
        super().update()

    
    def update_user_colors(self):
        try:
            self.foreground = self.kc.get_foreground_color_hex()
            self.background = self.kc.get_background_color_hex()
        except:
            self.foreground = "#000000"
            self.background = "#ffffff"