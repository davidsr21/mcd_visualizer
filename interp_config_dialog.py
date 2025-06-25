import os
from qgis.PyQt import uic, QtWidgets

UI_PATH = os.path.join(os.path.dirname(__file__), 'interp_config_dialog.ui')
Ui_InterpConfigDialog, _ = uic.loadUiType(UI_PATH)

class InterpConfigDialog(QtWidgets.QDialog, Ui_InterpConfigDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #If father has not this atributes yet, he uses this values as default
        cfg_time_raw = getattr(parent, "time_raw", True)
        cfg_time_step = getattr(parent, "time_step", "1 hour")

        if cfg_time_raw:
            self.Combo_Time_Mode.setCurrentText("Raw data")
            self.Combo_Time_Resolution.setEnabled(False)
        else:
            self.Combo_Time_Mode.setCurrentText("Interpolate data")
            self.Combo_Time_Resolution.setEnabled(True)

        self.Combo_Time_Resolution.setCurrentText(cfg_time_step)

        cfg_alt_raw = getattr(parent, "alt_raw", True)

        if cfg_alt_raw:
            self.Combo_Altitude_Mode.setCurrentText("Raw data")
        else:
            self.Combo_Altitude_Mode.setCurrentText("Interpolate data")

        cfg_lat_raw = getattr(parent, "lat_raw", True)
        cfg_lat_step = getattr(parent, "lat_step", "2")
        cfg_lon_raw = getattr(parent, "lon_raw", True)
        cfg_lon_step = getattr(parent, "lon_step", "2")

        if cfg_lat_raw:
            self.Combo_Latitude_Mode.setCurrentText("Raw data")
            self.Combo_Latitude_Resolution.setEnabled(False)
        else:
            self.Combo_Latitude_Mode.setCurrentText("Interpolate data")
            self.Combo_Latitude_Resolution.setEnabled(True)

        self.Combo_Latitude_Resolution.setCurrentText(cfg_lat_step)

        if cfg_lon_raw:
            self.Combo_Longitude_Mode.setCurrentText("Raw data")
            self.Combo_Longitude_Resolution.setEnabled(False)
        else:
            self.Combo_Longitude_Mode.setCurrentText("Interpolate data")
            self.Combo_Longitude_Resolution.setEnabled(True)

        self.Combo_Longitude_Resolution.setCurrentText(cfg_lon_step)

        #Signal Connections stablished
        self.Combo_Time_Mode.currentTextChanged.connect(self._on_mode_changed)
        self.Combo_Latitude_Mode.currentTextChanged.connect(self._on_lat_mode_changed)
        self.Combo_Longitude_Mode.currentTextChanged.connect(self._on_lon_mode_changed)
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)

        ok_btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        cancel_btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel)
        ok_btn.setText("Accept")
        cancel_btn.setText("Cancel")

    def _on_mode_changed(self, text):
        """
        Enables/disables time resolution selector depending on Data Input
        """
        is_interp_time = (text == "Interpolate data")
        self.Combo_Time_Resolution.setEnabled(is_interp_time) #If is_interp is not "Interpolation data" then, this is false and remains disabled

        if not is_interp_time:
            self.Combo_Time_Resolution.setCurrentIndex(0)

    def _on_lat_mode_changed(self, text):
        """
        Enables/disables latitude resolution selector depending on Data Input
        """
        is_interp_lat = (text == "Interpolate data")
        self.Combo_Latitude_Resolution.setEnabled(is_interp_lat)

        if not is_interp_lat:
            self.Combo_Latitude_Resolution.setCurrentIndex(0)

    def _on_lon_mode_changed(self, text):
        """
        Enables/disables latitude resolution selector depending on Data Input
        """
        is_interp_lon = (text == "Interpolate data")
        self.Combo_Longitude_Resolution.setEnabled(is_interp_lon)

        if not is_interp_lon:
            self.Combo_Longitude_Resolution.setCurrentIndex(0)

    def _on_accept(self): #Parent handler
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

        p.lat_raw = (self.Combo_Latitude_Mode.currentText() == "Raw data")
        p.lat_step = self.Combo_Latitude_Resolution.currentText()

        p.lon_raw = (self.Combo_Longitude_Mode.currentText() == "Raw data")
        p.lon_step = self.Combo_Longitude_Resolution.currentText()

        self.accept()
