# MCD Visualizer for QGIS

**MCD Visualizer** is a QGIS plugin designed to analyze and visualize atmospheric data from the [Mars Climate Database (MCD)](http://www-mars.lmd.jussieu.fr/).

## ⚠️ CRITICAL REQUIREMENTS

Due to license restrictions and file size, **this plugin does NOT include the MCD data**. 

### 1. Data Requirements (Mandatory)
You must have a local copy of the full Mars Climate Database (v5 or v6). On the first run, the plugin will ask you to select your local `data` folder.

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

> **Note:** If you select a folder that is missing any of these subdirectories, the plugin may not function correctly.

### 2. Software Requirements
This plugin requires external Python libraries not included in standard QGIS installations:
*   `xarray`
*   `netCDF4`

**How to install them:**
Open your **OSGeo4W Shell** (Windows) or Terminal (Mac/Linux) and run:
```bash
pip install xarray netCDF4

## Features
*   **Map Tool:** Visualize atmospheric variables (Temperature, Pressure, Wind, etc.) on a 2D map with spatial interpolation option.
*   **Profile Tool:** Generate vertical profiles, temporal evolution charts, and 2D cross-sections.
*   **Customization:** Toggle between "Raw Data" (exact grid points) and "Interpolated" modes for smoother visualization.
*   **MOLA Integration:** Automatically overlays MOLA topography isolines for context.

## Installation
1.  Open QGIS.
2.  Go to **Plugins > Manage and Install Plugins**.
3.  Search for **"MCD Visualizer"**.
4.  Install the plugin.
5.  On first launch, follow the prompt to select your MCD `data` folder.

## License
This plugin is released under the GNU General Public License (GPL) version 2 or later.
