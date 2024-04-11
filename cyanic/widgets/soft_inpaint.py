from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..settings_controller import SettingsController
from . import CollapsibleWidget

class SoftInpaintWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, settings_only=False):
        super().__init__()
        self.settings_controller = settings_controller
        self.settings_only = settings_only
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {
            'schedule_bias': self.settings_controller.get('soft_inpaint.schedule_bias'), # Float, 0.1 steps, 0.0-8.0
            'preservation_strength': self.settings_controller.get('soft_inpaint.preservation_strength'), # Float, 0.05 steps, 0.0-8.0
            'transition_contrast_boost': self.settings_controller.get('soft_inpaint.transition_contrast_boost'), # Float, 0.5 steps, 1.0-32.0
            'mask_influence': self.settings_controller.get('soft_inpaint.mask_influence'), # Float, 0.05 steps, 0.0-1.0
            'difference_threshold': self.settings_controller.get('soft_inpaint.difference_threshold'), # Float, 0.25 steps, 0.0-8.0
            'difference_contrast': self.settings_controller.get('soft_inpaint.difference_contrast'), # Float, 0.25 steps, 0.0-8.0
        }
        self.variable_parameters = {
            'schedule_bias': {
                'step_size': 0.1,
                'min': 0.0,
                'max': 8.0,
            },
            'preservation_strength': {
                'step_size': 0.05,
                'min': 0.0,
                'max': 8.0,
            },
            'transition_contrast_boost': {
                'step_size': 0.5,
                'min': 1.0,
                'max': 32.0,
            },
            'mask_influence': {
                'step_size': 0.05,
                'min': 0.0,
                'max': 1.0,
            },
            'difference_threshold': {
                'step_size': 0.25,
                'min': 0.0,
                'max': 8.0,
            },
            'difference_contrast': {
                'step_size': 0.25,
                'min': 0.0,
                'max': 8.0,
            }
        }
        self.enabled = False
        self.draw_ui()

    def draw_ui(self):
        soft_inpainting_enabled = QCheckBox('Soft Inpainting')
        soft_inpainting_enabled.setChecked(False)
        soft_inpainting_enabled.toggled.connect(lambda: self.update_enabled(soft_inpainting_enabled.isChecked()))

        # Build the settings
        self.settings_widget = QWidget()
        self.settings_widget.setLayout(QFormLayout())
        self.settings_widget.layout().setContentsMargins(0,0,0,0)

        self.settings_widget.layout().addRow('Schedule Bais', self.create_row('schedule_bias'))
        self.settings_widget.layout().addRow('Preservation Strength', self.create_row('preservation_strength'))
        self.settings_widget.layout().addRow('Transition Contrast Boost', self.create_row('transition_contrast_boost'))
        self.settings_widget.layout().addRow('Mask Influence', self.create_row('mask_influence'))
        self.settings_widget.layout().addRow('Difference Threshold', self.create_row('difference_threshold'))
        self.settings_widget.layout().addRow('Difference Contrast', self.create_row('difference_contrast'))

        if self.settings_only:
            self.layout().addWidget(self.settings_widget)
        else:
            self.layout().addWidget(soft_inpainting_enabled)
            settings_collapsible = CollapsibleWidget('Soft Inpaint Settings', self.settings_widget) # Collapsible settings 
            self.layout().addWidget(settings_collapsible)

    def create_row(self, variable_name):
        # Pull constants from variable_parameters
        label = QLabel('%s' % self.variables[variable_name])

        slider = QSlider(Qt.Horizontal)
        # Slider works on ints
        multiplier = 10
        if self.variable_parameters[variable_name]['step_size'] < 0.1:
            multiplier = 100
        min = int(self.variable_parameters[variable_name]['min'] * multiplier)
        max = int(self.variable_parameters[variable_name]['max'] * multiplier)
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.setValue(int(self.variables[variable_name] * multiplier))
        slider.valueChanged.connect(lambda: self.update_row(label, variable_name, slider.value() / multiplier))

        row = QWidget()
        row.setLayout(QHBoxLayout())
        row.layout().setContentsMargins(0,0,0,0)
        row.layout().addWidget(slider)
        row.layout().addWidget(label)
        return row

    def update_enabled(self, enable):
        self.enabled = enable

    def update_row(self, label, variable_name, value):
        self.variables[variable_name] = value
        label.setText('%s' % value)

    def save_settings(self):
        self.settings_controller.set('soft_inpaint.schedule_bias', self.variables['schedule_bias'])
        self.settings_controller.set('soft_inpaint.preservation_strength', self.variables['preservation_strength'])
        self.settings_controller.set('soft_inpaint.transition_contrast_boost', self.variables['transition_contrast_boost'])
        self.settings_controller.set('soft_inpaint.mask_influence', self.variables['mask_influence'])
        self.settings_controller.set('soft_inpaint.difference_threshold', self.variables['difference_threshold'])
        self.settings_controller.set('soft_inpaint.difference_contrast', self.variables['difference_contrast'])
        self.settings_controller.save()

    def get_generation_data(self):
        if not self.enabled:
            return {}
        data = {
            "alwayson_scripts": {
                "Soft Inpainting": {
                    "args": [
                        True,
                        self.variables['schedule_bias'],
                        self.variables['preservation_strength'],
                        self.variables['transition_contrast_boost'],
                        self.variables['mask_influence'],
                        self.variables['difference_threshold'],
                        self.variables['difference_contrast']
                    ]
                }
            }
        }
        self.save_settings()
        return data
    
