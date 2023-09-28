from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt
from ..widgets import CollapsibleWidget
from ..krita_controller import KritaController

class SeedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        # Seed
        row_1 = QWidget()
        row_1.setLayout(QHBoxLayout())
        row_1.layout().setContentsMargins(0,0,0,0)
        row_1.layout().addWidget(QLabel('Seed'))

        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText('Random')
        self.seed_edit.setValidator(QIntValidator())
        row_1.layout().addWidget(self.seed_edit)

        # self.layout().addWidget(row_1)

        # Reuse/Random seed buttons
        # random_button = QPushButton("Random Seed")
        random_button = QPushButton("Random")
        random_button.clicked.connect(lambda: self.seed_edit.setText(''))
        # self.layout().addWidget(random_button)
        row_1.layout().addWidget(random_button)

        # reuse_button = QPushButton("Use Layer Seed")
        reuse_button = QPushButton("Layer Seed")
        reuse_button.clicked.connect(self.get_seed_from_active_layer)
        # self.layout().addWidget(reuse_button)
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
        # self.layout().addWidget(self.subseed_edit)
        row_2.layout().addWidget(self.subseed_edit)

        # Variation Strength
        self.subseed_strength_slider = QSlider(Qt.Horizontal)
        self.subseed_strength_slider.setTickInterval(10)
        self.subseed_strength_slider.setTickPosition(QSlider.TicksAbove)
        self.subseed_strength_slider.setMinimum(0)
        self.subseed_strength_slider.setMaximum(100)

        row_2.layout().addWidget(self.subseed_strength_slider)
        self.percentage = QLabel()
        self.percentage.setText('%s%%' % 0)
        self.subseed_strength_slider.valueChanged.connect(lambda: self.percentage.setText('%s%%' % self.subseed_strength_slider.value()))
        row_2.layout().addWidget(self.percentage)

        self.layout().addWidget(row_2)

    def get_seed_from_active_layer(self):
        kc = KritaController()
        name = kc.get_active_layer_name()
        seed = name.lower().replace('seed: ', '').strip()
        self.seed_edit.setText(seed)

    def get_generation_data(self):
        data = {}
        if len(self.seed_edit.text()) > 0:
            data['seed'] = self.seed_edit.text()
        else:
            data['seed'] = -1
        if len(self.subseed_edit.text()) > 0:
            data['subseed'] = self.subseed_edit.text()
        else:
            data['subseed'] = -1
        data['subseed_strength'] = self.subseed_strength_slider.value() / 100
        return data