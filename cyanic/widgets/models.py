from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController

# Select model, VAE, sampler, steps for generation
# Yes, a better name would've been nice. No, I couldn't think of one
class ModelsWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        select_form = QWidget()
        select_form.setLayout(QFormLayout())
        select_form.layout().setContentsMargins(0,0,0,0)

        # Model Select
        self.model_box = QComboBox()
        models, server_default = self.api.get_models_and_default()
        self.model_box.addItems(models)
        self.model_box.setCurrentText(server_default)
        self.model_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.model_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.model_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        settings_model = self.settings_controller.get('defaults.model')
        if len(settings_model) > 0 and settings_model in models:
            self.model_box.setCurrentText(settings_model)
        # Send the changed model to settings. It'll get saved when the generate button is clicked
        self.model_box.currentTextChanged.connect(lambda: self.settings_controller.set('defaults.model', self.model_box.currentText()))
        self.model_box.setToolTip('SD Model')

        select_form.layout().addRow('Model', self.model_box)

        # VAE Select
        self.vae_box = QComboBox()
        vaes, server_default = self.api.get_vaes_and_default()
        if not 'None' in vaes:
            new_vaes = ['None']
            for vae in vaes:
                new_vaes.append(vae)
            vaes = new_vaes
        self.vae_box.addItems(vaes)
        self.vae_box.setCurrentText(server_default)
        self.vae_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.vae_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.vae_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        settings_vae = self.settings_controller.get('defaults.vae')
        if len(settings_vae) > 0 and settings_vae in vaes:
            self.vae_box.setCurrentText(settings_vae)
        else:
            self.vae_box.setCurrentIndex(0)
        # Send the changed model to settings. It'll get saved when the generate button is clicked
        self.vae_box.currentTextChanged.connect(lambda: self.settings_controller.set('defaults.vae', self.vae_box.currentText()))
        self.vae_box.setToolTip('VAE')

        select_form.layout().addRow('VAE', self.vae_box)
        

        # Sampler and Steps
        # self.layout().addWidget(self._sampler_settings())
        select_form.layout().addRow('Sampler', self._sampler_settings())

        self.layout().addWidget(select_form)

    def _sampler_settings(self):
        sampler_row = QWidget()
        sampler_row.setLayout(QHBoxLayout())
        sampler_row.layout().setContentsMargins(0,0,0,0)

        self.sampler_box = QComboBox()
        samplers, server_default = self.api.get_samplers_and_default()
        self.sampler_box.addItems(samplers)
        self.sampler_box.setCurrentText(server_default)
        self.sampler_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.sampler_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.sampler_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        settings_sampler = self.settings_controller.get('defaults.sampler')
        if len(settings_sampler) > 0 and settings_sampler in samplers:
            self.sampler_box.setCurrentIndex(samplers.index(settings_sampler))
        # Send the changed sampler to the settings. It'll get saved when the generate button is clicked
        self.sampler_box.currentTextChanged.connect(lambda: self.settings_controller.set('defaults.sampler', self.sampler_box.currentText()))
        self.sampler_box.setToolTip('Sampling method')
        sampler_row.layout().addWidget(self.sampler_box)

        self.sampling_steps = QSpinBox()
        self.sampling_steps.setMinimum(1)
        self.sampling_steps.setValue(self.settings_controller.get('defaults.sampling_steps'))
        self.sampling_steps.setMaximum(100)
        self.sampling_steps.valueChanged.connect(lambda: self.settings_controller.set('defaults.sampling_steps', self.sampling_steps.value()))
        self.sampling_steps.setToolTip('Sampling steps')
        sampler_row.layout().addWidget(self.sampling_steps)

        return sampler_row
    
    def get_generation_data(self):
        data = {
            'model': self.settings_controller.get('defaults.model'),
            'vae': self.settings_controller.get('defaults.vae'), # Note: Not sure if 'None', None, or '' are the expected value for the API
            'sampler': self.settings_controller.get('defaults.sampler'),
            'steps': self.settings_controller.get('defaults.sampling_steps'),
        }
        self.settings_controller.save()
        return data