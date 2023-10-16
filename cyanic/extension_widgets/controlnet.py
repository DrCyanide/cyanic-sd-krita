from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from enum import Enum
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import ImageInWidget, CollapsibleWidget

class ControlNetExtension(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.cnapi = ControlNetAPI(self.api)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.units = []

        server_supported = self.api.script_installed('controlnet')
        if not server_supported:
            error = QLabel('Host "%s" does not have ControlNet installed' % self.api.host)
            website = QLabel('Get it from https://github.com/lllyasviel/ControlNet')
            self.layout().addWidget(error)
            self.layout().addWidget(website)
            return

        tab_widget = QTabWidget()
        for i in range(0, self.cnapi.tabs):
            self.units.append(ControlNetUnit(self.settings_controller, self.api, self.cnapi))
            tab_widget.addTab(self.units[i], 'Unit %s' % i)
        
        self.layout().addWidget(tab_widget)

    def get_generation_data(self):
        enabled_controlnet_args = [unit.get_generation_data() for unit in self.units if unit.enabled]
        if len(enabled_controlnet_args) == 0:
            return {}
        
        data = {
            'alwayson_scripts': {
                'controlnet': {
                    'args': enabled_controlnet_args
                }
            }
        }
        return data

class ControlNetUnit(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, cnapi):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.cnapi = cnapi
        self.enabled = False
        self.low_vram = False
        self.pixel_perfect = False
        self.control_type = None
        self.preprocessor = None
        self.model = None
        self.control_weight = 1.0
        self.start_step = 0.0
        self.end_step = 0.0
        self.control_mode = 0
        self.resize_mode = 0
        self.variables = {
            "preprocessor_resolution": 512,
            "threshold_a": -1,
            "threshold_b": -1,
            'weight': 1.0,
            'start': 0,
            'end': 100,
        }

        # The available preprocessor/models, according to what's currently selected
        self.preprocessor_list = self.cnapi.module_list
        self.model_list = self.cnapi.models

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self.img_in = ImageInWidget(self.settings_controller, self.api, 'input_image')
        self.layout().addWidget(self.img_in)

        check_row = QWidget()
        check_row.setLayout(QHBoxLayout())
        check_row.layout().setContentsMargins(0,0,0,0)
        
        enable_cb = QCheckBox('Enable')
        enable_cb.toggled.connect(lambda: self.update_enabled(enable_cb.isChecked()))
        check_row.layout().addWidget(enable_cb)

        low_vram_cb = QCheckBox('Low VRAM')
        low_vram_cb.toggled.connect(lambda: self.update_low_vram(low_vram_cb.isChecked()))
        check_row.layout().addWidget(low_vram_cb)

        pixel_perfect_cb = QCheckBox('Pixel Perfect')
        pixel_perfect_cb.toggled.connect(lambda: self.update_pixel_perfect(pixel_perfect_cb.isChecked()))
        check_row.layout().addWidget(pixel_perfect_cb)

        self.layout().addWidget(check_row)

        # Add the Control Type filter
        control_type_row = QWidget()
        control_type_row.setLayout(QFormLayout())
        control_type_row.layout().setContentsMargins(0,0,0,0)
        control_type_select = QComboBox()
        control_type_select.addItems(self.cnapi.get_control_types_list())
        control_type_select.setCurrentText('All')
        control_type_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        control_type_select.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        control_type_select.setMaxVisibleItems(5) # Suppose to limit the number of visible options
        control_type_select.currentIndexChanged.connect(lambda: self.update_model_options(control_type_select.currentText()))
        control_type_row.layout().addRow('Control Type', control_type_select)

        # Preprocessor select
        self.preprocessor_select = QComboBox()
        self.preprocessor_select.addItems(self.preprocessor_list)
        self.preprocessor_select.setCurrentIndex(0)
        self.preprocessor_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.preprocessor_select.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.preprocessor_select.setMaxVisibleItems(5) # Suppose to limit the number of visible options
        # self.preprocessor_select.currentIndexChanged.connect(lambda: self.set_preprocessor_settings(self.preprocessor_select.currentText())) # ... This steps through EVERY index in between
        self.preprocessor_select.currentTextChanged.connect(lambda: self.set_preprocessor_settings(self.preprocessor_select.currentText()))
        control_type_row.layout().addRow('Preprocessor', self.preprocessor_select)

        # Model select
        self.model_select = QComboBox()
        self.model_select.addItems(self.model_list)
        self.model_select.setCurrentIndex(0)
        self.model_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.model_select.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.model_select.setMaxVisibleItems(5) # Suppose to limit the number of visible options
        # self.model_select.currentIndexChanged.connect(lambda: self.update_model(self.model_select.currentText()))
        self.model_select.currentTextChanged.connect(lambda: self.update_model(self.model_select.currentText()))
        control_type_row.layout().addRow('Model', self.model_select)

        self.layout().addWidget(control_type_row)

        # Preprocessor Specific Settings
        self.preprocessor_settings = QGroupBox("Preprocessor Settings")
        self.preprocessor_settings.setLayout(QVBoxLayout())
        self.preprocessor_settings.layout().setContentsMargins(0,0,0,0)

        self.resolution_row = self._setup_row('Resolution', 64, 2048, 512, 'preprocessor_resolution')
        self.preprocessor_settings.layout().addWidget(self.resolution_row)
        self.resolution_row.setHidden(True)

        # Threshold A (first set of options) Int and Float
        self.threshold_a_row_int = self._setup_row('A', 64, 2048, 512, 'threshold_a')
        self.preprocessor_settings.layout().addWidget(self.threshold_a_row_int)
        self.threshold_a_row_int.setHidden(True)

        self.threshold_a_row_float = self._setup_row('A', 0, 100, 0, 'threshold_a', 0.1)
        self.preprocessor_settings.layout().addWidget(self.threshold_a_row_float)
        self.threshold_a_row_float.setHidden(True)

        # Threshold B (second set of options) Int and Float
        self.threshold_b_row_int = self._setup_row('B', 64, 2048, 512, 'threshold_b')
        self.preprocessor_settings.layout().addWidget(self.threshold_b_row_int)
        self.threshold_b_row_int.setHidden(True)

        self.threshold_b_row_float = self._setup_row('B', 0, 100, 0, 'threshold_b', 0.1)
        self.preprocessor_settings.layout().addWidget(self.threshold_b_row_float)
        self.threshold_b_row_float.setHidden(True)

        # TODO: Run Preprocessor button?
        self.layout().addWidget(self.preprocessor_settings)
        self.preprocessor_settings.setHidden(True)

        # Controls below the prprocessor
        general_controls_row = QWidget()
        general_controls_row.setLayout(QFormLayout())
        general_controls_row.layout().setContentsMargins(0,0,0,0)
        
        # Control Mode
        control_mode_options = [ # Note: The index here matches what's in the ControlNet API. DO NOT CHANGE THE ORDER!
            'Balanced',
            'Prompt is more important',
            'ControlNet is more important'
        ]
        control_mode_select = QComboBox()
        control_mode_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        control_mode_select.addItems(control_mode_options)
        control_mode_select.setCurrentIndex(self.control_mode)
        control_mode_select.currentTextChanged.connect(lambda: self.update_control_mode(control_mode_select.currentIndex()))
        general_controls_row.layout().addRow('Control Mode', control_mode_select)

        # Resize Mode
        resize_mode_options = [ # Note: The index here matches what's in the ControlNet API. DO NOT CHANGE THE ORDER!
            'Just Resize',
            'Crop and Resize',
            'Resize and Fill'
        ]
        resize_mode_select = QComboBox()
        resize_mode_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        resize_mode_select.addItems(resize_mode_options)
        resize_mode_select.setCurrentIndex(self.resize_mode)
        resize_mode_select.currentTextChanged.connect(lambda: self.update_resize_mode(resize_mode_select.currentIndex()))
        general_controls_row.layout().addRow('Resize Mode', resize_mode_select)

        self.layout().addWidget(general_controls_row)

        # Start %, End %, Weight
        fine_controls = QWidget()
        fine_controls.setLayout(QFormLayout())
        fine_controls.layout().setContentsMargins(0,0,0,0)
        control_weight = self._setup_row('Weight', 0.0, 2.0, 1.0, 'weight', step=0.05)
        start_step = self._setup_row('Start %', 0, 100, 0, 'start')
        end_step = self._setup_row('End %', 0, 100, 100, 'end')
        fine_controls.layout().addWidget(control_weight)
        fine_controls.layout().addWidget(start_step)
        fine_controls.layout().addWidget(end_step)

        fine_collapse = CollapsibleWidget('Fine Controls', fine_controls)
        self.layout().addWidget(fine_collapse)

        # self.debug_text = QPlainTextEdit()
        # self.debug_text.setPlaceholderText('Debugging text')
        # self.layout().addWidget(self.debug_text)

    def _setup_row(self, label:str, min, max, value, variable_name:str, step=1):
        row = QWidget()
        row.setLayout(QHBoxLayout())
        row.layout().setContentsMargins(0,0,0,0)

        row.layout().addWidget(QLabel(label))

        slider = QSlider(Qt.Horizontal)
        box = QSpinBox()
        # Slider can't handle floats, so somethings might need to be adjusted
        if type(step) is float or type(max) is float or type(min) is float:
            slider.setMinimum(int(min * 100))
            slider.setMaximum(int(max * 100))
            slider.setValue(int(value * 100))
            row.layout().addWidget(slider)

            box = QDoubleSpinBox()
            box.setMinimum(min)
            box.setMaximum(max)
            box.setValue(value)
            row.layout().addWidget(box)

            slider.valueChanged.connect(lambda: self._sync_float_values(slider.value(), slider, box, variable_name))
            box.valueChanged.connect(lambda: self._sync_float_values(box.value(), slider, box, variable_name))

        else:
            # all ints, everything is normal
            slider.setMinimum(min)
            slider.setMaximum(max)
            slider.setValue(value)
            row.layout().addWidget(slider)

            box.setMinimum(min)
            box.setMaximum(max)
            box.setValue(value)
            row.layout().addWidget(box)

            slider.valueChanged.connect(lambda: self._sync_values(slider.value(), slider, box, variable_name))
            box.valueChanged.connect(lambda: self._sync_values(box.value(), slider, box, variable_name))

        return row
    
    # Update the row in place
    def _update_row(self, row:QWidget, label:str, min, max, value, variable_name:str, step=1):
        # row.children()[0] is the QHBoxLayout
        # Label
        row.children()[1].setText(label)
        if type(step) is float or type(max) is float or type(min) is float:
            # Sliders can't handle floats, adjust for that
            # Slider
            row.children()[2].setMinimum(int(min * 100))
            row.children()[2].setMaximum(int(max * 100))
            row.children()[2].setValue(int(value * 100))
            # Box
            row.children()[3] = QDoubleSpinBox()
            row.children()[3].setMinimum(min)
            row.children()[3].setMaximum(max)
            row.children()[3].setValue(value)
            # self.debug_text.setPlainText('%s\n(Floats) %s (%s to %s)' % (self.debug_text.toPlainText(), label, min, max))
            row.children()[2].valueChanged.connect(lambda: self._sync_float_values(row.children()[2].value(), row.children()[2], row.children()[3], variable_name)) # Slider changed, update box
            row.children()[3].valueChanged.connect(lambda: self._sync_float_values(row.children()[3].value(), row.children()[2], row.children()[3], variable_name)) # Box changed, update slider
        else:
            # Slider
            row.children()[2].setMinimum(min)
            row.children()[2].setMaximum(max)
            row.children()[2].setValue(value)
            # Box
            row.children()[3] = QSpinBox()
            row.children()[3].setMinimum(min)
            row.children()[3].setMaximum(max)
            row.children()[3].setValue(value)
            # self.debug_text.setPlainText('%s\n(Ints) %s (%s to %s)' % (self.debug_text.toPlainText(), label, min, max))
            row.children()[2].valueChanged.connect(lambda: self._sync_values(row.children()[2].value(), row.children()[2], row.children()[3], variable_name)) # Slider changed, update box
            row.children()[3].valueChanged.connect(lambda: self._sync_values(row.children()[3].value(), row.children()[2], row.children()[3], variable_name)) # Box changed, update slider


    def _sync_float_values(self, float_value, slider:QSlider, box:QDoubleSpinBox, variable_name):
        # Handle the * 100 for the slider
        if type(float_value) is int:
            if float_value > 0:
                float_value = float_value / 100
        if float_value == box.value() and int(float_value * 100) == slider.value():
            return # Don't update
        slider.setValue(int(float_value * 100))
        box.setValue(float_value)
        self.variables[variable_name] = float_value

    def _sync_values(self, value, slider:QSlider, box:QSpinBox, variable_name):
        if value == slider.value() and value == box.value():
            return # Don't update
        # self.debug_text.setPlainText('%s\nUpdating %s - %s' % (self.debug_text.toPlainText(), value, variable_name))
        slider.setValue(value)
        box.setValue(value)
        self.variables[variable_name] = value

    def update_enabled(self, enabled):
        self.enabled = enabled
    
    def update_low_vram(self, enabled):
        self.low_vram = enabled

    def update_pixel_perfect(self, enabled):
        self.pixel_perfect = enabled

    def update_resize_mode(self, index):
        self.resize_mode = index

    def update_control_mode(self, index):
        self.control_mode = index

    def update_model_options(self, control_type:str):
        # Remove the old values from the combobox
        self.preprocessor_select.clear()
        self.model_select.clear()

        self.preprocessor_list = self.cnapi.control_types[control_type]['module_list']
        self.model_list = self.cnapi.control_types[control_type]['model_list']

        self.preprocessor_select.addItems(self.preprocessor_list)
        self.model_select.addItems(self.model_list)

        if len(self.preprocessor_list) > 1 and self.preprocessor_list[0].lower() == 'none':
            self.preprocessor_select.setCurrentIndex(1)
        else:
            self.preprocessor_select.setCurrentIndex(0)
        
        if len(self.model_list) > 1 and self.model_list[0].lower() == 'none':
            self.model_select.setCurrentIndex(1)
        else:
            self.model_select.setCurrentIndex(0)

    def update_model(self, model_name:str):
        self.model = model_name

    def set_preprocessor_settings(self, preprocessor_name:str):
        if len(preprocessor_name) == 0:
            self.preprocessor_settings.setHidden(True)
            return
        
        self.preprocessor = preprocessor_name

        details = self.cnapi.module_details[preprocessor_name]
        self.model_select.setHidden(details['model_free'])
        
        self.preprocessor_settings.setHidden(len(details['sliders']) == 0) # If there's no sliders, just hide it all
        if details is None or details['sliders'] is None or len(details['sliders']) == 0:
            return
        
        slider_index = 0
        # some preprocessors have null in their sliders...
        if details['sliders'][slider_index] is None:
            slider_index += 1

        if 'name' in details['sliders'][slider_index] and details['sliders'][slider_index]['name'] == 'Preprocessor Resolution':
            slider_details = details['sliders'][slider_index]
            self.resolution_row.setHidden(False)
            # self.resolution_row = self._setup_row('Resolution', slider_details['min'], slider_details['max'], slider_details['value'], 'preprocessor_resolution', slider_details.get('step', 1))
            self._update_row(self.resolution_row, 'Resolution', slider_details['min'], slider_details['max'], slider_details['value'], 'preprocessor_resolution', slider_details.get('step', 1))
            slider_index += 1
        else:
            self.resolution_row.setHidden(True)
        
        # These are the unique settings that a preprocessor can have, passed into the API as threshold_a and threshold_b
        self.threshold_a_row_int.setHidden(True)
        self.threshold_a_row_float.setHidden(True)
        self.threshold_b_row_int.setHidden(True)
        self.threshold_b_row_float.setHidden(True)
        thresholds = details['sliders'][slider_index:len(details['sliders'])] # Remove the Preprocessor Resolution from the list
        if len(thresholds) > 0:
            steps = thresholds[0].get('step', 1)
            if type(steps) is float:
                self.threshold_a_row_float.setHidden(False)
                # self.debug_text.setPlainText('%s\nFloat %s' % (self.debug_text.toPlainText(), thresholds[0]['name']))
                self._update_row(self.threshold_a_row_float, thresholds[0]['name'], thresholds[0]['min'], thresholds[0]['max'], thresholds[0]['value'], 'threshold_a', steps)
            else:
                self.threshold_a_row_int.setHidden(False)
                # self.debug_text.setPlainText('%s\nInt %s' % (self.debug_text.toPlainText(), thresholds[0]['name']))
                self._update_row(self.threshold_a_row_float, thresholds[0]['name'], thresholds[0]['min'], thresholds[0]['max'], thresholds[0]['value'], 'threshold_a', steps)

        if len(thresholds) > 1:
            steps = thresholds[1].get('step', 1)
            if type(steps) is float:
                self.threshold_b_row_float.setHidden(False)
                self._update_row(self.threshold_b_row_float, thresholds[1]['name'], thresholds[1]['min'], thresholds[1]['max'], thresholds[1]['value'], 'threshold_b', steps)
            else:
                self.threshold_b_row_int.setHidden(False)
                self._update_row(self.threshold_b_row_int, thresholds[1]['name'], thresholds[1]['min'], thresholds[1]['max'], thresholds[1]['value'], 'threshold_b', steps)
        self.update()

    def get_generation_data(self):
        # https://github.com/Mikubill/sd-webui-controlnet/wiki/API
        if not self.enabled:
            return {}
        
        data = {
            # 'input_image': None, # Handled by self.img_in 
            # 'mask': None, # "mask pixel_perfect to filter the image". Ah yes, clear as crystal...
            'module': self.preprocessor,
            'model': self.model,
            'weight': self.variables['weight'],
            'resize_mode': self.resize_mode,
            'lowvram': self.low_vram,
            'preprocessor_res': self.variables['preprocessor_resolution'],
            'threshold_a': self.variables['threshold_a'], # API only uses this if preprocessor accepts values
            'threshold_b': self.variables['threshold_b'], # API only uses this if preprocessor accepts values
            'guidance_start': self.variables['start'] / 100 if self.variables['start'] > 0 else 0.0,
            'guidance_end': self.variables['end'] / 100 if self.variables['end'] > 0 else 0.0,
            'control_mode': self.control_mode,
            'pixel_perfect': self.pixel_perfect,
        }
        data.update(self.img_in.get_generation_data()) # Combines the image data with the rest of the data 
        return data

class ControlNetAPI():
    def __init__(self, api:SDAPI):
        self.api = api
        self.models = []
        self.module_list = [] # Preprocessors
        self.module_details = {}
        self.control_types = {}
        self.settings = {}
        self.tabs = 0

        self.get_models()
        self.get_modules()
        self.get_control_types()
        self.get_settings()


    def get_control_types_list(self):
        return self.control_types.keys()
    
    def get_preprocessors_for_control_type(self, control_type):
        return self.control_types[control_type]['module_list']
    
    def get_models_for_control_type(self, control_type):
        return self.control_types[control_type]['model_list']

    def get_version(self):
        return self.api.get('/controlnet/version')
    
    def get_models(self):
        self.models = self.api.get('/controlnet/model_list?update=true')
        # return self.models 
    
    def get_modules(self):
        results = self.api.get('/controlnet/module_list?alias_names=true')
        self.module_list = results['module_list']
        self.module_details = results['module_detail']

    def get_control_types(self):
        self.control_types = self.api.get('/controlnet/control_types')['control_types']

    def get_settings(self):
        self.settings = self.api.get('/controlnet/settings')
        self.tabs = self.settings['control_net_unit_count']

    # def detect(self, images):