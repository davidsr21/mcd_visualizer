import os
import tempfile
import uuid

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsRasterContourRenderer,
    QgsLineSymbol,
    QgsSingleBandPseudoColorRenderer,
    QgsStyle,
    Qgis
)
from osgeo import gdal, osr
from PyQt5.QtWidgets import QMessageBox, QApplication, QDialog, QDialogButtonBox
from qgis.utils import iface

import xarray as xr
import numpy as np


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__),
    'mcd_visualizer_dockwidget_base.ui'
))


class MCDVisualizerDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(MCDVisualizerDockWidget, self).__init__(parent)
        self.setupUi(self)

        self.ruta = r"C:\Users\lucia\Desktop\David\TFM\00_MCD_6.1\data"
        self.lista_carpetas = {
            "Promedio Anual": "clim_aveEUV",
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

        self.mola_loaded = False
        self.Push_Visualizar.clicked.connect(self.visualizar_variable)

        self.cambio_epoca(self.Combo_Epoca.currentText())
        self.toggle_altitude(self.Combo_Variable.currentText())

    def cambio_epoca(self, epoca):
        carpeta = self.lista_carpetas.get(epoca)
        self.Combo_Archivo.clear()
        if not carpeta:
            return
        folder = os.path.join(self.ruta, carpeta)
        try:
            archivos = sorted(f for f in os.listdir(folder)
                              if f.endswith("_me.nc") and "thermo" not in f)
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "No existe dicha carpeta")
            return
        self.Combo_Archivo.addItems(archivos)

    def cambio_archivo(self, archivo_nombre):
        if not archivo_nombre:
            return
        epoca_label = self.Combo_Epoca.currentText()
        carpeta = self.lista_carpetas[epoca_label]
        path = os.path.join(self.ruta, carpeta, archivo_nombre)
        try:
            self.ds = xr.open_dataset(path, decode_times=False)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir el archivo NetCDF", str(e))
            return

        # Poblado de combos
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
        self.Combo_Longitud_Max.addItems([f"{lon:.4f}" for lon in self.ds.longitude.values])

        self.toggle_altitude(self.Combo_Variable.currentText())

    def toggle_altitude(self, var_name):
        if hasattr(self, 'ds') and var_name in self.ds.data_vars:
            da = self.ds[var_name]
            if "altitude" in da.dims:
                self.Combo_Altitud.setEnabled(True)
                return
        self.Combo_Altitud.setEnabled(False)
        self.Combo_Altitud.setStyleSheet("QComboBox:disabled { background-color: red }")
        self.Combo_Altitud.setToolTip("Esta variable no tiene dimensión 'altitude'")

    def visualizar_variable(self):
        # 1) Leer valores numéricos de lat/lon
        lat_min = float(self.Combo_Latitud_Min.currentText())
        lat_max = float(self.Combo_Latitud_Max.currentText())
        lon_min = float(self.Combo_Longitud_Min.currentText())
        lon_max = float(self.Combo_Longitud_Max.currentText())

        # 2) Validar rangos si no es “mapa completo”
        if not self.Check_Mapa.isChecked():
            if lat_min >= lat_max:
                QMessageBox.warning(self, "Rango de latitudes inválido",
                                    "La latitud mínima debe ser menor que la máxima.")
                return
            if lon_min >= lon_max:
                QMessageBox.warning(self, "Rango de longitudes inválido",
                                    "La longitud mínima debe ser menor que la máxima.")
                return

        # 3) Carga MOLA solo la primera vez
        self.loadMolaBase()

        # 4) Saca el DataArray y selecciona hora/altitud
        da = self.ds[self.Combo_Variable.currentText()]
        if "Time" in da.dims:
            da = da.isel(Time=self.Combo_Hora.currentIndex())
        if "altitude" in da.dims and self.Combo_Altitud.isEnabled():
            da = da.isel(altitude=self.Combo_Altitud.currentIndex())

        # 5) Recorte espacial: detectamos orden de las coords
        if not self.Check_Mapa.isChecked():
            # orden de latitude
            lat_vals = self.ds.latitude.values
            if lat_vals[0] < lat_vals[-1]:
                # ascendente: slice(min, max)
                lat_slice = slice(lat_min, lat_max)
            else:
                # descendente: slice(max, min)
                lat_slice = slice(lat_max, lat_min)

            # orden de longitude
            lon_vals = self.ds.longitude.values
            if lon_vals[0] < lon_vals[-1]:
                lon_slice = slice(lon_min, lon_max)
            else:
                lon_slice = slice(lon_max, lon_min)

            da = da.sel(latitude=lat_slice, longitude=lon_slice)

        # 6) Extraer las coordenadas y el array resultante
        lats = da.latitude.values
        lons = da.longitude.values
        array = da.values

        # 7) Verificar que hay datos antes de pintar
        if array.size == 0:
            QMessageBox.warning(self, "Sin datos",
                                "El recorte seleccionado no contiene datos.")
            return

        # 8) Mostrar el ráster
        self._mostrar_raster(array, lats, lons, self.Combo_Variable.currentText())

    def loadMolaBase(self):
        if self.mola_loaded:
            return

        origen = os.path.join(self.ruta, "mola32_isolines.tif")

        if not self.Check_Mapa.isChecked():
            lon_min = float(self.Combo_Longitud_Min.currentText())
            lon_max = float(self.Combo_Longitud_Max.currentText())
            lat_min = float(self.Combo_Latitud_Min.currentText())
            lat_max = float(self.Combo_Latitud_Max.currentText())

            opts = gdal.TranslateOptions(
                format="GTiff",
                projWin=[lon_min, lat_max, lon_max, lat_min]
            )
            tmpfile = os.path.join(tempfile.gettempdir(), "mola_crop.tif")
            gdal.Translate(tmpfile, origen, options=opts)
            destino = tmpfile
        else:
            destino = origen

        layer = QgsRasterLayer(destino, "mola32 Isolines")
        if not layer.isValid():
            QMessageBox.critical(self, "Error", "Unable to upload MOLA layer")
            return

        symbol = QgsLineSymbol.createSimple({'color': '0,0,0', 'width': '0.5'})
        renderer = QgsRasterContourRenderer(layer.dataProvider())
        renderer.setContourInterval(1000.0)
        renderer.setContourSymbol(symbol)
        renderer.setContourIndexSymbol(symbol)
        renderer.setDownscale(4.0)

        layer.setRenderer(renderer)
        layer.triggerRepaint()

        root = QgsProject.instance().layerTreeRoot()
        QgsProject.instance().addMapLayer(layer, addToLegend=False)
        root.insertLayer(0, layer)

        self.mola_layer = layer
        self.mola_loaded = True

    def _mostrar_raster(self, array, lat, lon, nombre):
        arr = np.asarray(array)

        # 0) Validar que tenemos datos
        if arr.size == 0 or len(lat) == 0 or len(lon) == 0:
            QMessageBox.warning(
                self,
                "Sin datos",
                "El recorte seleccionado no contiene datos."
            )
            return

        # 1) Comprobar que es 2D
        if arr.ndim != 2:
            QMessageBox.warning(self, "No es un mapa 2D", "…")
            return

        # 2) Voltear para georreferenciar correctamente
        arr = np.flipud(arr)

        # 3) Preparar escritura del GeoTIFF
        temp_dir = tempfile.gettempdir()
        filename = f"{nombre}_{uuid.uuid4().hex}.tif"
        path = os.path.join(temp_dir, filename)

        nrows, ncols = arr.shape
        xres = (lon[-1] - lon[0]) / ncols
        yres = (lat[-1] - lat[0]) / nrows

        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(path, ncols, nrows, 1, gdal.GDT_Float32)
        ds.SetGeoTransform((lon[0], xres, 0, lat[-1], 0, -yres))
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        ds.SetProjection(srs.ExportToWkt())
        ds.GetRasterBand(1).WriteArray(arr)
        ds.FlushCache()
        ds = None

        layer = QgsRasterLayer(path, nombre)
        if not layer.isValid():
            QMessageBox.critical(self, "Error", "No se pudo cargar el raster.")
            return

        provider = layer.dataProvider()
        ramp = QgsStyle().defaultStyle().colorRamp('Turbo')
        renderer = QgsSingleBandPseudoColorRenderer(provider, 1)
        renderer.createShader(
            ramp,
            Qgis.ShaderInterpolationMethod.Linear,
            Qgis.ShaderClassificationMethod.Continuous,
            0
        )
        layer.setRenderer(renderer)
        layer.setOpacity(0.8)

        QgsProject.instance().addMapLayer(layer)
        layer.triggerRepaint()

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