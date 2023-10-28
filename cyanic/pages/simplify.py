from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import *

class SimplifyPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.setLayout(QVBoxLayout())
        self.auto_save = self.settings_controller.get('hide_ui.auto_save')
        self.hidden = {
            'model': self.settings_controller.get('hide_ui.model'),
            'vae': self.settings_controller.get('hide_ui.vae'),
            'sampler': self.settings_controller.get('hide_ui.sampler'),
            'batch': self.settings_controller.get('hide_ui.batch'),
            'seed': self.settings_controller.get('hide_ui.seed'),
            'negative_prompt': self.settings_controller.get('hide_ui.negative_prompt'),
            'styles': self.settings_controller.get('hide_ui.styles'),
            'extra_networks': self.settings_controller.get('hide_ui.extra_networks'),
            'color_correction': self.settings_controller.get('hide_ui.color_correction'),
            'denoise_strength': self.settings_controller.get('hide_ui.denoise_strength'),
            'extensions': self.settings_controller.get('hide_ui.extensions'),
            'hidden_extensions': self.settings_controller.get('hide_ui.hidden_extensions'),
            'controlnet_preprocessor_settings': self.settings_controller.get('hide_ui.controlnet_preprocessor_settings'),
            'controlnet_fine_settings': self.settings_controller.get('hide_ui.controlnet_fine_settings'),
            'inpaint_auto_update': self.settings_controller.get('hide_ui.inpaint_auto_update'),
            'inpaint_below_mask': self.settings_controller.get('hide_ui.inpaint_below_mask'),
            'inpaint_hide_mask': self.settings_controller.get('hide_ui.inpaint_hide_mask'),
        }
        self.server_supported = {
            'controlnet': self.api.script_installed('controlnet'),
            'adetailer': self.api.script_installed('adetailer'),
        }
        self.variables = {
            # These are variables that can't be updated by importing their component widget
            'auto_update_mask': self.settings_controller.get('inpaint.auto_update_mask'),
            'results_below_mask': self.settings_controller.get('inpaint.results_below_mask'),
            'hide_mask_on_gen': self.settings_controller.get('inpaint.hide_mask_on_gen'),
        }

        self.draw_ui()

    def draw_ui(self):
        instructions = QLabel("Reducing the clutter in the UI by hiding settings. Hidden settings will still be applied during generation. If you adjust a default setting remember to click the 'Save' button at the bottom of the page.")
        instructions.setWordWrap(True)
        self.layout().addWidget(instructions)

        # Autosave
        autosave_cb = QCheckBox('Autosave hidden changes (NOT default settings!)')
        autosave_cb.setChecked(self.auto_save)
        autosave_cb.stateChanged.connect(lambda: self._update_autosave(autosave_cb.isChecked()))
        self.layout().addWidget(autosave_cb)

        # Models
        model_settings = QGroupBox('Model')
        model_settings.setLayout(QVBoxLayout())

        hide_model = self._setup_checkbox('Hide Model', 'model')
        model_settings.layout().addWidget(hide_model)

        hide_vae = self._setup_checkbox('Hide VAE', 'vae')
        model_settings.layout().addWidget(hide_vae)

        hide_sampler = self._setup_checkbox('Hide Sampler and Steps', 'sampler')
        model_settings.layout().addWidget(hide_sampler)

        self.model_widget = ModelsWidget(self.settings_controller, self.api, ignore_hidden=True)
        model_settings.layout().addWidget(self.model_widget)

        self.layout().addWidget(model_settings)

        # Img2Img and Inpainting
        img2img_settings = QGroupBox('Img2Img and Inpainting')
        img2img_settings.setLayout(QVBoxLayout())        

        hide_denoise_strength = self._setup_checkbox('Hide Denoise Strength', 'denoise_strength')
        img2img_settings.layout().addWidget(hide_denoise_strength)

        hide_color_correction = self._setup_checkbox('Hide Color Correction', 'color_correction')
        img2img_settings.layout().addWidget(hide_color_correction)

        img2img_settings.layout().addWidget(QSplitter())

        self.denoise_widget = DenoiseWidget(self.settings_controller)
        img2img_settings.layout().addWidget(self.denoise_widget)

        self.color_correction = ColorCorrectionWidget(self.settings_controller, self.api)
        img2img_settings.layout().addWidget(self.color_correction)

        self.layout().addWidget(img2img_settings)

        # Inpaint Only settings
        inpaint_settings = QGroupBox('Inpainting')
        inpaint_settings.setLayout(QVBoxLayout())

        hide_auto_update = self._setup_checkbox('Hide Update Mask before Generation', 'inpaint_auto_update')
        inpaint_settings.layout().addWidget(hide_auto_update)

        hide_below_mask = self._setup_checkbox('Hide Results below Mask', 'inpaint_below_mask')
        inpaint_settings.layout().addWidget(hide_below_mask)
        
        hide_hide_mask = self._setup_checkbox('Hide... hide mask while generating', 'inpaint_hide_mask')
        hide_hide_mask.setToolTip('Yeah, I know...')
        inpaint_settings.layout().addWidget(hide_hide_mask)

        # TODO: add Mask Blur, Mask Mode, Masked Content, Inpaint Area

        # Update Mask before Generating
        auto_update_mask_cb = QCheckBox('Update mask before generating')
        auto_update_mask_cb.setToolTip('Will remember the last layer used as a mask and use the current state of that layer whenever the "Generate" button is clicked')
        auto_update_mask_cb.setChecked(self.variables['auto_update_mask'])
        auto_update_mask_cb.stateChanged.connect(lambda: self._update_variable('auto_update_mask', auto_update_mask_cb.isChecked()))
        inpaint_settings.layout().addWidget(auto_update_mask_cb)

        # Add Results below Mask
        results_below_mask_cb = QCheckBox('Results below mask')
        results_below_mask_cb.setToolTip('Will insert the results as a new layer below the mask')
        results_below_mask_cb.setChecked(self.variables['results_below_mask'])
        results_below_mask_cb.stateChanged.connect(lambda: self._update_variable('results_below_mask', results_below_mask_cb.isChecked()))
        inpaint_settings.layout().addWidget(results_below_mask_cb)

        # Hide mask on generation
        hide_mask_cb = QCheckBox('Hide mask when generating')
        hide_mask_cb.setToolTip('Turns off mask visibility so that you can see the results faster')
        hide_mask_cb.setChecked(self.variables['hide_mask_on_gen'])
        hide_mask_cb.stateChanged.connect(lambda: self._update_variable('hide_mask_on_gen', hide_mask_cb.isChecked()))
        inpaint_settings.layout().addWidget(hide_mask_cb)

        self.layout().addWidget(inpaint_settings)
        

        # Batch
        batch_settings = QGroupBox('Batch')
        batch_settings.setLayout(QVBoxLayout())

        hide_batch = self._setup_checkbox('Hide Batch Settings', 'batch')
        batch_settings.layout().addWidget(hide_batch)

        self.batch_widget = BatchWidget(self.settings_controller, self.api)
        batch_settings.layout().addWidget(self.batch_widget)
        self.layout().addWidget(batch_settings)

        # Seed
        seed_settings = QGroupBox('Seed')
        seed_settings.setLayout(QVBoxLayout())

        hide_seed = self._setup_checkbox('Hide Seed Settings', 'seed')
        seed_settings.layout().addWidget(hide_seed)
        
        self.seed_widget = SeedWidget(self.settings_controller)
        seed_settings.layout().addWidget(self.seed_widget)
        self.layout().addWidget(seed_settings)
        
        # Prompts
        prompt_settings = QGroupBox('Prompts')
        prompt_settings.setLayout(QVBoxLayout())
        # Negative Prompt
        hide_negative_prompt = self._setup_checkbox('Hide Negative Prompt', 'negative_prompt')
        prompt_settings.layout().addWidget(hide_negative_prompt)
        # Styles
        hide_styles = self._setup_checkbox('Hide Styles', 'styles')
        prompt_settings.layout().addWidget(hide_styles)
        # Extra Networks
        hide_extra_networks = self._setup_checkbox('Hide Extra Networks', 'extra_networks')
        prompt_settings.layout().addWidget(hide_extra_networks)
        self.layout().addWidget(prompt_settings)

        # CFG
        # Clip Skip
        # Color Correction
        # Hires Fix

        # Extensions
        extension_settings = QGroupBox('Extensions')
        extension_settings.setLayout(QVBoxLayout())

        hide_extensions = self._setup_checkbox('Hide All Extensions', 'extensions')
        extension_settings.layout().addWidget(hide_extensions)
        
        if self.server_supported['controlnet']:
            controlnet_settings = QGroupBox('ControlNet')
            controlnet_settings.setLayout(QVBoxLayout())

            hide_controlnet = self._setup_checkbox('Hide ControlNet', 'hidden_extensions', list_name='controlnet')
            controlnet_settings.layout().addWidget(hide_controlnet)

            # Controlnet preprocessor settings
            hide_cn_preprocessor = self._setup_checkbox('Hide ControlNet Preprocessor Settings', 'controlnet_preprocessor_settings')
            controlnet_settings.layout().addWidget(hide_cn_preprocessor)

            # Controlnet fine controls
            hide_cn_fine_controls = self._setup_checkbox('Hide ControlNet Fine Controls', 'controlnet_fine_settings')
            controlnet_settings.layout().addWidget(hide_cn_fine_controls)

            extension_settings.layout().addWidget(controlnet_settings)

        if self.server_supported['adetailer']:
            adetailer_settings = QGroupBox('ADetailer')
            adetailer_settings.setLayout(QVBoxLayout())

            hide_adetailer = self._setup_checkbox('Hide ADetailer', 'hidden_extensions', list_name='adetailer')
            adetailer_settings.layout().addWidget(hide_adetailer)

            extension_settings.layout().addWidget(adetailer_settings)
        
        self.layout().addWidget(extension_settings)
        
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(lambda: self.save())
        self.layout().addWidget(save_btn)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def _setup_checkbox(self, label, key, list_name=None):
        cb = QCheckBox(label)
        if list_name is None:
            cb.setChecked(self.hidden[key])
            cb.stateChanged.connect(lambda: self._update_hidden(key, cb.isChecked()))
        else:
            cb.setChecked(list_name in self.hidden[key])
            cb.stateChanged.connect(lambda: self._update_hidden(key, list_name))
        return cb

    def _update_hidden(self, key, value):
        if type(value) is bool:
            self.hidden[key] = value
        else:
            # Handling a list of hidden extensions, toggling them
            if value in self.hidden[key]:
                self.hidden[key].pop(self.hidden[key].index(value))
            else:
                self.hidden[key].append(value)

        if self.auto_save:
            self.save_hidden()

    def _update_autosave(self, value):
        self.auto_save = value
        self.settings_controller.set('hide_ui.auto_save', value) # Yes, it's ironic that autosave will always autosave itself

    def _update_variable(self, key, value):
        self.variables[key] = value

    def save_hidden(self):
        for key in self.hidden.keys():
            self.settings_controller.set('hide_ui.%s' % key, self.hidden[key])

    def save(self):
        # Save what's hidden and the default values to the config
        self.save_hidden()

        # Save default settings
        widgets = [self.model_widget, self.batch_widget, self.seed_widget, self.color_correction, self.denoise_widget]
        for widget in widgets:
            widget.save_settings()
        
        # Save the variables
        self.settings_controller.set('inpaint.auto_update_mask', self.variables['auto_update_mask'])
        self.settings_controller.set('inpaint.results_below_mask', self.variables['results_below_mask'])
        self.settings_controller.set('inpaint.hide_mask_on_gen', self.variables['hide_mask_on_gen'])

    