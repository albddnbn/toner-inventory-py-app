import os
import yaml
from PyQt5.QtWidgets import QDialog, QFormLayout, QSizePolicy, QLabel, QComboBox, QDialogButtonBox, QLineEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize
import qtawesome


class SettingsPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # TODO: make this entire class more efficient - it's a mess.

        self.setWindowTitle("App Settings")
        self.setWindowIcon(qtawesome.icon('ei.cogs', color='white'))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # instead of initializing config - read from the config/config.yaml file and create dict of current settings
        with open("config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        # config = current settings dict
        layout = QFormLayout()
        self.setLayout(layout)

        # some app settings need to have textboxes for user input, and some only need comboboxes or checkboxes
        # QLineEdits / textboxes
        setting_line_edits = ["campus", "icon", "api url",
                              "log path", "about", "docs", "success sound", "fail sound"]
        # QComboBoxes
        setting_comboboxes = ["theme", "safe close", "tray notifications"]
        # Get a list of all .qss files in the "qss-stuff" directory
        qss_dir = "themes"
        theme_choices = [filename[:-4]
                         for filename in os.listdir(qss_dir) if filename.endswith(".qss")]
        labels = {}
        self.line_edits = {}
        self.combos = {}
        # create the comboboxes first
        for setting in setting_comboboxes:
            labels[setting] = QLabel(setting.capitalize())
            self.combos[setting] = QComboBox()
            # right now, the only combobox that needs settings other than on/off is the theme combobox
            if setting == "theme":
                self.combos[setting].addItems(theme_choices)
            else:
                self.combos[setting].addItems(["On", "Off"])
            layout.addRow(labels[setting], self.combos[setting])

        # create the line edits
        for setting in setting_line_edits:
            labels[setting] = QLabel(setting.capitalize())
            self.line_edits[setting] = QLineEdit()
            layout.addRow(labels[setting], self.line_edits[setting])
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        # for now, individually set the initial values of these settings
        self.combos["theme"].setCurrentText(self.config["app"]["theme"])
        if self.config["preferences"]["safetynet"] == 0:
            self.combos["safe close"].setCurrentText("Off")
        else:
            self.combos["safe close"].setCurrentText("On")
        if self.config["preferences"]["mute"] == 0:
            self.combos["tray notifications"].setCurrentText("Off")
        else:
            self.combos["tray notifications"].setCurrentText("On")

        
        # pre-fill all of the line edits with their current settings
        self.line_edits["campus"].setText(self.config["app"]["campus"])
        self.line_edits["icon"].setText(self.config["app"]["icon"])
        self.line_edits["api url"].setText(self.config["app"]["apiurl"])
        self.line_edits["log path"].setText(self.config["logs"]["main"])
        self.line_edits["about"].setText(self.config["docs"]["guide"])
        self.line_edits["docs"].setText(self.config["docs"]["pdoc"])
        self.line_edits["success sound"].setText(
            self.config["sounds"]["success"])
        self.line_edits["fail sound"].setText(self.config["sounds"]["fail"])

        # Add OK and Cancel buttons to the dialog
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setContentsMargins(15, 5, 0, 5)
        buttons.button(QDialogButtonBox.Ok).setText("Save")
        buttons.button(QDialogButtonBox.Ok).clicked.connect(self.set_config)
        buttons.button(QDialogButtonBox.Cancel).setText("Cancel")
        buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        for button in buttons.buttons():
            button.setFont(QFont('Roboto', 11))
            button.setMinimumSize(75, 30)
            button.setMaximumSize(90, 35)
            button.setCursor(Qt.PointingHandCursor)
        layout.addRow(buttons)

    def set_config(self):
        # read from self.combos and line edits to set self.config
        # create empty self.config dict
        # read from combox
        self.config["app"]["theme"] = self.combos["theme"].currentText()
        if self.combos["safe close"].currentText() == "Off":
            self.config["preferences"]["safetynet"] = 0
        else:
            self.config["preferences"]["safetynet"] = 1
        if self.combos["tray notifications"].currentText() == "Off":
            self.config["preferences"]["mute"] = 0
        else:
            self.config["preferences"]["mute"] = 1
        # read from line edits
        self.config["app"]["campus"] = self.line_edits["campus"].text()
        self.config["app"]["icon"] = self.line_edits["icon"].text()
        self.config["app"]["apiurl"] = self.line_edits["api url"].text()
        self.config["logs"]["main"] = self.line_edits["log path"].text()
        self.config["docs"]["guide"] = self.line_edits["about"].text()
        self.config["docs"]["pdoc"] = self.line_edits["docs"].text()
        self.config["sounds"]["success"] = self.line_edits["success sound"].text()
        self.config["sounds"]["fail"] = self.line_edits["fail sound"].text()
        # write to self.config.yaml
        with open("config/config.yaml", "w") as f:
            yaml.dump(self.config, f)

        self.accept()

    def sizeHint(self) -> QSize:
        return QSize(500, 300)
