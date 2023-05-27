import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QPlainTextEdit, QVBoxLayout,
                             QSizePolicy, QFrame, QPushButton, QHBoxLayout,
                             QFileDialog, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtMultimedia import QSound
# App-specific imports
from utils.upclookup import ItemLookup
from widgets.ledindicator import LedIndicator
from widgets.itemnotes import NotesPopup
from utils.toner_utils import initialize_config, write_log


class ScanInputWindow(QFrame):

    def __init__(self, parent=None, systemtray=None, *args, **kwargs):
        """
        __init__ pop up window that will attempt to look up upc codes & update the database accordingly every time a upc code is scanned into the textbox.

        The list of scanned codes is saved to a text file, and any items that were not able to be added to the database are also written to a separate file of missed items, along with the user's notes about the item.

        Args:
            parent (_type_, optional): parent Qt. Defaults to None.
            systemtray (_type_, optional): The app system tray icon, when passed allows for system tray notifications. Defaults to None.
        """
        super().__init__(parent=None, *args, **kwargs)
        # config
        initialize_config(self)
        self.setWindowTitle("Scan Inventory")
        self.setWindowIcon(QIcon(self.icon))
        self.setProperty("class", "ScanInputWindow")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.systemtray = systemtray
        # items that failed to be added to database, but have already been added to missed w/notes, so they don't need to slow up scanning process again
        self.known_missed_items = []
        self.missed_items = {}
        vbox = QVBoxLayout()
        # the textbox that codes are scanned into
        self.textEdit = QPlainTextEdit(parent=self)
        self.textEdit.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
        self.textEdit.setPlaceholderText("Scan in UPCs here")
        self.textEdit.setMaximumWidth(2000)
        self.textEdit.setMaximumHeight(2000)
        self.textEdit.resize(250, 800)
        self.textEdit.setProperty("class", "scanbox")
        # Set the initial value of the num_lines property to 0
        self.textEdit.setProperty("num_lines", 0)
        # Connect the textChanged signal to the onTextChanged function
        self.textEdit.cursorPositionChanged.connect(self.check_input_box)
        # -- the red & green lights --
        self.red_led = LedIndicator(parent=self, color="red")
        self.green_led = LedIndicator(parent=self, color="green")

        hbox = QHBoxLayout()
        # the buttons are in a horizontal frame
        hframe = QFrame()

        hframe.setProperty("class", "hframe")
        hframe.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hbox.addWidget(self.red_led)
        hbox.addWidget(self.green_led)
        hframe.setLayout(hbox)
        vbox.addWidget(hframe)

        for led in [self.green_led, self.red_led]:
            led.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.ok_button = QPushButton("Annotate item", self)
        self.ok_button.setToolTip(
            "Enter notes for failed item before proceeding w/scan")
        self.ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        # only show this button if there's been a failure, so user can enter some notes to remember the item and manually add to database later
        self.ok_button.hide()
        self.ok_button.clicked.connect(self.click_enter_item_notes)

        vbox.addWidget(self.ok_button)
        vbox.addWidget(self.textEdit)

        # create hbox for save / exit button]
        button_hbox = QHBoxLayout()
        # create the save button
        save_button = QPushButton("Save", self)
        save_button.clicked.connect(self.save_file)
        save_button.setCursor(QCursor(Qt.PointingHandCursor))
        save_button.setProperty("class", "savebutton")

        exit_button = QPushButton("Exit", self)
        exit_button.clicked.connect(self.save_files_and_exit)
        exit_button.setCursor(QCursor(Qt.PointingHandCursor))
        exit_button.setProperty("class", "exitbutton")

        button_hbox.addWidget(save_button)
        button_hbox.addWidget(exit_button)

        vbox.addLayout(button_hbox)
        vbox.setAlignment(Qt.AlignHCenter)

        self.setLayout(vbox)

        # -- the success & failure sounds (actual file paths are in config)
        self.success_sound = QSound(os.path.abspath(self.success))
        self.fail_sound = QSound(os.path.abspath(self.fail))

        now = datetime.now()
        date_string = now.strftime("%m-%d")
        time_string = now.strftime("%I%p").lower()
        self.filestring = f"{date_string}-{time_string}.txt"
        self.missedfile = f"./output/MISSED-{self.filestring}"
        self.available = True
        self.input_code = ""
        self.current_row = 0
        # will not enter a code from the same row twice no matter where the cursor moves
        self.entered_rows = []
        # every unique missed item will have these keys/values: input_scan: the code scanned in, count: number of times it was scanned in, notes: user notes about the item
        self.missed_items_dict = {}
        self.green_led.turn_on()
        self.red_led.turn_off()

    def check_input_box(self):
        """
        check_input_box every time the cursor changes position, this function is run.

        When the cursor moves to a new line, function will grab the code from preceding line and attempt to add it to the database and/or update stock.
        """
        # this function is called every time a character is entered into the textbox, input_code stores citem_lookurrent line of text
        # get current block number that cursor is on
        cursor = self.textEdit.textCursor()
        row = cursor.blockNumber()

        block = cursor.block()
        text = block.text()
        if self.available:
            if row == self.current_row:
                if row not in self.entered_rows:
                    self.entered_rows.append(row)
                # incoming scanned codes will be changed to all lowercase here (I've ran into some that are the same code/item but when scanned, have different cases for letters)
                self.input_code = text.lower()

            else:
                if row not in self.entered_rows:
                    self.input_code = self.input_code.lower()
                    # self.input_code = text
                    # run search of input code
                    write_log(self.logfile,
                              "LOOKING UP",
                              f"Looking up entry: {self.input_code}",
                              prt=True)
                    # try to look up the item in database, then in api
                    item_lookup = ItemLookup(self.input_code)
                    # make doubly sure the input code is stripped, lowercase, etc
                    self.input_code = self.input_code.lower().strip()
                    # lookup item
                    result = item_lookup.look_up_code()
                    if result:
                        write_log(
                            self.logfile,
                            "SCAN SUCCESS",
                            f"Stock was increased by 1 for {self.input_code}.",
                            prt=True)
                        self.success_sound.play()
                    # if all lookups fail - prompt user for notes about item if they haven't already entered them
                    elif not result:
                        # print("not a upc code:")
                        write_log(
                            self.logfile,
                            "SCAN ERROR",
                            f"Entry {self.input_code} needs to be added to database manually.",
                            prt=True)
                        self.missed_code = self.input_code

                        if self.missed_code in self.missed_items_dict.keys():
                            # add one to the item's count
                            self.missed_items_dict[self.missed_code][0] += 1
                        else:
                            # add to missed_items_dict
                            self.missed_items_dict[self.missed_code] = [1, ""]
                            # --------------------------------------------------------------------------------
                            # SCAN WILL ONLY BE DISABLED FOR FIRST TIME A CODE IS MISSED.
                            # after the user enters notes for the item, scan will be re-enabled, and any future scans of the same item will be ignored, i.e. won't stop the scanning process.
                            # they will be counted and output to a missed items file after the scan dialog has been exited.
                            self.disable_scan()

                    self.input_code = ""
                    self.current_row = row

    def save_file(self, output_file: str = None):
        """
        save_file create QfileDialog to save text in textedit to text file
        """
        if not output_file:
            filename, filter = QFileDialog.getSaveFileName(
                self, 'Save File', directory=".", filter="Text Files (*.txt)")
        else:
            filename = output_file
        file = open(filename, 'w+')
        text = self.textEdit.toPlainText()
        file.write(text)
        file.close()

    def save_files_and_exit(self):
        '''
        save_files_and_exit ask user if they'd like to save their scan file and then exit.
        '''
        response = QMessageBox.question(
            self, 'Exiting',
            "Do you want to save your scan list to a text file?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if response == QMessageBox.Yes:
            self.save_file()

        else:
            self.save_file(output_file=f"output/scanlist-{self.filestring}")

        try:
            # CREATING MISSED ITEMS REPORT
            # -------------------------------------------------------------------------
            with open(self.missedfile, 'w+') as f:
                # cycle through self.missed_items_dict
                f.write(
                    f"Missed items report from {self.filestring} scan:\n"
                )
                f.write(
                    "-----------------------------------------------------------------------------\n"
                )
                for scanned_code, count_list in self.missed_items_dict.items():
                    f.write(f"""Code: {scanned_code} [{count_list[0]}x]\n
        - Notes: {count_list[1]}\n""")
                f.write(
                    "-----------------------------------------------------------------------------\n"
                )

                # close the window
                self.close()
        # unless error, like the 'output' folder not existing
        except Exception as e:
            # create file in current directory
            # CREATING MISSED ITEMS REPORT
            # -------------------------------------------------------------------------
            with open(f"MISSED-{self.filestring}", 'w+') as f:
                # cycle through self.missed_items_dict
                f.write(
                    f"Missed items report from {self.filestring} scan:\n"
                )
                f.write(
                    "-----------------------------------------------------------------------------\n"
                )
                for scanned_code, count_list in self.missed_items_dict.items():
                    f.write(f"""Code: {scanned_code} [{count_list[0]}x]\n
        - Notes: {count_list[1]}\n""")
                f.write(
                    "-----------------------------------------------------------------------------\n"
                )

                # close the window
                self.close()

    def enable_scan(self):
        """
        enable_scan Turn the green LED on, red LED off, and reactivate the TextEdit widget, and play corresponding sound.

        If the textedit widget is activated when the newline is inserted, it will trigger the alert/red light again.
        """
        if not self.available:
            self.textEdit.setEnabled(True)
            self.success_sound.play()
            # hide the manual entry button and disable it
            self.ok_button.hide()
            self.green_led.turn_on()
            self.red_led.turn_off()
        # set focus back innside the  textbox
        self.textEdit.setFocus()
        self.available = True

    def disable_scan(self):
        """ disable_scan Turn red LED on and essentially lock the console until the user presses the button to acknowledge the error in upc code intake. """
        # turn green off, red on
        if self.available:

            self.ok_button.show()

            self.fail_sound.play()
            self.available = False
            self.textEdit.setDisabled(True)
            self.green_led.turn_off()
            self.red_led.turn_on()

    def click_enter_item_notes(self):
        # prompt for notes
        user_notes = NotesPopup(parent=self)
        if user_notes.exec_() == QDialog.Accepted:
            notes = user_notes.textValue()
            if not notes:
                notes = "No notes entered."
            self.missed_items_dict[self.missed_code][1] = notes
        # now, just have to loop through this dict at the end, in the save and exit function, and write to file.

        self.enable_scan()

    def sizeHint(self) -> QSize:
        return QSize(350, 700)


if __name__ == '__main__':
    app = QApplication([])
    window = ScanInputWindow()
    window.show()
    app.exec_()
