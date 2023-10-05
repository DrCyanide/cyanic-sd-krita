from PyQt5.QtWidgets import *
from krita import QTimer
import json
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import PromptWidget

# Generate Button, Progress Bar, and the threading logic for previews
# list_of_widgets is txt2img/img2img's [self.model_widget, self.prompt_widget, etc].
# All of them should have `def get_generation_data(self)`.
# Yes, I should've made an abstract class for that.
class GenerateWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, list_of_widgets:list, mode:str):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.list_of_widgets = list_of_widgets
        self.mode = mode
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.kc = KritaController()
        self.is_generating = False
        self.abort = False
        self.debug = False

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(1)
        self.progress_bar.setHidden(True)
        self.layout().addWidget(self.progress_bar)

        self.generate_btn = QPushButton()
        self.generate_btn.setText('Generate')
        self.generate_btn.clicked.connect(self.handle_generate_btn_click)
        self.layout().addWidget(self.generate_btn)

        if self.debug:
            self.debug_data = QTextEdit()
            self.debug_data.setPlaceholderText('JSON data used to generate the image will be shown here')
            self.layout().addWidget(self.debug_data)

    def handle_generate_btn_click(self):
        if self.is_generating:
            self.cancel()
        else:
            self.generate()
        self.update()

    def generate(self):
        # TODO: Give some sort of indicator if the backend is loading a new model/VAE, because that makes everything take longer.
        self.is_generating = True
        self.generate_btn.setText('Cancel')
        self.progress_bar.setHidden(False)
        self.update()

        # Get the size to generate the image
        x, y, w, h = self.kc.get_selection_bounds()
        if w == 0 or h == 0:
            x, y = 0, 0
            w, h = self.kc.get_canvas_size()
        
        data = {
            "width": w,
            "height": h,
        }

        # Whether or not to save the images on the server
        if self.settings_controller.get('server.save_imgs'):
            data['save_images'] = True

        for widget in self.list_of_widgets:
            data.update(widget.get_generation_data())
            if type(widget) is PromptWidget:
                widget.save_prompt()
        # TODO: Check settings for anything that changes the parameters, such as limiting generation size, HR Fix, upscaling, clip skip, etc
        if self.debug:
            self.debug_data.setPlainText('%s' % json.dumps(self.api.cleanup_data(data)))
            # return
        try:
            if self.kc.doc is None:
                self.kc.create_new_doc()
            self.kc.run_as_thread(lambda: self.threadable_run(data), lambda: self.threadable_return(x, y, w, h))
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(lambda: self.progress_check(x,y,w,h))
            # Set the refresh rate
            if self.settings_controller.has_key('previews.refresh_seconds'):
                self.progress_timer.start(1000 * self.settings_controller.get('previews.refresh_seconds'))
            else:
                self.progress_timer.start(1000)

        except Exception as e:
            self.generate_btn.setText('Generate') # Want the UI to look right, even if we have an exception
            self.update()
            self.is_generating = False
            raise Exception('Cyanic SD - Error getting %s: %s' % (self.mode, e))

    def progress_check(self, x, y, w, h):
        try:
            results = self.api.get_progress()
            if results['progress'] == 0 or self.abort: # The operation has stopped
                self.abort = False
                self.progress_bar.setValue(1)
                self.kc.delete_preview_layer()
                self.progress_timer.stop()
                self.is_generating = False
                return
            self.progress_bar.setValue(results['progress'] * 100)
            # Show the preview
            if self.settings_controller.has_key('previews.enabled') and self.settings_controller.get('previews.enabled'):
                if results['current_image'] is not None and len(results['current_image']) > 0:
                    self.kc.update_preview_layer(results['current_image'], x, y, w, h)
        except Exception as e:
            # Kill the progress check
            self.abort = False
            self.progress_bar.setValue(1)
            self.kc.delete_preview_layer()
            self.progress_timer.stop()
            self.is_generating = False
            raise Exception('Cyanic SD - Error in progress loop: %s' % e)

    def threadable_run(self, data):
        self.generate_btn.setText('Cancel')
        self.update()
        if self.mode == 'txt2img':
            self.results = self.api.txt2img(data)
        elif self.mode == 'img2img':
            self.results = self.api.img2img(data)
        elif self.mode == 'inpaint':
            self.results = self.api.img2img(data)

    def threadable_return(self, x, y, w, h):
        KritaController().results_to_layers(self.results, x, y, w, h)
        self.generate_btn.setText('Generate')
        self.progress_bar.setValue(0)
        self.progress_bar.setHidden(True)
        self.update()

    def cancel(self):
        self.api.interrupt()
        self.abort = True
        self.generate_btn.setText('Generate')
        self.progress_bar.setValue(0)
        self.progress_bar.setHidden(True)
        self.update()