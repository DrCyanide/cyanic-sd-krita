from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QBuffer, QIODevice, QByteArray
import json
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController
from ..widgets import PromptWidget, SeedWidget, CollapsibleWidget, ModelsWidget, GenerateWidget, ImageInWidget, DenoiseWidget, ExtensionWidget, MaskWidget, ColorCorrectionWidget

class UpscalePage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api
        self.kc = KritaController()
        self.setLayout(QVBoxLayout())
        self.max_scale = 10
        self.generating = False

        self.scale_tabs = QTabWidget()

        # Scale By
        scale_by_form = QWidget()
        scale_by_form.setLayout(QFormLayout())
        # resize amount
        resize_entry = QDoubleSpinBox()
        resize_entry.setMinimum(0.0)
        resize_entry.setMaximum(self.max_scale)
        resize_entry.setValue(self.settings_controller.get('upscale.resize'))
        resize_entry.valueChanged.connect(lambda: self.settings_controller.set('upscale.resize', resize_entry.value()))
        scale_by_form.layout().addRow('Resize', resize_entry)

        # Scale To
        scale_to_form = QWidget()
        scale_to_form.setLayout(QFormLayout())
        # Width
        width_entry = QSpinBox()
        width_entry.setMinimum(0)
        width_entry.setMaximum(512 * self.max_scale)
        width_entry.setValue(self.settings_controller.get('upscale.width'))
        width_entry.valueChanged.connect(lambda: self.settings_controller.set('upscale.width', width_entry.value()))
        scale_to_form.layout().addRow('Width', width_entry)
        # Height
        height_entry = QSpinBox()
        height_entry.setMinimum(0)
        height_entry.setMaximum(512 * self.max_scale)
        height_entry.setValue(self.settings_controller.get('upscale.height'))
        height_entry.valueChanged.connect(lambda: self.settings_controller.set('upscale.height', height_entry.value()))
        scale_to_form.layout().addRow('Height', height_entry)
        # Flip?

        # crop to fit
        crop_to_fit_cb = QCheckBox()
        crop_to_fit_cb.setChecked(self.settings_controller.get('upscale.crop_to_fit'))
        crop_to_fit_cb.toggled.connect(lambda: self.settings_controller.set('upscale.crop_to_fit', crop_to_fit_cb.isChecked()))
        scale_to_form.layout().addRow('Crop to fit', crop_to_fit_cb)

        self.scale_tabs.addTab(scale_by_form, 'Scale by')
        self.scale_tabs.addTab(scale_to_form, 'Scale to')
        self.scale_tabs.setCurrentIndex(self.settings_controller.get('upscale.tab'))

        self.layout().addWidget(self.scale_tabs)

        # Resize Canvas checkbox
        resize_canvas_cb = QCheckBox('Resize Canvas')
        resize_canvas_cb.setChecked(self.settings_controller.get('upscale.resize_canvas'))
        resize_canvas_cb.setToolTip('Check to resize the canvas to match the upscaled dimensions')
        resize_canvas_cb.toggled.connect(lambda: self.settings_controller.set('upscale.resize_canvas', resize_canvas_cb.isChecked()))
        self.layout().addWidget(resize_canvas_cb)

        # Select Upscaler
        upscaler_form = QWidget()
        upscaler_form.setLayout(QFormLayout())
        upscaler_form.layout().setContentsMargins(0,0,0,0)
        upscalers, default_upscaler = self.api.get_upscaler_and_default()
        upscaler_select = QComboBox()
        upscaler_select.addItems(upscalers)
        if len(default_upscaler) > 0:
            upscaler_select.setCurrentText(default_upscaler)
        settings_upscaler = self.settings_controller.get('defaults.upscaler')
        if len(settings_upscaler) > 0:
            upscaler_select.setCurrentText(settings_upscaler)
        upscaler_select.currentIndexChanged.connect(lambda: self.settings_controller.set('defaults.upscaler', upscaler_select.currentText()))

        upscaler_form.layout().addRow('Upscaler', upscaler_select)
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

    def update(self):
        super().update()

    def btn_click(self):
        if self.generating:
            self.upscale_btn.setText('Upscale')

    def upscale(self):
        tab = self.scale_tabs.currentIndex()
        self.settings_controller.set('upscale.tab', tab)
        self.settings_controller.save()
        
        data = {
            'resize_mode': tab, # 0 = "Upscale By", 1 = "Upscale to"
            'upscaling_resize': self.settings_controller.get('upscale.resize'),
            'upscaling_resize_w': self.settings_controller.get('upscale.width'),
            'upscaling_resize_h': self.settings_controller.get('upscale.height'),
            'upscaling_crop': self.settings_controller.get('upscale.crop_to_fit'),
            'upscaler_1': self.settings_controller.get('defaults.upscaler'),
            'image': self.kc.qimage_to_b64_str(self.kc.get_canvas_img()),
        }
        # self.debug_text.setPlainText(json.dumps(data))
        # self.debug_text.setPlainText('%s' % type(data))
        # self.kc.run_as_thread(lambda: self.threadable_run(data), lambda: self.threadable_return())
        self.results = self.api.extra(data)
        self.threadable_return()


    def threadable_run(self, data):
        self.results = self.api.extra(data)

        self.upscale_btn.setText('Upscaling')
        self.upscale_btn.setDisabled(True)
        self.update()

    def threadable_return(self):
        x, y, canvas_w, canvas_h = self.kc.get_canvas_bounds()
        if self.settings_controller.get('upscale.tab') == 0:
            # Upscale was a %
            scale = self.settings_controller.get('upscale.resize')
            canvas_w = int(canvas_w * scale)
            canvas_h = int(canvas_h * scale)
        else:
            # Upscale was a specific value
            canvas_w = self.settings_controller.get('upscale.width')
            canvas_h = self.settings_controller.get('upscale.height')

        if self.settings_controller.get('upscale.resize_canvas'):
            self.kc.resize_canvas(canvas_w, canvas_h)

        # self.debug_text.setPlainText('%s, %s - %sx%s' % (x, y, canvas_w, canvas_h))
        self.kc.results_to_layers(self.results, x, y, canvas_w, canvas_h, layer_name='Upscaled')

        self.upscale_btn.setText('Upscale')
        self.upscale_btn.setDisabled(False)
        self.update()