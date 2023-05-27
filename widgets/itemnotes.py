from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt
import qtawesome


class NotesPopup(QDialog):
    def __init__(self, parent=None):
        """
        __init__ a popup that allows the user to enter notes about a scanned code/item that the app was not able to lookup successfully either online or locally.

        The notes, code, and a count of how many times each unique code was scanned during the inventory process will be written to a file saved to the 'output' directory in the format: MISSED-mm-dd-hh[am|pm].txt

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
        """
        super(NotesPopup, self).__init__(parent)

        self.setWindowTitle('Enter notes about the item:')
        self.setMinimumSize(300, 75)
        self.setMaximumSize(300, 75)
        # set the window icon to something having to do with looking things up
        self.setWindowIcon(qtawesome.icon('mdi6.printer-search', color='white'))

        # create the QLineEdit and OK button
        self.text_edit = QLineEdit()
        self.text_edit.setToolTip("Enter 1-2 sentences about the item to help with manual addition to database later.")
        ok_button = QPushButton("OK")
        ok_button.setFont(QFont('Roboto', 11))
        ok_button.setMinimumSize(75, 30)
        ok_button.setMaximumSize(90, 35)
        ok_button.setCursor(QCursor(Qt.PointingHandCursor))

        # when clicked - return whatever is in the qlineedit                                                      
        ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.text_edit)
        hbox.addWidget(ok_button)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def textValue(self):
        return self.text_edit.text()
    
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = NotesPopup()
    window.show()
    sys.exit(app.exec_())
