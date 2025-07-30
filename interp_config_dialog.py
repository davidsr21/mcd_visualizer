import os
from qgis.PyQt import uic, QtWidgets

UI_PATH = os.path.join(os.path.dirname(__file__), 'interp_config_dialog.ui')
Ui_InterpConfigDialog, _ = uic.loadUiType(UI_PATH)

class InterpConfigDialog(QtWidgets.QDialog, Ui_InterpConfigDialog):
    """
    Diálogo para ajustar modos 'raw' vs 'interpolate' y resoluciones
    de tiempo, altitud, latitud y longitud en la herramienta de mapas.

    - Lee los flags actuales del plugin padre al abrirse.
    - Permite cambiar estos flags. Al aceptar, los vuelca al padre.
    - Desactiva/activa automáticamente los selectores de resolución según el modo.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #Volcamos valores por defecto la primera vez que lo abrimos
        cfg_time_raw = getattr(parent, "time_raw", True) # Coge el atributo del padre, si este es lat_raw da True, si ocurre lo contrario, False
        cfg_time_step = getattr(parent, "time_step", "1 hour")

        #Configuracion inicial del combo de modo de tiempo
        if cfg_time_raw:
            #Si escogemos raw data, no hay que hacer selector de resolucion
            self.Combo_Time_Mode.setCurrentText("Raw data")
            self.Combo_Time_Resolution.setEnabled(False)
        else:
            #Si se escoge interpolar datos, activa el selector de resolución
            self.Combo_Time_Mode.setCurrentText("Interpolate data")
            self.Combo_Time_Resolution.setEnabled(True)

        #Establece resolucion configurada si interpolate data esta seleccionado
        self.Combo_Time_Resolution.setCurrentText(cfg_time_step)

        # Si el padre aún no tiene atributos, usa estos valores, por defecto
        cfg_alt_raw = getattr(parent, "alt_raw", True)

        #Configuracion inicial del combo de modo de altitud
        if cfg_alt_raw:
            self.Combo_Altitude_Mode.setCurrentText("Raw data")
        else:
            self.Combo_Altitude_Mode.setCurrentText("Interpolate data")
        #Nota: La resolución de altitud se escoge en el plugin principal y no en este menú auxiliar de interpolación

        # Si el padre aún no tiene atributos, usa estos valores, por defecto
        cfg_lat_raw = getattr(parent, "lat_raw", True) # Coge el atributo del padre, si este es lat_raw da True, si ocurre lo contrario, False
        cfg_lat_step = getattr(parent, "lat_step", "2")
        cfg_lon_raw = getattr(parent, "lon_raw", True)
        cfg_lon_step = getattr(parent, "lon_step", "2")

        #Configuracion inicial del combo de modo de latitud
        if cfg_lat_raw:
            self.Combo_Latitude_Mode.setCurrentText("Raw data")
            self.Combo_Latitude_Resolution.setEnabled(False)
        else:
            self.Combo_Latitude_Mode.setCurrentText("Interpolate data")
            # Habilita el paso de interpolación para Latitud
            self.Combo_Latitude_Resolution.setEnabled(True)

        #Establece el paso configurado si no es lat_raw
        self.Combo_Latitude_Resolution.setCurrentText(cfg_lat_step)

        if cfg_lon_raw:
            self.Combo_Longitude_Mode.setCurrentText("Raw data")
            self.Combo_Longitude_Resolution.setEnabled(False)
        else:
            self.Combo_Longitude_Mode.setCurrentText("Interpolate data")
            #Habilita el paso de de interpolation para longitud
            self.Combo_Longitude_Resolution.setEnabled(True)

        #Establece el paso configurado si no es lon_raw
        self.Combo_Longitude_Resolution.setCurrentText(cfg_lon_step)

        #Conecta las señales con las funciones respectivas:
        # - currentTextChanged se emite al cambiar selección de combo
        # - accepted/rejected del buttonBox gestionan cerrar diálogo
        self.Combo_Time_Mode.currentTextChanged.connect(self._on_mode_changed)
        self.Combo_Latitude_Mode.currentTextChanged.connect(self._on_lat_mode_changed)
        self.Combo_Longitude_Mode.currentTextChanged.connect(self._on_lon_mode_changed)
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)

        #Renombramos los nombres por consistencia y estilo
        ok_btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok) #Manejamos aqui el texto Ok
        cancel_btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel) # Manejamos aquí el botón cancel
        ok_btn.setText("Accept") #Escogemos el texto
        cancel_btn.setText("Cancel") #Escogemos el texto que va a aparecer en el Plugin

    def _on_mode_changed(self, text):
        """
        Habilita/deshabilita el selector de resolución de tiempo
        según si el modo es 'Interpolate data' o no.
        """
        is_interp_time = (text == "Interpolate data") # Se encuentra a True si el usuario escogió poner Interpolate Data, de lo contrario marca False
        self.Combo_Time_Resolution.setEnabled(is_interp_time) #Si is_interp_time se encuentra a true, habilita el selector de resolucion

        if not is_interp_time:
            self.Combo_Time_Resolution.setCurrentIndex(0) #Resetea índice para evitar valor inválido y ponerlo siempre el primer valor que el usuario escoja

    def _on_lat_mode_changed(self, text):
        """
        Habilita/deshabilita el selector de resolución de latitud
        según si el modo es 'Interpolate data' o no.
        """
        is_interp_lat = (text == "Interpolate data")  # Se encuentra a True si el usuario escogió poner Interpolate Data, de lo contrario marca False
        self.Combo_Latitude_Resolution.setEnabled(is_interp_lat)#Si is_interp_time se encuentra a true, habilita el selector de resolucion

        if not is_interp_lat:
            self.Combo_Latitude_Resolution.setCurrentIndex(0)

    def _on_lon_mode_changed(self, text):
        """
        Habilita/deshabilita el selector de resolución de longitud
        según si el modo es 'Interpolate data' o no.
        """
        is_interp_lon = (text == "Interpolate data") # Se encuentra a True si el usuario escogió poner Interpolate Data, de lo contrario marca False
        self.Combo_Longitude_Resolution.setEnabled(is_interp_lon)#Si is_interp_time se encuentra a true, habilita el selector de resolucion

        if not is_interp_lon:
            self.Combo_Longitude_Resolution.setCurrentIndex(0) #Resetea índice para evitar valor inválido y ponerlo siempre el primer valor que el usuario escoja

    def _on_accept(self): #Parent handler
        """
        Invocado al pulsar 'Accept':
          - Extrae todos los valores actuales de los combos.
          - Asigna esos valores a los atributos del plugin padre.
          - Cierra el diálogo (self.accept()) para aplicar cambios.
        """
        p = self.parent() # p referencia al objeto padre, que es el plugin principal

        p.time_raw = (self.Combo_Time_Mode.currentText() == "Raw data") # Comprueba el texto actual del combo de tiempo; True si es "Raw data", False si es "Interpolate data", y lo asigna a p.time_raw
        p.time_step = self.Combo_Time_Resolution.currentText()  # Lee el texto del combo de resolución de tiempo y lo almacena en p.time_step

        p.alt_raw = (self.Combo_Altitude_Mode.currentText() == "Raw data")

        p.lat_raw = (self.Combo_Latitude_Mode.currentText() == "Raw data")
        p.lat_step = self.Combo_Latitude_Resolution.currentText()

        p.lon_raw = (self.Combo_Longitude_Mode.currentText() == "Raw data")
        p.lon_step = self.Combo_Longitude_Resolution.currentText()

        #Cierra el dialogo al pulsar en Accept
        self.accept()