# MCD Visualizer for QGIS

**MCD Visualizer** is a QGIS plugin designed to analyze and visualize atmospheric data from the [Mars Climate Database (MCD)](http://www-mars.lmd.jussieu.fr/).

## ⚠️ CRITICAL REQUIREMENTS

Due to license restrictions and file size, **this plugin does NOT include the MCD data**. 

### 1. Data Requirements (Mandatory)
You must have a local copy of the full Mars Climate Database (v5 or v6). On the first run, the plugin will launch an interactive setup dialog asking you to select your local `data` folder.

**Your `data` folder MUST contain ALL the following subdirectories:**

#### Climate Scenarios:
*   `clim_aveEUV` (Yearly Average)
*   `cold`
*   `warm`
*   `strm` (Dust Storm)

#### Martian Years (Historic Data):
*   `MY24`
*   `MY25`
*   `MY26`
*   `MY27`
*   `MY28`
*   `MY29`
*   `MY30`
*   `MY31`
*   `MY32`
*   `MY33`
*   `MY34`
*   `MY35`

> **Note on Folder Validation:** The plugin automatically verifies that required subdirectories exist. If you select an invalid folder, the plugin will warn you and ask you to select the correct location. If you cancel the folder selection, the plugin will safely close without crashing and will prompt you again the next time you open it.

### 2. Software Requirements (Python Libraries)
This plugin requires two external Python libraries not included in standard QGIS installations: `xarray` and `netCDF4`.

**How to install them:**
*   **In Windows:** Open the **OSGeo4W Shell** (you can find it by searching in your Windows Start menu). In the black window that opens, type exactly the following command and press Enter:
    `pip install xarray netCDF4`
*   **In Mac/Linux:** Open your Terminal, type the same command and press Enter:
    `pip install xarray netCDF4`

## Features
*   **Map Tool:** Visualize atmospheric variables (Temperature, Pressure, Wind, etc.) on a 2D map with spatial interpolation option.
*   **Profile Tool:** Generate vertical profiles, temporal evolution charts, and 2D cross-sections.
*   **Customization:** Toggle between "Raw Data" (exact grid points) and "Interpolated" modes for smoother visualization.
*   **MOLA Integration:** Automatically overlays MOLA topography isolines for context.

## Installation

1.  Open QGIS.
2.  Go to **Plugins > Manage and Install Plugins**.
3.  Go to the **Settings** tab and check the box **"Show also experimental plugins"**.
4.  Go back to the **All** tab and search for **"MCD Visualizer"**.
5.  Click on **Install Plugin**.
6.  On first launch, follow the interactive prompt to select your MCD `data` folder.

> **Troubleshooting:** 
> * **Data Folder Prompt:** If you ever move your MCD data folder or cancel the initial setup, simply click the MCD Visualizer icon again to launch the folder setup dialog.
> * **Installation Fatal Error:** If you receive a "Fatal Error" during installation mentioning `dataclasses`, it is caused by a conflict with another third-party plugin called **qpip**. To solve this: go to your Installed plugins tab, temporarily uncheck "qpip", install MCD Visualizer, and then re-check "qpip".

## License
This plugin is released under the GNU General Public License (GPL) version 2 or later.