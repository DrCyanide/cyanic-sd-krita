from PyQt5.QtWidgets import *
from krita import *
from .sdapi_v1 import SDAPI
from .widgets import *
from .pages import *
from .settings_controller import SettingsController
from .dialogs import SettingsDialog
from .krita_controller import KritaController

DEFAULT_HOST = "http://127.0.0.1:7860"

class CyanicDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.settings_controller = SettingsController()
        self.api = SDAPI(self.settings_controller.get('host') if self.settings_controller.has_key('host') else DEFAULT_HOST, self.on_api_change)

        self.setWindowTitle("Cyanic SD")
        self.main_widget = QWidget(self)
        self.main_widget.setLayout(QVBoxLayout())
        self.setWidget(self.main_widget)        

        self.header_bar = QWidget()
        self.header_bar.setLayout(QGridLayout())
        self.header_bar.layout().setContentsMargins(0,0,0,0)

        self.settings_dialog = SettingsDialog(self.settings_controller, self.api)
        self.show_settings_btn = QPushButton()
        self.show_settings_btn.setIcon( Krita.instance().icon('properties') )
        self.show_settings_btn.setToolTip('Open Cyanic SD Settings')
        self.show_settings_btn.clicked.connect(lambda: self.settings_dialog.show())

        # A separate widget is needed to hold the pages, because QScrollArea can't add multiple widgets.
        self.page_holder = QWidget()
        self.page_holder.setLayout(QVBoxLayout())
        self.page_holder.layout().setContentsMargins(0,0,0,0)

        # Initialize all the pages
        self.txt2img = Txt2ImgPage(self.settings_controller, self.api)
        self.img2img = Img2ImgPage(self.settings_controller, self.api)
        self.inpaint = InpaintPage(self.settings_controller, self.api)
        self.interrogate = InterrogatePage(self.settings_controller, self.api)
        self.upscale = UpscalePage(self.settings_controller, self.api)
        self.rembg = RemBGPage(self.settings_controller, self.api)

        # Set up the page select
        self.page_combobox = QComboBox()
        self.pages = [
            {'name': 'Txt2Img', 'page': self.txt2img},
            {'name': 'Img2Img', 'page': self.img2img},
            {'name': 'Inpaint', 'page': self.inpaint},
            {'name': 'Interrogate', 'page': self.interrogate},
            {'name': 'Upscale', 'page': self.upscale},
            {'name': 'Remove Background', 'page': self.rembg},
            # {'name': 'Segmentation Map', 'page': self.segmap}, # TODO
        ]
        # Add pages to the page_holder
        for page in self.pages:
            self.page_combobox.addItem(page['name'])
            self.page_holder.layout().addWidget(page['page'])
            page['page'].setHidden(True)
        self.page_combobox.activated.connect(self.change_page)

        self.header_bar.layout().addWidget(self.page_combobox, 0, 0)
        self.header_bar.layout().addWidget(self.show_settings_btn, 0, 1)
        self.header_bar.layout().setColumnStretch(0, 99999)
        self.main_widget.layout().addWidget(self.header_bar)

        # Initialize contentWidget
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.main_widget.layout().addWidget(self.content_area)
        self.content_area.setWidget(self.page_holder)
        self.content_area.setHidden(True) # Not sure if this is needed

        # Resume the last page it was on ONLY if the API is running. Otherwise the pages try to pull defaults and it becomes a big mess...
        if self.api.connected:
            last_page = self.settings_controller.get('cyanic_sd_last_page')
            if last_page and last_page in list(map(lambda x: x['name'], self.pages)):
                self.page_combobox.setCurrentText(last_page)

        self.connection = SDConnectionWidget(self.settings_controller, self.api)
        self.connection_panel = QWidget()
        self.connection_panel.setLayout(QVBoxLayout())
        self.connection_panel.layout().addWidget(self.connection)
        self.connection_panel.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top
        self.main_widget.layout().addWidget(self.connection_panel)

        # Hide if the API isn't set
        self.on_api_change()

        # Set the initial page
        self.change_page() 

    def on_api_change(self):
        if self.api.connected:
            self.connection_panel.setHidden(True)
            self.content_area.setHidden(False)
            # Reload the API
            for page in self.pages:
                try:
                    page['page'].load_server_data()
                except:
                    # This page must not implement CyanicPage()
                    pass
        else:
            self.connection_panel.setHidden(False)
            self.content_area.setHidden(True)

    # Update the content widget based on the selected page
    def change_page(self):
        for page in self.pages:
            if page['name'] == self.page_combobox.currentText():
                page['page'].save_settings()
                self.settings_controller.save_kra_settings()
                self.settings_controller.set('cyanic_sd_last_page', page['name'])
                self.settings_controller.save()
                # page['content']()
                page['page'].setHidden(False)
            else:
                page['page'].setHidden(True)
        self.update()

    # This needs to be present in any class that implements DockWidget, even if it's not used
    def canvasChanged(self, canvas):
        # Can be used to detect active document change, which can update settings
        self.settings_controller.load_kra_settings()
        for page in self.pages:
            page['page'].load_settings()
        self.settings_dialog.load_settings()


# This is what tells Krita to add the docker in the first place.
Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "cyanicSD",
        DockWidgetFactoryBase.DockTornOff,
        CyanicDocker
    )
)
