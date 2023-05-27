from PyQt5.QtWidgets import QSizePolicy,QPushButton
from PyQt5.QtCore import QSize,Qt
from PyQt5.QtGui import QFont


class SearchButton(QPushButton):
    # Additional constructor with a custom text label
    def __init__(self, text:str, parent=None):
        """
        __init__ button used on parts of the app that have a search button (usually have a search textbox to the left of it).

        Args:
            text (str): the text that will be displayed on the button
            parent (_type_, optional): parent Qt object. Defaults to None.
        """
        super().__init__(text, parent)

        # set size policy for main buttons
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(125, 40)
        self.setMaximumSize(150, 50)
        # set DTCC Font
        self.setFont(QFont("Roboto", 18))
        # set button text
        self.setText(text.upper())
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "search-button")

    def sizeHint(self):
        return QSize(150, 40)

class HomepageButton(QPushButton):
    # Additional constructor with a custom text label
    def __init__(self, text, parent=None):
        """
        __init__ the big buttons that are shown on the main page of the app ('dell', 'lexmark', 'hp', etc).

        Args:
            text (_type_): _description_
            parent (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(text, parent)

        # set size policy for main buttons
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(350, 50)
        self.setMaximumSize(550, 100)
        # set DTCC Font
        self.setFont(QFont("Roboto", 18))
        # set button text
        self.setText(text.upper())

    def sizeHint(self):
        return QSize(450, 60)