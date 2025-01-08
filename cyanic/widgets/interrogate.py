from PyQt5.QtWidgets import *
from krita import QTimer
import json
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import CyanicWidget, PromptWidget, ImageInWidget, InterrogateModelWidget

# Interrogate was originally designed by tectin0 - https://github.com/DrCyanide/cyanic-sd-krita/pull/29
class InterrogateWidget(CyanicWidget):
    def __init__(
        self,
        settings_controller: SettingsController,
        api: SDAPI,
        interrogate_model_widget: InterrogateModelWidget,
        prompt_widget: PromptWidget,
        image_in: ImageInWidget,
        size_dict={"x": 0, "y": 0, "w": 0, "h": 0},
    ):
        super().__init__(settings_controller, api)
        self.interrogate_model_widget = interrogate_model_widget
        self.prompt_widget = prompt_widget
        self.image_in = image_in
        self.size_dict = size_dict
        self.results = None
        self.debug = False
        self.init_ui()

    def init_ui(self):
        self.interrogate_btn = QPushButton()
        self.interrogate_btn.setText("Interrogate")
        self.interrogate_btn.clicked.connect(self.handle_interrogate_btn_click)
        self.layout().addWidget(self.interrogate_btn)

        if self.debug:
            self.debug_data = QTextEdit()
            self.debug_data.setPlaceholderText(
                "JSON data used to interrogate the image will be shown here"
            )
            self.layout().addWidget(self.debug_data)

    def set_widget_values(self):
        pass

    def load_server_data(self):
        pass

    def handle_interrogate_btn_click(self):
        self.interrogate()
        self.update()

    def interrogate(self):
        self.interrogate_btn.setText('Interrogating')
        self.interrogate_btn.setDisabled(True)
        self.update()

        self.kc = KritaController()
        self.generating_for_doc = self.kc.doc

        x = self.size_dict["x"]
        y = self.size_dict["y"]
        w = self.size_dict["w"]
        h = self.size_dict["h"]
        if w == 0 or h == 0:
            # Size dict was not updated, try to use the selection size
            x, y, w, h = self.kc.get_selection_bounds(doc=self.generating_for_doc)
            if w == 0 or h == 0:
                # Nothing was selected, use the canvas size
                x, y = 0, 0
                w, h = self.kc.get_canvas_size(doc=self.generating_for_doc)

        image = self.image_in.get_generation_data()[self.image_in.key]
        if image == None or len(image) == 0:
            # The user probably forgot to select Use Canvas or similar.
            self.image_in.get_canvas_img()
            image = self.image_in.get_generation_data()[self.image_in.key]

        data = {
            "model": self.interrogate_model_widget.get_model(),
            "width": w,
            "height": h,
            "image": image,
        }

        # TODO: Check settings for anything that changes the parameters, such as limiting generation size, HR Fix, upscaling, clip skip, etc
        if self.debug:
            self.debug_data.setPlainText("%s" % json.dumps(data))
            # return

        self.kc.run_as_thread(lambda: self.threadable_run(data), lambda: self.threadable_return())

    def threadable_run(self, data):
        self.results = self.api.interrogate(data)
        self.interrogate_btn.setText('Interrogate')
        self.interrogate_btn.setDisabled(False)
        self.update()

    def threadable_return(self):
        if self.results is not None:
            if "caption" in self.results:
                # self.prompt_widget.mode = (
                #     self.interrogate_model_widget.get_prompt_mode()
                # )

                self.prompt_widget.prompt_text_edit.setPlainText(
                    self.results["caption"]
                )
                self.prompt_widget.save_settings()

            if self.debug:
                self.debug_data.setPlainText(self.results["caption"])

        else:
            if self.debug:
                self.debug_data.setPlainText(
                    "%s\nThreadable Return found no results"
                    % self.debug_data.toPlainText()
                )

        self.update()

    def get_generation_data(self):
        return {}