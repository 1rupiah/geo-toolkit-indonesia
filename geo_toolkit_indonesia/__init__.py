"""
GeoToolkit Indonesia
====================
A Python toolkit for geoscience and survey workflows in Indonesia.

Modules:
    - coordinate: UTM / Lat-Lon conversion (WGS84, DGN95)
    - survey: Bearing and distance calculations
    - geological: LAS and well-log file readers
    - gis_export: GeoJSON and KML export utilities
    - visualization: Survey line and borehole plots
"""

from geo_toolkit_indonesia.modules.coordinate import utm_to_latlon, latlon_to_utm
from geo_toolkit_indonesia.modules.survey import calculate_bearing, calculate_distance
from geo_toolkit_indonesia.modules.geological import read_las, read_well_log
from geo_toolkit_indonesia.modules.gis_export import to_geojson, to_kml
from geo_toolkit_indonesia.modules.visualization import plot_survey_line, plot_borehole

__version__ = "1.0.0"
__author__ = "GeoToolkit Indonesia"
__license__ = "MIT"

__all__ = [
    "utm_to_latlon",
    "latlon_to_utm",
    "calculate_bearing",
    "calculate_distance",
    "read_las",
    "read_well_log",
    "to_geojson",
    "to_kml",
    "plot_survey_line",
    "plot_borehole",
]
