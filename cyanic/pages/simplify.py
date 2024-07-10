from PyQt5.QtWidgets import *
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..widgets import *
from . import CyanicPage


class SimplifyPage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.auto_save = self.settings_controller.get('hide_ui_auto_save')
        self.hidden = {
            'model': self.settings_controller.get('hide_ui_model'),
            'vae': self.settings_controller.get('hide_ui_vae'),
            'refiner': self.settings_controller.get('hide_ui_refiner'),
            'sampler': self.settings_controller.get('hide_ui_sampler'),
            'batch': self.settings_controller.get('hide_ui_batch'),
            'seed': self.settings_controller.get('hide_ui_seed'),
            'negative_prompt': self.settings_controller.get('hide_ui_negative_prompt'),
            'styles': self.settings_controller.get('hide_ui_styles'),
            'extra_networks': self.settings_controller.get('hide_ui_extra_networks'),
            'cfg': self.settings_controller.get('hide_ui_cfg'),
            'color_correction': self.settings_controller.get('hide_ui_color_correction'),
            'denoise_strength': self.settings_controller.get('hide_ui_denoise'),
            'hires_fix': self.settings_controller.get('hide_ui_hires_fix'),
            'hires_fix_auto': self.settings_controller.get('hide_ui_hires_fix_auto'),
            'hires_upscaler': self.settings_controller.get('hide_ui_hires_upscaler'),
            'hires_denoise': self.settings_controller.get('hide_ui_hires_denoise'),
            'extensions': self.settings_controller.get('hide_ui_extensions'),
            'hidden_extensions': self.settings_controller.get('hide_ui_hidden_extensions'),
            'controlnet_preprocessor_settings': self.settings_controller.get('hide_ui_controlnet_preprocessor_settings'),
            'controlnet_fine': self.settings_controller.get('hide_ui_controlnet_fine'),
            'inpaint_auto_update': self.settings_controller.get('hide_ui_inpaint_auto_update'),
            'inpaint_mask_above_results': self.settings_controller.get('hide_ui_inpaint_mask_above_results'),
            'inpaint_hide_mask': self.settings_controller.get('hide_ui_inpaint_hide_mask'),
            'soft_inpaint': self.settings_controller.get('hide_ui_soft_inpaint'),
            "interrogate_img2img": self.settings_controller.get("hide_ui_interrogate_img2img"),
            "interrogate_model": self.settings_controller.get("hide_ui_interrogate_model"),
        }
        self.server_supported = {
            'controlnet': self.api.script_installed('controlnet'),
            'adetailer': self.api.script_installed('adetailer'),
        }
        self.variables = {
            # These are variables that can't be updated by importing their component widget
            'mask_auto_update': self.settings_controller.get('inpaint_mask_auto_update'),
            'mask_above_results': self.settings_controller.get('inpaint_mask_above_results'),
            'mask_hide_while_gen': self.settings_controller.get('inpaint_mask_hide_while_gen'),
        }

        self.init_ui()

    def init_ui(self):
        # instructions = QLabel("Reducing the clutter in the UI by hiding settings. Hidden settings will still be applied during generation. If you adjust a default setting remember to click the 'Save' button at the bottom of the page.")
        instructions = QLabel("Reducing the clutter in the UI by hiding settings. Hidden settings will still be applied during generation.")
        instructions.setWordWrap(True)
        self.layout().addWidget(instructions)

        # Autosave
        # autosave_cb = QCheckBox('Autosave hidden changes (NOT default settings!)')
        # autosave_cb.setChecked(self.auto_save)
        # autosave_cb.stateChanged.connect(lambda: self._update_autosave(autosave_cb.isChecked()))
        # self.layout().addWidget(autosave_cb)

        # Models
        model_settings = QGroupBox('Model')
        model_settings.setLayout(QVBoxLayout())

        hide_model = self._setup_checkbox('Hide Model', 'model')
        model_settings.layout().addWidget(hide_model)

        hide_vae = self._setup_checkbox('Hide VAE', 'vae')
        model_settings.layout().addWidget(hide_vae)

        hide_refiner = self._setup_checkbox('Hide Refiner options', 'refiner')
        model_settings.layout().addWidget(hide_refiner)

        hide_sampler = self._setup_checkbox('Hide Sampler and Steps', 'sampler')
        model_settings.layout().addWidget(hide_sampler)

        # self.model_widget = ModelsWidget(self.settings_controller, self.api, ignore_hidden=True)
        # model_settings.layout().addWidget(self.model_widget)

        self.layout().addWidget(model_settings)

        # Hires Fix
        hires_fix_settings = QGroupBox('Hires Fix')
        hires_fix_settings.setLayout(QVBoxLayout())

        hide_hires_fix = self._setup_checkbox('Hide Hires Fix', 'hires_fix')
        hires_fix_settings.layout().addWidget(hide_hires_fix)

        hide_hires_fix_auto = self._setup_checkbox('Hide Automatic Hires Fix', 'hires_fix_auto')
        hires_fix_settings.layout().addWidget(hide_hires_fix_auto)

        hide_hires_upscaler = self._setup_checkbox('Hide Hires Fix Upscaler and Steps', 'hires_upscaler')
        hires_fix_settings.layout().addWidget(hide_hires_upscaler)

        hide_hires_denoise = self._setup_checkbox('Hide Hires Fix Denoise Strength', 'hires_denoise')
        hires_fix_settings.layout().addWidget(hide_hires_denoise)

        # self.hires_fix_widget = HiResFixWidget(self.settings_controller, self.api, ignore_hidden=True)
        # hires_fix_settings.layout().addWidget(self.hires_fix_widget)

        self.layout().addWidget(hires_fix_settings)

        # CFG
        cfg_settings = QGroupBox('CFG Scale')
        cfg_settings.setLayout(QVBoxLayout())
        hide_cfg = self._setup_checkbox('Hide CFG Scale', 'cfg')
        cfg_settings.layout().addWidget(hide_cfg)

        # self.cfg_widget = CFGWidget(self.settings_controller, self.api)
        # cfg_settings.layout().addWidget(self.cfg_widget)

        self.layout().addWidget(cfg_settings)

        # Img2Img and Inpainting
        img2img_settings = QGroupBox('Img2Img and Inpainting')
        img2img_settings.setLayout(QVBoxLayout())        

        hide_denoise_strength = self._setup_checkbox('Hide Denoise Strength', 'denoise_strength')
        img2img_settings.layout().addWidget(hide_denoise_strength)

        hide_color_correction = self._setup_checkbox('Hide Color Correction', 'color_correction')
        img2img_settings.layout().addWidget(hide_color_correction)

        # img2img_settings.layout().addWidget(QSplitter())

        # self.denoise_widget = DenoiseWidget(self.settings_controller)
        # img2img_settings.layout().addWidget(self.denoise_widget)

        # self.color_correction = ColorCorrectionWidget(self.settings_controller, self.api)
        # img2img_settings.layout().addWidget(self.color_correction)

        self.layout().addWidget(img2img_settings)

        # Inpaint Only settings
        inpaint_settings = QGroupBox('Inpainting')
        inpaint_settings.setLayout(QVBoxLayout())

        hide_auto_update = self._setup_checkbox('Hide Update Mask before Generation', 'inpaint_auto_update')
        inpaint_settings.layout().addWidget(hide_auto_update)

        hide_below_mask = self._setup_checkbox('Hide Mask above Results', 'inpaint_mask_above_results')
        inpaint_settings.layout().addWidget(hide_below_mask)
        
        hide_hide_mask = self._setup_checkbox('Hide... hide mask while generating', 'inpaint_hide_mask')
        hide_hide_mask.setToolTip('Yeah, I know...')
        inpaint_settings.layout().addWidget(hide_hide_mask)

        # TODO: add Mask Blur, Mask Mode, Masked Content, Inpaint Area

        #     # Update Mask before Generating
        # mask_auto_update_cb = QCheckBox('Update mask before generating')
        # mask_auto_update_cb.setToolTip('Will remember the last layer used as a mask and use the current state of that layer whenever the "Generate" button is clicked')
        # mask_auto_update_cb.setChecked(self.variables['mask_auto_update'])
        # mask_auto_update_cb.stateChanged.connect(lambda: self._update_variable('mask_auto_update', mask_auto_update_cb.isChecked()))
        # inpaint_settings.layout().addWidget(mask_auto_update_cb)

        #     # Add Results below Mask
        # mask_above_results_cb = QCheckBox('Mask above results')
        # mask_above_results_cb.setToolTip('Will insert the results as a new layer below the mask')
        # mask_above_results_cb.setChecked(self.variables['mask_above_results'])
        # mask_above_results_cb.stateChanged.connect(lambda: self._update_variable('mask_above_results', mask_above_results_cb.isChecked()))
        # inpaint_settings.layout().addWidget(mask_above_results_cb)

        #     # Hide mask on generation
        # hide_mask_cb = QCheckBox('Hide mask when generating')
        # hide_mask_cb.setToolTip('Turns off mask visibility so that you can see the results faster')
        # hide_mask_cb.setChecked(self.variables['mask_hide_while_gen'])
        # hide_mask_cb.stateChanged.connect(lambda: self._update_variable('mask_hide_while_gen', hide_mask_cb.isChecked()))
        # inpaint_settings.layout().addWidget(hide_mask_cb)

        self.layout().addWidget(inpaint_settings)

            # Soft Inpainting
        hide_soft_inpainting = self._setup_checkbox('Hide Soft Inpainting', 'soft_inpaint')
        inpaint_settings.layout().addWidget(hide_soft_inpainting)

        # soft_inpaint_settings = QGroupBox('Soft Inpaint Settings')
        # soft_inpaint_settings.setLayout(QVBoxLayout())
        # self.soft_inpaint = SoftInpaintWidget(self.settings_controller, self.api, settings_only=True)
        # soft_inpaint_settings.layout().addWidget(self.soft_inpaint)
        # inpaint_settings.layout().addWidget(soft_inpaint_settings)

        # Batch
        batch_settings = QGroupBox('Batch')
        batch_settings.setLayout(QVBoxLayout())

        hide_batch = self._setup_checkbox('Hide Batch Settings', 'batch')
        batch_settings.layout().addWidget(hide_batch)

        # self.batch_widget = BatchWidget(self.settings_controller, self.api)
        # batch_settings.layout().addWidget(self.batch_widget)
        self.layout().addWidget(batch_settings)

        # Seed
        seed_settings = QGroupBox('Seed')
        seed_settings.setLayout(QVBoxLayout())

        hide_seed = self._setup_checkbox('Hide Seed Settings', 'seed')
        seed_settings.layout().addWidget(hide_seed)
        
        # self.seed_widget = SeedWidget(self.settings_controller)
        # seed_settings.layout().addWidget(self.seed_widget)
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
            hide_cn_fine_controls = self._setup_checkbox('Hide ControlNet Fine Controls', 'controlnet_fine')
            controlnet_settings.layout().addWidget(hide_cn_fine_controls)

            extension_settings.layout().addWidget(controlnet_settings)

        if self.server_supported['adetailer']:
            adetailer_settings = QGroupBox('ADetailer')
            adetailer_settings.setLayout(QVBoxLayout())

            hide_adetailer = self._setup_checkbox('Hide ADetailer', 'hidden_extensions', list_name='adetailer')
            adetailer_settings.layout().addWidget(hide_adetailer)

            extension_settings.layout().addWidget(adetailer_settings)
        
        self.layout().addWidget(extension_settings)

        # Interrogate
        interrogate_settings = QGroupBox("Interrogate")
        interrogate_settings.setLayout(QVBoxLayout())

        hide_interrogate_model = self._setup_checkbox(
            "Hide Interrogate Model", "interrogate_model"
        )

        interrogate_settings.layout().addWidget(hide_interrogate_model)

        hide_interrogate = self._setup_checkbox(
            "Hide Interrogate in Img2Img", "interrogate_img2img"
        )
        interrogate_settings.layout().addWidget(hide_interrogate)

        self.layout().addWidget(interrogate_settings)

        # save_btn = QPushButton("Save")
        # save_btn.clicked.connect(lambda: self.save())
        # self.layout().addWidget(save_btn)

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
        self.settings_controller.set('hide_ui_auto_save', value) # Yes, it's ironic that autosave will always autosave itself

    def _update_variable(self, key, value):
        self.variables[key] = value

    def save_hidden(self):
        for key in self.hidden.keys():
            self.settings_controller.set('hide_ui_%s' % key, self.hidden[key])

    def save(self):
        # Save what's hidden and the default values to the config
        self.save_hidden()

        # Save default settings
        widgets = [self.model_widget, self.hires_fix_widget, self.cfg_widget, self.batch_widget, self.seed_widget, self.color_correction, self.soft_inpaint, self.denoise_widget]
        for widget in widgets:
            widget.save_settings()
        
        # Save the variables
        self.settings_controller.set('inpaint_mask_auto_update', self.variables['mask_auto_update'])
        self.settings_controller.set('inpaint_mask_above_results', self.variables['mask_above_results'])
        self.settings_controller.set('inpaint_mask_hide_while_gen', self.variables['mask_hide_while_gen'])

    