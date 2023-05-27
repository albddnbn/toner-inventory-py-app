from PyQt5.QtWidgets import (
    QSizePolicy,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,QWidget)
from PyQt5.QtCore import QSize,Qt, pyqtSignal
from PyQt5.QtGui import QLinearGradient, QColor
from widgets.qroundprogressbars import QRoundProgressBar
from utils.toner_utils import initialize_config


# TODO: add a refresh_item method to this class that will update the radial's value anytime the item's stock value is changed.
class RadialFrame(QWidget):
    # create signals for when the radial is doubleclicked
    userClicked = pyqtSignal(dict)
    def __init__(self, item:dict, parent=None):
        """
        __init__ QFrame that holds a toner radial widget, and provides the item's code via a QLabel, along with some other formatting and styling.

        _extended_summary_

        Args:
            item (dict): dictionary containing details about an item. Column names as keys, and values.
            parent (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(parent)

        self.colors_dict = {'cyan': '#00B7EB', 'yellow': '#ffff00', 'magenta': '#ff00ff', 'black': '#0f0f0f',
                            'matte black': '#333333', 'photo black': '#444444', '': '#333333', 'grey': '#808080', 'gray': '#808080', }
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        initialize_config(self)
        # set to radial frame QSS class (property)
        self.setProperty("class", "radialframe")

        layout = QVBoxLayout()
        bottom_hbox = QHBoxLayout()

        self.setToolTip(item["description"])

        # create 'gradient' for colored line
        circular_line = QLinearGradient(0, 0, 0, 100)
        circular_line.setColorAt(0.0, QColor(self.colors_dict[item["color"]]))
        circular_line.setColorAt(1.0, QColor(self.colors_dict[item["color"]]))

        # create QProgressBar to display toner radial
        self.radial_widget = QRoundProgressBar(
            parent=self, linecolor=circular_line, stockvalue=item["stock"])
        # configure the radial
        self.radial_widget.setFixedSize(125, 125)
        self.radial_widget.setBarStyle(QRoundProgressBar.BarStyle.LINE)
        self.radial_widget.setDecimals(0)
        self.radial_widget.setOutlinePenWidth(width=5.0)
        self.radial_widget.setFormat("%v")
        self.radial_widget.setRange(minval=0.0, maxval=10.0)
        # set the value of the self.radial_widget
        self.radial_widget.setValue(float(item["stock"]))
        # connect the radial's doubleclicked signal to the userClicked signal
        self.mouseDoubleClickEvent = lambda s=self: self.userClicked.emit(item)
        self.radial_widget.setStyleSheet(self.parent().styleSheet())
        code_label = QLabel(item["code"], parent=self)
        code_label.setProperty("class", "codelabel")
        code_label.setStyleSheet("""QLabel {font-size:18px;}""")
        layout.addWidget(code_label)
        # layout.addWidget(self.radial_widget)
        bottom_hbox.addWidget(self.radial_widget)
        # bottom_hbox.addWidget(self.button_frame)
        layout.addLayout(bottom_hbox)
        layout.setAlignment(code_label, Qt.AlignTop | Qt.AlignHCenter)
        layout.setAlignment(self.radial_widget, Qt.AlignRight | Qt.AlignVCenter)
        # layout.setAlignment(self.button_frame, Qt.AlignTop | Qt.AlignHCenter)
        layout.setAlignment(Qt.AlignCenter)
        
        self.setLayout(layout)

    def sizeHint(self) -> QSize:
        return QSize(100, 250)