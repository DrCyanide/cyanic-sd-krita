from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from . import CollapsibleWidget, CyanicWidget, LabeledSlider

class SoftInpaintWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, settings_only=False):
        super().__init__(settings_controller, api)
        self.settings_only = settings_only
        # self.variables = {
        #     'schedule_bias': self.settings_controller.get('soft_inpaint_schedule_bias'), # Float, 0.1 steps, 0.0-8.0
        #     'preservation_strength': self.settings_controller.get('soft_inpaint_preservation_strength'), # Float, 0.05 steps, 0.0-8.0
        #     'transition_contrast_boost': self.settings_controller.get('soft_inpaint_transition_contrast'), # Float, 0.5 steps, 1.0-32.0
        #     'mask_influence': self.settings_controller.get('soft_inpaint_mask_influence'), # Float, 0.05 steps, 0.0-1.0
        #     'difference_threshold': self.settings_controller.get('soft_inpaint_difference_threshold'), # Float, 0.25 steps, 0.0-8.0
        #     'difference_contrast': self.settings_controller.get('soft_inpaint_difference_contrast'), # Float, 0.25 steps, 0.0-8.0
        # }
        self.variables = {
            'soft_inpaint_schedule_bias': 1.1, # Float, 0.1 steps, 0.0-8.0
            'soft_inpaint_preservation_strength': 0.95, # Float, 0.05 steps, 0.0-8.0
            'soft_inpaint_transition_contrast': 4.4, # Float, 0.5 steps, 1.0-32.0
            'soft_inpaint_mask_influence': 0.02, # Float, 0.05 steps, 0.0-1.0
            'soft_inpaint_difference_threshold': 0.4, # Float, 0.25 steps, 0.0-8.0
            'soft_inpaint_difference_contrast': 1.9, # Float, 0.25 steps, 0.0-8.0
        }
        self.variable_parameters = {
            # 'schedule_bias': {
            'soft_inpaint_schedule_bias': {
                'name': 'Schedule Bias',
                'step_size': 0.1,
                'min': 0.0,
                'max': 8.0,
            },
            # 'preservation_strength': {
            'soft_inpaint_preservation_strength': {
                'name': 'Preservation Strength',
                'step_size': 0.05,
                'min': 0.0,
                'max': 8.0,
            },
            # 'transition_contrast_boost': {
            'soft_inpaint_transition_contrast': {
                'name': 'Transition Contrast Boost',
                'step_size': 0.5,
                'min': 1.0,
                'max': 32.0,
            },
            # 'mask_influence': {
            'soft_inpaint_mask_influence': {
                'name': 'Mask Influence',
                'step_size': 0.05,
                'min': 0.0,
                'max': 1.0,
            },
            # 'difference_threshold': {
            'soft_inpaint_difference_threshold': {
                'name': 'Difference Threshold',
                'step_size': 0.25,
                'min': 0.0,
                'max': 8.0,
            },
            # 'difference_contrast': {
            'soft_inpaint_difference_contrast': {
                'name': 'Difference Contrast',
                'step_size': 0.25,
                'min': 0.0,
                'max': 8.0,
            }
        }
        self.widgets = {}
        for key in self.variable_parameters.keys():
            self.widgets[key] = None

        self.enabled = False
        self.installed = False
        self.init_ui()
        self.set_widget_values()
    
    def set_widget_values(self):
        for key in self.widgets.keys():
            self.widgets[key].set_value(self.variables[key])

    def load_server_data(self):
        self.installed = self.api.script_installed('soft inpainting') 

    def load_settings(self):
        # self.variables = {
        #     'schedule_bias': self.settings_controller.get('soft_inpaint_schedule_bias'), # Float, 0.1 steps, 0.0-8.0
        #     'preservation_strength': self.settings_controller.get('soft_inpaint_preservation_strength'), # Float, 0.05 steps, 0.0-8.0
        #     'transition_contrast_boost': self.settings_controller.get('soft_inpaint_transition_contrast'), # Float, 0.5 steps, 1.0-32.0
        #     'mask_influence': self.settings_controller.get('soft_inpaint_mask_influence'), # Float, 0.05 steps, 0.0-1.0
        #     'difference_threshold': self.settings_controller.get('soft_inpaint_difference_threshold'), # Float, 0.25 steps, 0.0-8.0
        #     'difference_contrast': self.settings_controller.get('soft_inpaint_difference_contrast'), # Float, 0.25 steps, 0.0-8.0
        # }
        super().load_settings()
        self.enabled = self.settings_controller.get('soft_inpaint_enabled')

    def init_ui(self):
        soft_inpainting_enabled = QCheckBox('Soft Inpainting')
        soft_inpainting_enabled.setChecked(self.enabled)
        soft_inpainting_enabled.toggled.connect(lambda: self.update_enabled(soft_inpainting_enabled.isChecked()))

        # Build the settings
        self.settings_widget = QWidget()
        self.settings_widget.setLayout(QFormLayout())
        self.settings_widget.layout().setContentsMargins(0,0,0,0)

        # self.settings_widget.layout().addRow('Schedule Bais', self.create_row('schedule_bias'))
        # self.settings_widget.layout().addRow('Preservation Strength', self.create_row('preservation_strength'))
        # self.settings_widget.layout().addRow('Transition Contrast Boost', self.create_row('transition_contrast_boost'))
        # self.settings_widget.layout().addRow('Mask Influence', self.create_row('mask_influence'))
        # self.settings_widget.layout().addRow('Difference Threshold', self.create_row('difference_threshold'))
        # self.settings_widget.layout().addRow('Difference Contrast', self.create_row('difference_contrast'))

        for key in self.variable_parameters.keys():
            self.widgets[key] = LabeledSlider(self.variable_parameters[key]['min'], self.variable_parameters[key]['max'], self.variables[key], as_percent=False, step_size=self.variable_parameters[key]['step_size'])
            self.settings_widget.layout().addRow(self.variable_parameters[key]['name'], self.widgets[key])

        if self.settings_only:
            self.layout().addWidget(self.settings_widget)
        else:
            self.layout().addWidget(soft_inpainting_enabled)
            settings_collapsible = CollapsibleWidget('Soft Inpaint Settings', self.settings_widget) # Collapsible settings 
            self.layout().addWidget(settings_collapsible)

    # def create_row(self, variable_name):
    #     # Pull constants from variable_parameters
    #     label = QLabel('%s' % self.variables[variable_name])

    #     slider = QSlider(Qt.Horizontal)
    #     # Slider works on ints
    #     multiplier = 10
    #     if self.variable_parameters[variable_name]['step_size'] < 0.1:
    #         multiplier = 100
    #     min = int(self.variable_parameters[variable_name]['min'] * multiplier)
    #     max = int(self.variable_parameters[variable_name]['max'] * multiplier)
    #     slider.setMinimum(min)
    #     slider.setMaximum(max)
    #     slider.setValue(int(self.variables[variable_name] * multiplier))
    #     slider.valueChanged.connect(lambda: self.update_row(label, variable_name, slider.value() / multiplier))

    #     row = QWidget()
    #     row.setLayout(QHBoxLayout())
    #     row.layout().setContentsMargins(0,0,0,0)
    #     row.layout().addWidget(slider)
    #     row.layout().addWidget(label)
    #     return row

    def update_enabled(self, enable):
        self.enabled = enable
        self.settings_controller.set('soft_inpaint_enabled', enable)

    def update_row(self, label, variable_name, value):
        self.variables[variable_name] = value
        label.setText('%s' % value)

    def save_settings(self):
        # self.settings_controller.set('soft_inpaint_schedule_bias', self.variables['schedule_bias'])
        # self.settings_controller.set('soft_inpaint_preservation_strength', self.variables['preservation_strength'])
        # self.settings_controller.set('soft_inpaint_transition_contrast_boost', self.variables['transition_contrast_boost'])
        # self.settings_controller.set('soft_inpaint_mask_influence', self.variables['mask_influence'])
        # self.settings_controller.set('soft_inpaint_difference_threshold', self.variables['difference_threshold'])
        # self.settings_controller.set('soft_inpaint_difference_contrast', self.variables['difference_contrast'])
        # self.settings_controller.save()
        super().save_settings()
        self.settings_controller.set('soft_inpaint_enabled', self.enabled)

    def get_generation_data(self):
        if not self.enabled or not self.installed:
            return {}
        data = {
            "alwayson_scripts": {
                "Soft Inpainting": {
                    "args": [
                        True, # Enabled
                        # self.variables['schedule_bias'],
                        # self.variables['preservation_strength'],
                        # self.variables['transition_contrast_boost'],
                        # self.variables['mask_influence'],
                        # self.variables['difference_threshold'],
                        # self.variables['difference_contrast']
                        self.variable_parameters['soft_inpaint_schedule_bias'],
                        self.variable_parameters['soft_inpaint_preservation_strength'],
                        self.variable_parameters['soft_inpaint_transition_contrast'],
                        self.variable_parameters['soft_inpaint_mask_influence'],
                        self.variable_parameters['soft_inpaint_difference_threshold'],
                        self.variable_parameters['soft_inpaint_difference_contrast']
                    ]
                }
            }
        }
        self.save_settings()
        return data
    