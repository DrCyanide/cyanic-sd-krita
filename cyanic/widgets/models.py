from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController

# Select model, VAE, sampler, steps for generation
# Yes, a better name would've been nice. No, I couldn't think of one
class ModelsWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, ignore_hidden=False):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.ignore_hidden = ignore_hidden
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {
            'model': '',
            'vae': '',
            'sampler': '',
            'steps': '',
        }
        self.init_variables()

        self.draw_ui()
    
    def init_variables(self):
        # Model
        models, self.variables['model'] = self.api.get_models_and_default()
        settings_model = self.settings_controller.get('defaults.model')
        if len(settings_model) > 0 and settings_model in models:
            self.variables['model'] = settings_model

        # VAE
        vaes, self.variables['vae'] = self.api.get_vaes_and_default()
        settings_vae = self.settings_controller.get('defaults.vae')
        if len(settings_vae) > 0 and settings_vae in vaes:
            self.variables['vae'] = settings_vae

        # Sampler
        samplers, self.variables['sampler'] = self.api.get_samplers_and_default()
        settings_sampler = self.settings_controller.get('defaults.sampler')
        if len(settings_sampler) > 0 and settings_sampler in samplers:
            self.variables['sampler'] = settings_sampler

        # Steps
        self.variables['steps'] = self.settings_controller.get('defaults.sampling_steps')


    def draw_ui(self):
        select_form = QWidget()
        select_form.setLayout(QFormLayout())
        select_form.layout().setContentsMargins(0,0,0,0)

        # Model Select
        self.model_box = QComboBox()
        models, server_default_model = self.api.get_models_and_default()
        self.model_box.addItems(models)
        # self.model_box.setCurrentText(server_default_model)
        self.model_box.setCurrentText(self.variables['model'])
        self.model_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.model_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.model_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        # settings_model = self.settings_controller.get('defaults.model')
        # if len(settings_model) > 0 and settings_model in models:
        #     self.model_box.setCurrentText(settings_model)
        # else:
        #     # The model might be deleted?
        #     self.settings_controller.set('defaults.model', server_default_model)
        # # Send the changed model to settings. It'll get saved when the generate button is clicked
        # self.model_box.currentTextChanged.connect(lambda: self.settings_controller.set('defaults.model', self.model_box.currentText()))
        self.model_box.currentTextChanged.connect(lambda: self._update_variables('model', self.model_box.currentText()))
        self.model_box.setToolTip('SD Model')

        if self.ignore_hidden or not self.settings_controller.get('hide_ui.model'):
            select_form.layout().addRow('Model', self.model_box)

        # VAE Select
        self.vae_box = QComboBox()
        vaes, server_default_vae = self.api.get_vaes_and_default()
        if not 'None' in vaes:
            new_vaes = ['None']
            for vae in vaes:
                new_vaes.append(vae)
            vaes = new_vaes
        self.vae_box.addItems(vaes)
        self.vae_box.setCurrentText(server_default_vae)
        self.vae_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.vae_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.vae_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        settings_vae = self.settings_controller.get('defaults.vae')
        if len(settings_vae) > 0 and settings_vae in vaes:
            self.vae_box.setCurrentText(settings_vae)
        else:
            self.settings_controller.set('defaults.vae', server_default_vae)
        # Send the changed model to settings. It'll get saved when the generate button is clicked
        # self.vae_box.currentTextChanged.connect(lambda: self.settings_controller.set('defaults.vae', self.vae_box.currentText()))
        self.vae_box.currentTextChanged.connect(lambda: self._update_variables('vae', self.vae_box.currentText()))
        self.vae_box.setToolTip('VAE')

        if self.ignore_hidden or not self.settings_controller.get('hide_ui.vae'):
            select_form.layout().addRow('VAE', self.vae_box)
        

        # Sampler and Steps
        if self.ignore_hidden or not self.settings_controller.get('hide_ui.sampler'):
            select_form.layout().addRow('Sampler', self._sampler_settings())

        self.layout().addWidget(select_form)

    def _sampler_settings(self):
        sampler_row = QWidget()
        sampler_row.setLayout(QHBoxLayout())
        sampler_row.layout().setContentsMargins(0,0,0,0)

        self.sampler_box = QComboBox()
        samplers, server_default_sampler = self.api.get_samplers_and_default()
        self.sampler_box.addItems(samplers)
        self.sampler_box.setCurrentText(server_default_sampler)
        self.sampler_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.sampler_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.sampler_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        settings_sampler = self.settings_controller.get('defaults.sampler')
        if len(settings_sampler) > 0 and settings_sampler in samplers:
            self.sampler_box.setCurrentIndex(samplers.index(settings_sampler))
        else:
            self.settings_controller.set('defaults.sampler', server_default_sampler)
        # Send the changed sampler to the settings. It'll get saved when the generate button is clicked
        # self.sampler_box.currentTextChanged.connect(lambda: self.settings_controller.set('defaults.sampler', self.sampler_box.currentText()))
        self.sampler_box.currentTextChanged.connect(lambda: self._update_variables('sampler', self.sampler_box.currentText()))
        self.sampler_box.setToolTip('Sampling method')
        sampler_row.layout().addWidget(self.sampler_box)

        self.sampling_steps = QSpinBox()
        self.sampling_steps.setMinimum(1)
        # self.sampling_steps.setValue(self.settings_controller.get('defaults.sampling_steps'))
        self.sampling_steps.setValue(self.variables['steps'])
        self.sampling_steps.setMaximum(100)
        # self.sampling_steps.valueChanged.connect(lambda: self.settings_controller.set('defaults.sampling_steps', self.sampling_steps.value()))
        self.sampling_steps.valueChanged.connect(lambda: self._update_variables('sampling_steps', self.sampling_steps.value()))
        self.sampling_steps.setToolTip('Sampling steps')
        sampler_row.layout().addWidget(self.sampling_steps)

        return sampler_row
    
    def _update_variables(self, key, value):
        self.variables[key] = value

    def save_settings(self):
        self.settings_controller.set('defaults.model', self.variables['model'])
        self.settings_controller.set('defaults.vae', self.variables['vae'])
        self.settings_controller.set('defaults.sampler', self.variables['sampler'])
        self.settings_controller.set('defaults.sampling_steps', self.variables['steps'])
    
    def get_generation_data(self):
        # data = {
        #     'model': self.settings_controller.get('defaults.model'),
        #     'vae': self.settings_controller.get('defaults.vae'), # Note: Not sure if 'None', None, or '' are the expected value for the API
        #     'sampler': self.settings_controller.get('defaults.sampler'),
        #     'steps': self.settings_controller.get('defaults.sampling_steps'),
        # }
        self.save_settings()
        self.settings_controller.save()
        # return data
        return self.variables