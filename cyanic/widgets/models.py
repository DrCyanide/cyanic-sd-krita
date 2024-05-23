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
            'steps': 20,
        }
        self.server_const = {
            'models': [],
            'vaes': ['None'],
            'refiners': [],
            'samplers': [],
        }
        self.init_ui()
        self.load_server_data()
        self.load_settings()

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
        self.form_panel.layout().addRow('Model', self.model_box)

        # VAE select
        self.vae_box = QComboBox()
        self.vae_box.wheelEvent = lambda event : None
        self.vae_box.setMinimumContentsLength(VISIBLE_ITEMS)
        self.vae_box.setStyleSheet(STYLESHEET)
        self.vae_box.setMaxVisibleItems(VISIBLE_ITEMS)
        self.vae_box.setToolTip('Variational Autoencoder. If your images look desaturated, you probably need to download and use a VAE with it.')
        self.form_panel.layout().addRow('VAE', self.vae_box)

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

        self.form_panel.layout().addRow('Sampler', self.sampler_row)

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
        self.model_box.setHidden(self.settings_controller.get('hide_ui_model'))
        self.vae_box.setHidden(self.settings_controller.get('hide_ui_vae'))
        self.sampler_box.setHidden(self.settings_controller.get('hide_ui_sampler'))
        self.refiner_collapse.setHidden(self.settings_controller.get('hide_ui_refiner'))

    def load_server_data(self):
        # Refresh UI elements that depend on SD server settings (models, vaes, etc)
        self.server_const['samplers'], self.variables['sampler'] = self.api.get_samplers_and_default()
        self.server_const['models'], self.variables['model'] = self.api.get_models_and_default()
        self.server_const['vaes'], self.variables['vae'] = self.api.get_vaes_and_default()
        self.server_const['refiners'], self.variables['refiner'] = self.api.get_refiners_and_default()
        self.refresh_ui()

    def load_settings(self):
        # Refresh UI elements that depend on settings saved to file (prompt history, selected images, selected models, etc)
        self.variables['model'] = self.settings_controller.get('model')
        self.variables['vae'] = self.settings_controller.get('vae')
        self.variables['sampler'] = self.settings_controller.get('sampler')
        self.variables['steps'] = self.settings_controller.get('steps')
        self.variables['refiner'] = self.settings_controller.get('refiner')
        self.variables['refiner_enabled'] = self.settings_controller.get('refiner_enabled')
        self.variables['refiner_start'] = self.settings_controller.get('refiner_start')
        self.refresh_ui()

    def save_settings(self):
        # Write widget settings to settings_controller
        self.variables['model'] = self.model_box.currentText()
        self.variables['vae'] = self.vae_box.currentText()
        self.variables['sampler'] = self.sampler_box.currentText()
        self.variables['steps'] = self.steps_spin.value()
        self.variables['refiner'] = self.refiner_box.currentText()
        self.variables['refiner_enabled'] = self.refiner_enable.isChecked()
        self.variables['refiner_start'] = self.refiner_start_slider.value()

        for key in self.variables.keys():
            self.settings_controller.set(key, self.variables[key])
        self.settings_controller.save()

    def get_generation_data(self):
        # Return a formatted dict with data used to generate images.
        self.save_settings() # Updates the variables
        data = {**self.variables}
        # SD only starts the refiner if 'refiner' and 'refiner_start' is there.
        data.pop('refiner_enabled') # Unused by SD API
        if not self.variables['refiner_enabled']:
            # Remove the refiner stuff if it's not enabled
            data.pop('refiner')
            data.pop('refiner_start')
        return data

    # -----------------------
    # Widget specific methods
    # -----------------------

    def refresh_ui(self):
        # Model
        self.model_box.clear()
        try:
            self.model_box.addItems(self.server_const['models'])
            self.model_box.setCurrentText(self.variables['model'])
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


# class ModelsWidget(QWidget):
#     def __init__(self, settings_controller:SettingsController, api:SDAPI, ignore_hidden=False):
#         super().__init__()
#         self.settings_controller = settings_controller
#         self.api = api
#         self.ignore_hidden = ignore_hidden
#         self.setLayout(QVBoxLayout())
#         self.layout().setContentsMargins(0,0,0,0)
#         self.variables = {
#             'model': '',
#             'vae': '',
#             'enable_refiner': self.settings_controller.get('refiner_enabled'),
#             'refiner': '',
#             'refiner_start': self.settings_controller.get('refiner_start'),
#             'sampler': '',
#             'sampling_steps': self.settings_controller.get('steps'),
#         }
#         self.models = []
#         self.vaes = []
#         self.refiners = []
#         self.samplers = []

#         self.init_variables()

#         self.draw_ui()
    
#     def init_variables(self):
#         # Model
#         self.models, self.variables['model'] = self.api.get_models_and_default()
#         settings_model = self.settings_controller.get('model')
#         if settings_model is not None and len(settings_model) > 0 and settings_model in self.models:
#             self.variables['model'] = settings_model

#         # VAE
#         self.vaes, self.variables['vae'] = self.api.get_vaes_and_default()
#         settings_vae = self.settings_controller.get('vae')
#         if settings_vae is not None and len(settings_vae) > 0 and settings_vae in self.vaes:
#             self.variables['vae'] = settings_vae

#         # Refiner
#         self.refiners, self.variables['refiner'] = self.api.get_refiners_and_default() # Refiners are treated the same as models right now, but could change in the future
#         settings_refiner = self.settings_controller.get('refiner')
#         if settings_refiner is not None and len(settings_refiner) > 0 and settings_refiner in self.refiners:
#             self.variables['refiner'] = settings_refiner

#         # Sampler
#         self.samplers, self.variables['sampler'] = self.api.get_samplers_and_default()
#         settings_sampler = self.settings_controller.get('sampler')
#         if settings_sampler is not None and len(settings_sampler) > 0 and settings_sampler in self.samplers:
#             self.variables['sampler'] = settings_sampler

#         # Steps
#         self.variables['sampling_steps'] = self.settings_controller.get('steps')


#     def draw_ui(self):
#         select_form = QWidget()
#         select_form.setLayout(QFormLayout())
#         select_form.layout().setContentsMargins(0,0,0,0)

#         # Model Select
#         self.model_box = QComboBox()
#         # models, server_default_model = self.api.get_models_and_default()
#         self.model_box.addItems(self.models)
#         # self.model_box.setCurrentText(server_default_model)
#         self.model_box.setCurrentText(self.variables['model'])
#         self.model_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
#         self.model_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
#         self.model_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options

#         # Send the changed model to settings. It'll get saved when the generate button is clicked
#         self.model_box.currentTextChanged.connect(lambda: self._update_variables('model', self.model_box.currentText()))
#         self.model_box.setToolTip('SD Model')

#         if self.ignore_hidden or not self.settings_controller.get('hide_ui_model'):
#             select_form.layout().addRow('Model', self.model_box)

#         # VAE Select
#         self.vae_box = QComboBox()
#         # vaes, server_default_vae = self.api.get_vaes_and_default()
#         if not 'None' in self.vaes:
#             new_vaes = ['None']
#             for vae in self.vaes:
#                 new_vaes.append(vae)
#             self.vaes = new_vaes
#         self.vae_box.addItems(self.vaes)
#         self.vae_box.setCurrentText(self.variables['vae'])
#         self.vae_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
#         self.vae_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
#         self.vae_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
#         settings_vae = self.settings_controller.get('vae')
#         if len(settings_vae) > 0 and settings_vae in self.vaes:
#             self.vae_box.setCurrentText(settings_vae)
#         else:
#             self.settings_controller.set('vae', self.variables['vae'])
#         # Send the changed model to settings. It'll get saved when the generate button is clicked
#         self.vae_box.currentTextChanged.connect(lambda: self._update_variables('vae', self.vae_box.currentText()))
#         self.vae_box.setToolTip('VAE')

#         if self.ignore_hidden or not self.settings_controller.get('hide_ui_vae'):
#             select_form.layout().addRow('VAE', self.vae_box)
        
        
#         # Refiner enable
#         self.refiner_enable = QCheckBox()
#         self.refiner_enable.setChecked(self.variables['enable_refiner'])
#         self.refiner_enable.stateChanged.connect(lambda: self._update_variables('enable_refiner', self.refiner_enable.isChecked()))

#         # Refiner select
#         self.refiner_box = QComboBox()
#         # refiners, server_default_refiner = self.api.get_models_and_default()
#         self.refiner_box.addItems(self.refiners)
#         self.refiner_box.setCurrentText(self.variables['refiner'])
#         self.refiner_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
#         self.refiner_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
#         self.refiner_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
#         self.refiner_box.currentTextChanged.connect(lambda: self._update_variables('refiner', self.refiner_box.currentText()))
#         self.refiner_box.setToolTip('Refiner model')

#         # Refiner start at
#         refiner_start = QWidget()
#         refiner_start.setLayout(QHBoxLayout())
#         refiner_start.layout().setContentsMargins(0,0,0,0)
#         self.refiner_start_slider = QSlider(Qt.Horizontal)
#         self.refiner_start_slider.setTickInterval(10)
#         self.refiner_start_slider.setTickPosition(QSlider.TicksAbove)
#         self.refiner_start_slider.setMinimum(0)
#         self.refiner_start_slider.setMaximum(100)
#         self.refiner_start_slider.setValue(int(self.variables['refiner_start'] * 100))
#         self.refiner_start_slider.valueChanged.connect(lambda: self.update_slider(self.refiner_start_slider.value()))
#         refiner_start.layout().addWidget(self.refiner_start_slider)
#         self.refiner_start_label = QLabel()
#         self.refiner_start_label.setText('%s%%' % int(self.variables['refiner_start'] * 100))
#         refiner_start.layout().addWidget(self.refiner_start_label)

#         if self.ignore_hidden or not self.settings_controller.get('hide_ui_refiner'):
#             if self.api.supports_refiners:
#                 select_form.layout().addRow('Enable Refiner', self.refiner_enable)
#                 select_form.layout().addRow('Refiner', self.refiner_box)
#                 select_form.layout().addRow('Refiner start %', refiner_start)
#             else:
#                 message = QLabel()
#                 if self.api.host_version == 'SD.Next':
#                     message = QLabel('SD.Next setting "Execution Backend" must be "Diffusers" to use refiners.')
#                 else:
#                     message = QLabel("Your API doesn't support refiners")
#                 message.setWordWrap(True)
#                 select_form.layout().addRow('Refiner', message)
        
#         # Sampler and Steps
#         if self.ignore_hidden or not self.settings_controller.get('hide_ui_sampler'):
#             select_form.layout().addRow('Sampler', self._sampler_settings())

#         self.layout().addWidget(select_form)

#     def update_slider(self, value):
#         if value == 0:
#             self._update_variables('refiner_start', value)
#         else:
#             self._update_variables('refiner_start', value / 100)
#         self.refiner_start_label.setText('%s%%' % int(self.variables['refiner_start'] * 100))

#     def _sampler_settings(self):
#         sampler_row = QWidget()
#         sampler_row.setLayout(QHBoxLayout())
#         sampler_row.layout().setContentsMargins(0,0,0,0)

#         self.sampler_box = QComboBox()
#         # samplers, server_default_sampler = self.api.get_samplers_and_default()
#         self.sampler_box.addItems(self.samplers)
#         self.sampler_box.setCurrentText(self.variables['sampler'])
#         self.sampler_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
#         self.sampler_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
#         self.sampler_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
#         settings_sampler = self.settings_controller.get('sampler')
#         if len(settings_sampler) > 0 and settings_sampler in self.samplers:
#             self.sampler_box.setCurrentIndex(self.samplers.index(settings_sampler))
#         else:
#             self.settings_controller.set('sampler', self.variables['sampler'])
#         # Send the changed sampler to the settings. It'll get saved when the generate button is clicked
#         self.sampler_box.currentTextChanged.connect(lambda: self._update_variables('sampler', self.sampler_box.currentText()))
#         self.sampler_box.setToolTip('Sampling method')
#         sampler_row.layout().addWidget(self.sampler_box)

#         self.sampling_steps = QSpinBox()
#         self.sampling_steps.setMinimum(1)
#         # self.sampling_steps.setValue(self.settings_controller.get('defaults.sampling_steps'))
#         self.sampling_steps.setValue(self.variables['sampling_steps'])
#         self.sampling_steps.setMaximum(100)
#         self.sampling_steps.valueChanged.connect(lambda: self._update_variables('steps', self.sampling_steps.value()))
#         self.sampling_steps.setToolTip('Sampling steps')
#         sampler_row.layout().addWidget(self.sampling_steps)

#         return sampler_row
    
#     def _update_variables(self, key, value):
#         self.variables[key] = value

#     def save_settings(self):
#         self.settings_controller.set('model', self.variables['model'])
#         self.settings_controller.set('vae', self.variables['vae'])
#         self.settings_controller.set('sampler', self.variables['sampler'])
#         self.settings_controller.set('steps', self.variables['sampling_steps'])
#         self.settings_controller.set('enable_refiner', self.variables['enable_refiner'])
#         self.settings_controller.set('refiner', self.variables['refiner'])
#         self.settings_controller.set('refiner_start', self.variables['refiner_start'])
#         self.settings_controller.save()
    
#     def get_generation_data(self):
#         self.save_settings()
#         self.settings_controller.save()
#         data = {**self.variables}
#         if not data['enable_refiner']:
#             # Remove the refiner stuff if it's not enabled
#             # data['refiner'] = 'none'
#             # data['refiner_start'] = 1.0
#             data.pop('refiner')
#             data.pop('refiner_start')
#         data.pop('enable_refiner')
#         return data