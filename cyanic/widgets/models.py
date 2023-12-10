from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
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
            'enable_refiner': self.settings_controller.get('defaults.enable_refiner'),
            'refiner': '',
            'refiner_start': self.settings_controller.get('defaults.refiner_start'),
            'sampler': '',
            'sampling_steps': self.settings_controller.get('defaults.sampling_steps'),
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

        # Refiner
        refiners, self.variables['refiner'] = self.api.get_refiners_and_default() # Refiners are treated the same as models right now, but could change in the future
        settings_refiner = self.settings_controller.get('defaults.refiner')
        if len(settings_refiner) > 0 and settings_refiner in refiners:
            self.variables['refiner'] = settings_refiner

        # Sampler
        samplers, self.variables['sampler'] = self.api.get_samplers_and_default()
        settings_sampler = self.settings_controller.get('defaults.sampler')
        if len(settings_sampler) > 0 and settings_sampler in samplers:
            self.variables['sampler'] = settings_sampler

        # Steps
        self.variables['sampling_steps'] = self.settings_controller.get('defaults.sampling_steps')


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
        self.vae_box.currentTextChanged.connect(lambda: self._update_variables('vae', self.vae_box.currentText()))
        self.vae_box.setToolTip('VAE')

        if self.ignore_hidden or not self.settings_controller.get('hide_ui.vae'):
            select_form.layout().addRow('VAE', self.vae_box)
        
        
        # Refiner enable
        self.refiner_enable = QCheckBox()
        self.refiner_enable.setChecked(self.variables['enable_refiner'])
        self.refiner_enable.stateChanged.connect(lambda: self._update_variables('enable_refiner', self.refiner_enable.isChecked()))

        # Refiner select
        self.refiner_box = QComboBox()
        refiners, server_default_refiner = self.api.get_models_and_default()
        self.refiner_box.addItems(refiners)
        self.refiner_box.setCurrentText(self.variables['refiner'])
        self.refiner_box.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        self.refiner_box.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        self.refiner_box.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        self.refiner_box.currentTextChanged.connect(lambda: self._update_variables('refiner', self.refiner_box.currentText()))
        self.refiner_box.setToolTip('Refiner model')

        # Refiner start at
        refiner_start = QWidget()
        refiner_start.setLayout(QHBoxLayout())
        refiner_start.layout().setContentsMargins(0,0,0,0)
        self.refiner_start_slider = QSlider(Qt.Horizontal)
        self.refiner_start_slider.setTickInterval(10)
        self.refiner_start_slider.setTickPosition(QSlider.TicksAbove)
        self.refiner_start_slider.setMinimum(0)
        self.refiner_start_slider.setMaximum(100)
        self.refiner_start_slider.setValue(int(self.variables['refiner_start'] * 100))
        self.refiner_start_slider.valueChanged.connect(lambda: self.update_slider(self.refiner_start_slider.value()))
        refiner_start.layout().addWidget(self.refiner_start_slider)
        self.refiner_start_label = QLabel()
        self.refiner_start_label.setText('%s%%' % int(self.variables['refiner_start'] * 100))
        refiner_start.layout().addWidget(self.refiner_start_label)

        if self.ignore_hidden or not self.settings_controller.get('hide_ui.refiner'):
            if self.api.supports_refiners:
                select_form.layout().addRow('Enable Refiner', self.refiner_enable)
                select_form.layout().addRow('Refiner', self.refiner_box)
                select_form.layout().addRow('Refiner start %', refiner_start)
            else:
                message = QLabel()
                if self.api.host_version == 'SD.Next':
                    message = QLabel('SD.Next setting "Execution Backend" must be "Diffusers" to use refiners.')
                else:
                    message = QLabel("Your API doesn't support refiners")
                message.setWordWrap(True)
                select_form.layout().addRow('Refiner', message)
        
        # Sampler and Steps
        if self.ignore_hidden or not self.settings_controller.get('hide_ui.sampler'):
            select_form.layout().addRow('Sampler', self._sampler_settings())

        self.layout().addWidget(select_form)

    def update_slider(self, value):
        if value == 0:
            self._update_variables('refiner_start', value)
        else:
            self._update_variables('refiner_start', value / 100)
        self.refiner_start_label.setText('%s%%' % int(self.variables['refiner_start'] * 100))

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
        self.sampler_box.currentTextChanged.connect(lambda: self._update_variables('sampler', self.sampler_box.currentText()))
        self.sampler_box.setToolTip('Sampling method')
        sampler_row.layout().addWidget(self.sampler_box)

        self.sampling_steps = QSpinBox()
        self.sampling_steps.setMinimum(1)
        # self.sampling_steps.setValue(self.settings_controller.get('defaults.sampling_steps'))
        self.sampling_steps.setValue(self.variables['sampling_steps'])
        self.sampling_steps.setMaximum(100)
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
        self.settings_controller.set('defaults.sampling_steps', self.variables['sampling_steps'])
        self.settings_controller.set('defaults.enable_refiner', self.variables['enable_refiner'])
        self.settings_controller.set('defaults.refiner', self.variables['refiner'])
        self.settings_controller.set('defaults.refiner_start', self.variables['refiner_start'])
        self.settings_controller.save()
    
    def get_generation_data(self):
        self.save_settings()
        self.settings_controller.save()
        data = {**self.variables}
        if not data['enable_refiner']:
            # Remove the refiner stuff if it's not enabled
            # data['refiner'] = 'none'
            # data['refiner_start'] = 1.0
            data.pop('refiner')
            data.pop('refiner_start')
        data.pop('enable_refiner')
        return data