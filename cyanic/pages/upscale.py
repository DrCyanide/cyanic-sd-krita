from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QBuffer, QIODevice, QByteArray
import json
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from . import CyanicPage

class UpscalePage(CyanicPage):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__(settings_controller, api)
        self.variables = {
            'upscaler': '',
            'upscale_tab': 0, # 0 = "Upscale By", 1 = "Upscale to"
            'upscale_resize': 2.0,
            'upscale_width': 1024,
            'upscale_height': 1024,
            'upscale_crop_to_fit': True,
            'upscale_resize_canvas': False,
        }

        self.max_scale = 10
        self.generating = False
        self.upscalers = []
        self.default_upscaler = ''

        self.init_ui()

    def load_settings(self):
        for key in self.variables:
            self.variables[key] = self.settings_controller.get(key)
        
        self.resize_entry.setValue(self.variables['upscale_resize'])
        self.width_entry.setValue(self.variables['upscale_width'])
        self.height_entry.setValue(self.variables['upscale_height'])
        self.crop_to_fit_cb.setChecked(self.variables['upscale_crop_to_fit'])
        self.scale_tabs.setCurrentIndex(self.variables['upscale_tab'])
        self.resize_canvas_cb.setChecked(self.variables['upscale_resize_canvas'])
        self.upscaler_select.setCurrentText(self.variables['upscaler'])

    def load_server_data(self):
        self.upscalers, self.default_upscaler = self.api.get_upscaler_and_default()
        self.upscaler_select.clear()
        self.upscaler_select.addItems(self.upscalers)
        if len(self.default_upscaler) > 0:
            self.upscaler_select.setCurrentText(self.default_upscaler)
        if len(self.variables['upscaler']) > 0:
            self.upscaler_select.setCurrentText(self.variables['upscaler'])

    def init_ui(self):
        self.scale_tabs = QTabWidget()

        # Scale By
        scale_by_form = QWidget()
        scale_by_form.setLayout(QFormLayout())
        # resize amount
        self.resize_entry = QDoubleSpinBox()
        self.resize_entry.setMinimum(0.0)
        self.resize_entry.setMaximum(self.max_scale)
        self.resize_entry.setValue(self.variables['upscale_resize'])
        self.resize_entry.valueChanged.connect(lambda: self.update_variable('upscale_resize', self.resize_entry.value()))
        scale_by_form.layout().addRow('Resize', self.resize_entry)

        # Scale To
        scale_to_form = QWidget()
        scale_to_form.setLayout(QFormLayout())
        # Width
        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(0)
        self.width_entry.setMaximum(512 * self.max_scale)
        self.width_entry.setValue(self.variables['upscale_width'])
        self.width_entry.valueChanged.connect(lambda: self.update_variable('upscale_width', self.width_entry.value()))
        scale_to_form.layout().addRow('Width', self.width_entry)
        # Height
        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(0)
        self.height_entry.setMaximum(512 * self.max_scale)
        self.height_entry.setValue(self.variables['upscale_height'])
        self.height_entry.valueChanged.connect(lambda: self.update_variable('upscale_height', self.height_entry.value()))
        scale_to_form.layout().addRow('Height', self.height_entry)
        # Flip?

        # crop to fit
        self.crop_to_fit_cb = QCheckBox()
        self.crop_to_fit_cb.setChecked(self.variables['upscale_crop_to_fit'])
        self.crop_to_fit_cb.toggled.connect(lambda: self.update_variable('upscale_crop_to_fit', self.crop_to_fit_cb.isChecked()))
        scale_to_form.layout().addRow('Crop to fit', self.crop_to_fit_cb)

        self.scale_tabs.addTab(scale_by_form, 'Scale by')
        self.scale_tabs.addTab(scale_to_form, 'Scale to')
        self.scale_tabs.setCurrentIndex(self.variables['upscale_tab'])

        self.layout().addWidget(self.scale_tabs)

        # Resize Canvas checkbox
        self.resize_canvas_cb = QCheckBox('Resize Canvas')
        self.resize_canvas_cb.setChecked(self.variables['upscale_resize_canvas'])
        self.resize_canvas_cb.setToolTip('Check to resize the canvas to match the upscaled dimensions')
        self.resize_canvas_cb.toggled.connect(lambda: self.update_variable('upscale_resize_canvas', self.resize_canvas_cb.isChecked()))
        self.layout().addWidget(self.resize_canvas_cb)

        # Select Upscaler
        upscaler_form = QWidget()
        upscaler_form.setLayout(QFormLayout())
        upscaler_form.layout().setContentsMargins(0,0,0,0)
        self.upscaler_select = QComboBox()
        self.upscaler_select.addItems(self.upscalers)
        if len(self.default_upscaler) > 0:
            self.upscaler_select.setCurrentText(self.default_upscaler)
        if len(self.variables['upscaler']) > 0:
            self.upscaler_select.setCurrentText(self.variables['upscaler'])
        self.upscaler_select.currentIndexChanged.connect(lambda: self.update_variable('upscaler', self.upscaler_select.currentText()))

        upscaler_form.layout().addRow('Upscaler', self.upscaler_select)
        self.layout().addWidget(upscaler_form)

        # Upscaler 2 + visiblity?

        # Activate button
        # It's not worth using the Generate component for this...
        self.upscale_btn = QPushButton("Upscale")
        self.upscale_btn.clicked.connect(lambda: self.upscale())
        self.layout().addWidget(self.upscale_btn)

        # self.debug_text = QPlainTextEdit()
        # self.debug_text.setPlaceholderText('Debuging output')
        # self.layout().addWidget(self.debug_text)

        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top

    def update_variable(self, key, value):
        self.variables[key] = value

    def update(self):
        super().update()

    def btn_click(self):
        if self.generating:
            self.upscale_btn.setText('Upscale')

    def upscale(self):
        kc = KritaController()
        tab = self.scale_tabs.currentIndex()
        self.settings_controller.set('upscale_tab', tab)
        self.settings_controller.save()
        
        data = {
            'resize_mode': tab, # 0 = "Upscale By", 1 = "Upscale to"
            'upscaling_resize': self.settings_controller.get('upscale_resize'),
            'upscaling_resize_w': self.settings_controller.get('upscale_width'),
            'upscaling_resize_h': self.settings_controller.get('upscale_height'),
            'upscaling_crop': self.settings_controller.get('upscale_crop_to_fit'),
            'upscaler_1': self.settings_controller.get('upscaler'),
            'image': kc.qimage_to_b64_str(kc.get_canvas_img()),
        }
        # self.debug_text.setPlainText(json.dumps(data))
        # self.debug_text.setPlainText('%s' % type(data))
        # kc.run_as_thread(lambda: self.threadable_run(data), lambda: self.threadable_return())
        self.results = self.api.extra(data)
        self.threadable_return()


    def threadable_run(self, data):
        self.results = self.api.extra(data)

        self.upscale_btn.setText('Upscaling')
        self.upscale_btn.setDisabled(True)
        self.update()

    def threadable_return(self):
        kc = KritaController()
        x, y, canvas_w, canvas_h = kc.get_canvas_bounds()
        if self.settings_controller.get('upscale_tab') == 0:
            # Upscale was a %
            scale = self.settings_controller.get('upscale_resize')
            canvas_w = int(canvas_w * scale)
            canvas_h = int(canvas_h * scale)
        else:
            # Upscale was a specific value
            canvas_w = self.settings_controller.get('upscale_width')
            canvas_h = self.settings_controller.get('upscale_height')

        if self.settings_controller.get('upscale_resize_canvas'):
            kc.resize_canvas(canvas_w, canvas_h)

        # self.debug_text.setPlainText('%s, %s - %sx%s' % (x, y, canvas_w, canvas_h))
        kc.results_to_layers(self.results, x, y, canvas_w, canvas_h, layer_name='Upscaled')

        self.upscale_btn.setText('Upscale')
        self.upscale_btn.setDisabled(False)
        self.update()