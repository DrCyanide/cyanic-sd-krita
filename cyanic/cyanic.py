from PyQt5.QtWidgets import *
from krita import *
from .sdapi_v1 import SDAPI
from .widgets import *
from .pages import *
from .settings_controller import SettingsController

DEFAULT_HOST = "http://127.0.0.1:7860"

class CyanicDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.settings_controller = SettingsController()
        self.api = SDAPI(self.settings_controller.get('server.host') if self.settings_controller.has_key('server.host') else DEFAULT_HOST)

        self.setWindowTitle("Cyanic SD")
        self.main_widget = QWidget(self)
        self.main_widget.setLayout(QVBoxLayout())
        self.setWidget(self.main_widget)        
        
        # NOTE: This page setup creates a new page each time the select is changed, which would clear prompts/settings.
        # A better design might be to re-use the pages.
        # However that has the drawback that there needs to be a way to update the prompts across pages 

        # Set up the page select
        self.page_combobox = QComboBox()
        self.pages = [
            {'name': 'Settings', 'content': self.show_settings},
            {'name': 'Txt2Img', 'content': self.show_txt2img},
            {'name': 'Img2Img', 'content': self.show_img2img},
            # {'name': 'Extensions', 'content': self.show_extensions},
            {'name': 'Inpaint', 'content': self.show_inpaint},
            #{'name': 'Upscale', 'content': self.show_upscale},
        ]
        for page in self.pages:
            self.page_combobox.addItem(page['name'])
        self.page_combobox.activated.connect(self.change_page)
        self.main_widget.layout().addWidget(self.page_combobox)

        # Resume the last page it was on ONLY if the API is running. Otherwise the pages try to pull defaults and it becomes a big mess...
        if self.api.connected:
            last_page = self.settings_controller.get('pages.last')
            if last_page and last_page in list(map(lambda x: x['name'], self.pages)):
                self.page_combobox.setCurrentText(last_page)

        # Initialize contentWidget
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.main_widget.layout().addWidget(self.content_area)

        # Set the initial page
        self.change_page() 

    # This was part of the template, might be relevant later
    def canvasChanged(self, canvas):
        pass

    # Update the content widget based on the selected page
    def change_page(self):
        for page in self.pages:
            if page['name'] == self.page_combobox.currentText():
                self.settings_controller.set('pages.last', page['name'])
                self.settings_controller.save()
                page['content']()
        self.update()


    def show_settings(self):
        self.content_area.setWidget(SettingsPage(self.settings_controller, self.api))

    def show_txt2img(self):
        self.content_area.setWidget(Txt2ImgPage(self.settings_controller, self.api))

    def show_img2img(self):
        self.content_area.setWidget(Img2ImgPage(self.settings_controller, self.api))

    def show_inpaint(self):
        self.content_area.setWidget(InpaintPage(self.settings_controller, self.api))

    def show_upscale(self):
        self.showOther('Upscale')

    def showOther(self, text):
        contentWidget = QWidget()
        contentWidget.setLayout(QVBoxLayout())
        contentWidget.layout().addWidget(QLabel(text))
        self.content_area.setWidget(contentWidget)


Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "cyanicSD",
        DockWidgetFactoryBase.DockTornOff,
        CyanicDocker
    )
)