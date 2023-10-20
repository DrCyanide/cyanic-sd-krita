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
    def __init__(self, settings_controller:SettingsController, api:SDAPI, list_of_widgets:list, mode:str, size_dict={"x":0,"y":0,"w":0,"h":0}):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.list_of_widgets = list_of_widgets
        self.mode = mode
        self.size_dict = size_dict
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.kc = KritaController()
        self.results = None
        self.is_generating = False
        self.abort = False
        self.debug = True

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

        x = self.size_dict["x"]
        y = self.size_dict["y"]
        w = self.size_dict["w"]
        h = self.size_dict["h"]
        if w == 0 or h == 0 :
            # Size dict was not updated, try to use the selection size
            x, y, w, h = self.kc.get_selection_bounds() 
            if w == 0 or h == 0:
                # Nothing was selected, use the canvas size
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
            self.kc.refresh_doc()
            if self.kc.doc is None: 
                self.kc.create_new_doc()
            self.kc.run_as_thread(lambda: self.threadable_run(data), lambda: self.threadable_return(x, y, w, h))
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(lambda: self.progress_check(x,y,w,h))
            # Set the refresh rate
            if self.settings_controller.has_key('previews.refresh_seconds'):
                self.progress_timer.start(int(1000 * self.settings_controller.get('previews.refresh_seconds')))
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
            if results is None or results['progress'] == 0 or self.abort: # The operation has stopped
                self.abort = False
                self.progress_bar.setValue(1)
                self.kc.delete_preview_layer()
                self.progress_timer.stop()
                self.is_generating = False
                return
            self.progress_bar.setValue(int(results['progress'] * 100))
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
        # if self.debug:
            # self.debug_data.setPlainText('%s\nThreadable Run start' % self.debug_data.toPlainText())
        if self.mode == 'txt2img':
            self.results = self.api.txt2img(data)
        elif self.mode == 'img2img':
            self.results = self.api.img2img(data)
        elif self.mode == 'inpaint':
            self.results = self.api.img2img(data)
        # if self.debug:
            # self.debug_data.setPlainText('Threadable Run!\n%s' % self.results)

    def threadable_return(self, x, y, w, h):
        # self.debug_data.setPlainText('Threadable Return!\n%s' % self.results)
        if self.results is not None:
            # Prune the results images so that ControlNet preprocessors or masks aren't included in the results
            if 'images' in self.results and 'parameters' in self.results and 'batch_size' in self.results['parameters'] and 'n_iter' in self.results['parameters']:
                expected_images = self.results['parameters']['batch_size'] * self.results['parameters']['n_iter']
                if len(self.results['images']) > expected_images:
                    self.results['images'] = self.results['images'][:expected_images]
            KritaController().results_to_layers(self.results, x, y, w, h)
            if self.debug:
                temp_results = self.results
                if 'images' in temp_results:
                    for i in range(len(temp_results['images'])):
                        temp_results['images'][i] = '...'
                self.debug_data.setPlainText('%s' % temp_results)
        else:
            if self.debug:
                self.debug_data.setPlainText('%s\nThreadable Return found no results' % self.debug_data.toPlainText())
        self.generate_btn.setText('Generate')
        self.progress_bar.setValue(0)
        self.progress_bar.setHidden(True)
        self.update()

    def cancel(self):
        # raise Exception('Cyanic SD - Cancel!')
        try:
            self.api.interrupt()
            # self.progress_timer.stop()
            self.abort = True
            self.generate_btn.setText('Generate')
            self.progress_bar.setValue(0)
            self.progress_bar.setHidden(True)
            self.update()
        except Exception as e:
            raise Exception('Cyanic SD - Exception trying to interrupt: %s' % e)