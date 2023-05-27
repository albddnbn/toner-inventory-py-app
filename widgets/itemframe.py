from PyQt5.QtWidgets import (QHBoxLayout,QLabel,QWidget)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, Qt
# app imports
from utils.toner_utils import initialize_config
from widgets.hstocklevelindicator import HStockLevelIndicator


class ItemFrame(QWidget):

    # signal for wh en the frame is clicked, emits the item dict
    userClicked = pyqtSignal(dict)

    def __init__(self, item: dict, parent=None):
        """
        __init__ A QWidget that holds the information for a single item, in the form of a horizontal stock level indicator (different class).

        This was a generic way to deal with items that weren't toner or ink. In the future, may be able to come up with better-looking widget, or widget specific to different item types (fusers, imaging units, etc.)

        Args:
            item (dict): dictionary containing item details - description, code, type, stock (all of the column values from db table).
            parent (_type_, optional): Parent Qt widget. Defaults to None.
            systemtray (QSystemTrayIcon, optional): system tray icon. Defaults to None.
        """
        super().__init__(parent)
        initialize_config(self)
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # self.setMaximumWidth(200)
        self.setMaximumHeight(125)
        # self.setFixedSize(175, 235)
        self.setToolTip(item["description"])
        # vbox = qtw.QVBoxLayout()
        hbox = QHBoxLayout()
        code_label = QLabel(f"{item['code']}\n{item['type'].upper()}")
        code_label.setFont(QFont("Roboto", 14, QFont.Bold))
        # code_label.setProperty("class", "codelabel")

        # vbox = QVBoxLayout()
        # title_vbox = QVBoxLayout()
        # title_vbox.addWidget(code_label)
        hbox.addWidget(code_label)
        hbox.setAlignment(code_label, Qt.AlignCenter)
        # TODO: add a few more bars to the stock level indicator - maybe 3-5
        stock_meter = HStockLevelIndicator(parent=self,
                                           stocklevel=int(item["stock"]), size=80)
        print("creating itemframe")
        hbox.addWidget(stock_meter)
        # hbox.setAlignment(stock_meter, Qt.AlignCenter)
        stock_meter.show()
        self.setLayout(hbox)
        self.setProperty("class", "itemframe")
        self.setStyleSheet(self.styleSheet())
        self.mouseDoubleClickEvent = lambda s=self: self.userClicked.emit(item)

