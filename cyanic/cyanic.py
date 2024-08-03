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
        host = self.settings_controller.get('host') if self.settings_controller.has_key('host') else DEFAULT_HOST
        self.api = SDAPI(host, self.on_api_change)
        self.last_page = ''

        self.setWindowTitle("Cyanic SD")
        self.main_widget = QWidget(self)
        self.main_widget.setLayout(QVBoxLayout())
        self.setWidget(self.main_widget)        

        self.header_bar = QWidget()
        self.header_bar.setLayout(QGridLayout())
        self.header_bar.layout().setContentsMargins(0,0,0,0)

        self.settings_dialog = SettingsDialog(self.settings_controller, self.api, on_close=self.on_dialog_close)
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
        kc = KritaController()
        self.pages = [
            {'name': 'Txt2Img', 'page': self.txt2img, 'icon': kc.get_custom_icon('txt2img')},
            {'name': 'Img2Img', 'page': self.img2img, 'icon': kc.get_custom_icon('img2img')},
            {'name': 'Inpaint', 'page': self.inpaint, 'icon': kc.get_custom_icon('inpaint')},
            {'name': 'Interrogate', 'page': self.interrogate, 'icon': kc.get_custom_icon('interrogate')},
            {'name': 'Upscale', 'page': self.upscale, 'icon': Krita.instance().icon('transform_icons_liquify_resize') },
            {'name': 'Remove Background', 'page': self.rembg, 'icon': kc.get_custom_icon('rembg') },
            # TODO pages that would be nice to add, but aren't ready yet
            # {'name': 'Segmentation Map', 'page': self.segmap}, 
            # {'name': 'Face Tools', 'page': self.facetools}
        ]
        # Add pages to the page_holder
        for page in self.pages:
            if 'icon' in page.keys() and page['icon'] is not None:
                self.page_combobox.addItem(page['icon'], page['name'])
            else:
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

        # Load the settings for all pages
        self.update_all_page_settings()

        # Set the initial page
        self.change_page() 

    def on_api_change(self):
        if self.api.connected:
            self.connection_panel.setHidden(True)
            self.content_area.setHidden(False)

            # Reload the API
            self.settings_dialog.load_all_settings()
            for page in self.pages:
                try:
                    page['page'].load_server_data()
                except:
                    # This page must not implement CyanicPage
                    pass
        else:
            self.connection_panel.setHidden(False)
            self.content_area.setHidden(True)

    # Update the content widget based on the selected page
    def change_page(self):
        current_page = self.page_combobox.currentText()

        # Save the last page's settings, since that's the only one that could've changed
        last_entry = [x for x in self.pages if x['name'] == self.last_page]
        if len(last_entry) > 0:
            last_entry[0]['page'].save_settings()
            # Update the last page in settings, so it'll resume at the new page
            self.settings_controller.set('cyanic_sd_last_page', current_page)
            self.settings_controller.save_kra_settings()
            self.settings_controller.save()

        

        for page in self.pages:
            if page['name'] == current_page:
                page['page'].setHidden(False)
                page['page'].load_all_settings()
            else:
                page['page'].setHidden(True)

        self.last_page = current_page
        self.update()
    
    def update_all_page_settings(self):
        for page in self.pages:
            page['page'].load_settings()

    def on_dialog_close(self):
        # Reload settings, since they could be changed in the dialog
        self.update_all_page_settings()
        # I don't think there needs to be an API update

    # This needs to be present in any class that implements DockWidget, even if it's not used
    def canvasChanged(self, canvas):
        # Can be used to detect active document change, which can update settings
        doc = Krita.instance().activeDocument()
        if doc is None or doc.width() <= 0:
            return # The document doesn't exist yet.
        
        # canvasChanged is triggered twice when creating files (creates as a pop-out window, then docks it), and once when switching to different files
        # raise Exception('Prompt: %s' % self.txt2img.prompt_widget.prompt_text_edit.toPlainText())

        # Save the settings to the existing Krita doc
        for page in self.pages:
            page['page'].save_settings()

        # Load the new doc's settings
        self.settings_controller.update_active_doc()

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
