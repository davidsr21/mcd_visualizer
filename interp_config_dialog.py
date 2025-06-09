import os
from qgis.PyQt import uic, QtWidgets

UI_PATH = os.path.join(os.path.dirname(__file__), 'interp_config_dialog.ui')
Ui_InterpConfigDialog, _ = uic.loadUiType(UI_PATH)

class InterpConfigDialog(QtWidgets.QDialog, Ui_InterpConfigDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #If father has not this atributes yet, he uses this values as default
        cfg_raw = getattr(parent, "time_raw", True)
        cfg_step = getattr (parent, "time_step", "1 Hour")

        if cfg_raw:
            self.Combo_Time_Mode.setCurrentText("Raw data")
            self.Combo_Time_Resolution.setEnabled(False)
            self.Combo_Time_Resolution.setCurrentText("1 hour")
        else:
            self.Combo_Time_Mode.setCurrentText("Interpolate data")
            self.Combo_Time_Resolution.setEnabled(True)
            self.Combo_Time_Resolution.setCurrentText("1 hour")

        cfg_alt_raw = getattr(parent, "time_raw", True)
        cfg_alt_step = getattr (parent, "time_step", "1 Hour")

        if cfg_alt_raw:
            self.Combo_Altitude_Mode.setCurrentText("Raw data")
            self.Combo_Altitude_Resolution.setEnabled(False)
            self.Combo_Altitude_Resolution.setCurrentText("1 km")
        else:
            self.Combo_Altitude_Mode.setCurrentText("Interpolate data")
            self.Combo_Altitude_Resolution.setEnabled(True)
            self.Combo_Altitude_Resolution.setCurrentText("1 km")

        #Signal Connections stablished
        self.Combo_Time_Mode.currentTextChanged.connect(self._on_mode_changed)
        self.Combo_Altitude_Mode.currentTextChanged.connect(self._on_alt_mode_changed)
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)

        ok_btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        cancel_btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel)
        ok_btn.setText("Accept")
        cancel_btn.setText("Cancel")

    def _on_mode_changed(self, text):
        """
        Enables/disables resolution selector depending on Data Input
        """
        is_interp_time = (text == "Interpolate data")
        self.Combo_Time_Resolution.setEnabled(is_interp_time) #If is_interp is not "Interpolation data" then, this is false and remains disabled

        if not is_interp_time:
            self.Combo_Time_Resolution.setCurrentIndex(0)

    def _on_alt_mode_changed(self, text):
        """
        Enables/disables resolution selector depending on Data Input
        """
        is_interp_alt = (text == "Interpolate data")
        self.Combo_Altitude_Resolution.setEnabled(is_interp_alt) #If is_interp is not "Interpolation data" then, this is false and remains disabled

        if not is_interp_alt:
            self.Combo_Altitude_Resolution.setCurrentIndex(0)

    def _on_accept(self):
        """
        This function is invocated when Ok buton is pushed:
            - Writes the chosen config by parent object
            - Closes dialog with Accepted
        """
        p = self.parent()
        #Throws new values into main plugin
        p.time_raw = (self.Combo_Time_Mode.currentText() == "Raw data")
        p.time_step = self.Combo_Time_Resolution.currentText()
        p.alt_raw = (self.Combo_Altitude_Mode.currentText() == "Raw data")
        p.alt_step = self.Combo_Altitude_Resolution.currentText()
        self.accept()
