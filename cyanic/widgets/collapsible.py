# A remake of simonxeko's collapseable widget CollapseButton.h 
# https://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class CollapsibleWidget(QWidget):
    def __init__(self, text="Toggle", child:QWidget=None):
        super().__init__()
        self.setLayout(QVBoxLayout())
        # self.setStyleSheet('background: none;')
        self.layout().setContentsMargins(0,0,0,0)
        self.show_child = False
        
        self.toggle_label = QToolButton()
        self.toggle_label.setStyleSheet('border:none; font-weight: bold;')
        self.toggle_label.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_label.setCheckable(True)
        # self.toggle_label.setIconSize(QSize(8, 8))
        self.toggle_label.setArrowType(Qt.DownArrow if self.show_child else Qt.RightArrow)
        self.toggle_label.setText(text)
        # Add action on button press
        self.toggle_label.clicked.connect(self.toggle)
        self.layout().addWidget(self.toggle_label)

        self.animator = QPropertyAnimation(child, b'maximumHeight')
        self.animator.setStartValue(0)
        self.animator.setEasingCurve(QEasingCurve.InOutQuad)
        self.animator.setDuration(300)
        self.animator.setEndValue(child.geometry().height() + 10)

        if not self.show_child:
            child.setMaximumHeight(0)
        
        self.layout().addWidget(child)

        # indented = QWidget()
        # indented.setLayout(QVBoxLayout())
        # indented.setContentsMargins(5,0,0,0)
        # indented.layout().addWidget(child)

        # self.layout().addWidget(indented)
        
    def toggle(self):
        self.show_child = self.toggle_label.isChecked()
        self.toggle_label.setArrowType(Qt.DownArrow if self.show_child else Qt.RightArrow)
        if self.show_child:
            self.animator.setDirection(QAbstractAnimation.Forward)
            self.animator.start()
        else:
            self.animator.setDirection(QAbstractAnimation.Backward)
            self.animator.start()
        self.update()