from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt
from ..widgets import CollapsibleWidget
from ..krita_controller import KritaController
from ..settings_controller import SettingsController
from ..sdapi_v1 import SDAPI

class SeedWidget(QWidget):
    def __init__(self, settings_controller:SettingsController, api:SDAPI=None):
        super().__init__()
        self.settings_controller = settings_controller
        self.api = api # Not used here
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.variables = {
            'seed': self.settings_controller.get('seed'),
            'subseed': self.settings_controller.get('subseed'),
            'subseed_strength': self.settings_controller.get('subseed_strength'),
        }
        self.draw_ui()

    def draw_ui(self):
        # Seed
        row_1 = QWidget()
        row_1.setLayout(QHBoxLayout())
        row_1.layout().setContentsMargins(0,0,0,0)
        row_1.layout().addWidget(QLabel('Seed'))

        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText('Random')
        self.seed_edit.setValidator(QIntValidator())
        if self.variables['seed'] != -1:
            self.seed_edit.setText(self.variables['seed'])
        self.seed_edit.textChanged.connect(lambda: self._update_variable('seed', self.seed_edit.text()))
        row_1.layout().addWidget(self.seed_edit)

        # Reuse/Random seed buttons
        random_button = QPushButton("Random")
        random_button.clicked.connect(lambda: self.seed_edit.setText(''))
        row_1.layout().addWidget(random_button)

        # reuse_button = QPushButton("Use Layer Seed")
        reuse_button = QPushButton("Layer Seed")
        reuse_button.clicked.connect(self.get_seed_from_active_layer)
        row_1.layout().addWidget(reuse_button)

        self.layout().addWidget(row_1)


        # Variation Seed (subseed)
        row_2 = QWidget()
        row_2.setLayout(QHBoxLayout())
        row_2.layout().setContentsMargins(0,0,0,0)
        row_2.layout().addWidget(QLabel('Subseed'))

        self.subseed_edit = QLineEdit()
        self.subseed_edit.setPlaceholderText('Random')
        self.subseed_edit.setValidator(QIntValidator())
        if self.variables['subseed'] != -1:
            self.seed_edit.setText(self.variables['subseed'])
        self.subseed_edit.textChanged.connect(lambda: self._update_variable('subseed', self.subseed_edit.text()))
        row_2.layout().addWidget(self.subseed_edit)

        # Variation Strength
        self.subseed_strength_slider = QSlider(Qt.Horizontal)
        self.subseed_strength_slider.setTickInterval(10)
        self.subseed_strength_slider.setTickPosition(QSlider.TicksAbove)
        self.subseed_strength_slider.setMinimum(0)
        self.subseed_strength_slider.setMaximum(100)
        self.subseed_strength_slider.setValue(int(self.variables['subseed_strength'] * 100))


        row_2.layout().addWidget(self.subseed_strength_slider)
        self.percentage = QLabel()
        self.percentage.setText('%s%%' % 0)
        # self.subseed_strength_slider.valueChanged.connect(lambda: self.percentage.setText('%s%%' % self.subseed_strength_slider.value()))
        self.subseed_strength_slider.valueChanged.connect(lambda: self._update_variable('subseed_strength', self.subseed_strength_slider.value()))
        row_2.layout().addWidget(self.percentage)

        self.layout().addWidget(row_2)

    def get_seed_from_active_layer(self):
        kc = KritaController()
        name = kc.get_active_layer_name()
        seed = ''
        if 'seed' in name.lower():
            seed = name.lower().replace('seed: ', '').strip()
        self.seed_edit.setText(seed)

    def _update_variable(self, key, value):
        if key == 'subseed_strength':
            self.percentage.setText('%s%%' % value)
            self.variables[key] = value / 100
        else:
            if len(value) == 0:
                value = -1
            self.variables[key] = int(value)

    def save_settings(self):
        for key in self.variables.keys():
            self.settings_controller.set('seed.%s' % key, self.variables[key])

    def get_generation_data(self):
        # data = {}
        # if len(self.seed_edit.text()) > 0:
        #     data['seed'] = self.seed_edit.text()
        # else:
        #     data['seed'] = -1
        # if len(self.subseed_edit.text()) > 0:
        #     data['subseed'] = self.subseed_edit.text()
        # else:
        #     data['subseed'] = -1
        # data['subseed_strength'] = self.subseed_strength_slider.value() / 100
        data = {
            'seed': self.variables['seed'],
            'subseed': self.variables['subseed'],
            'subseed_strength': self.variables['subseed_strength'],
        }
        return data