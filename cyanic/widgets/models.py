from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import CollapsibleWidget, CyanicWidget, LabeledSlider

# Select model, VAE, sampler, steps for generation
class ModelsWidget(CyanicWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, ignore_hidden=False):
        super().__init__(settings_controller, api)
        self.variables = {
            'model': '',
            'vae': '',
            'refiner_enabled': False,
            'refiner': '',
            'refiner_start': 0.7,
            'sampler': '',
            'scheduler': '',
            'steps': 20,
        }
        self.server_const = {
            'models': [],
            'vaes': ['None'],
            'refiners': [],
            'samplers': [],
            'schedulers': [],
        }
        self.init_ui()
        self.set_widget_values()

    def get_simplified_model_names(self):
        # Remove the extension if there is one
        return [self.get_simplified_name(x) for x in self.server_const['models']]
    
    def get_simplified_name(self, name):
        if '.' in name:
            return '.'.join(name.split('.')[:-1])
        return name

    def get_full_model_name(self, short_name):
        matched_name = [x for x in self.server_const['models'] if self.get_simplified_name(x) == short_name]
        if len(matched_name) > 0:
            return matched_name[0]
        return ''

    def set_widget_values(self):
        # Model
        self.model_box.clear()
        try:
            # self.model_box.addItems(self.server_const['models'])
            # self.model_box.setCurrentText(self.variables['model'])
            simple_model_names = self.get_simplified_model_names()
            self.model_box.addItems(simple_model_names)
            self.model_box.setCurrentText(self.get_simplified_name(self.variables['model']))
        except:
            self.model_box.setCurrentIndex(0)

        # VAE
        self.vae_box.clear()
        try:
            self.vae_box.addItems(self.server_const['vaes'])
            self.vae_box.setCurrentText(self.variables['vae'])
        except:
            self.vae_box.setCurrentIndex(0)

        # Sampler
        self.sampler_box.clear()
        try:
            self.sampler_box.addItems(self.server_const['samplers'])
            self.sampler_box.setCurrentText(self.variables['sampler'])
        except:
            self.sampler_box.setCurrentIndex(0)

        # Steps
        self.steps_spin.setValue(self.variables['steps'])

        # Scheduler (Added in A1111 1.10)
        self.scheduler_box.clear()
        try:
            self.scheduler_box.addItems(self.server_const['schedulers'])
            self.scheduler_box.setCurrentText(self.variables['scheduler'])
        except:
            self.scheduler_box.setCurrentIndex(0)

        # Refiner
        self.refiner_box.clear()
        try:
            self.refiner_box.addItems(self.server_const['refiners'])
            self.refiner_box.setCurrentText(self.variables['refiner'])
        except:
            self.refiner_box.setCurrentIndex(0)

        # Refiner start
        self.refiner_start_slider.set_value(self.variables['refiner_start'])

        # Refiner enabled
        self.refiner_enable.setChecked(self.variables['refiner_enabled'])

        self.handle_hidden()


    def init_ui(self):
        VISIBLE_ITEMS = 10
        STYLESHEET = "QComboBox { combobox-popup: 0; }"

        self.form_panel = QWidget()
        self.form_panel.setLayout(QFormLayout())
        self.form_panel.layout().setContentsMargins(0,0,0,0)

        # Model select
        self.model_box = QComboBox()
        self.model_box.wheelEvent = lambda event : None
        self.model_box.setMinimumContentsLength(VISIBLE_ITEMS) # Allows the box to be smaller than the longest item's char length
        self.model_box.setStyleSheet(STYLESHEET) # Needed for setMaxVisibleItems to work
        self.model_box.setMaxVisibleItems(VISIBLE_ITEMS) # Suppose to limit the number of visible options
        self.model_box.setToolTip('SD Model')
        # self.form_panel.layout().addRow('Model', self.model_box)
        self.model_box_label = QLabel('Model')
        self.form_panel.layout().addRow(self.model_box_label, self.model_box)

        # VAE select
        self.vae_box = QComboBox()
        self.vae_box.wheelEvent = lambda event : None
        self.vae_box.setMinimumContentsLength(VISIBLE_ITEMS)
        self.vae_box.setStyleSheet(STYLESHEET)
        self.vae_box.setMaxVisibleItems(VISIBLE_ITEMS)
        self.vae_box.setToolTip('Variational Autoencoder. If your images look desaturated, you probably need to download and use a VAE with it.')
        # self.form_panel.layout().addRow('VAE', self.vae_box)
        self.vae_box_label = QLabel('VAE')
        self.form_panel.layout().addRow(self.vae_box_label, self.vae_box)

        # Sampler + Steps
        self.sampler_row = QWidget()
        self.sampler_row.setLayout(QHBoxLayout())
        self.sampler_row.layout().setContentsMargins(0,0,0,0)

        self.sampler_box = QComboBox()
        self.sampler_box.wheelEvent = lambda event : None
        self.sampler_box.setMinimumContentsLength(VISIBLE_ITEMS)
        self.sampler_box.setStyleSheet(STYLESHEET)
        self.sampler_box.setMaxVisibleItems(VISIBLE_ITEMS)
        self.sampler_box.setToolTip('Samplers change how the image is generated.')
        self.sampler_row.layout().addWidget(self.sampler_box)

        self.steps_spin = QSpinBox()
        self.steps_spin.wheelEvent = lambda event : None
        self.steps_spin.setMinimum(1)
        self.steps_spin.setMaximum(100)
        self.steps_spin.setValue(self.variables['steps'])
        self.steps_spin.setToolTip('How many times SD should try to improve the image. More isn\'t always better.')

        self.sampler_row.layout().addWidget(self.steps_spin)

        # self.form_panel.layout().addRow('Sampler', self.sampler_row)
        self.sampler_row_label = QLabel('Sampler')
        self.form_panel.layout().addRow(self.sampler_row_label, self.sampler_row)

        # Scheduler (Added in A1111 1.10)
        self.scheduler_box = QComboBox()
        self.scheduler_box.wheelEvent = lambda event: None
        self.scheduler_box.setMinimumContentsLength(VISIBLE_ITEMS)
        self.scheduler_box.setStyleSheet(STYLESHEET)
        self.scheduler_box.setMaxVisibleItems(VISIBLE_ITEMS)
        # self.scheduler_box.setToolTip('') # To be honest, I don't know how to describe this
        # self.form_panel.layout().addRow('Scheduler', self.scheduler_box)
        self.scheduler_box_label = QLabel('Scheduler')
        self.form_panel.layout().addRow(self.scheduler_box_label, self.scheduler_box)

        self.layout().addWidget(self.form_panel)

        # Refiner Collapse
        self.refiner_settings = QWidget()
        self.refiner_settings.setLayout(QFormLayout())
        self.refiner_settings.layout().setContentsMargins(0,0,0,0)

        self.refiner_collapse = CollapsibleWidget('Refiner', self.refiner_settings)
        self.layout().addWidget(self.refiner_collapse)

        # Refiner enable
        self.refiner_enable = QCheckBox()
        self.refiner_enable.setToolTip('A Refiner lets you switch to another model partway through generating an image. Some SD servers require specific settings to use refiners.')
        self.refiner_settings.layout().addRow('Enable Refiner', self.refiner_enable)

        # Refiner select
        self.refiner_box = QComboBox()
        self.refiner_box.wheelEvent = lambda event : None
        self.refiner_box.setMinimumContentsLength(VISIBLE_ITEMS)
        self.refiner_box.setStyleSheet(STYLESHEET)
        self.refiner_box.setMaxVisibleItems(VISIBLE_ITEMS)
        self.refiner_box.setToolTip('Refiner model')

        self.refiner_settings.layout().addRow('Refiner', self.refiner_box)

        # Refiner start
        self.refiner_start_slider = LabeledSlider()
        self.refiner_settings.layout().addRow('Refiner start', self.refiner_start_slider)

    def handle_hidden(self):
        # Hide widgets that settings specify shouldn't show up. Must be called in init_ui() and on load_settings()
        # Due to the row nature of the layout, this may encounter issues.

        # The rows can't be hidden like this... they don't hide the title
        self.model_box.setHidden(self.settings_controller.get('hide_ui_model'))
        self.model_box_label.setHidden(self.settings_controller.get('hide_ui_model'))

        self.vae_box.setHidden(self.settings_controller.get('hide_ui_vae'))
        self.vae_box_label.setHidden(self.settings_controller.get('hide_ui_vae'))

        self.sampler_row.setHidden(self.settings_controller.get('hide_ui_sampler'))
        self.sampler_row_label.setHidden(self.settings_controller.get('hide_ui_sampler'))

        self.scheduler_box.setHidden(self.settings_controller.get('hide_ui_scheduler') or len(self.server_const['schedulers']) == 0) # Older versions don't expose this, so hide it if the server doesn't support it
        self.scheduler_box_label.setHidden(self.settings_controller.get('hide_ui_scheduler') or len(self.server_const['schedulers']) == 0) # Older versions don't expose this, so hide it if the server doesn't support it
        
        self.refiner_collapse.setHidden(self.settings_controller.get('hide_ui_refiner'))

    def load_server_data(self):
        # Refresh UI elements that depend on SD server settings (models, vaes, etc)
        self.server_const['samplers'], self.variables['sampler'] = self.api.get_samplers_and_default()
        self.server_const['schedulers'], self.variables['scheduler'] = self.api.get_schedulers_and_default()
        self.server_const['models'], self.variables['model'] = self.api.get_models_and_default()
        self.server_const['vaes'], self.variables['vae'] = self.api.get_vaes_and_default()
        self.server_const['refiners'], self.variables['refiner'] = self.api.get_refiners_and_default()
        self.set_widget_values()

    def load_settings(self):
        # Refresh UI elements that depend on settings saved to file (prompt history, selected images, selected models, etc)
        super().load_settings()
        self.set_widget_values()

    def save_settings(self):
        # Write widget settings to settings_controller
        # self.variables['model'] = self.model_box.currentText()
        # full_model_name = [x for x in self.server_const['models'] if x.rsplit('.')[0] == self.model_box.currentText()]
        # if len(full_model_name) > 0:
        #     full_model_name = full_model_name[0]
        # else:
        #     full_model_name = ''
        # self.variables['model'] = full_model_name
        self.variables['model'] = self.get_full_model_name(self.model_box.currentText())

        self.variables['vae'] = self.vae_box.currentText()
        self.variables['sampler'] = self.sampler_box.currentText()
        self.variables['scheduler'] = self.scheduler_box.currentText()
        self.variables['steps'] = self.steps_spin.value()
        self.variables['refiner'] = self.refiner_box.currentText()
        self.variables['refiner_enabled'] = self.refiner_enable.isChecked()
        self.variables['refiner_start'] = self.refiner_start_slider.value()

        for key in self.variables.keys():
            self.settings_controller.set(key, self.variables[key])
        
        
        # self.settings_controller.save()

    def get_generation_data(self):
        # Return a formatted dict with data used to generate images.
        self.save_settings() # Updates the variables
        data = {**self.variables}

        # Remove the scheduler if it's not supported by the server
        if len(self.server_const['schedulers']) == 0:
            data.pop('scheduler')

        # SD only starts the refiner if 'refiner' and 'refiner_start' is there.
        data.pop('refiner_enabled') # Unused by SD API
        if not self.variables['refiner_enabled']:
            # Remove the refiner stuff if it's not enabled
            data.pop('refiner')
            data.pop('refiner_start')
        return data
