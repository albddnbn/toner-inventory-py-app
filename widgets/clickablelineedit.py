from PyQt5.QtWidgets import QLineEdit

class ClickableLineEdit(QLineEdit):
    def __init__(self, parent=None, placeholder_text=None, *args, **kwargs):
        """
        __init__ Slightly modified subclass of the QLineEdit which deletes it's initial text contents when clicked for the first time. 

        After being clicked for the first time, the event that triggers the erasing of the text is disconnected. This makes it so any text entered by the user won't be deleted.

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
        """
        super(ClickableLineEdit, self).__init__(parent, *args, **kwargs)
        self.mousePressEvent = lambda s=self: self._mousePressEvent(s)
        if placeholder_text:
            self.setPlaceholderText(placeholder_text)
        self.setMaximumWidth(750)
    def change_placeholder_text(self, text:str):
        self.setPlaceholderText(text)

    def _mousePressEvent(self, event):
        self.clear()
        self.mousePressEvent = None

        # hbox layout for the search bar/buttons
