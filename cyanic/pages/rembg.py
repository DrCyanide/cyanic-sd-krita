from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import ImageInWidget
import json

class RemBGPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.kc = KritaController()
        self.setLayout(QVBoxLayout())
        self.debug = False
        self.size_dict = {"x":0,"y":0,"w":0,"h":0}

        # NOTE: There's no API call to get these models, nor is there one to see if RemBG is installed.
        self.rembg_models = [ 
            'u2net',
            'u2netp',
            'u2net_human_seg',
            'u2net_cloth_seg',
            'silueta',
            'isnet-general-use',
            'isnet-anime',
        ]

        # Image select
        self.img_in = ImageInWidget(self.settings_controller, self.api, 'input_image', self.size_dict)
        self.layout().addWidget(self.img_in)

        # Background Removal model
        model_select = QComboBox()
        model_select.addItems(self.rembg_models)
        model_select.setCurrentText(self.settings_controller.get('rembg.model'))
        model_select.currentTextChanged.connect(lambda: self.settings_controller.set('rembg.model', model_select.currentText()))
        self.layout().addWidget(model_select)

        # As Mask
        as_mask_cb = QCheckBox('Results as Mask')
        as_mask_cb.setToolTip('Enable to automatically make the results a mask of the active layer')
        as_mask_cb.setChecked(self.settings_controller.get('rembg.results_as_mask'))
        as_mask_cb.stateChanged.connect(lambda: self.settings_controller.set('rembg.results_as_mask', as_mask_cb.isChecked()))
        self.layout().addWidget(as_mask_cb)

        # Alpha Matting
        alpha_matting_cb = QCheckBox('Alpha Matting')
        alpha_matting_cb.setToolTip('Enable for better tranparent/translucent masks')
        alpha_matting_cb.setChecked(self.settings_controller.get('rembg.alpha_matting'))
        alpha_matting_cb.stateChanged.connect(lambda: self.set_alpha_matting(alpha_matting_cb.isChecked()))
        self.layout().addWidget(alpha_matting_cb)

        # Alpha Matting settings
        self.alpha_matting_settings = QGroupBox()
        self.alpha_matting_settings.setLayout(QFormLayout())
        self.alpha_matting_settings.setVisible(self.settings_controller.get('rembg.alpha_matting'))
        #   Erode Size
        # erode_size = QSlider(Qt.Horizontal)
        # erode_size.setMinimum(0)
        # erode_size.setMaximum(40)
        # erode_size.setValue(self.settings_controller.get('rembg.erode_size'))
        # erode_size.valueChanged.connect(lambda: self.settings_controller.set('rembg.erode_size', erode_size.value()))
        erode_size = self.make_slider_row(0, 40, 'rembg.erode_size')
        self.alpha_matting_settings.layout().addRow('Erode Size', erode_size)

        #   Foreground Threshold
        # foreground_threshold = QSlider(Qt.Horizontal)
        # foreground_threshold.setMinimum(0)
        # foreground_threshold.setMaximum(255)
        # foreground_threshold.setValue(self.settings_controller.get('rembg.foreground_threshold'))
        # foreground_threshold.valueChanged.connect(lambda: self.settings_controller.set('rembg.foreground_threshold', foreground_threshold.value()))
        foreground_threshold = self.make_slider_row(0, 255, 'rembg.foreground_threshold')
        self.alpha_matting_settings.layout().addRow('Foreground Threshold', foreground_threshold)

        #   Background Threshold
        # background_threshold = QSlider(Qt.Horizontal)
        # background_threshold.setMinimum(0)
        # background_threshold.setMaximum(255)
        # background_threshold.setValue(self.settings_controller.get('rembg.background_threshold'))
        # background_threshold.valueChanged.connect(lambda: self.settings_controller.set('rembg.background_threshold', background_threshold.value()))
        background_threshold = self.make_slider_row(0, 255, 'rembg.background_threshold')
        self.alpha_matting_settings.layout().addRow('Background Threshold', background_threshold)
        self.layout().addWidget(self.alpha_matting_settings)

        # Remove Background/Generate button
        generate_btn = QPushButton('Remove Background')
        generate_btn.clicked.connect(lambda: self.run_rembg())
        self.layout().addWidget(generate_btn)

        # Disclaimer
        disclaimer_text = "The RemBG extension is created by Automatic1111, and available in the extensions tab as 'stable-diffusion-webui-rembg'."
        disclaimer = QLabel(disclaimer_text)
        disclaimer.setWordWrap(True)
        self.layout().addWidget(disclaimer)

        if self.debug:
            self.debug_text = QPlainTextEdit()
            self.debug_text.setPlaceholderText('Debug Text')
            self.layout().addWidget(self.debug_text)
        
        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def make_slider_row(self, min, max, settings_key):
        widget = QWidget()
        widget.setLayout(QHBoxLayout())
        widget.layout().setContentsMargins(0,0,0,0)

        init_value = self.settings_controller.get(settings_key)

        slider = QSlider(Qt.Horizontal)
        slider.setMaximum(max)
        slider.setMinimum(min)
        slider.setValue(init_value)
        widget.layout().addWidget(slider)

        box = QSpinBox()
        box.setMaximum(max)
        box.setMinimum(min)
        box.setValue(init_value)
        widget.layout().addWidget(box)
        
        slider.valueChanged.connect(lambda: self._sync_values(slider.value(), slider, box, settings_key))
        box.valueChanged.connect(lambda: self._sync_values(box.value(), slider, box, settings_key))

        return widget
    
    def _sync_values(self, value, slider, box, settings_key):
        if slider.value() != value:
            slider.setValue(value)
        if box.value() != value:
            box.setValue(value)
        self.settings_controller.set(settings_key, value)

    def set_alpha_matting(self, value):
        self.settings_controller.set('rembg.alpha_matting', value)
        # Disable/Enable the other alpha_matting settings
        self.alpha_matting_settings.setVisible(value)

    def get_generation_data(self):
        data = {
            'model': self.settings_controller.get('rembg.model'),
            'return_mask': self.settings_controller.get('rembg.results_as_mask'),
            'alpha_matting': self.settings_controller.get('rembg.alpha_matting'),
            'alpha_matting_foreground_threshold': self.settings_controller.get('rembg.foreground_threshold'),
            'alpha_matting_background_threshold': self.settings_controller.get('rembg.background_threshold'),
            'alpha_matting_erode_size': self.settings_controller.get('rembg.erode_size'),
        }
        # Add the image
        data.update(self.img_in.get_generation_data())
        return data
    
    def run_rembg(self):
        data = self.get_generation_data()
        # if self.debug:
        #     self.debug_text.setPlainText('%s' % json.dumps(data))
        # TODO: Make this async
        results = self.api.post('/rembg', data)
        if results is not None:
            if not self.settings_controller.get('rembg.results_as_mask'):
                self.kc.results_to_layers(results, self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'])
            else:
                self.kc.result_to_transparency_mask(results, self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'])