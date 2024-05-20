from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDoubleValidator
from ..sdapi_v1 import SDAPI
from ..settings_controller import SettingsController
from ..krita_controller import KritaController

class SettingsPage(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI):
        super().__init__()
        self.settings_controller = settings_controller
        self.kc = KritaController()
        self.api = api
        self.connected = False

        self.setLayout(QVBoxLayout())
        self._server_settings_group()
        # self._generation_group()
        self._size_group()
        self._previews_group()
        self._prompt_group()
        self.layout().addStretch() # Takes up the remaining space at the bottom, allowing everything to be pushed to the top


    def _server_settings_group(self):
        host_form = QGroupBox('Server Settings')
        host_form.setLayout(QFormLayout())
        host_addr = QLineEdit(self.settings_controller.get('host'))
        host_addr.setPlaceholderText(self.api.DEFAULT_HOST)
        host_form.layout().addRow('Host', host_addr)
        
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(lambda: self.test_new_host(host_addr.text()))
        host_form.layout().addWidget(connect_btn)
        self.connection_label = QLabel()
        host_form.layout().addWidget(self.connection_label)

        host_form.layout().addRow('Save images on host', self.create_checkbox('host_save_imgs'))
        self.add_tooltip(host_form, 'Enable to have the host save generated images, the same way it would in the WebUI.')

        # IDK what server setting to change to toggle this, so it'll have to be server default
        # host_form.layout().addRow('Filter NSFW', self.create_checkbox('server.filter_nsfw'))

        self.layout().addWidget(host_form)


    def _size_group(self):
        size_form = QGroupBox('Size')
        size_form.setLayout(QFormLayout())

        min_size_entry = QSpinBox()
        min_size_entry.setRange(256, 2048)
        min_size_entry.setValue(self.settings_controller.get('model_min_size'))
        min_size_entry.valueChanged.connect(lambda: self.settings_controller.set('model_min_size', min_size_entry.value()))
        size_form.layout().addRow('Minimum Size', min_size_entry)
        self.add_tooltip(size_form, 'The smallest size an image generated by the server will be. If the selected area is smaller than this size, the server response will be scaled to fit.')

        size_form.layout().addRow('Enable max size', self.create_checkbox('model_max_size_enable'))
        self.add_tooltip(size_form, 'Enabling will scale up images to fit a large canvas or selection, rather than have the server generate an extremely large image.')

        max_size_entry = QSpinBox()
        max_size_entry.setRange(256, 5*2048)
        max_size_entry.setValue(self.settings_controller.get('model_max_size'))
        max_size_entry.valueChanged.connect(lambda: self.settings_controller.set('model_max_size', max_size_entry.value()))
        size_form.layout().addRow('Maximum Size', max_size_entry)
        self.add_tooltip(size_form, 'The largest size an image generated by the server will be. If the selected area is larger than this size, the server response will be scaled to fit.')

        self.layout().addWidget(size_form)

    def _previews_group(self):
        previews_form = QGroupBox('Previews')
        previews_form.setLayout(QFormLayout())

        previews_form.layout().addRow('Show Previews', self.create_checkbox('preview_shown'))
        self.add_tooltip(previews_form, 'Enable to have preview images generated on the canvas.')

        refresh_time = QLineEdit('%s' % self.settings_controller.get('preview_refresh'))
        refresh_time.setPlaceholderText('1.0')
        refresh_time.setValidator(QDoubleValidator(0.5, 10.0, 1))
        refresh_time.textChanged.connect(lambda: self.settings_controller.set('preview_refresh', float(refresh_time.text()) if len(refresh_time.text()) > 0 else 1.0))
        previews_form.layout().addRow('Refresh Time (seconds)', refresh_time)
        self.add_tooltip(previews_form, 'Sets how often Krita asks SD for an update. Progress bar will update faster or slower depending on this setting.')

        self.layout().addWidget(previews_form)


    def _prompt_group(self):
        prompt_form = QGroupBox('Prompts')
        prompt_form.setLayout(QFormLayout())

        prompt_form.layout().addRow('Share Prompts', self.create_checkbox('prompt_share'))
        self.add_tooltip(prompt_form, 'Share prompt/negative prompt text between Txt2Img, Img2Img, etc.')

        # Excluded from sharing
        exclude_form = QWidget()
        exclude_form.setLayout(QVBoxLayout())
        exclude_txt2img = QCheckBox('Txt2Img')
        exclude_txt2img.setChecked('txt2img' in self.settings_controller.get('prompt_share_excludes'))
        exclude_txt2img.toggled.connect(lambda: self._toggle_and_save('prompt_share_excludes', 'txt2img'))
        exclude_form.layout().addWidget(exclude_txt2img)

        exclude_img2img = QCheckBox('Img2Img')
        exclude_img2img.setChecked('img2img' in self.settings_controller.get('prompt_share_excludes'))
        exclude_img2img.toggled.connect(lambda: self._toggle_and_save('prompt_share_excludes', 'img2img'))
        exclude_form.layout().addWidget(exclude_img2img)

        exclude_inpaint = QCheckBox('Inpaint')
        exclude_inpaint.setChecked('inpaint' in self.settings_controller.get('prompt_share_excludes'))
        exclude_inpaint.toggled.connect(lambda: self._toggle_and_save('prompt_share_excludes', 'inpaint'))
        exclude_form.layout().addWidget(exclude_inpaint)

        if self.api.script_installed('adetailer'):
            exclude_adetailer = QCheckBox('ADetailer')
            exclude_adetailer.setChecked('adetailer' in self.settings_controller.get('prompt_share_excludes'))
            exclude_adetailer.toggled.connect(lambda: self._toggle_and_save('prompt_share_excludes', 'adetailer'))
            exclude_form.layout().addWidget(exclude_adetailer)
        
        prompt_form.layout().addRow('Exclude from sharing', exclude_form)
        self.add_tooltip(prompt_form, 'Changes to the checked prompts/negative prompts won\'t override the unchecked')

        # TODO: Replace with the amount of prompts to save, and include the options.
        # prompt_form.layout().addRow('Save Prompts', self.create_checkbox('prompts.save_prompts'))
        # self.add_tooltip(prompt_form, 'Save prompts/negative prompts in Krita\'s UI for next time.')
        # self.layout().addWidget(prompt_form)
        save_history_size = QSpinBox()
        save_history_size.setRange(0, 15)
        save_history_size.setValue(self.settings_controller.get('prompt_history_max'))
        save_history_size.valueChanged.connect(lambda: self.settings_controller.set('prompt_history_max', save_history_size.value()))
        prompt_form.layout().addRow('Prompts to save', save_history_size)
        self.add_tooltip(prompt_form, 'How many unique prompts should be saved in the prompt history. 0 won\'t save any prompts.')


    def _toggle_and_save(self, key, value):
        self.settings_controller.toggle(key, value)
        self.settings_controller.save()

    def _generation_group(self):
        generation_form = QGroupBox('Generation Settings')
        generation_form.setLayout(QFormLayout())

        generation_form.layout().addRow('Sampler', QComboBox())
        generation_form.layout().addRow('Steps', QSpinBox())
        generation_form.layout().addRow('Model', QComboBox())
        generation_form.layout().addRow('VAE', QComboBox())
        generation_form.layout().addRow('Refiner', QComboBox())
        generation_form.layout().addRow('Upscaler', QComboBox())
        generation_form.layout().addRow('Face Restorer', QComboBox())
        generation_form.layout().addRow('Clip Skip', QSpinBox())
        generation_form.layout().addRow('Batch Count', QSpinBox())
        generation_form.layout().addRow('Batch Size', QSpinBox())
        generation_form.layout().addRow('CFG Scale', QSpinBox())


        self.layout().addWidget(generation_form)


    def update(self):
        super().update()
        self.repaint()


    def add_tooltip(self, form:QWidget, text):
        # Add tooltips to the last 2 items added to the form, which should be the label and the input
        index = len(form.children()) - 2 # layout() is listed as a child, which throws off the count
        form.layout().itemAt(index).widget().setToolTip(text)
        form.layout().itemAt(index - 1).widget().setToolTip(text)


    def get_key_from_value(self, dict, value):
        # The order of keys and values doesn't change unless the dict is modified
        return list(dict.keys())[list(dict.values()).index(value)]
    

    def create_checkbox(self, settings_key):
        cb = QCheckBox()
        cb.setChecked(self.settings_controller.get(settings_key))
        cb.toggled.connect(lambda: self.update_setting(settings_key, cb.isChecked()))
        return cb
    

    def create_combobox(self, options, default, settings_key):
        cb = QComboBox()
        cb.addItems(options)
        cb.setCurrentText(default)
        # cb.eventFilter(self, QtGui.QWheelEvent()) # Would like to filter out scroll wheel changing combobox
        cb.currentIndexChanged.connect(lambda: self.update_setting(settings_key, cb.currentText()))
        return cb
    

    def test_new_host(self, host=''):
        self.connection_label.setText('Testing...')
        if len(host) == 0: # Check if the host provided in the API is a valid server (or running)
            try:
                status = self.api.get_status()
                if status is None:
                    self.connection_label.setText('No Connection')
                    self.connected = False
                else:
                    self.connection_label.setText('Connected')
                    self.connected = True
            except:
                self.connection_label.setText('No Connection')
                self.connected = False
            return
        # Check a user entered host
        try:
            test_api = SDAPI(host)
            status = test_api.get_status()
            if status is None:
                self.connection_label.setText('No Connection')
                self.connected = False
            # Test passed, inform user, update api
            self.connection_label.setText('Connected')
            self.api.change_host(host)
            self.settings_controller.set('host', host)
            self.settings_controller.save()
            self.connected = True
        except:
            # Test failed, inform user
            self.connection_label.setText('No Connection')
            self.connected = False


    def update_setting(self, key, value):
        self.settings_controller.set(key, value)


    def save_user_settings(self):
        try:
            self.settings_controller.save()
            self.save_message.setText('Saved settings!')
        except Exception as e:
            self.save_message.setText('Unable to save settings: %s' % e)

