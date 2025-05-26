import os
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import pyqtSignal
import xarray as xr        # Para abrir y trabajar con archivos NetCDF
import numpy as np         # Para manipular matrices (arrays de datos)
from qgis.core import QgsProject, QgsRasterLayer, Qgis, QgsMessageLog, QgsSingleBandPseudoColorRenderer, QgsRasterShader, QgsColorRampShader, QgsStyle, QgsSingleBandPseudoColorRenderer,QgsRasterBandStats  # Todo lo necesario para modificar apariencia en QGIS
from osgeo import gdal, osr                       # Para crear archivos GeoTIFF
from PyQt5.QtWidgets import QMessageBox, QApplication, QDialog, QDialogButtonBox # Me muestra mensajes de error cuando ejecuto
from qgis.utils import iface
import tempfile
import uuid

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'mcd_visualizer_dockwidget_base.ui')) # Carga el archivo .ui (GUI) y lo convierte en codigo python usablee


class MCDVisualizerDockWidget(QtWidgets.QDockWidget, FORM_CLASS): # Empieza clase definiendo el panel lateral

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(MCDVisualizerDockWidget, self).__init__(parent)
        self.setupUi(self) # Carga la interfaz desde el .ui en el constructor de mi clase

        self.ruta =  r"C:\Users\lucia\Desktop\David\TFM\00_MCD_6.1\data"
        self.lista_carpetas = {
            "Promedio Anual" : "clim_aveEUV",
            "Frio": "cold",
            "Templado": "warm",
            "Tormentoso": "strm",
            "Año Marciano 24": "MY24",
            "Año Marciano 25": "MY25",
            "Año Marciano 26": "MY26",
            "Año Marciano 27": "MY27",
            "Año Marciano 28": "MY28",
            "Año Marciano 29": "MY29",
            "Año Marciano 30": "MY30",
            "Año Marciano 31": "MY31",
            "Año Marciano 32": "MY32",
            "Año Marciano 33": "MY33",
            "Año Marciano 34": "MY34",
            "Año Marciano 35": "MY35",
        }

        self.Combo_Archivo.currentTextChanged.connect(self.cambio_archivo)
        self.Combo_Epoca.currentTextChanged.connect(self.cambio_epoca)
        self.Combo_Variable.currentTextChanged.connect(self.toggle_altitude)
        self.Push_Visualizar.clicked.connect(self.visualizar_variable)

        self.cambio_epoca(self.Combo_Epoca.currentText())
        self.toggle_altitude(self.Combo_Variable.currentText())

        self._raster_counter = 0 # Para modificar el nombre del raster y poder plotear varios simultaneamente

    def cambio_epoca(self, epoca):
        """
        Rellena Combo_Archivo en función de la
        epoca seleccionada por el usuario
        """
        carpeta = self.lista_carpetas.get(epoca)

        self.Combo_Archivo.clear()

        if not carpeta:
            return

        folder = os.path.join(self.ruta, carpeta)

        try:
            archivos = sorted(f for f in os.listdir(folder) if f.endswith("_me.nc") and "thermo" not in f)
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "No existe dicha carpeta")
            return

        self.Combo_Archivo.addItems(archivos)

    def cambio_archivo(self, archivo_nombre):
        """
        Cuando se selecciona un archivo en Combo_Archivo, abre ese archivo .nc
        y rellena los demas Combo_Variable, Hora, Altitud...
        """
        if not archivo_nombre:
            return

        epoca_label = self.Combo_Epoca.currentText()
        carpeta = self.lista_carpetas[epoca_label]
        path = os.path.join(self.ruta, carpeta, archivo_nombre)

        try:
            self.ds = xr.open_dataset(path, decode_times = False)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir el archivo NetCDF", str(e))
            return

        self.Combo_Variable.clear()
        self.Combo_Variable.addItems(list(self.ds.data_vars.keys()))

        self.Combo_Hora.clear()
        self.Combo_Hora.addItems([str(int(t)) for t in self.ds.Time.values])

        self.Combo_Altitud.clear()
        self.Combo_Altitud.addItems([f"{a:.4f}" for a in self.ds.altitude.values])

        self.Combo_Latitud_Min.clear()
        self.Combo_Latitud_Max.clear()
        self.Combo_Longitud_Min.clear()
        self.Combo_Longitud_Max.clear()
        self.Combo_Latitud_Min.addItems([f"{lat:.4f}" for lat in self.ds.latitude.values])
        self.Combo_Latitud_Max.addItems([f"{lat:.4f}" for lat in self.ds.latitude.values])
        self.Combo_Longitud_Min.addItems([f"{lon:.4f}" for lon in self.ds.longitude.values])
        self.Combo_Longitud_Max.addItems([f"{lat:.4f}" for lat in self.ds.longitude.values])

        self.toggle_altitude(self.Combo_Variable.currentText())

    def toggle_altitude(self, var_name):
        "Función que se encarga de habilitar o deshabilitar Combo_Altitud en función de si el archivo tiene tiene altitud o no"
        if hasattr(self, 'ds') and var_name in self.ds.data_vars:
            da = self.ds[var_name]
            if "altitude" in da.dims:
                self.Combo_Altitud.setEnabled(True)
                return

        self.Combo_Altitud.setEnabled(False)
        self.Combo_Altitud.setStyleSheet("QComboBox:disabled { background-color: red }")
        self.Combo_Altitud.setToolTip("Esta variable no tiene dimensión 'altitude'")

    def visualizar_variable(self):
        """
        Lee los valores seleccionados en la GUI y:
          - usa currentIndex() para Time y Altitude
          - hace recorte espacial SOLO si lat/lon != "ALL"
          - llama a _mostrar_raster
        """

        var = self.Combo_Variable.currentText()
        hora = self.Combo_Hora.currentIndex()
        altitud = self.Combo_Altitud.currentIndex()

        da = self.ds[var]

        if "Time" in da.dims:
            da = da.isel(Time=hora)
        if "altitude" in da.dims and self.Combo_Altitud.isEnabled():
            da = da.isel(altitude = altitud)

        if not self.Check_Mapa.isChecked():
            lat_min_idx = self.Combo_Latitud_Min.currentIndex()
            lat_max_idx = self.Combo_Latitud_Max.currentIndex()
            lon_min_idx = self.Combo_Longitud_Min.currentIndex()
            lon_max_idx = self.Combo_Longitud_Max.currentIndex()

            if lat_min_idx > lat_max_idx:
                QMessageBox.warning(
                    self, "Rango de latitudes inválido"
                )
                return

            if lon_min_idx > lon_max_idx:
                QMessageBox.warning(
                    self, "Rango de longitudes inválido"
                )
                return

            da = da.isel(
                latitude = slice(lat_min_idx, lat_max_idx + 1),
                longitude = slice(lon_min_idx, lon_max_idx + 1)
            )

            lats = self.ds.latitude.values[lat_min_idx:lat_max_idx + 1]
            lons = self.ds.longitude.values[lon_min_idx:lon_max_idx + 1]

        else:
            lats = self.ds.latitude.values
            lons = self.ds.longitude.values

        array = da.values
        self._mostrar_raster(array, lats, lons, var)

    def _mostrar_raster(self, array, lat, lon, nombre):
        """
        1) Crea un GeoTIFF único en temp con GDAL (EPSG:4326)
        2) Carga el layer en QGIS
        3) Calcula min/max reales de la banda
        4) Aplica pseudocolor Turbo, interpolación lineal,
           modo CONTINUOUS y fija min/max en el renderer
        5) Añade la capa y refresca canvas + simbología
        """
        # 1) Validar 2D
        arr = np.asarray(array)
        if arr.ndim != 2:
            QMessageBox.warning(self, "No es un mapa 2D", "…")
            return

        # 2) Nombre único en temp
        temp_dir = tempfile.gettempdir()
        filename = f"{nombre}_{uuid.uuid4().hex}.tif"
        path = os.path.join(temp_dir, filename)

        # 3) Crear GeoTIFF
        nrows, ncols = arr.shape
        xres = (lon[-1] - lon[0]) / ncols
        yres = (lat[-1] - lat[0]) / nrows
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(path, ncols, nrows, 1, gdal.GDT_Float32)
        ds.SetGeoTransform((lon[0], xres, 0, lat[0], 0, -yres))
        srs = osr.SpatialReference();
        srs.ImportFromEPSG(4326)
        ds.SetProjection(srs.ExportToWkt())
        ds.GetRasterBand(1).WriteArray(arr)
        ds.FlushCache();
        ds = None

        # 4) Cargar layer
        layer = QgsRasterLayer(path, nombre)
        if not layer.isValid():
            QMessageBox.critical(self, "Error", "No se pudo cargar el raster.")
            return
        provider = layer.dataProvider()

        # 5) Aplicar pseudocolor continuo Turbo + interpolación lineal
        ramp = QgsStyle().defaultStyle().colorRamp('Turbo')
        renderer = QgsSingleBandPseudoColorRenderer(provider, 1)
        renderer.createShader(
            ramp,
            Qgis.ShaderInterpolationMethod.Linear,
            Qgis.ShaderClassificationMethod.Continuous,
            0
        )
        layer.setRenderer(renderer)

        # 6) Ajustar opacidad al 70%
        layer.setOpacity(0.7)

        # 7) Añadir y repintar
        QgsProject.instance().addMapLayer(layer)
        layer.triggerRepaint()

        # 8) Abrir diálogo de Simbología y forzar “Aplicar”+cierre
        iface.showLayerProperties(layer, 'symbology')
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QDialog) and w.windowTitle().startswith("Propiedades de capa"):
                w.close()
        iface.showLayerProperties(layer, 'symbology')
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QDialog) and w.windowTitle().startswith("Propiedades de capa"):
                for bb in w.findChildren(QDialogButtonBox):
                    btn_apply = bb.button(QDialogButtonBox.Apply)
                    if btn_apply:
                        btn_apply.click()
                        w.close()
                break


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()