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
        value = self._from_slider_value(self.slider.value())
        if self.as_percent:
            value = value * 100

        if value % self.step_size != 0:
            value = value - (value % self.step_size) # Rounds down by 

        # Format the label string
        if self.step_size >= 1:
            value = "%d" % value
        elif self.step_size < 1:
            value = "%.1f" % value
        elif self.step_size < 0.1:
            value = "%.2f" % value
        else:
            value = "%.3f" % value

        # TODO: have "0%" and "100%" take the same width.
        # Seems like QLabel trims leading spaces
        if self.as_percent:
            self.label.setText('%s%%' % value)
        else:
            self.label.setText('%s' % value)

    def set_value(self, value):
        value = self._to_slider_value(value)
        self.slider.setValue(value)
        self.on_value_change()

    def set_range(self, min=0, max=100):
        # ControlNet may reuse sliders and change their ranges.
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)

    def _to_slider_value(self, value):
        # Used to account for step_size
        slider_value = value * self.multiplier
        if self.as_percent:
            if slider_value < 1.0:
                slider_value = slider_value * 100
            # return int(slider_value * 100)
        return int(slider_value)
    
    def _from_slider_value(self, slider_value):
        value = slider_value / self.multiplier
        # convert to %
        if self.as_percent and value > 0:
            return value / 100
        return value

    def value(self):
        value = self._from_slider_value(self.slider.value())
        return value
