import os
from qgis.PyQt import uic, QtWidgets

UI_PATH = os.path.join(os.path.dirname(__file__), 'interp_config_dialog_profile.ui')
Ui_InterpConfigDialogProfile, _ = uic.loadUiType(UI_PATH)

class InterpConfigDialogProfile(QtWidgets.QDialog, Ui_InterpConfigDialogProfile):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #If father has not this atributes yet, he uses this values as default
        cfg_time_raw = getattr(parent, "time_raw_profile", True)
        cfg_time_step = getattr(parent, "time_step_profile", "1 hour")

        if cfg_time_raw:
            self.Combo_Time_Mode_Profile.setCurrentText("Raw data")
            self.Combo_Time_Resolution_Profile.setEnabled(False)
        else:
            self.Combo_Time_Mode_Profile.setCurrentText("Interpolate data")
            self.Combo_Time_Resolution_Profile.setEnabled(True)

        self.Combo_Time_Resolution_Profile.setCurrentText(cfg_time_step)

        cfg_alt_raw = getattr(parent, "alt_raw_profile", True)

        if cfg_alt_raw:
            self.Combo_Altitude_Mode_Profile.setCurrentText("Raw data")
        else:
            self.Combo_Altitude_Mode_Profile.setCurrentText("Interpolate data")

        cfg_lat_raw = getattr(parent, "lat_raw_profile", True)
        cfg_lat_step = getattr(parent, "lat_step_profile", "2")
        cfg_lon_raw = getattr(parent, "lon_raw_profile", True)
        cfg_lon_step = getattr(parent, "lon_step_profile", "2")

        if cfg_lat_raw:
            self.Combo_Latitude_Mode_Profile.setCurrentText("Raw data")
            self.Combo_Latitude_Resolution_Profile.setEnabled(False)
        else:
            self.Combo_Latitude_Mode_Profile.setCurrentText("Interpolate data")
            self.Combo_Latitude_Resolution_Profile.setEnabled(True)

        self.Combo_Latitude_Resolution_Profile.setCurrentText(cfg_lat_step)

        if cfg_lon_raw:
            self.Combo_Longitude_Mode_Profile.setCurrentText("Raw data")
            self.Combo_Longitude_Resolution_Profile.setEnabled(False)
        else:
            self.Combo_Longitude_Mode_Profile.setCurrentText("Interpolate data")
            self.Combo_Longitude_Resolution_Profile.setEnabled(True)

        self.Combo_Longitude_Resolution_Profile.setCurrentText(cfg_lon_step)

        #Signal Connections stablished
        self.Combo_Time_Mode_Profile.currentTextChanged.connect(self._on_mode_changed)
        self.Combo_Latitude_Mode_Profile.currentTextChanged.connect(self._on_lat_mode_changed)
        self.Combo_Longitude_Mode_Profile.currentTextChanged.connect(self._on_lon_mode_changed)
        self.buttonBox_Profile.accepted.connect(self._on_accept)
        self.buttonBox_Profile.rejected.connect(self.reject)

        ok_btn = self.buttonBox_Profile.button(QtWidgets.QDialogButtonBox.Ok)
        cancel_btn = self.buttonBox_Profile.button(QtWidgets.QDialogButtonBox.Cancel)
        ok_btn.setText("Accept")
        cancel_btn.setText("Cancel")

    def _on_mode_changed(self, text):
        """
        Enables/disables time resolution selector depending on Data Input
        """
        is_interp_time = (text == "Interpolate data")
        self.Combo_Time_Resolution_Profile.setEnabled(is_interp_time) #If is_interp is not "Interpolation data" then, this is false and remains disabled

        if not is_interp_time:
            self.Combo_Time_Resolution_Profile.setCurrentIndex(0)

    def _on_lat_mode_changed(self, text):
        """
        Enables/disables latitude resolution selector depending on Data Input
        """
        is_interp_lat = (text == "Interpolate data")
        self.Combo_Latitude_Resolution_Profile.setEnabled(is_interp_lat)

        if not is_interp_lat:
            self.Combo_Latitude_Resolution_Profile.setCurrentIndex(0)

    def _on_lon_mode_changed(self, text):
        """
        Enables/disables latitude resolution selector depending on Data Input
        """
        is_interp_lon = (text == "Interpolate data")
        self.Combo_Longitude_Resolution_Profile.setEnabled(is_interp_lon)

        if not is_interp_lon:
            self.Combo_Longitude_Resolution_Profile.setCurrentIndex(0)

    def _on_accept(self): #Parent handler
        """
        This function is invocated when Ok buton is pushed:
            - Writes the chosen config by parent object
            - Closes dialog with Accepted
        """
        p = self.parent()
        #Throws new values into main plugin
        p.time_raw_profile = (self.Combo_Time_Mode_Profile.currentText() == "Raw data")
        p.time_step_profile = self.Combo_Time_Resolution_Profile.currentText()

        p.alt_raw_profile = (self.Combo_Altitude_Mode_Profile.currentText() == "Raw data")

        p.lat_raw_profile = (self.Combo_Latitude_Mode_Profile.currentText() == "Raw data")
        p.lat_step_profile = self.Combo_Latitude_Resolution_Profile.currentText()

        p.lon_raw_profile = (self.Combo_Longitude_Mode_Profile.currentText() == "Raw data")
        p.lon_step_profile = self.Combo_Longitude_Resolution_Profile.currentText()

        self.accept()