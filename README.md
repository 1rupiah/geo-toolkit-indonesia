# Geo-Toolkit Indonesia

**Portfolio Project by Rahmat Hidayat**

Geoscientist turned Technology Professional - building tools at the intersection of earth science and software engineering.

Available for **freelance**, **consulting**, **contract**, and **full-time** opportunities.

- **Email**: rahmat6hidayat@gmail.com
- **LinkedIn**: [linkedin.com/in/rahmat6hidayat](https://www.linkedin.com/in/rahmat6hidayat)
- **Location**: Jakarta, Indonesia

---

## Overview

**GeoToolkit Indonesia** is a professional-grade Python toolkit for geoscience and survey workflows, built specifically for the Indonesian context - covering coordinate systems, geodetic calculations, well-log data processing, GIS export, and borehole visualization.

The toolkit addresses a common pain point in Indonesian O&G and geoscience workflows: the lack of a unified, open-source Python library that handles Indonesia-specific geodetic parameters (UTM zones 46–54, WGS84/DGN95 datums), standard well-log formats (LAS 2.0), and GIS export to formats compatible with tools used in the field (QGIS, ArcGIS, Google Earth).

This project demonstrates applied software engineering in a geoscience domain - translating years of field and subsurface experience into clean, tested, and reusable code.

---

## Features

| Module                    | Functions                                     | Description                                                                                                                            |
| ------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Coordinate Conversion** | `utm_to_latlon()`, `latlon_to_utm()`          | Convert between UTM and geographic coordinates using WGS84 / DGN95. Auto-detects Indonesia UTM zones (46–54).                          |
| **Survey Calculation**    | `calculate_bearing()`, `calculate_distance()` | Geodetic bearing and distance using Vincenty's formula on the WGS84 ellipsoid. Sub-millimetre accuracy at any distance.                |
| **Geological Data**       | `read_las()`, `read_well_log()`               | Parse LAS 2.0/3.0 well-log files and CSV-based log tables. Returns structured data with curve metadata and null handling.              |
| **GIS Export**            | `to_geojson()`, `to_kml()`                    | Export points, lines, and polygons to GeoJSON (RFC 7946) and KML 2.2. Compatible with QGIS, ArcGIS, Google Earth, Leaflet, and Mapbox. |
| **Visualization**         | `plot_survey_line()`, `plot_borehole()`       | Publication-quality survey line maps and multi-track borehole log displays.                                                            |

---

## Visual Output

### Borehole Log - Well SUMATRA-A-01, Minas Field

Multi-track petrophysical log display showing GR, RHOB, NPHI, and RT curves from a sample LAS file. Each track includes min/max/avg statistics and is rendered with a clean, publication-ready layout.

![Borehole Log](https://raw.githubusercontent.com/1rupiah/geo-toolkit-indonesia/main/docs/borehole_log_plot.png)

### Seismic Survey Line - Jawa Barat Corridor

Geographic survey line plot with labelled stations, direction arrow, total line length, and coordinate range info box. Rendered from real UTM/geographic coordinates.

![Survey Line](https://raw.githubusercontent.com/1rupiah/geo-toolkit-indonesia/main/docs/survey_line_plot.png)

---

## Test Report

Full test documentation is available in the repository:

[GeoToolkit Indonesia - Test Report (Excel)](https://github.com/1rupiah/geo-toolkit-indonesia/raw/main/docs/GeoToolkit%20Indonesia%20-%20Test%20Report.xlsx)

53 tests across 6 test classes. All passed.

---

## Project Structure

```
geo-toolkit-indonesia/
├── geo_toolkit_indonesia/
│   ├── __init__.py                 # Package entry point, public API
│   ├── modules/
│   │   ├── coordinate.py           # Module 1 - Coordinate Conversion
│   │   ├── survey.py               # Module 2 - Survey Calculation
│   │   ├── geological.py           # Module 3 - Geological Data
│   │   ├── gis_export.py           # Module 4 - GIS Export
│   │   └── visualization.py        # Module 5 - Visualization
│   └── data/sample/
│       ├── WELL_A.LAS              # Sample LAS 2.0 file (synthetic Sumatra well)
│       └── well_log_B.csv          # Sample CSV well log
├── docs/
│   ├── borehole_log_plot.png       # Sample borehole visualization output
│   ├── survey_line_plot.png        # Sample survey line visualization output
│   └── GeoToolkit Indonesia - Test Report.xlsx
├── tests/
│   └── test_all_modules.py         # 53 unit + integration tests
├── demo.py                         # Automated demonstration script
├── setup.py
├── requirements.txt
└── README.md
```

---

## Installation

**Requirements:** Python 3.8 or higher.

```bash
# 1. Clone the repository
git clone https://github.com/1rupiah/geo-toolkit-indonesia.git
cd geo-toolkit-indonesia

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the package in development mode
pip install -e .
```

**Dependencies:**

| Package      | Purpose                                            |
| ------------ | -------------------------------------------------- |
| `pyproj`     | Geodetic coordinate transformations (WGS84, DGN95) |
| `lasio`      | LAS 2.0 / 3.0 file parsing                         |
| `numpy`      | Numerical computing                                |
| `matplotlib` | Plotting and visualization                         |
| `scipy`      | Scientific utilities                               |

---

## Quick Start

### Module 1 - Coordinate Conversion

```python
from geo_toolkit_indonesia.modules.coordinate import latlon_to_utm, utm_to_latlon

# Convert Lat/Lon to UTM
utm = latlon_to_utm(-6.200, 106.816)
print(utm)
# UTM(E=700934.3, N=9314342.9, Zone=48S, datum=WGS84)

# Convert UTM back to Lat/Lon
latlon = utm_to_latlon(700934.3, 9314342.9, zone=48, hemisphere="S")
print(latlon)
# LatLon(6.200000°S, 106.816000°E, datum=WGS84)

# Access individual fields
print(utm.easting, utm.northing, utm.zone, utm.hemisphere)

# Export as dict
print(utm.to_dict())
```

### Module 2 - Survey Calculation

```python
from geo_toolkit_indonesia.modules.survey import calculate_bearing, calculate_distance

# Geodetic distance Jakarta to Surabaya
d = calculate_distance(-6.200, 106.816, -7.257, 112.752)
print(d.kilometres)       # ~680 km
print(d.nautical_miles)
print(d.statute_miles)

# Bearing between two survey stations
b = calculate_bearing(-6.200, 106.816, -7.257, 112.752)
print(b.forward_bearing)  # degrees 0 to 360
print(b.back_bearing)
```

### Module 3 - Geological Data

```python
from geo_toolkit_indonesia.modules.geological import read_las, read_well_log

# Read a LAS file
las = read_las("path/to/your_well.las")
print(las.summary())

# Access curve data as numpy arrays
gr    = las.curves["GR"]    # Gamma Ray
rhob  = las.curves["RHOB"]  # Bulk Density
depth = las.depth

# Read a CSV well log
log = read_well_log(
    "path/to/well_log.csv",
    depth_col="DEPTH",
    value_cols=["GR", "RHOB", "NPHI"]   # optional: filter specific curves
)
print(log.summary())
```

### Module 4 - GIS Export

```python
from geo_toolkit_indonesia.modules.gis_export import (
    to_geojson, to_kml,
    point_feature, linestring_feature, polygon_feature
)

# Create features
well  = point_feature(-6.200, 106.816, name="Well-Jakarta-01", operator="Pertamina EP")
line  = linestring_feature([(-6.2, 106.8), (-7.0, 107.8)], name="Seismic Line SL-001")
block = polygon_feature(
    [(-6.0, 106.5), (-6.0, 107.5), (-7.5, 107.5), (-7.5, 106.5)],
    name="Block Jawa Barat"
)

# Export to GeoJSON - open in QGIS, ArcGIS, Mapbox, Leaflet
to_geojson([well, line, block], output_path="output/assets.geojson")

# Export to KML - open in Google Earth, QGIS
to_kml([well, line, block], output_path="output/assets.kml")
```

### Module 5 - Visualization

```python
from geo_toolkit_indonesia.modules.visualization import plot_survey_line, plot_borehole
from geo_toolkit_indonesia.modules.geological import read_las

# Survey line plot
stations = [(-6.2, 106.8), (-6.5, 107.2), (-7.0, 107.8)]
labels   = ["SP-001", "SP-002", "SP-003"]

plot_survey_line(
    stations,
    title="Seismic Line SL-001",
    point_labels=labels,
    output_path="output/survey_line.png"
)

# Borehole log from a LAS file
las    = read_las("your_well.las")
curves = {k: las.curves[k] for k in ["GR", "RHOB", "NPHI", "RT"] if k in las.curves}
units  = {"GR": "gAPI", "RHOB": "g/cc", "NPHI": "v/v", "RT": "Ohm.m"}

plot_borehole(
    las.depth,
    curves,
    title=f"Well Log - {las.well_name}",
    units=units,
    output_path="output/borehole.png"
)
```

---

## Running the Demo

`demo.py` is a self-contained demonstration script that runs all five modules end-to-end using built-in sample data. No external files or inputs are required.

```bash
python demo.py
```

When you run it, the script will:

1. **Module 1** - Convert coordinates for five major Indonesian cities and verify round-trip accuracy.
2. **Module 2** - Calculate geodetic distances and bearings for a 5-station seismic survey line across West Java.
3. **Module 3** - Parse the sample LAS file (`WELL_A.LAS`) and CSV well log, then print curve statistics to console.
4. **Module 4** - Export well locations, a seismic line, and an exploration block to GeoJSON and KML files.
5. **Module 5** - Render a survey line map and a 4-track borehole log as PNG images.

All output files are saved automatically to `./demo_output/`. This folder is created on first run and is safe to delete at any time.

> **Note:** The sample data (`WELL_A.LAS`, `well_log_B.csv`) is synthetic - designed to demonstrate realistic Indonesian O&G data structures. It is not sourced from any actual well or field.

---

## Running the Tests

```bash
# Run all 53 tests with verbose output
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ -v --cov=geo_toolkit_indonesia --cov-report=term-missing
```

**Test results: 53/53 passed.**

| Module                | Tests | What Is Covered                                                    |
| --------------------- | ----- | ------------------------------------------------------------------ |
| Coordinate Conversion | 9     | Zone detection, round-trips, hemisphere assignment, error handling |
| Survey Calculation    | 10    | Distance units, bearing direction, Vincenty accuracy, edge cases   |
| Geological Data       | 13    | LAS parsing, null handling, curve filtering, missing file errors   |
| GIS Export            | 10    | GeoJSON RFC 7946, KML 2.2, all geometry types, file I/O            |
| Visualization         | 8     | Figure return, PNG file save, input validation                     |
| Integration           | 3     | End-to-end pipelines across multiple modules                       |

Full test documentation: [GeoToolkit Indonesia - Test Report](https://github.com/1rupiah/geo-toolkit-indonesia/raw/main/docs/GeoToolkit%20Indonesia%20-%20Test%20Report.xlsx)

---

## About the Author

**Rahmat Hidayat** is a Jakarta-based professional with a background in geoscience and oil and gas who transitioned into technology in 2023. He brings a rare combination of subsurface domain expertise and software delivery experience - understanding both what the data means geologically and how to build reliable systems that work with it at scale.

His experience spans geoscience fieldwork and interpretation, O&G project management, commercial management, and technology delivery across enterprise and government accounts in Indonesia.

**GeoToolkit Indonesia** reflects a core belief: that deep domain knowledge, when combined with software engineering skills, produces tools that are genuinely useful - not just technically correct, but built around how geoscientists and engineers actually work. The coordinate systems are the ones used in Indonesian surveys. The well-log format is the one actually produced by logging tools in the field. The GIS export formats are the ones opened by the tools sitting on every geoscientist's desktop.

Open to freelance projects, consulting engagements, contract roles, and full-time opportunities in geoscience technology, digital transformation, data analytics, and software delivery.

---

## Disclaimer

This repository is presented for portfolio and demonstration purposes only. The sample well data included (`WELL_A.LAS`, `well_log_B.csv`) is entirely synthetic and does not represent any real well, field, or subsurface asset. No proprietary or confidential data from any company or project has been used. All rights to third-party libraries and tools belong to their respective owners. If you would like to discuss similar projects, consulting opportunities, freelance work, or full-time positions, feel free to reach out through the contact information provided above.
