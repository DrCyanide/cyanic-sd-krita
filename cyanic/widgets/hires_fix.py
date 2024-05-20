from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ..sdapi_v1 import SDAPI
from ..krita_controller import KritaController
from ..settings_controller import SettingsController

# There are a lot of extra settings for hires fix, like the option to change checkpoint, sampler, prompts, etc.
# This widget is going to focus on the basics: enable_hr, hr_upscaler, hr_steps
class HiResFixWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI, ignore_hidden=False):
        super().__init__()
        self.settings_controller = settings_controller
        self.kc = KritaController()
        self.api = api
        self.ignore_hidden = ignore_hidden
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {
            'enable_hr': False,
            'auto_enable_hr': self.settings_controller.get('hr_fix_auto'),
            'auto_enable_min': self.settings_controller.get('hr_fix_auto_min'),
            'hr_upscaler': self.settings_controller.get('hr_fix_upscaler'),
            'hr_steps': self.settings_controller.get('hr_fix_steps'), # if 0, API uses same number of steps as the first pass
            'min_size': self.settings_controller.get('hr_fix_sd_min'),
            'denoising_strength': self.settings_controller.get('hr_fix_denoise'),
        }

        self.hires_only_upscalers = [
            'Latent',
            'Latent (antialiased)',
            'Latent (bicubic)',
            'Latent (bicubic antialiased)',
            'Latent (nearest)',
            'Latent (nearest-exact)',
        ]

        self.draw_ui()


    def draw_ui(self):
        enable_row = QWidget()
        enable_row.setLayout(QHBoxLayout())
        enable_row.layout().setContentsMargins(0,0,0,0)
        # Enable
        enable_cb = QCheckBox('Enable Hires Fix')
        enable_cb.setToolTip('Enable Hires Fix for this image')
        enable_cb.setChecked(self.variables['enable_hr'])
        enable_cb.toggled.connect(lambda: self._update_variables('enable_hr', enable_cb.isChecked()))
        enable_row.layout().addWidget(enable_cb)

        # Min Size
        min_size_layout = QWidget()
        min_size_layout.setLayout(QHBoxLayout())
        min_size_layout.layout().setContentsMargins(0,0,0,0)

        min_size_layout.layout().addWidget(QLabel('SD Min Size'))
        min_size_layout.setToolTip('The smallest size for a side of the first pass of the image. For SD 1.5, 512 recommended. For SDXL, 1025 recommended.')

        min_size = QSpinBox()
        min_size.setMinimum(1)
        min_size.setMaximum(99999)
        min_size.setValue(self.variables['min_size'])
        min_size.valueChanged.connect(lambda: self._update_variables('hr_fix_sd_min', min_size.value()))
        min_size_layout.layout().addWidget(min_size)

        enable_row.layout().addWidget(min_size_layout)
        self.layout().addWidget(enable_row)

        auto_enable_row = QWidget()
        auto_enable_row.setLayout(QHBoxLayout())
        auto_enable_row.layout().setContentsMargins(0,0,0,0)

        # Auto-enable
        auto_enable_cb = QCheckBox('Auto-Enable Hires Fix')
        auto_enable_cb.setChecked(self.variables['auto_enable_hr'])
        auto_enable_cb.setToolTip('Enable Hires fix every time the image has a side bigger than the specified value')
        auto_enable_cb.toggled.connect(lambda: self._update_variables('auto_enable_hr', auto_enable_cb.isChecked()))
        auto_enable_row.layout().addWidget(auto_enable_cb)

        # Auto min size
        hr_min_size_layout = QWidget()
        hr_min_size_layout.setLayout(QHBoxLayout())
        hr_min_size_layout.layout().setContentsMargins(0,0,0,0)

        hr_min_size_layout.layout().addWidget(QLabel('HR Min Size'))
        hr_min_size_layout.setToolTip('The smallest size for a side of the first pass of the image. Recommend about 1.5x larger than SD Min Size.')

        auto_min_size = QSpinBox()
        auto_min_size.setMinimum(1)
        auto_min_size.setMaximum(99999)
        auto_min_size.setValue(self.variables['auto_enable_min'])
        auto_min_size.valueChanged.connect(lambda: self._update_variables('auto_enable_min', auto_min_size.value()))
        hr_min_size_layout.layout().addWidget(auto_min_size)

        auto_enable_row.layout().addWidget(hr_min_size_layout)
        if self.ignore_hidden or not self.settings_controller.get('hide_ui_hires_fix_auto'):
            self.layout().addWidget(auto_enable_row)

        # Upscaler + Latent
        upscaler_row = QWidget()
        upscaler_row.setLayout(QHBoxLayout())
        upscaler_row.layout().setContentsMargins(0,0,0,0)

        upscaler_row.layout().addWidget(QLabel('Upscaler'))

        upscalers = self.hires_only_upscalers
        upscalers.extend(self.api.get_upscaler_names())
        upscaler_select = QComboBox()
        upscaler_select.addItems(upscalers)
        upscaler_select.setStyleSheet("QComboBox { combobox-popup: 0; }") # Needed for setMaxVisibleItems to work
        upscaler_select.setMinimumContentsLength(10) # Allows the box to be smaller than the longest item's char length
        upscaler_select.setMaxVisibleItems(10) # Suppose to limit the number of visible options
        upscaler_select.setCurrentText(self.variables['hr_upscaler'])
        upscaler_select.currentTextChanged.connect(lambda: self._update_variables('hr_upscaler', upscaler_select.currentText()))
        upscaler_row.layout().addWidget(upscaler_select)

        # Steps
        steps = QSpinBox()
        steps.setValue(self.variables['hr_steps'])
        steps.valueChanged.connect(lambda: self._update_variables('hr_steps', steps.value()))
        steps.setToolTip('Hires Steps. 0 steps will match the number of steps used for the first generation.')
        upscaler_row.layout().addWidget(steps)

        if self.ignore_hidden or not self.settings_controller.get('hide_ui_hires_upscaler'):
            self.layout().addWidget(upscaler_row)

        # Denoise Strength
        denoise_settings = QWidget()
        denoise_settings.setLayout(QFormLayout())
        denoise_settings.layout().setContentsMargins(0,0,0,0)

        denoise = QWidget()
        denoise.setLayout(QHBoxLayout())
        denoise.layout().setContentsMargins(0,0,0,0)

        # Denoise label
        default_noise = self.variables['denoising_strength']
        self.denoise_percent = QLabel('%s%%' % int(default_noise * 100))

        # Denoise Strength
        self.denoise_slider = QSlider(Qt.Horizontal)
        self.denoise_slider.setTickInterval(10)
        self.denoise_slider.setTickPosition(QSlider.TicksAbove)
        self.denoise_slider.setMinimum(0)
        self.denoise_slider.setMaximum(100)
        self.denoise_slider.setValue(int(default_noise * 100))
        self.denoise_slider.valueChanged.connect(lambda: self._update_denoise_slider(self.denoise_slider.value()))
        
        denoise.layout().addWidget(self.denoise_slider)
        denoise.layout().addWidget(self.denoise_percent)
        denoise_settings.layout().addRow('Denoise Strength', denoise)

        if self.ignore_hidden or not self.settings_controller.get('hide_ui_hires_denoise'):
            self.layout().addWidget(denoise_settings)

    def _update_variables(self, key, value):
        self.variables[key] = value

    def _update_denoise_slider(self, value):
        self.denoise_percent.setText('%s%%' % value)
        if value > 0:
            self.variables['denoising_strength'] = value / 100
        else:
            self.variables['denoising_strength'] = 0.0

    def save_settings(self):
        self.settings_controller.set('hr_fix_upscaler', self.variables['hr_upscaler'])
        self.settings_controller.set('hr_fix_steps', self.variables['hr_steps'])
        self.settings_controller.set('hr_fix_sd_min', self.variables['min_size'])
        self.settings_controller.set('hr_fix_auto', self.variables['auto_enable_hr'])
        self.settings_controller.set('hr_fix_auto_min', self.variables['auto_enable_min'])
        self.settings_controller.set('hr_fix_denoise', self.variables['denoising_strength'])
        self.settings_controller.save()

    def get_generation_data(self):
        # Resize x and resize y should be canvas/selection size
        # This means that the first-pass size will need to be scaled down
        x, y, w, h = self.kc.get_selection_bounds() 
        if w == 0 or h == 0:
            # Nothing was selected, use the canvas size
            x, y = 0, 0
            w, h = self.kc.get_canvas_size()

        data = {
            "enable_hr": False
        }
        if self.variables['enable_hr'] or self.variables['auto_enable_hr'] and (w > self.variables['auto_enable_min'] or h > self.variables['auto_enable_min']):
            scaled_down_w = w
            scaled_down_h = h
            if w < h: # width is the smaller value
                scaled_down_w = self.variables['min_size']
                scaled_down_h = int( 1/(w / self.variables['min_size']) * h)
            else: # height is the smaller value
                scaled_down_w = int( 1/(h / self.variables['min_size']) * w)
                scaled_down_h = self.variables['min_size']
            
            data = {
                "enable_hr": True,
                "hr_upscaler": self.variables['hr_upscaler'],
                "hr_steps": self.variables['hr_steps'],
                "denoising_strength": self.variables['denoising_strength'],
                "hr_resize_y": h,
                "hr_resize_x": w,
                "width": scaled_down_w,
                "height": scaled_down_h,
            }
        self.save_settings()
        return data