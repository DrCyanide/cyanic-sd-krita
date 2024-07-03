from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import ImageInWidget
from . import CyanicPage

class RemBGPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.debug = True
        self.size_dict = {"x":0,"y":0,"w":0,"h":0}

        self.variables = {
            'rembg_model': '',
            'rembg_results_as_mask': True,
            'rembg_apply_mask': True,
            'rembg_alpha_mat': False,
            'rembg_erode': 10,
            'rembg_threshold_foreground': 240,
            'rembg_threshold_background': 10,
        }

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

        self.init_ui()

    def load_settings(self):
        for key in self.variables:
            self.variables[key] = self.settings_controller.get(key)

        if self.variables['rembg_model'] not in self.rembg_models:
            self.variables['rembg_model'] = self.rembg_models[0]

        self.model_select.setCurrentText(self.variables['rembg_model'])
        self.as_mask_cb.setChecked(self.variables['rembg_results_as_mask'])
        self.apply_mask_cb.setChecked(self.variables['rembg_apply_mask'])
        self.alpha_matting_cb.setChecked(self.variables['rembg_alpha_mat'])
        self.alpha_matting_settings.setVisible(self.variables['rembg_alpha_mat'])

    def init_ui(self):
        # Image select
        self.img_in = ImageInWidget(self.settings_controller, self.api, 'input_image', 'rembg', self.size_dict)
        self.cyanic_widgets.append(self.img_in)
        self.layout().addWidget(self.img_in)

        # Background Removal model
        self.model_select = QComboBox()
        self.model_select.addItems(self.rembg_models)
        if self.variables['rembg_model'] not in self.rembg_models:
            self.variables['rembg_model'] = self.rembg_models[0]
        self.model_select.setCurrentText(self.variables['rembg_model'])
        self.model_select.currentTextChanged.connect(lambda: self.update_variable('rembg_model', self.model_select.currentText()))
        self.layout().addWidget(self.model_select)

        # As Mask
        self.as_mask_cb = QCheckBox('Results as Mask')
        self.as_mask_cb.setToolTip('Enable to automatically make the results a mask of the active layer')
        self.as_mask_cb.setChecked(self.variables['rembg_results_as_mask'])
        self.as_mask_cb.stateChanged.connect(lambda: self.set_as_mask(self.as_mask_cb.isChecked()))
        self.layout().addWidget(self.as_mask_cb)

        # Apply Mask
        self.apply_mask_cb = QCheckBox('Apply Mask')
        self.apply_mask_cb.setChecked(self.variables['rembg_apply_mask'])
        self.apply_mask_cb.stateChanged.connect(lambda: self.update_variable('rembg_apply_mask', self.apply_mask_cb.isChecked()))
        self.layout().addWidget(self.apply_mask_cb)

        # Alpha Matting
        self.alpha_matting_cb = QCheckBox('Alpha Matting')
        self.alpha_matting_cb.setToolTip('Enable for better tranparent/translucent masks')
        self.alpha_matting_cb.setChecked(self.variables['rembg_alpha_mat'])
        self.alpha_matting_cb.stateChanged.connect(lambda: self.set_alpha_matting(self.alpha_matting_cb.isChecked()))
        self.layout().addWidget(self.alpha_matting_cb)

        # Alpha Matting settings
        self.alpha_matting_settings = QGroupBox()
        self.alpha_matting_settings.setLayout(QFormLayout())
        self.alpha_matting_settings.setVisible(self.variables['rembg_alpha_mat'])

        #   Erode Size
        erode_size = self.make_slider_row(0, 40, 'rembg_erode')
        self.alpha_matting_settings.layout().addRow('Erode Size', erode_size)

        #   Foreground Threshold
        foreground_threshold = self.make_slider_row(0, 255, 'rembg_threshold_foreground')
        self.alpha_matting_settings.layout().addRow('Foreground Threshold', foreground_threshold)

        #   Background Threshold
        background_threshold = self.make_slider_row(0, 255, 'rembg_threshold_background')
        self.alpha_matting_settings.layout().addRow('Background Threshold', background_threshold)
        self.layout().addWidget(self.alpha_matting_settings)

        # Remove Background/Generate button
        generate_btn = QPushButton('Remove Background')
        generate_btn.clicked.connect(lambda: self.run_rembg())
        self.layout().addWidget(generate_btn)

        # Disclaimer
        disclaimer_text = "The RemBG extension is created by Automatic1111, and is available in the extensions tab as 'stable-diffusion-webui-rembg'."
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

    def update_variable(self, key, value):
        self.variables[key] = value

    def set_alpha_matting(self, value):
        # self.settings_controller.set('rembg_alpha_mat', value)
        self.variables['rembg_alpha_mat'] = value
        # Disable/Enable the other alpha_matting settings
        self.alpha_matting_settings.setVisible(value)

    def set_as_mask(self, value):
        # self.settings_controller.set('rembg_results_as_mask', value)
        self.variables['rembg_results_as_mask'] = value
        self.apply_mask_cb.setDisabled(not value)


    def save_settings(self):
        for key in self.variables.keys():
            self.settings_controller.set(key, self.variables[key])


    def get_generation_data(self):
        # data = {
        #     'model': self.settings_controller.get('rembg_model'),
        #     'return_mask': self.settings_controller.get('rembg_results_as_mask'),
        #     'alpha_matting': self.settings_controller.get('rembg_alpha_mat'),
        #     'alpha_matting_foreground_threshold': self.settings_controller.get('rembg_foreground_threshold'),
        #     'alpha_matting_background_threshold': self.settings_controller.get('rembg_background_threshold'),
        #     'alpha_matting_erode_size': self.settings_controller.get('rembg_erode'),
        # }
        data = {
            'model': self.variables['rembg_model'],
            'return_mask': self.variables['rembg_results_as_mask'],
            'alpha_matting': self.variables['rembg_alpha_mat'],
            'alpha_matting_foreground_threshold': self.variables['rembg_threshold_foreground'],
            'alpha_matting_background_threshold': self.variables['rembg_threshold_background'],
            'alpha_matting_erode_size': self.variables['rembg_erode'],
        }
        # Add the image
        data.update(self.img_in.get_generation_data())
        return data
    
    def run_rembg(self):
        kc = KritaController()
        data = self.get_generation_data()
        
        if self.debug:
            import json
            self.debug_text.setPlainText("%s" % json.dumps(data))
        # TODO: Make this async
        results = self.api.post('/rembg', data)
        if results is not None:
            apply_mask = self.settings_controller.get('rembg_apply_mask')
            as_mask = self.settings_controller.get('rembg_results_as_mask')
            if (as_mask and not apply_mask) or not as_mask:
                kc.results_to_layers(results, self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'])
            else:
                kc.result_to_transparency_mask(results, self.size_dict['x'], self.size_dict['y'], self.size_dict['w'], self.size_dict['h'])
        else:
            raise Exception('No results?')