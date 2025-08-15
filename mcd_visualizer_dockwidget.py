"""
Mandatory libraries for performing the job
"""
import os
import tempfile
import uuid
import processing
import matplotlib.pyplot as plt
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.core import QgsProject,QgsRasterLayer,QgsSingleBandPseudoColorRenderer,QgsStyle,Qgis, QgsVectorLayer
from osgeo import gdal, osr
from PyQt5.QtWidgets import QMessageBox, QApplication, QDialog, QDialogButtonBox, QProgressDialog
from qgis.utils import iface
from qgis.PyQt.QtGui import QColor
import xarray as xr
import numpy as np
from processing.core.Processing import Processing
from .interp_config_dialog import InterpConfigDialog
from .interp_config_dialog_profile import InterpConfigDialogProfile



# Carga de la UI principal generada con Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'mcd_visualizer_dockwidget_base_profiles.ui'))

# Definición de la clase principal del plugin, que hereda de QDockWidget y la UI cargada
class MCDVisualizerDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(MCDVisualizerDockWidget, self).__init__(parent)
        self.setupUi(self) # Monta widgets y layouts definidos en el .ui

        osr.DontUseExceptions() #Silencia avisos al usar IAU 49900 como CSR, ademas de mantener modo sin excepciones

        # Flags de interpolación para Map Tool:
        self.time_raw = True #Valor por defecto, si esta a true usa raw data, si esta a false, usa interpolate data
        self.time_step = "1 hour" #Resolution of selected interpolation

        self.alt_raw = True # True: usa valores crudos de altitud

        self.lat_raw = True
        self.lat_step = "2"

        self.lon_raw = True
        self.lon_step = "2"

        # Flags de interpolación para Profile Tool:

        self.time_raw_profile = True #True =  Uses raw data, False = Interpolates
        self.time_step_profile = "1 hour" #Resolucion por defecto

        self.alt_raw_profile = True # True: usa valores crudos de altitud

        self.lat_raw_profile = True
        self.lat_step_profile = "2"

        self.lon_raw_profile = True
        self.lon_step_profile = "2"

        # Ruta base donde se almacenan los NetCDF
        self.ruta = r"C:\MCD6.1\data" # Cadena cruda con la ruta absoluta
        # Diccionario que mapea nombre legible → Nombre carpeta
        self.lista_carpetas = {
            "Yearly Average": "clim_aveEUV",
            "Cold": "cold",
            "Warm": "warm",
            "Dust Storm": "strm",
            "Martian Year 24": "MY24",
            "Martian Year 25": "MY25",
            "Martian Year 26": "MY26",
            "Martian Year 27": "MY27",
            "Martian Year 28": "MY28",
            "Martian Year 29": "MY29",
            "Martian Year 30": "MY30",
            "Martian Year 31": "MY31",
            "Martian Year 32": "MY32",
            "Martian Year 33": "MY33",
            "Martian Year 34": "MY34",
            "Martian Year 35": "MY35",
        }

        #Diccionario que mapea nombre original de la variable con nombre que aparece en MCD
        self.variable_descriptions = {
            # --- ME (mean) ---
            "tsurf": "Surface temperature (K)",
            "ps": "Surface pressure (Pa)",
            "co2ice": "CO₂ ice cover (kg m⁻²)",
            "fluxsurf_lw": "LW (thermal IR) radiative flux to surface (W m⁻²)",
            "fluxtop_lw": "LW (thermal IR) radiative flux to space (W m⁻²)",
            "fluxsurf_dn_sw": "SW (solar) incoming radiative flux to surface (W m⁻²)",
            "fluxsurf_dir_dn_sw": "SW (solar) direct incoming radiative flux to surface (W m⁻²)",
            "fluxsurf_up_sw": "SW (solar) reflected radiative flux from surface (W m⁻²)",
            "fluxtop_up_sw": "SW (solar) outgoing radiative flux to space (W m⁻²)",
            "fluxtop_dn_sw": "SW (solar) incoming radiative flux from space (W m⁻²)",
            "tau_pref_gcm": "Monthly mean visible dust optical depth at 610 Pa (unitless)",
            "col_h2ovapor": "Water vapor column (kg m⁻²)",
            "col_h2oice": "Water ice column (kg m⁻²)",
            "zmax": "Height of thermals in the PBL (m)",
            "hfmax": "Maximum thermals heat flux (K·m/s)",
            "wstar": "Vertical velocity scale in thermals (m/s)",
            "h2oice": "H₂O ice cover (seasonal frost) (kg m⁻²)",
            "c_co2": "CO₂ column (molecules/cm²)",
            "c_co": "CO column (molecules/cm²)",
            "c_o": "O column (molecules/cm²)",
            "c_o2": "O₂ column (molecules/cm²)",
            "c_o3": "O₃ column (molecules/cm²)",
            "c_h": "H column (molecules/cm²)",
            "c_h2": "H₂ column (molecules/cm²)",
            "c_n2": "N₂ column (molecules/cm²)",
            "c_ar": "Ar column (molecules/cm²)",
            "c_he": "He column (molecules/cm²)",
            "c_elec": "Total Electronic Content (TEC) (electrons/cm²)",
            "rho": "Atmospheric density (kg m⁻³)",
            "temp": "Atmospheric temperature (K)",
            "u": "Zonal (East–West) wind (m/s)",
            "v": "Meridional (North–South) wind (m/s)",
            "w": "Vertical (up–down) wind (m/s)",
            "vmr_h2ovapor": "Water vapor volume mixing ratio (mol/mol)",
            "vmr_h2oice": "Water ice volume mixing ratio (mol/mol)",
            "vmr_co2": "CO₂ volume mixing ratio (mol/mol)",
            "vmr_co": "CO volume mixing ratio (mol/mol)",
            "vmr_o": "O volume mixing ratio (mol/mol)",
            "vmr_o2": "O₂ volume mixing ratio (mol/mol)",
            "vmr_o3": "O₃ volume mixing ratio (mol/mol)",
            "vmr_h": "H volume mixing ratio (mol/mol)",
            "vmr_h2": "H₂ volume mixing ratio (mol/mol)",
            "vmr_n2": "N₂ volume mixing ratio (mol/mol)",
            "vmr_ar": "Ar volume mixing ratio (mol/mol)",
            "vmr_he": "He volume mixing ratio (mol/mol)",
            "vmr_elec": "Electron number density (mol/mol)",
            "dustq": "Dust mass mixing ratio (kg/kg)",
            "reffdust": "Dust effective radius (m)",
            "reffice": "Water ice effective radius (m)",

            # --- SD (standard deviation / RMS) ---
            "rmstsurf": "RMS of surface temperature (K)",
            "rmsps": "RMS of surface pressure (Pa)",
            "rmstau_pref_gcm": "RMS of dust optical depth at 610 Pa (unitless)",
            "armstemp": "Altitude-wise RMS of atmospheric temperature (K)",
            "rmstemp": "Pressure-wise RMS of atmospheric temperature (K)",
            "armsrho": "Altitude-wise RMS of atmospheric density (kg m⁻³)",
            "rmsrho": "Pressure-wise RMS of atmospheric density (kg m⁻³)",
            "armsu": "Altitude-wise RMS of zonal (East–West) wind (m/s)",
            "rmsu": "Pressure-wise RMS of zonal (East–West) wind (m/s)",
            "armsv": "Altitude-wise RMS of meridional (North–South) wind (m/s)",
            "rmsv": "Pressure-wise RMS of meridional (North–South) wind (m/s)",
            "armsw": "Altitude-wise RMS of vertical (up–down) wind (m/s)",
            "rmsw": "Pressure-wise RMS of vertical (up–down) wind (m/s)",
            "armspressure": "Altitude-wise RMS of atmospheric pressure (Pa)"
        }

        # Inicialización del combo de épocas
        self.Combo_Epoca.clear() # Vacía el combo de selección de época
        self.Combo_Estadistica.clear()
        self.Combo_Estadistica.addItems(["me", "sd"])
        self.Combo_Estadistica.setCurrentText("me")
        self.Combo_Epoca.addItems(list(self.lista_carpetas.keys())) # Añade los nombres de las épocas
        self.Combo_Epoca.setCurrentIndex(0) # Selecciona la primera época por defecto
        self.cambio_epoca(self.Combo_Epoca.currentText()) # Llama a cambio_epoca() para poblar archivos

        # Conexión de señales a manejadores
        self.Combo_Epoca.currentTextChanged.connect(self.cambio_epoca)  # Al cambiar época
        self.Combo_Archivo.currentTextChanged.connect(self.cambio_archivo)  # Al cambiar archivo .nc
        self.Combo_Variable.itemSelectionChanged.connect(self.toggle_altitude_multi) # Al cambiar variable
        self.Check_Mapa.stateChanged.connect(self.toggle_map_latlon_mode) # Al alternar full map
        self.Push_Visualizar.clicked.connect(self.visualizar_variable) # Al pulsar Visualizar
        self.Push_Reset.clicked.connect(self.reset_all)  # Al pulsar Reset
        self.Push_InterpConfig.clicked.connect(self.open_interp_config) # Al pulsar Config Interp

        # Configuración inicial de controles de altitud
        self.Combo_Altitud.setEnabled(False) # Deshabilita combo de altitud
        self.Combo_Altitud.setStyleSheet("QComboBox:disabled { background-color: red }") # Rojo si está deshabilitado
        self.Combo_Altitud.setToolTip("Select one variable at least") #Tooltip explicativo que salta si se pone el cursor encima

        self.Interpolate_Altitude.setEnabled(False) # Deshabilita input altitud manual
        self.Interpolate_Altitude.clear()  # Limpia cualquier texto previo
        self.Interpolate_Altitude.setPlaceholderText("Introduce altitude (m)") # Texto que indica al usuario como introducir el dato

        self.Combo_Estadistica.currentTextChanged.connect(self.estadistica_changed)  # Salta al cambiar de estadística

        # Evaluación inicial de estado de altitud y full map
        self.toggle_altitude_multi() # Habilita control de altitud altitud según variable seleccionada
        self.toggle_map_latlon_mode(self.Check_Mapa.checkState()) # Ajusta recorte vs mapa completo

        # Inicialización de pestaña Profile Tool
        self.Combo_Epoca_Profile.clear() # Vacía combo de Profile Épocas
        self.Combo_Estadistica_Profile.clear()
        self.Combo_Estadistica_Profile.addItems(["me", "sd"])
        self.Combo_Estadistica_Profile.setCurrentText("me")
        self.Combo_Epoca_Profile.addItems(list(self.lista_carpetas.keys())) # Añade épocas al combo Profile
        self.Combo_Epoca_Profile.setCurrentIndex(0)  # Selecciona primera época Profile por defecto
        self.Combo_Epoca_Profile.currentTextChanged.connect(self.cambio_epoca_profile) # Señal cambio época Profile
        self.Combo_Archivo_Profile.currentTextChanged.connect(self.cambio_archivo_profile)

        self.cambio_epoca_profile(self.Combo_Epoca_Profile.currentText())

        self.Combo_Profile_X.currentIndexChanged.connect(self.on_profile_axes_changed)
        self.Combo_Profile_Y.currentIndexChanged.connect(self.on_profile_axes_changed)
        self.Combo_Variable_Profile.itemSelectionChanged.connect(self.on_profile_axes_changed)

        self.Combo_Estadistica_Profile.currentTextChanged.connect(self.estadistica_changed_profile)  # Salta al cambiar de estadística

        self.Push_Reset_Profile.clicked.connect(self.reset_all_profile)

        self.Push_Visualizar_Profile.clicked.connect(self.visualize_variable_profile)

        self.on_profile_axes_changed()

        self.Push_InterpConfig_Profile.clicked.connect(self.open_interp_config_profile)

        self.Interpolate_Altitude_Profile.setEnabled(False)
        self.Interpolate_Altitude_Profile.clear()
        self.Interpolate_Altitude_Profile.setPlaceholderText("Introduce altitude (m)")

        self.Check_Mapa_Profile.stateChanged.connect(self.on_profile_axes_changed)

    def open_interp_config(self):
        # Guarda el estado actual de cada flag y paso para comparar tras cerrar el diálogo
        prev_time_raw = self.time_raw
        prev_time_step = self.time_step
        prev_alt_raw = self.alt_raw
        prev_lat_raw = self.lat_raw
        prev_lat_step = self.lat_step
        prev_lon_raw = self.lon_raw
        prev_lon_step = self.lon_step

        dlg = InterpConfigDialog(parent=self) # Crea el diálogo de configuración, pasando este widget como padre
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return # Si el usuario pulsa Cancel o cierra el diálogo, aborta sin cambios

        # Tras aceptar, vuelca el estado elegido en los controles del diálogo a los atributos del plugin
        self.time_raw  = (dlg.Combo_Time_Mode.currentText() == "Raw data")
        self.time_step = dlg.Combo_Time_Resolution.currentText()

        self.alt_raw = (dlg.Combo_Altitude_Mode.currentText() == "Raw data")

        self.lat_raw  = (dlg.Combo_Latitude_Mode.currentText() == "Raw data")
        self.lat_step = dlg.Combo_Latitude_Resolution.currentText()

        self.lon_raw  = (dlg.Combo_Longitude_Mode.currentText() == "Raw data")
        self.lon_step = dlg.Combo_Longitude_Resolution.currentText()

        # Si cambió cualquiera de las opciones de tiempo, refresca la lista de horas
        if (self.time_raw != prev_time_raw) or (self.time_step != prev_time_step):
            self.refresh_time_combo()

        # Si cambió el modo de altitud, repuebla altitudes crudas y ajusta controles de altitud en toggle_altitude_multi
        if self.alt_raw != prev_alt_raw:
            self.refresh_alt_combo()
            self.toggle_altitude_multi()

        # Si cambió cualquiera de las opciones de latitud, refresca la lista de latitudes
        if (self.lat_raw != prev_lat_raw) or (self.lat_step != prev_lat_step):
            self.refresh_lat_combo()

        # Si cambió cualquiera de las opciones de longitud, refresca la lista de longitud
        if (self.lon_raw != prev_lon_raw) or (self.lon_step != prev_lon_step):
            self.refresh_lon_combo()

    def refresh_time_combo(self):
        """
        Función que refresca el combo de tiempo cuando sea requerido. En especial cuando se pasa de raw a interpolate y viceversa
        """
        times = self.ds.Time.values.astype(float)# Extrae los valores de la dimensión Time del Dataset como floats
        t_min = times.min() # Hora mínima en el NetCDF
        t_max = times.max() # Hora máxima en el NetCDF

        # Decide si usa los valores crudos o crea una grilla interpolada
        if self.time_raw:
            grid = times # Sin interpolación: se usan los tiempos tal cual aparecen
        else:
            # Convierte la cadena de resolución en un número de horas
            if self.time_step == "1 hour":
                step = 1
            elif self.time_step == "30 min":
                step = 0.5
            elif self.time_step == "15 min":
                step = 0.25
            else:
                step = 1.0

            # Crea valores previos al primer tiempo para permitir ciclos. Es decir, poder coger horas entre 00.00 y 02.00
            extra = np.arange(step, t_min, step)
            # Crea la grilla principal desde t_min hasta t_max
            main = np.arange(t_min, t_max + 1e-6, step)
            #Une ambas partes, asi se obtiene una secuencia continua
            grid = np.concatenate([extra, main])

        # Formatea cada valor de grid como "HH:MM"
        labels = []

        for t in grid:
            h = int(t)
            m = int(round((t-h) * 60))

            if m == 60:
                t = t+1
                m = 0

            labels.append(f"{h:02d}:{m:02d}")

        # Actualiza el combo de horas en la interfaz
        self.Combo_Hora.clear() # Limpia entradas previas
        self.Combo_Hora.addItems(labels) # Añade todas las nuevas etiquetas

    def refresh_alt_combo(self):
        """
        Función que refresca el combo de altitud cuando sea requerido. En especial cuando se pasa de raw a interpolate y viceversa
        """
        if not self.alt_raw:
            return

        alts = self.ds.altitude.values.astype(float)
        labels = []

        for a in alts:
            labels.append(f"{a:.4f}")

        self.Combo_Altitud.clear()
        self.Combo_Altitud.addItems(labels)

    def refresh_lat_combo(self):
        """
        Función que refresca el combo de latitud cuando sea requerido. En especial cuando se pasa de raw a interpolate y viceversa
        """
        lats = self.ds.latitude.values.astype(float)
        lat_min = lats.min()
        lat_max = lats.max()

        if self.lat_raw:
            grid = lats
        else:
            if self.lat_step == "2":
                step = 2
            elif self.lat_step == "1":
                step = 1
            elif self.lat_step == "0.5":
                step = 0.5
            elif self.lat_step == "0.25":
                step = 0.25
            elif self.lat_step == "0.1":
                step = 0.1
            else:
                step = 1.0

            extra = np.arange(step, lat_min, step)
            main = np.arange(lat_min, lat_max + 1e-6, step)
            grid = np.concatenate([extra, main])

        labels = []
        for v in grid:
            labels.append(f"{v:.4f}")

        if not self.lat_raw:
            labels.reverse()

        self.Combo_Latitud_Min.clear()
        self.Combo_Latitud_Min.addItems(labels)
        self.Combo_Latitud_Max.clear()
        self.Combo_Latitud_Max.addItems(labels)

    def refresh_lon_combo(self):
        """
        Función que refresca el combo de tiempo cuando sea requerido. En especial cuando se pasa de raw a interpolate y viceversa
        """
        lons = self.ds.longitude.values.astype(float)
        lon_min = lons.min()
        lon_max = lons.max()

        if self.lon_raw:
            grid = lons
        else:
            if self.lon_step == "2":
                step = 2
            elif self.lon_step == "1":
                step = 1
            elif self.lon_step == "0.5":
                step = 0.5
            elif self.lon_step == "0.25":
                step = 0.25
            elif self.lon_step == "0.1":
                step = 0.1
            else:
                step = 1.0

            extra = np.arange(step, lon_min, step)
            main = np.arange(lon_min, lon_max + 1e-6, step)
            grid = np.concatenate([extra, main])

        labels = []
        for v in grid:
            labels.append(f"{v:.4f}")

        self.Combo_Longitud_Min.clear()
        self.Combo_Longitud_Min.addItems(labels)
        self.Combo_Longitud_Max.clear()
        self.Combo_Longitud_Max.addItems(labels)

    def estadistica_changed(self):
        self.cambio_epoca(self.Combo_Epoca.currentText())

    def cambio_epoca(self, epoca):
        carpeta = self.lista_carpetas.get(epoca)
        if not carpeta:
            QMessageBox.warning(self, "Error", "Folder not found")
            return

        prev_archivo = self.Combo_Archivo.currentData() or self.Combo_Archivo.currentText()
        self.Combo_Archivo.clear()

        folder = os.path.join(self.ruta, carpeta)
        stat = self.Combo_Estadistica.currentText().lower()

        try:
            archivos = []
            for f in os.listdir(folder):
                if f.endswith(f"_{stat}.nc") and "thermo" not in f.lower():
                    archivos.append(f)
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "File not found")
            return

        for f in archivos:
            label = f
            if "_01_" in f:
                label = "Month 01"
            elif "_02_" in f:
                label = "Month 02"
            elif "_03_" in f:
                label = "Month 03"
            elif "_04_" in f:
                label = "Month 04"
            elif "_05_" in f:
                label = "Month 05"
            elif "_06_" in f:
                label = "Month 06"
            elif "_07_" in f:
                label = "Month 07"
            elif "_08_" in f:
                label = "Month 08"
            elif "_09_" in f:
                label = "Month 09"
            elif "_10_" in f:
                label = "Month 10"
            elif "_11_" in f:
                label = "Month 11"
            elif "_12_" in f:
                label = "Month 12"

            self.Combo_Archivo.addItem(label, f)

        if self.Combo_Archivo.count() > 0:
            self.Combo_Archivo.setCurrentIndex(0)
            self.cambio_archivo(self.Combo_Archivo.currentData())


    def cambio_archivo(self, archivo_nombre):
        archivo_nombre = self.Combo_Archivo.currentData() or archivo_nombre
        if not archivo_nombre:
            return

        epoca_label = self.Combo_Epoca.currentText()
        carpeta = self.lista_carpetas.get(epoca_label)
        if not carpeta:
           return

        path = os.path.join(self.ruta, carpeta, archivo_nombre)
        try:
            ds_nuevo = xr.open_dataset(path, decode_times=False)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir NetCDF", str(e))
            return

        self.ds = ds_nuevo

        if self.Combo_Estadistica.currentText() == "sd":
            self.Combo_Hora.setEnabled(False)
            self.Combo_Hora.setStyleSheet("QComboBox {background-color: red; }")
            self.Combo_Hora.setToolTip("Disabled for SD Files (No time dimension)")
        else:
            self.Combo_Hora.setEnabled(True)
            self.Combo_Hora.setStyleSheet("")
            self.Combo_Hora.setToolTip("")

        prev_vars = []

        for item in self.Combo_Variable.selectedItems():
            prev_vars.append(item.data(Qt.UserRole))

        self.Combo_Variable.clear()

        for varname in self.ds.data_vars.keys():
            data_array = self.ds[varname]
            if("latitude" in data_array.dims) and ("longitude" in data_array.dims): #I just want to have variables that contain latitude and longitude dimensions. Otherwise, none of my interest
                if varname in self.variable_descriptions:
                    label = self.variable_descriptions[varname] # I assign a "human" name to thoses varnames (e.g. temp = "Surface Temparature (K)")
                    item = QtWidgets.QListWidgetItem(label)
                else:
                    item = QtWidgets.QListWidgetItem(f"ERROR: {varname}")
                    item.setForeGround(QColor("red"))

                item.setData(Qt.UserRole, varname)
                self.Combo_Variable.addItem(item)

        for i in range(self.Combo_Variable.count()):
            itm = self.Combo_Variable.item(i)
            if itm.data(Qt.UserRole) in prev_vars:
                itm.setSelected(True)

        prev_hora = self.Combo_Hora.currentText()
        self.refresh_time_combo()

        items = []
        for i in range(self.Combo_Hora.count()):
            items.append(self.Combo_Hora.itemText(i))

        if prev_hora in items:
            self.Combo_Hora.setCurrentText(prev_hora)
        elif self.Combo_Hora.count() > 0:
            self.Combo_Hora.setCurrentIndex(0)

        prev_alt_combo = self.Combo_Altitud.currentText()
        prev_alt_manual = self.Interpolate_Altitude.text()
        self.refresh_alt_combo()

        items_a = []

        for i in range(self.Combo_Altitud.count()):
            items_a.append(self.Combo_Altitud.itemText(i))

        if prev_alt_combo in items_a:
            self.Combo_Altitud.setCurrentText(prev_alt_combo)
        else:
            self.Combo_Altitud.setCurrentIndex(0)

        if not self.alt_raw:
            self.Interpolate_Altitude.setText(prev_alt_manual)
        else:
            self.Interpolate_Altitude.clear()

        self.toggle_altitude_multi()

        prev_lat_min = self.Combo_Latitud_Min.currentText()
        prev_lat_max = self.Combo_Latitud_Max.currentText()
        prev_lon_min = self.Combo_Longitud_Min.currentText()
        prev_lon_max = self.Combo_Longitud_Max.currentText()

        self.refresh_lat_combo()
        self.refresh_lon_combo()

        items_lat = []
        items_lon = []

        for i in range(self.Combo_Latitud_Min.count()):
            items_lat.append(self.Combo_Latitud_Min.itemText(i))

        if prev_lat_min in items_lat:
            self.Combo_Latitud_Min.setCurrentText(prev_lat_min)
        if prev_lat_max in items_lat:
            self.Combo_Latitud_Max.setCurrentText(prev_lat_max)

        for i in range(self.Combo_Longitud_Min.count()):
            items_lon.append(self.Combo_Longitud_Min.itemText(i))

        if prev_lon_min in items_lon:
            self.Combo_Longitud_Min.setCurrentText(prev_lon_min)
        if prev_lon_max in items_lon:
            self.Combo_Longitud_Max.setCurrentText(prev_lon_max)

    def toggle_altitude_multi(self):
        vars_marcadas = []
        for item in self.Combo_Variable.selectedItems():
            vars_marcadas.append(item.data(Qt.UserRole))

        if not vars_marcadas:
            self.Combo_Altitud.setEnabled(False)
            self.Combo_Altitud.setStyleSheet("QComboBox:disabled { background-color: red }")
            self.Combo_Altitud.setToolTip("Select one variable at least")
            self.Interpolate_Altitude.setEnabled(False)
            return

        for var in vars_marcadas:
            if var in self.ds.data_vars and "altitude" in self.ds[var].dims:
                if self.alt_raw:
                    self.Combo_Altitud.setEnabled(True)
                    self.Combo_Altitud.setStyleSheet("")
                    self.Combo_Altitud.setToolTip("")
                    self.Interpolate_Altitude.setEnabled(False)
                else:
                    self.Combo_Altitud.setEnabled(False)
                    self.Combo_Altitud.setStyleSheet("QComboBox:disabled { background-color: red }")
                    self.Combo_Altitud.setToolTip("Manual mode selected")
                    self.Interpolate_Altitude.setEnabled(True)
                return

        self.Combo_Altitud.setEnabled(False)
        self.Combo_Altitud.setStyleSheet("QComboBox:disabled { background-color: red }")
        self.Combo_Altitud.setToolTip("No variable selected contains 'altitude' dimension")
        self.Interpolate_Altitude.setEnabled(False)

    def toggle_map_latlon_mode(self, estado):

        checked = (estado != 0)

        combos = [self.Combo_Latitud_Min, self.Combo_Latitud_Max, self.Combo_Longitud_Min, self.Combo_Longitud_Max]

        if checked:
            for combo in combos:
                combo.setEnabled(False)
                combo.setStyleSheet("QComboBox { background-color: red; }")
                combo.setToolTip("Latitude/Longitude Selector is disabled when full map is selected")
        else:
            for combo in combos:
                combo.setEnabled(True)
                combo.setStyleSheet("")

    def reset_all(self):
        self.Combo_Epoca.setCurrentIndex(0)

        self.Combo_Estadistica.setCurrentText("me")

        if self.Combo_Archivo.count() > 0:
            self.Combo_Archivo.setCurrentIndex(0)

        if self.Combo_Variable.count() > 0:
            for i in range(self.Combo_Variable.count()):
                self.Combo_Variable.item(i).setSelected(False)

        if self.Combo_Hora.count() > 0:
            self.Combo_Hora.setCurrentIndex(0)

        self.time_raw = True
        self.time_step = "1 hour"
        self.refresh_time_combo()

        self.alt_raw = True

        self.refresh_alt_combo()
        if self.Combo_Altitud.count() > 0:
            self.Combo_Altitud.setCurrentIndex(0)

        self.Interpolate_Altitude.clear()
        self.toggle_altitude_multi()

        self.lat_raw = True
        self.lon_raw = True

        self.lat_step = "2"
        self.lon_step = "2"

        self.refresh_lat_combo()
        self.refresh_lon_combo()

        if self.Combo_Latitud_Min.count() > 0:
            self.Combo_Latitud_Min.setCurrentIndex(0)
        if self.Combo_Latitud_Max.count() > 0:
            self.Combo_Latitud_Max.setCurrentIndex(0)
        if self.Combo_Longitud_Min.count() > 0:
            self.Combo_Longitud_Min.setCurrentIndex(0)
        if self.Combo_Longitud_Max.count() > 0:
            self.Combo_Longitud_Max.setCurrentIndex(0)

        if self.Check_Mapa.isChecked():
            self.Check_Mapa.setChecked(False)

    def visualizar_variable(self):
        #Main handler for visualizing the selected variable
        #Read numeric lat/lon from combos
        lat_min = float(self.Combo_Latitud_Min.currentText())
        lat_max = float(self.Combo_Latitud_Max.currentText())
        lon_min = float(self.Combo_Longitud_Min.currentText())
        lon_max = float(self.Combo_Longitud_Max.currentText())

        #Validate ranges if not showing full map
        if not self.Check_Mapa.isChecked():
            if lat_min >= lat_max:
                QMessageBox.warning(self, "Invalid latitude range",
                                    "Min latitude must be lower than max latitude")
                return
            if lon_min >= lon_max:
                QMessageBox.warning(self, "Invalid longitude range",
                                    "Min longitude must be lower than max longitude")
                return

        vars_sel = [item.data(Qt.UserRole) for item in self.Combo_Variable.selectedItems()]

        if not vars_sel:
            QMessageBox.warning(self, "No variables", "You must select at least one variable")
            return

        dlg = QProgressDialog("Generating raster layers...", None, 0, len(vars_sel), self)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setCancelButton(None)
        dlg.setMinimumDuration(0)
        dlg.setWindowTitle("Please, wait")
        dlg.show()

        try:
            for idx, varname in enumerate(vars_sel):
                da = self.ds[varname]

                if "Time" in da.dims:
                    if self.time_raw:
                        da = da.isel(Time = self.Combo_Hora.currentIndex())
                    else:
                        time_str = self.Combo_Hora.currentText()
                        h, m = map(int, time_str.split(":"))
                        user_time = h + m/60.0

                        t_min = float(self.ds.Time.values.min())
                        t_max = float(self.ds.Time.values.max())

                        if user_time >= t_min:
                            da = da.interp(Time = user_time, method = "linear") #normal interp [t_min, t_max]
                        else:
                            frac = user_time/t_min
                            v_low = da.sel(Time = t_max)
                            v_high = da.sel(Time = t_min)
                            da = v_low*(1-frac) + v_high*frac

                if "altitude" in da.dims:
                    if self.alt_raw:
                        da = da.isel(altitude = self.Combo_Altitud.currentIndex())
                    else:
                        text = self.Interpolate_Altitude.text()
                        if not text:
                            QMessageBox.warning(self, "Altitude", "Introduce altitude value in m")
                            return

                        #Forcing value to be in altitude limits coming from NetCDF data
                        if not text.isdigit():
                            QMessageBox.warning(self, "Altitude", "Do not introduce decimal values")
                            return

                        v = int(text)

                        if v < 5:
                            v = 5
                        elif v > 108000:
                            v = 108000

                        self.Interpolate_Altitude.setText(str(v))

                        user_alt_km = v / 1000.0
                        da = da.interp(altitude = user_alt_km, method = "linear")

                lat_vals = self.ds.latitude.values
                lon_vals = self.ds.longitude.values

                if self.Check_Mapa.isChecked():
                    # Full map + posible interpolación espacial
                    # — si lat_raw es False, interpola toda la grilla en latitudes
                    if not self.lat_raw:
                        new_lats = np.arange(lat_vals.min(),
                                             lat_vals.max() + 1e-6,
                                             float(self.lat_step))
                        da = da.interp(latitude=new_lats, method="linear")
                    # — si lon_raw es False, interpola toda la grilla en longitudes
                    if not self.lon_raw:
                        new_lons = np.arange(lon_vals.min(),
                                             lon_vals.max() + 1e-6,
                                             float(self.lon_step))
                        da = da.interp(longitude=new_lons, method="linear")
                else:
                    # Recorte clásico + posible interpolación espacial
                    if self.lat_raw:
                        if lat_vals[0] < lat_vals[-1]:
                            lat_slice = slice(lat_min, lat_max)
                        else:
                            lat_slice = slice(lat_max, lat_min)
                        da = da.sel(latitude=lat_slice)
                    else:
                        new_lats = np.arange(lat_min, lat_max + 1e-6,
                                             float(self.lat_step))
                        da = da.interp(latitude=new_lats, method="linear")

                    if self.lon_raw:
                        if lon_vals[0] < lon_vals[-1]:
                            lon_slice = slice(lon_min, lon_max)
                        else:
                            lon_slice = slice(lon_max, lon_min)
                        da = da.sel(longitude=lon_slice)
                    else:
                        new_lons = np.arange(lon_min, lon_max + 1e-6,
                                             float(self.lon_step))
                        da = da.interp(longitude=new_lons, method="linear")

                lats = da.latitude.values
                lons = da.longitude.values
                array = da.values

                if array.size == 0:
                    QMessageBox.warning(self, "No data", f"Variable {self.variable_descriptions[varname]} has no data in the lat/lon cut.")
                    dlg.setValue(idx + 1)
                    QApplication.processEvents()
                    continue

                display_name = self.variable_descriptions[varname]
                self._mostrar_raster(array, lats, lons, varname, display_name)

                dlg.setValue(idx + 1)
                QApplication.processEvents()

            self.loadMolaBase()

        finally:
            dlg.close()

    def loadMolaBase(self):
        """
        Inicializa o recarga la capa de contornos obtenidos por imágenes MOLA en el mapa. Siempre en la capa superior
        """

        Processing.initialize() #Asegura que el framework de Processing esté inicializado antes de usar algoritmos

        # Obtiene el ID de la capa MOLA anterior, si existe
        prev_id = getattr(self, 'mola_layer_id', None)
        if prev_id:
            # Si existe, la recupera y la elimina del proyecto para evitar duplicados
            lyr = QgsProject.instance().mapLayer(prev_id)
            if lyr:
            # Resetea el identificador y el estado de carga
                QgsProject.instance().removeMapLayer(prev_id)
            self.mola_layer_id = None
            self.mola_loaded = False

        # Construye la ruta al GeoTIFF original de isolines MOLA incluido en el plugin
        plugin_dir = os.path.dirname(__file__)
        origen = os.path.join(plugin_dir, "mola32_isolines.tif")

        mola_ds = gdal.OpenEx(origen, gdal.OF_RASTER | gdal.OF_UPDATE, open_options=["IGNORE_COG_LAYOUT_BREAK=YES"])
        if mola_ds:
            srs = osr.SpatialReference()
            srs.SetFromUserInput("IAU_2015:49900")
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            mola_ds.SetProjection(srs.ExportToWkt())
            mola_ds = None

        max_lon_mcd = 174.375 # Limita el tamaño del mola32_isolines para que se ajuste a las dimensiones de datos NetCDF

        # Si el usuario no muestra el mapa completo, recorta el GeoTIFF al rectángulo seleccionado
        if not self.Check_Mapa.isChecked():
            lon_min = float(self.Combo_Longitud_Min.currentText())
            lon_max = float(self.Combo_Longitud_Max.currentText())
            lat_min = float(self.Combo_Latitud_Min.currentText())
            lat_max = float(self.Combo_Latitud_Max.currentText())

            if lon_max > max_lon_mcd:
                lon_max = max_lon_mcd

            # Opciones para GDAL Translate: define la ventana de recorte con projWin
            opts = gdal.TranslateOptions(format="GTiff",projWin=[lon_min, lat_max, lon_max, lat_min])
            tmp_tif = os.path.join(tempfile.gettempdir(), "mola_crop.tif")
            # Ejecuta el recorte
            gdal.Translate(tmp_tif, origen, options=opts)
            raster_path = tmp_tif
        else:
            #Si muestra mapa completo, recorta igualmente para ajustar imagen
            opts = gdal.TranslateOptions(format="GTiff",projWin=[-180, 90, max_lon_mcd, -90])
            tmp_tif = os.path.join(tempfile.gettempdir(), "mola_crop_full.tif")
            # Ejecuta el recorte
            gdal.Translate(tmp_tif, origen, options=opts)
            raster_path = tmp_tif

        # Abre el ráster resultante para leerlo
        ds = gdal.Open(raster_path)
        gt = ds.GetGeoTransform()
        # Genera un ráster de menor resolución (factor 4) para ser más rápido generando el mapa MOLA
        down_tif = os.path.join(tempfile.gettempdir(), "mola_down.tif")
        gdal.Warp(down_tif, ds,xRes=gt[1] * 4,yRes=abs(gt[5]) * 4,resampleAlg='bilinear') #Incrementa tamaño de píxeles y usa remuestreo bilineal
        ds = None
        raster_path = down_tif

        # Crea una ruta única para el shapefile de contornos usando UUID
        shp_path = os.path.join(tempfile.gettempdir(), f"mola_contours_{uuid.uuid4().hex}.shp")
        # Crea una ruta única para el shapefile de contornos usando UUID
        for ext in ("shp", "shx", "dbf", "prj"):
            try:
                os.remove(shp_path[:-3] + ext)
            except OSError:
                pass

        # Parámetros para el algoritmo gdal:contour. Contornos cada 1000m
        params = {'INPUT': raster_path,'BAND': 1,'INTERVAL': 1000.0,'FIELD_NAME': 'ELEV','OUTPUT': shp_path}
        # Ejecuta la generación de contornos
        result = processing.run("gdal:contour", params)
        if 'OUTPUT' not in result or not result['OUTPUT']:
            QMessageBox.critical(self, "Error", "gdal:contour failed without exit.")
            return

        # Load resulting shapefile as a vector layer
        cont_layer = QgsVectorLayer(result['OUTPUT'], "MOLA Isolines", "ogr")
        if not cont_layer.isValid():
            QMessageBox.critical(self, "Error", "MOLA isolines could not be created.")
            return

        # Aplica estilo: líneas negras de 0.2mm de grosor
        sym = cont_layer.renderer().symbol()
        sym.setColor(QColor(0, 0, 0))
        sym.setWidth(0.2)
        cont_layer.triggerRepaint()

        # Inserta la capa de contornos en la posición superior del proyecto QGIS
        root = QgsProject.instance().layerTreeRoot()
        QgsProject.instance().addMapLayer(cont_layer, addToLegend=False)
        root.insertLayer(0, cont_layer)

        # Guarda el ID y marca la capa como cargada para futuras actualizaciones
        self.mola_layer_id = cont_layer.id()
        self.mola_loaded = True

    def _mostrar_raster(self, array, lat, lon, safe_name, layer_name):
        arr = np.asarray(array) # Convierte el array que recibe como parametro en un objeto de typo NumPy

        # Si no hay datos o coordenadas lat/lon estan vacias, muestra un warning y sale de la funcion
        if arr.size == 0 or len(lat) == 0 or len(lon) == 0:
            QMessageBox.warning(self,"No data","Selected crop has no info")
            return

        # Confirma de que se trata de un array bidimensional, si no lo es, no puede crear ráster y se sale
        if arr.ndim != 2:
            QMessageBox.warning(self, "ERROR", "Raster is not a 2D File. Cannot be desplayed")
            return

        # Invierte verticalmente el array para que la primera fila de datos coincida con la latitud inferior.
        arr = np.flipud(arr)

        # Construye ruta temporal para escribir el GeoTIFF
        temp_dir = tempfile.gettempdir()
        filename = f"{safe_name}_{uuid.uuid4().hex}.tif"
        path = os.path.join(temp_dir, filename)

        # Calcula filas y columnas que contienen el array
        nrows, ncols = arr.shape
        # Calcula resolución espacial del array a partir de los vectores de coordenadas
        xres = (lon[-1] - lon[0]) / ncols
        yres = (lat[-1] - lat[0]) / nrows

        # Crea el GeoTIFF vacío con GDAL, un solo canal de tipo float32
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(path, ncols, nrows, 1, gdal.GDT_Float32)
        # Define la transformación georeferencial, calculando el origen y resoluciones calculadas
        ds.SetGeoTransform((lon[0], xres, 0, lat[-1], 0, -yres))
        # Crea un objeto de tipo SpatialReference y lo fija a IAU_49900
        srs = osr.SpatialReference()
        srs.SetFromUserInput("IAU_2015:49900")
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        ds.SetProjection(srs.ExportToWkt())
        # Escribe los datos del array en la banda 1 del ráster
        ds.GetRasterBand(1).WriteArray(arr)
        # Asegura que los datos se escriben en disco
        ds.FlushCache()
        # Cierra el dataset
        ds = None

        # Carga el GeoTIFF como una capa ráster
        layer = QgsRasterLayer(path, layer_name)
        if not layer.isValid():
            QMessageBox.critical(self, "Error", "Unable to charge raster layer.")
            return

        # Prepara un renderizador continuo usando la rampa Turbo
        provider = layer.dataProvider()
        ramp = QgsStyle().defaultStyle().colorRamp('Turbo')
        renderer = QgsSingleBandPseudoColorRenderer(provider, 1)
        renderer.createShader(ramp,Qgis.ShaderInterpolationMethod.Linear,Qgis.ShaderClassificationMethod.Continuous,0)
        # Asigna al renderizador y ajusta la opacidad al 80%
        layer.setRenderer(renderer)
        layer.setOpacity(0.8)

        # Añade la capa al proyecto QGIS y la repinta con el renderizador que configuramos antes
        QgsProject.instance().addMapLayer(layer)
        layer.triggerRepaint()

        # Abre el panel de propiedades de simbología y aplica los cambios
        iface.showLayerProperties(layer, 'symbology')
        for w in QApplication.topLevelWidgets():
            # Aquñi busca el dialogo propiedades de capa que se ha abierto
            if isinstance(w, QDialog) and w.windowTitle().startswith("Propiedades de capa"):
                w.close()
        iface.showLayerProperties(layer, 'symbology')
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QDialog) and w.windowTitle().startswith("Propiedades de capa"):
                # Dentro del diálogo clicka en "Apply" y lo pulsa para aplicar los cambios
                for bb in w.findChildren(QDialogButtonBox):
                    btn_apply = bb.button(QDialogButtonBox.Apply)
                    if btn_apply:
                        btn_apply.click()
                        w.close()
                break

    # PROFILE TOOL BEGINNING

    def open_interp_config_profile(self):
        prev_time_raw = self.time_raw_profile
        prev_time_step = self.time_step_profile
        prev_alt_raw = self.alt_raw_profile
        prev_lat_raw = self.lat_raw_profile
        prev_lat_step = self.lat_step_profile
        prev_lon_raw = self.lon_raw_profile
        prev_lon_step = self.lon_step_profile

        dlg = InterpConfigDialogProfile(parent=self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        self.time_raw_profile  = (dlg.Combo_Time_Mode_Profile.currentText() == "Raw data")
        self.time_step_profile = dlg.Combo_Time_Resolution_Profile.currentText()

        self.alt_raw_profile = (dlg.Combo_Altitude_Mode_Profile.currentText() == "Raw data")

        self.lat_raw_profile  = (dlg.Combo_Latitude_Mode_Profile.currentText() == "Raw data")
        self.lat_step_profile = dlg.Combo_Latitude_Resolution_Profile.currentText()

        self.lon_raw_profile  = (dlg.Combo_Longitude_Mode_Profile.currentText() == "Raw data")
        self.lon_step_profile = dlg.Combo_Longitude_Resolution_Profile.currentText()

        if (self.time_raw_profile != prev_time_raw) or (self.time_step_profile != prev_time_step):
            self.refresh_time_combo_profile()

        if self.alt_raw_profile != prev_alt_raw:
            self.refresh_alt_combo_profile()

        if (self.lat_raw_profile != prev_lat_raw) or (self.lat_step_profile != prev_lat_step):
            self.refresh_lat_combo_profile()

        if (self.lon_raw_profile != prev_lon_raw) or (self.lon_step_profile != prev_lon_step):
            self.refresh_lon_combo_profile()

        self.on_profile_axes_changed()

    def refresh_time_combo_profile(self):
        times = self.ds.Time.values.astype(float)
        t_min = times.min()
        t_max = times.max()

        if self.time_raw_profile:
            grid = times
        else:
            if self.time_step_profile == "1 hour":
                step = 1
            elif self.time_step_profile == "30 min":
                step = 0.5
            elif self.time_step_profile == "15 min":
                step = 0.25
            else:
                step = 1.0

            extra = np.arange(step, t_min, step)
            main = np.arange(t_min, t_max + 1e-6, step)
            grid = np.concatenate([extra, main])

        labels = []

        for t in grid:
            h = int(t)
            m = int(round((t-h) * 60))

            if m == 60:
                t = t+1
                m = 0

            labels.append(f"{h:02d}:{m:02d}")

        self.Combo_Hora_Profile.clear()
        self.Combo_Hora_Profile.addItems(labels)

    def refresh_alt_combo_profile(self): #Repoblate Combo_Altitud when alt_raw is true

        if not self.alt_raw_profile:
            return

        alts = self.ds.altitude.values.astype(float)
        labels = []

        for a in alts:
            labels.append(f"{a:.4f}")

        self.Combo_Altitud_Profile.clear()
        self.Combo_Altitud_Profile.addItems(labels)

    def refresh_lat_combo_profile(self):
        lats = self.ds.latitude.values.astype(float)
        lat_min = lats.min()
        lat_max = lats.max()

        if self.lat_raw_profile:
            grid = lats
        else:
            if self.lat_step_profile == "2":
                step = 2
            elif self.lat_step_profile == "1":
                step = 1
            elif self.lat_step_profile == "0.5":
                step = 0.5
            elif self.lat_step_profile == "0.25":
                step = 0.25
            elif self.lat_step_profile == "0.1":
                step = 0.1
            else:
                step = 1.0

            extra = np.arange(step, lat_min, step)
            main = np.arange(lat_min, lat_max + 1e-6, step)
            grid = np.concatenate([extra, main])

        labels = []
        for v in grid:
            labels.append(f"{v:.4f}")

        if not self.lat_raw_profile:
            labels.reverse()

        self.Combo_Latitud_Min_Profile.clear()
        self.Combo_Latitud_Min_Profile.addItems(labels)
        self.Combo_Latitud_Max_Profile.clear()
        self.Combo_Latitud_Max_Profile.addItems(labels)

    def refresh_lon_combo_profile(self):
        lons = self.ds.longitude.values.astype(float)
        lon_min = lons.min()
        lon_max = lons.max()

        if self.lon_raw_profile:
            grid = lons
        else:
            if self.lon_step_profile == "2":
                step = 2
            elif self.lon_step_profile == "1":
                step = 1
            elif self.lon_step_profile == "0.5":
                step = 0.5
            elif self.lon_step_profile == "0.25":
                step = 0.25
            elif self.lon_step_profile == "0.1":
                step = 0.1
            else:
                step = 1.0

            extra = np.arange(step, lon_min, step)
            main = np.arange(lon_min, lon_max + 1e-6, step)
            grid = np.concatenate([extra, main])

        labels = []
        for v in grid:
            labels.append(f"{v:.4f}")

        self.Combo_Longitud_Min_Profile.clear()
        self.Combo_Longitud_Min_Profile.addItems(labels)
        self.Combo_Longitud_Max_Profile.clear()
        self.Combo_Longitud_Max_Profile.addItems(labels)

    def estadistica_changed_profile(self):
        self.cambio_epoca_profile(self.Combo_Epoca_Profile.currentText())

    def cambio_epoca_profile(self, epoca):
        carpeta = self.lista_carpetas.get(epoca)
        if carpeta is None:
            QMessageBox.warning(self, "Error", f"Unknown scenario: {epoca}")
            return

        ruta_carpeta = os.path.join(self.ruta, carpeta)
        stat = self.Combo_Estadistica_Profile.currentText().lower()

        try:
            archivos = []
            for f in os.listdir(ruta_carpeta):
                if f.endswith(f"_{stat}.nc") and "thermo" not in f.lower():
                    archivos.append(f)
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", f"File not found:\n{ruta_carpeta}")
            return

        # Limpiar y añadir con label personalizado
        self.Combo_Archivo_Profile.clear()
        for f in archivos:
            label = f
            if "_01_" in f:
                label = "Month 01"
            elif "_02_" in f:
                label = "Month 02"
            elif "_03_" in f:
                label = "Month 03"
            elif "_04_" in f:
                label = "Month 04"
            elif "_05_" in f:
                label = "Month 05"
            elif "_06_" in f:
                label = "Month 06"
            elif "_07_" in f:
                label = "Month 07"
            elif "_08_" in f:
                label = "Month 08"
            elif "_09_" in f:
                label = "Month 09"
            elif "_10_" in f:
                label = "Month 10"
            elif "_11_" in f:
                label = "Month 11"
            elif "_12_" in f:
                label = "Month 12"

            self.Combo_Archivo_Profile.addItem(label, f)

        if self.Combo_Archivo_Profile.count() > 0:
            self.Combo_Archivo_Profile.setCurrentIndex(0)
            self.cambio_archivo_profile(self.Combo_Archivo_Profile.currentData())

    def cambio_archivo_profile(self, archivo_nombre):
        archivo_nombre = self.Combo_Archivo_Profile.currentData() or archivo_nombre
        if not archivo_nombre:
            return

        epoca_label = self.Combo_Epoca_Profile.currentText()
        carpeta = self.lista_carpetas.get(epoca_label)
        if not carpeta:
            return

        path = os.path.join(self.ruta, carpeta, archivo_nombre)
        try:
            ds_nuevo = xr.open_dataset(path, decode_times=False)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir NetCDF", str(e))
            return

        self.ds = ds_nuevo

        if self.Combo_Estadistica_Profile.currentText() == "sd":
            self.Combo_Hora_Profile.setEnabled(False)
            self.Combo_Hora_Profile.setStyleSheet("QComboBox {background-color: red; }")
            self.Combo_Hora_Profile.setToolTip("Disabled for SD Files (No time dimension)")
        else:
            self.Combo_Hora_Profile.setEnabled(True)
            self.Combo_Hora_Profile.setStyleSheet("")
            self.Combo_Hora_Profile.setToolTip("")

        prev_vars = []

        for item in self.Combo_Variable_Profile.selectedItems():
            prev_vars.append(item.data(Qt.UserRole))

        self.Combo_Variable_Profile.clear()

        for varname in self.ds.data_vars.keys():
            data_array = self.ds[varname]
            if("latitude" in data_array.dims) and ("longitude" in data_array.dims): #I just want to have variables that contain latitude and longitude dimensions. Otherwise, none of my interest
                if varname in self.variable_descriptions:
                    label = self.variable_descriptions[varname] # I assign a "human" name to thoses varnames (e.g. temp = "Surface Temparature (K)")
                    item = QtWidgets.QListWidgetItem(label)
                else:
                    item = QtWidgets.QListWidgetItem(f"ERROR: {varname}")
                    item.setForeGround(QColor("red"))

                item.setData(Qt.UserRole, varname)
                self.Combo_Variable_Profile.addItem(item)

        for i in range(self.Combo_Variable_Profile.count()):
            itm = self.Combo_Variable_Profile.item(i)
            if itm.data(Qt.UserRole) in prev_vars:
                itm.setSelected(True)

        prev_hora = self.Combo_Hora_Profile.currentText()
        self.refresh_time_combo_profile()

        hora_items = []
        for i in range(self.Combo_Hora_Profile.count()):
            hora_items.append(self.Combo_Hora_Profile.itemText(i))

        if prev_hora in hora_items:
            self.Combo_Hora_Profile.setCurrentText(prev_hora)
        elif self.Combo_Hora_Profile.count() > 0:
            self.Combo_Hora_Profile.setCurrentIndex(0)

        prev_alt = self.Combo_Altitud_Profile.currentText()
        prev_alt_manual = self.Interpolate_Altitude_Profile.text()

        self.refresh_alt_combo_profile()

        alt_items = []
        for i in range(self.Combo_Altitud_Profile.count()):
            alt_items.append(self.Combo_Altitud_Profile.itemText(i))

        if prev_alt in alt_items:
            self.Combo_Altitud_Profile.setCurrentText(prev_alt)
        elif self.Combo_Altitud_Profile.count() > 0:
            self.Combo_Altitud_Profile.setCurrentIndex(0)

        if not self.alt_raw_profile:
            self.Interpolate_Altitude_Profile.setText(prev_alt_manual)
        else:
            self.Interpolate_Altitude_Profile.clear()

        prev_lat_min = self.Combo_Latitud_Min_Profile.currentText()
        prev_lat_max = self.Combo_Latitud_Max_Profile.currentText()

        self.refresh_lat_combo_profile()

        lat_min_items = []
        for i in range(self.Combo_Latitud_Min_Profile.count()):
            lat_min_items.append(self.Combo_Latitud_Min_Profile.itemText(i))

        if prev_lat_min in lat_min_items:
            self.Combo_Latitud_Min_Profile.setCurrentText(prev_lat_min)
        elif self.Combo_Latitud_Min_Profile.count() > 0:
            self.Combo_Latitud_Min_Profile.setCurrentIndex(0)

        lat_max_items = []
        for i in range(self.Combo_Latitud_Max_Profile.count()):
            lat_max_items.append(self.Combo_Latitud_Max_Profile.itemText(i))

        if prev_lat_max in lat_max_items:
            self.Combo_Latitud_Max_Profile.setCurrentText(prev_lat_max)
        elif self.Combo_Latitud_Max_Profile.count() > 0:
            self.Combo_Latitud_Max_Profile.setCurrentIndex(0)

        prev_lon_min = self.Combo_Longitud_Min_Profile.currentText()
        prev_lon_max = self.Combo_Longitud_Max_Profile.currentText()

        self.refresh_lon_combo_profile()

        lon_min_items = []
        for i in range(self.Combo_Longitud_Min_Profile.count()):
            lon_min_items.append(self.Combo_Longitud_Min_Profile.itemText(i))

        if prev_lon_min in lon_min_items:
            self.Combo_Longitud_Min_Profile.setCurrentText(prev_lon_min)
        elif self.Combo_Longitud_Min_Profile.count() > 0:
            self.Combo_Longitud_Min_Profile.setCurrentIndex(0)

        lon_max_items = []
        for i in range(self.Combo_Longitud_Max_Profile.count()):
            lon_max_items.append(self.Combo_Longitud_Max_Profile.itemText(i))

        if prev_lon_max in lon_max_items:
            self.Combo_Longitud_Max_Profile.setCurrentText(prev_lon_max)
        elif self.Combo_Longitud_Max_Profile.count() > 0:
            self.Combo_Longitud_Max_Profile.setCurrentIndex(0)

        self.on_profile_axes_changed()

    def on_profile_axes_changed(self, idx=None):
        combo = self.sender()

        x = self.Combo_Profile_X.currentText()
        y = self.Combo_Profile_Y.currentText()

        if x == y and x != "N/A":
            QMessageBox.warning(self,"Profile","Axis Variable X cannot be the same as Axis Variable Y")
            combo.setCurrentIndex(0)
            return

        if self.Combo_Estadistica_Profile.currentText().lower() == "sd":
            self.Combo_Hora_Profile.setEnabled(False)
            self.Combo_Hora_Profile.setStyleSheet("QComboBox {background-color: red; }")
            self.Combo_Hora_Profile.setToolTip("Disabled for SD Files (No time dimension)")
        elif x == "Local Time" or y == "Local Time":
            self.Combo_Hora_Profile.setEnabled(False)
            self.Combo_Hora_Profile.setStyleSheet("QComboBox{background:red}")
            self.Combo_Hora_Profile.setToolTip("Local Time locked as axis")
        else:
            self.Combo_Hora_Profile.setEnabled(True)
            self.Combo_Hora_Profile.setStyleSheet("")
            self.Combo_Hora_Profile.setToolTip("")

        sel = self.Combo_Variable_Profile.selectedItems()

        if x == "Altitude" or y == "Altitude":
            self.Combo_Altitud_Profile.setEnabled(False)
            self.Combo_Altitud_Profile.setStyleSheet("QComboBox{background:red}")
            self.Combo_Altitud_Profile.setToolTip("Altitude locked as axis")
            self.Interpolate_Altitude_Profile.setEnabled(False)

        elif sel and 'altitude' not in self.ds[sel[0].data(Qt.UserRole)].dims:
            self.Interpolate_Altitude_Profile.setEnabled(False)
            self.Combo_Altitud_Profile.setEnabled(False)
            self.Combo_Altitud_Profile.setStyleSheet("QComboBox{background:red}")
            self.Combo_Altitud_Profile.setToolTip("Selected variable has no 'altitude' dimension")

        else:
            if self.alt_raw_profile:
                self.Combo_Altitud_Profile.setEnabled(True)
                self.Combo_Altitud_Profile.setStyleSheet("")
                self.Combo_Altitud_Profile.setToolTip("")
                self.Interpolate_Altitude_Profile.setEnabled(False)
            else:
                self.Combo_Altitud_Profile.setEnabled(False)
                self.Combo_Altitud_Profile.setStyleSheet("QComboBox { background:red }")
                self.Combo_Altitud_Profile.setToolTip("Manual mode selected")
                self.Interpolate_Altitude_Profile.setEnabled(True)

        if x == "Latitude" or y == "Latitude":
            self.Combo_Latitud_Min_Profile.setEnabled(True)
            self.Combo_Latitud_Min_Profile.setStyleSheet("")
            self.Combo_Latitud_Min_Profile.setToolTip("")

            self.Combo_Latitud_Max_Profile.setEnabled(True)
            self.Combo_Latitud_Max_Profile.setStyleSheet("")
            self.Combo_Latitud_Max_Profile.setToolTip("")
        else:
            self.Combo_Latitud_Min_Profile.setEnabled(True)
            self.Combo_Latitud_Min_Profile.setStyleSheet("")
            self.Combo_Latitud_Min_Profile.setToolTip("")

            self.Combo_Latitud_Max_Profile.setEnabled(False)
            self.Combo_Latitud_Max_Profile.setStyleSheet("QComboBox{background:red}")
            self.Combo_Latitud_Max_Profile.setToolTip("Latitude range disabled when not axis")

        if x == "Longitude" or y == "Longitude":
            self.Combo_Longitud_Min_Profile.setEnabled(True)
            self.Combo_Longitud_Min_Profile.setStyleSheet("")
            self.Combo_Longitud_Min_Profile.setToolTip("")

            self.Combo_Longitud_Max_Profile.setEnabled(True)
            self.Combo_Longitud_Max_Profile.setStyleSheet("")
            self.Combo_Longitud_Max_Profile.setToolTip("")
        else:
            self.Combo_Longitud_Min_Profile.setEnabled(True)
            self.Combo_Longitud_Min_Profile.setStyleSheet("")
            self.Combo_Longitud_Min_Profile.setToolTip("")

            self.Combo_Longitud_Max_Profile.setEnabled(False)
            self.Combo_Longitud_Max_Profile.setStyleSheet("QComboBox{background:red}")
            self.Combo_Longitud_Max_Profile.setToolTip("Longitude range disabled when not axis")

        if (x == "Latitude" and y == "Longitude") or (x == "Longitude" and y == "Latitude"):
            self.Check_Mapa_Profile.setEnabled(True)
            self.Check_Mapa_Profile.setStyleSheet("")
            self.Check_Mapa_Profile.setToolTip("")
        else:
            self.Check_Mapa_Profile.setEnabled(False)
            self.Check_Mapa_Profile.setStyleSheet("QCheckBox { background-color: lightgray }")
            self.Check_Mapa_Profile.setToolTip("Enabled only when axes are Latitude and Longitude")
            if self.Check_Mapa_Profile.isChecked():
                self.Check_Mapa_Profile.setChecked(False)

        if self.Check_Mapa_Profile.isChecked():
            for c in (self.Combo_Latitud_Min_Profile, self.Combo_Latitud_Max_Profile,self.Combo_Longitud_Min_Profile, self.Combo_Longitud_Max_Profile):
                c.setEnabled(False)
                c.setStyleSheet("QComboBox{background:red}")
                c.setToolTip("Disabled when full map is selected")

        self.Combo_Variable_Profile.setEnabled(True)
        self.Combo_Variable_Profile.setStyleSheet("")
        self.Combo_Variable_Profile.setToolTip("")

        if x != "N/A" and y != "N/A" and sel:
            self.Push_Visualizar_Profile.setEnabled(True)
        else:
            self.Push_Visualizar_Profile.setEnabled(False)

    def reset_all_profile(self):
        self.Combo_Epoca_Profile.setCurrentIndex(0)
        if self.Combo_Archivo_Profile.count() > 0:
            self.Combo_Archivo_Profile.setCurrentIndex(0)

        self.Combo_Estadistica_Profile.setCurrentText("me")

        self.time_raw_profile = True
        self.time_step_profile = "1 hour"
        self.refresh_time_combo_profile()

        self.alt_raw_profile = True
        self.refresh_alt_combo_profile()

        self.lat_raw_profile = True
        self.lat_step_profile = "2"
        self.refresh_lat_combo_profile()

        self.lon_raw_profile = True
        self.lon_step_profile = "2"
        self.refresh_lon_combo_profile()

        self.Combo_Profile_X.setCurrentIndex(0)
        self.Combo_Profile_Y.setCurrentIndex(0)

        for i in range(self.Combo_Variable_Profile.count()):
            self.Combo_Variable_Profile.item(i).setSelected(False)

        if self.Combo_Hora_Profile.count() > 0:
            self.Combo_Hora_Profile.setCurrentIndex(0)

        if self.Combo_Altitud_Profile.count() > 0:
            self.Combo_Altitud_Profile.setCurrentIndex(0)

        if self.Combo_Latitud_Min_Profile.count() > 0:
            self.Combo_Latitud_Min_Profile.setCurrentIndex(0)

        if self.Combo_Latitud_Max_Profile.count() > 0:
            self.Combo_Latitud_Max_Profile.setCurrentIndex(0)

        if self.Combo_Longitud_Min_Profile.count() > 0:
            self.Combo_Longitud_Min_Profile.setCurrentIndex(0)

        if self.Combo_Longitud_Max_Profile.count() > 0:
            self.Combo_Longitud_Max_Profile.setCurrentIndex(0)

        self.on_profile_axes_changed()

    def visualize_variable_profile(self):
        """
        Funcion que muestra perfil o superficie de la variable seleccionada,
        aplicando según la configuración escogida por el usuario de "raw" o "interpolate"
        para cada una de las dimensiones
        """
        # Se obtienen el texto de los ejes X e Y seleccionados por el usuario
        x_axis = self.Combo_Profile_X.currentText()
        y_axis = self.Combo_Profile_Y.currentText()

        # Se recogen la lista de variables marcadas. Si no hay ninguna, salta warning (Se puede eliminar, la comprobación
        # se hace mejor en otro lado)
        sel_items = self.Combo_Variable_Profile.selectedItems()
        if not sel_items:
            QMessageBox.warning(self, "Profile", "Select a variable to plot")
            return

        # Se extrae el nombre de la variable (almacenada en Qt.UserRole) y se obtiene el DataArray
        var = sel_items[0].data(Qt.UserRole)
        da = self.ds[var]

        # Se recupera del diccionario el nombre de la variable para usarlo en etiquetas, titulos, etc...
        desc = self.variable_descriptions.get(var, var)
        # Se crea diccionario sobre el que luego se irán llenando aquellas dimensiones que se encuentren
        # fijadas al no estar puestas como variables en eje X o Y
        fixed = {}

        # Si la dimensión Time está presente y el usuario la ha elegido usar como eje
        if "Time" in da.dims and "Local Time" in (x_axis, y_axis):
            # Solo en modo interpolate se genera una grilla continua de datos
            if not self.time_raw_profile:
                # Se convierten los valores en la coordenada Time a Float y se obtienen extremos
                t_vals = self.ds.Time.values.astype(float)
                t_min, t_max = t_vals.min(), t_vals.max()
                # Se determina paso en horas en función de la decisión del usuario
                if self.time_step_profile == "1 hour":
                    step = 1.0
                elif self.time_step_profile == "30 min":
                    step = 0.5
                elif self.time_step_profile == "15 min":
                    step = 0.25
                else:
                    step = 1.0
                # Se crea array desde t_min hasta t_max con el paso escogido
                grid = np.arange(t_min, t_max + 1e-6, step)
                # Se interpola el DataArray en la dimensión Time usando grilla definida
                da = da.interp(Time=grid, method="linear")

        # Si Time existe pero no se usa como un eje, se fija un instante en concreto
        elif "Time" in da.dims and "Local Time" not in (x_axis, y_axis):
            # Se lee la hora escogida como cadena HH:MM
            time_str = self.Combo_Hora_Profile.currentText()
            if self.time_raw_profile:
                # Si se esta en modo Raw se escoge indice exacto
                idx = self.Combo_Hora_Profile.currentIndex()
                da = da.isel(Time=idx)
            else:
                # En modo interpolate se convierte cadena a valor decimal y se aplica interp
                h, m = map(int, time_str.split(":"))
                user_t = h + m / 60.0
                t_min = float(self.ds.Time.values.min())
                t_max = float(self.ds.Time.values.max())
                if user_t >= t_min:
                    # Interpolación dentro de los limites 02:00 - 24:00
                    da = da.interp(Time=user_t, method="linear")
                else:
                    # Si el momento es anterior a t_min, se hace interpolación cíclica
                    frac = user_t / t_min
                    v_low = da.sel(Time=t_max)
                    v_high = da.sel(Time=t_min)
                    da = v_low * (1 - frac) + v_high * frac
            # Se guarda la hora fija para el titulo
            fixed["Local Time"] = f"{time_str} h"

        # Altitude se maneja de forma similar
        # Si existe y se usa como eje, se deja para el bloque de dibujo
        if "altitude" in da.dims and "Altitude" in (x_axis, y_axis):
            pass

        elif "altitude" in da.dims:
            if self.alt_raw_profile:
                idx = self.Combo_Altitud_Profile.currentIndex()
                da = da.isel(altitude=idx)
                fixed["Altitude"] = f"{self.Combo_Altitud_Profile.currentText()} km"
            else:
                text = self.Interpolate_Altitude_Profile.text()
                if not text.isdigit():
                    QMessageBox.warning(self, "Altitude", "Do not introduce decimal values")
                    return
                v_m = int(text)
                v_m = max(5, min(108000, v_m))
                self.Interpolate_Altitude_Profile.setText(str(v_m))
                km = v_m / 1000.0
                da = da.interp(altitude=km, method="linear")
                fixed["Altitude"] = f"{km:.4f} km"

        # Leemos si estamos en modo full map y los valores minimos y maximos para recortar en lat y lon
        full_map = self.Check_Mapa_Profile.isChecked()
        lat_min = float(self.Combo_Latitud_Min_Profile.currentText())
        lat_max = float(self.Combo_Latitud_Max_Profile.currentText())
        lon_min = float(self.Combo_Longitud_Min_Profile.currentText())
        lon_max = float(self.Combo_Longitud_Max_Profile.currentText())

        #Validate ranges if not showing full map
        if not self.Check_Mapa_Profile.isChecked():
            lat_min_enabled = self.Combo_Latitud_Min_Profile.isEnabled()
            lat_max_enabled = self.Combo_Latitud_Max_Profile.isEnabled()
            lon_min_enabled = self.Combo_Longitud_Min_Profile.isEnabled()
            lon_max_enabled = self.Combo_Longitud_Max_Profile.isEnabled()
            if lat_min_enabled and lat_max_enabled:
                if lat_min >= lat_max:
                    QMessageBox.warning(self, "Invalid latitude range",
                                        "Min latitude must be lower than max latitude")
                    return
            if lon_min_enabled and lon_max_enabled:
                if lon_min >= lon_max:
                    QMessageBox.warning(self, "Invalid longitude range",
                                        "Min longitude must be lower than max longitude")
                    return

        if "latitude" in da.dims:
            if "Latitude" in (x_axis, y_axis):
                if self.lat_raw_profile:
                    if not full_map:
                        vals = da.latitude.values
                        if vals[0] < vals[-1]:
                            da = da.sel(latitude=slice(lat_min, lat_max))
                        else:
                            da = da.sel(latitude=slice(lat_max, lat_min))
                else:
                    if full_map:
                        lo, hi = self.ds.latitude.values.min(), self.ds.latitude.values.max()
                    else:
                        lo, hi = lat_min, lat_max
                    step = float(self.lat_step_profile)
                    # Igual que en Map Tool: rango desde lo hasta hi con step
                    grid = np.arange(lo, hi + 1e-6, step)
                    da = da.interp(latitude=grid, method="linear")
            else:
                if self.lat_raw_profile:
                    da = da.sel(latitude=lat_min, method="nearest")
                else:
                    da = da.interp(latitude=lat_min, method="linear")
                fixed["Latitude"] = f"{lat_min}°"

        if "longitude" in da.dims:
            if "Longitude" in (x_axis, y_axis):
                if self.lon_raw_profile:
                    if not full_map:
                        vals = da.longitude.values
                        if vals[0] < vals[-1]:
                            da = da.sel(longitude=slice(lon_min, lon_max))
                        else:
                            da = da.sel(longitude=slice(lon_max, lon_min))
                else:
                    if full_map:
                        lo, hi = self.ds.longitude.values.min(), self.ds.longitude.values.max()
                    else:
                        lo, hi = lon_min, lon_max
                    step = float(self.lon_step_profile)
                    grid = np.arange(lo, hi + 1e-6, step)
                    da = da.interp(longitude=grid, method="linear")
            else:
                if self.lon_raw_profile:
                    da = da.sel(longitude=lon_min, method="nearest")
                else:
                    da = da.interp(longitude=lon_min, method="linear")
                fixed["Longitude"] = f"{lon_min}°"

        # Se prepara la figura de Matplotlib
        dims_left = list(da.dims) # Dimensiones que no están fijadas y se van a dibujar
        fig, ax = plt.subplots() # Se crean figura y ejes

        # Si uno de los ejes es variable, se dibuja un perfil 1D
        if "Variable" in (x_axis, y_axis):
            # Se comprueba que efectivamente quede una dimensión libre únicamente (sin contar variable como dimensión)
            if len(dims_left) != 1:
                QMessageBox.warning(self, "Profile","You must select at least one variable to display. Please,"
                                                    "check your Axis and Variables choices")
                return
            d = dims_left[0]
            coords = da.coords[d].values
            vals = da.values
            # En función de si la variable va en eje X o Y, se invierten ejes
            if x_axis == "Variable":
                ax.plot(vals, coords, "-o")
                xlabel, ylabel = desc, d
            else:
                ax.plot(coords, vals, "-o")
                xlabel, ylabel = d, desc

        # Si ninguno de los ejes es variable, se dibuja superficie 2D
        else:
            if len(dims_left) != 2:
                QMessageBox.warning(self, "Profile","You must select at least one variable to display. Please,"
                                                    "check your Axis and Variables Choices")
                return
            # Mapeo de etiquetas que aparecen en la GUI a nombres de coordenadas
            gui2dim = {"Local Time": "Time", "Altitude": "altitude","Latitude": "latitude", "Longitude": "longitude"}

            xdim = gui2dim[x_axis]
            ydim = gui2dim[y_axis]
            # Se transponen para que pcolormesh reciba ejes correctamente
            arr = da.transpose(ydim, xdim)
            xs = arr.coords[xdim].values
            ys = arr.coords[ydim].values
            zs = arr.values
            mesh = ax.pcolormesh(xs, ys, zs, shading="auto", cmap="inferno", vmin=zs.min(), vmax=zs.max())
            fig.colorbar(mesh, ax=ax).set_label(desc)
            xlabel, ylabel = x_axis, y_axis

        # Se añaden unidades a los ejes
        suffix = {"Time": " (h)", "altitude": " (km)","latitude": " (º)", "longitude": " (º)","Local Time": " (h)", "Altitude": " (km)","Latitude": " (º)", "Longitude": " (º)"}
        
        ax.set_xlabel(xlabel + suffix.get(xlabel, ""))
        ax.set_ylabel(ylabel + suffix.get(ylabel, ""))

        # Se contruye el titulo incluyendo epoca, archivo actual y valores fijados
        era = self.Combo_Epoca_Profile.currentText()
        arc = self.Combo_Archivo_Profile.currentText()
        fixed_str = " | ".join(f"{k}: {v}" for k, v in fixed.items())
        ax.set_title(f"{era} | {arc}\n{fixed_str}\n")

        # Se muestra la figura
        ax.grid(True, linestyle=":")
        plt.tight_layout()
        plt.show()

    def closeEvent(self, event):
        #Emit signal and accept close event when plugin is closed
        self.closingPlugin.emit()
        event.accept()