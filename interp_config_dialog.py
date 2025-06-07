import os
from qgis.PyQt import uic, QtWidgets

UI_PATH = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'interp_config_dialog.ui'))
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
            self.Combo_Time_Resolution.currentText("1 hour")
        else:
            self.Combo_Time_Mode.setCurrentText("Interpolate data")
            self.Combo_Time_Resolution.setEnabled(True)
            self.Combo_Time_Resolution.currentText("1 hour")

        #Signal Connections stablished
        self.Combo_Time_Mode.currentTextChanged.connect(self._on_mode_changed)
        self.ButtonBox.accepted.connect(self._on_accept)
        self.ButtonBox.rejected.connect(self.reject)

        ok_btn = self.ButtonBox.button(QtWidgets.QDialogButtonBox.Ok)
        cancel_btn = self.ButtonBox.button(QtWidgets.QDialogButtonBox.Cancel)
        ok_btn.setText("Ok")
        cancel_btn.setText("Cancel")

    def _on_mode_changed(self, text):
        """
        Enables/disables resolution selector depending on Data Input
        """
        is_interp = (text == "Interpolate data")
        self.Combo_Time_Resolution.setEnabled(is_interp) #If is_interp is not "Interpolation data" then, this is false and remains disabled

        if not is_interp:
            self.Combo_Time_Resolution.setCurrentIndex(0)

    def _on_accept(self):
        """
        This function is invocated when Ok buton is pushed:
            - Writes the chosen config by parent object
            - Closes dialog with Accepted
        """
        p = self.parent()
        #Throws new values into main plugin
        p.time_raw = (self.Combo_Time_Mode.CurrentText() == "Raw data")
        p.time_step = self.Combo_Time_Resolution.currentText()
        self.accept()
