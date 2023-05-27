from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QPushButton, QSizePolicy
import qtawesome


class GenericIconButton(QPushButton):
    def __init__(self,qta_icon_str:str,icon_color:str,parent=None):
        """
        __init__ uses qtawesome to create a button with a qta icon that changes between two states when clicked.

        _extended_summary_

        Args:
            qta_icon_str (str): the icon name, from qta-browser.exe
            icon_color (str): icon color (hex code string)
            parent (_type_, optional): parent Qt object. Defaults to None.
        """
        super(GenericIconButton, self).__init__(parent)

        btn_icon = qtawesome.icon(qta_icon_str, color=icon_color)
        self.setCheckable(True)
        self.setIcon(btn_icon)
        self.setIconSize(QSize(30,30))

        # set mouse pointer to cursor
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setProperty("class", "geniconbtn")
        try:
            self.setStyleSheet(parent.styleSheet())
        except:
            print("generic icon button couldn't apply parets stylesheet ")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMaximumSize(40, 40)

    def sizeHint(self) -> QSize:
        return QSize(65, 10)
    

class IconButton(QPushButton):
    def __init__(self, parent=None,direction: str = "right", iconcolor="#333333"):
        """
        __init__ uses qtawesome to create a button with a qta icon that changes between two states when clicked.

        _extended_summary_

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
            direction (str, optional): _description_. Defaults to "right".
        """
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMaximumSize(75, 50)

        self.direction = direction
        self.icons = {
            "left":  {"1": qtawesome.icon('ph.arrow-fat-left-fill', color=iconcolor),
                      "2": qtawesome.icon('ph.arrow-fat-left-fill', color=iconcolor)},
            "right": {"1": qtawesome.icon('ph.arrow-fat-right-fill', color=iconcolor),
                        "2": qtawesome.icon('ph.arrow-fat-right-fill', color=iconcolor)},
        }
        self.setCheckable(True)
        self.setIcon(self.icons[self.direction]["1"])
        self.setIconSize(QSize(45,45))

        # set mouse pointer to cursor
        self.setCursor(QCursor(Qt.PointingHandCursor))

        self.setObjectName("iconButton")
        self.setStyleSheet("""
            QPushButton#iconButton {
                padding: 5px;
                border: 2px solid #2b6afe;
                padding-top: 10px;
                padding-bottom: 10px;
                border-radius: 5px;
            }
            QPushButton::pressed {
                background-color: #2b6afe;
                }
            QPushButton::pressed QIcon {
                padding-left:5px;
                }
            """)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
    def sizeHint(self) -> QSize:
        return QSize(85, 75)