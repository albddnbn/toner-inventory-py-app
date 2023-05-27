from PyQt5.QtWidgets import QToolBar
from PyQt5.QtCore import QSize


class TonerToolbar(QToolBar):
    def __init__(self, parent=None):
        """
        TonerToolbar QToolBar class - secondary toolbar for underneath the main menubar. It has big buttons for some of the most common actions that users may perform.

        I'm using icons from qtawesome for the buttons on this bar. After installing qtawesome with: "python -m pip install qtawesome", you should be able to open the **qtawesome icon browser** using the command: "qta-browser". More info on qta-browser can be found here: https://qtawesome.readthedocs.io/en/latest/icon_browser.html.

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
        """
        super().__init__(parent)

        self.setMovable(False)
        # self.setIconSize(QSize(16, 16))