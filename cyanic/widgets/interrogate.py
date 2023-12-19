from PyQt5.QtWidgets import *
from krita import QTimer
import json
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import PromptWidget
from ..widgets import ImageInWidget
from ..widgets import InterrogateModelWidget


class InterrogateWidget(QWidget):
    def __init__(
        self,
        settings_controller: SettingsController,
        api: SDAPI,
        interrogate_model_widget: InterrogateModelWidget,
        prompt_widget: PromptWidget,
        image_in: ImageInWidget,
        size_dict={"x": 0, "y": 0, "w": 0, "h": 0},
    ):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.interrogate_model_widget = interrogate_model_widget
        self.prompt_widget = prompt_widget
        self.image_in = image_in
        self.size_dict = size_dict
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.kc = KritaController()
        self.results = None
        self.debug = False

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

    def handle_interrogate_btn_click(self):
        self.interrogate()
        self.update()

    def interrogate(self):
        # TODO: Give some sort of indicator if the backend is loading a new model/VAE, because that makes everything take longer.
        self.update()

        x = self.size_dict["x"]
        y = self.size_dict["y"]
        w = self.size_dict["w"]
        h = self.size_dict["h"]
        if w == 0 or h == 0:
            # Size dict was not updated, try to use the selection size
            x, y, w, h = self.kc.get_selection_bounds()
            if w == 0 or h == 0:
                # Nothing was selected, use the canvas size
                x, y = 0, 0
                w, h = self.kc.get_canvas_size()

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

        processing_instructions = {}

        try:
            self.kc.refresh_doc()
            if self.kc.doc is None:
                self.kc.create_new_doc()

            self.results = self.api.interrogate(data)

        except Exception as e:
            self.interrogate_btn.setText(
                "Interrogate"
            )  # Want the UI to look right, even if we have an exception
            self.update()
            self.is_interrogating = False
            raise Exception(
                "Cyanic SD - Error getting %s: %s"
                % (self.interrogate_model_widget.get_model(), e)
            )

        if self.results is not None:
            self.finished = True

            if "caption" in self.results:
                self.prompt_widget.mode = (
                    self.interrogate_model_widget.get_prompt_mode()
                )

                self.prompt_widget.prompt_text_edit.setPlainText(
                    self.results["caption"]
                )

                self.prompt_widget.save_prompt()

            if self.debug:
                self.debug_data.setPlainText(self.results["caption"])

        else:
            if self.debug:
                self.debug_data.setPlainText(
                    "%s\nThreadable Return found no results"
                    % self.debug_data.toPlainText()
                )
