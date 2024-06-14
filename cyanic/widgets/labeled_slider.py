from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSlider, QLabel

class LabeledSlider (QWidget):
    # A slider with a label.
    def __init__(self, min=0, max=100, value=0.5, as_percent=True, step_size=1):
        # as_percent will add a '%' to the label, and return values as floats (so 70% becomes 0.7)
        # step_size is used to create rigid step sizes. So min=1, max=20, step_size=0.5 would give a slider that goes 1 to 20, stopping at 1.5, 2.0, 2.5, etc
        super().__init__()
        self.as_percent = as_percent
        self.step_size = step_size
        self.multiplier = 1.0
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.wheelEvent = lambda event : None
        # self.slider.setTickInterval(10)
        self.slider.setTickPosition(QSlider.TicksAbove)
        if self.step_size == 1:
            self.slider.setMinimum(min)
            self.slider.setMaximum(max)
        else:
            self.multiplier = 10
            if self.step_size < 0.1:
                self.multiplier = 100
            self.slider.setMinimum(int(min * self.multiplier))
            self.slider.setMaximum(int(max * self.multiplier))
        value_range = int((max - min) * self.multiplier)
        self.slider.setTickInterval(int(value_range / 10))
        self.slider.valueChanged.connect(self.on_value_change)

        self.layout().addWidget(self.slider)

        self.label = QLabel('')

        self.layout().addWidget(self.label)

        # Calling a function to have consistent behavior on initialization and to trigger the label update
        self.set_value(value)

    def on_value_change(self):
        value = self.slider.value() / self.multiplier

        # TODO: have "0%" and "100%" take the same width.
        if self.as_percent:
            self.label.setText('%s%%' % value)
        else:
            self.label.setText('%s' % value)

    def set_value(self, value):
        value = int(value * self.multiplier) # Used to account for step_size

        if self.as_percent:
            self.slider.setValue(int(value * 100))
        else:
            self.slider.setValue(value)
        self.on_value_change()

    def set_range(self, min=0, max=100):
        # ControlNet may reuse sliders and change their ranges.
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)

    def value(self):
        if self.as_percent and self.slider.value() > 0:
            return self.slider.value() / 100
        else:
            return self.slider.value()
