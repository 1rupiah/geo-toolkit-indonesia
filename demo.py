#!/usr/bin/env python3
"""
GeoToolkit Indonesia – Full Demo
=================================
Demonstrates all 5 modules with real-world Indonesia geoscience scenarios.

Run:
    python demo.py

Outputs saved to: ./demo_output/
"""

import sys
import os
from pathlib import Path
import numpy as np

# Make sure local package is found
sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path("demo_output")
OUTPUT_DIR.mkdir(exist_ok=True)

SAMPLE_DIR = Path("geo_toolkit_indonesia/data/sample")

print("=" * 60)
print("  GeoToolkit Indonesia v1.0 – Demo")
print("=" * 60)

# ===========================================================================
# MODULE 1 – Coordinate Conversion
# ===========================================================================
print("\n[MODULE 1] Coordinate Conversion")
print("-" * 40)

from geo_toolkit_indonesia.modules.coordinate import utm_to_latlon, latlon_to_utm

# Well locations across Indonesia (realistic O&G coordinates)
locations = [
    ("Jakarta",   -6.200,  106.816),
    ("Surabaya",  -7.257,  112.752),
    ("Balikpapan",-1.267,  116.829),
    ("Medan",      3.595,   98.672),
    ("Makassar",  -5.147,  119.432),
]

for name, lat, lon in locations:
    utm = latlon_to_utm(lat, lon)
    recovered = utm_to_latlon(utm.easting, utm.northing, utm.zone, utm.hemisphere)
    print(f"  {name:<12} | {lat:+.4f}°, {lon:.4f}° → "
          f"Zone {utm.zone}{utm.hemisphere} | E={utm.easting:.1f}, N={utm.northing:.1f}")
    err = max(abs(recovered.latitude - lat), abs(recovered.longitude - lon))
    print(f"               Round-trip error: {err:.2e}°  ({'✓ PASS' if err < 1e-4 else '✗ FAIL'})")


# ===========================================================================
# MODULE 2 – Survey Calculation
# ===========================================================================
print("\n[MODULE 2] Survey Calculation")
print("-" * 40)

from geo_toolkit_indonesia.modules.survey import calculate_bearing, calculate_distance

survey_stations = [
    ("Station-01", -6.200, 106.800),
    ("Station-02", -6.450, 107.100),
    ("Station-03", -6.700, 107.450),
    ("Station-04", -7.000, 107.850),
    ("Station-05", -7.300, 108.200),
]

total_km = 0.0
print(f"  {'Leg':<20} {'Distance':>12}  {'Bearing':>10}")
print(f"  {'-'*20} {'-'*12}  {'-'*10}")

for i in range(len(survey_stations) - 1):
    a_name, lat1, lon1 = survey_stations[i]
    b_name, lat2, lon2 = survey_stations[i + 1]
    d = calculate_distance(lat1, lon1, lat2, lon2)
    b = calculate_bearing(lat1, lon1, lat2, lon2)
    total_km += d.kilometres
    leg = f"{a_name} → {b_name}"
    print(f"  {leg:<20} {d.kilometres:>10.4f} km  {b.forward_bearing:>8.2f}°")

print(f"  {'TOTAL':<20} {total_km:>10.4f} km")


# ===========================================================================
# MODULE 3 – Geological Data
# ===========================================================================
print("\n[MODULE 3] Geological Data")
print("-" * 40)

from geo_toolkit_indonesia.modules.geological import read_las, read_well_log

# LAS file
las = read_las(SAMPLE_DIR / "WELL_A.LAS")
print(f"  LAS File loaded:")
print("\n".join(f"    {l}" for l in las.summary().splitlines()))

# CSV well log
log = read_well_log(SAMPLE_DIR / "well_log_B.csv", depth_col="DEPTH")
print(f"\n  CSV Well Log loaded:")
print("\n".join(f"    {l}" for l in log.summary().splitlines()))

# Quick stats on GR curve
gr = las.curves.get("GR", np.array([]))
if len(gr):
    print(f"\n  GR Statistics (Well-A):")
    print(f"    Min: {np.nanmin(gr):.2f} gAPI")
    print(f"    Max: {np.nanmax(gr):.2f} gAPI")
    print(f"    Mean: {np.nanmean(gr):.2f} gAPI")


# ===========================================================================
# MODULE 4 – GIS Export
# ===========================================================================
print("\n[MODULE 4] GIS Export")
print("-" * 40)

from geo_toolkit_indonesia.modules.gis_export import (
    to_geojson, to_kml,
    point_feature, linestring_feature, polygon_feature
)

# Create well location points
well_points = [
    point_feature(-6.200, 106.816, name="Well-Jakarta-01", operator="PT Pertamina EP", depth_m=2500),
    point_feature(-7.257, 112.752, name="Well-Surabaya-01", operator="PT Medco Energi", depth_m=3100),
    point_feature(-1.267, 116.829, name="Well-Balikpapan-01", operator="Total E&P", depth_m=4200),
]

# Create seismic survey line
survey_line = linestring_feature(
    [(-6.200, 106.800), (-6.450, 107.100), (-6.700, 107.450), (-7.000, 107.850)],
    name="Seismic Line SL-001",
    survey_type="2D Seismic",
    year=2023,
)

# Create exploration block polygon
block = polygon_feature(
    [(-6.0, 106.5), (-6.0, 107.5), (-7.5, 107.5), (-7.5, 106.5)],
    name="Block Jawa Barat",
    operator="PT Pertamina EP",
    status="Exploration",
    area_km2=16650,
)

all_features = well_points + [survey_line, block]

# GeoJSON export
gj_path = OUTPUT_DIR / "indonesia_geo_export.geojson"
to_geojson(all_features, output_path=gj_path)
print(f"  GeoJSON exported → {gj_path}")

# KML export
kml_path = OUTPUT_DIR / "indonesia_geo_export.kml"
to_kml(all_features, output_path=kml_path, document_name="Indonesia Exploration Assets")
print(f"  KML exported     → {kml_path}")


# ===========================================================================
# MODULE 5 – Visualization
# ===========================================================================
print("\n[MODULE 5] Visualization")
print("-" * 40)

from geo_toolkit_indonesia.modules.visualization import plot_survey_line, plot_borehole

# Survey line plot
survey_pts   = [(lat, lon) for _, lat, lon in survey_stations]
survey_labels = [name for name, _, _ in survey_stations]
sl_path = OUTPUT_DIR / "survey_line_plot.png"
fig = plot_survey_line(
    survey_pts,
    title="Seismic Survey Line – Jawa Barat Corridor",
    point_labels=survey_labels,
    output_path=str(sl_path),
    dpi=150,
)
print(f"  Survey line plot  → {sl_path}")

# Borehole log plot (synthetic + LAS curves)
depth = las.depth
curves = {
    "GR":   las.curves.get("GR",   np.full_like(depth, np.nan)),
    "RHOB": las.curves.get("RHOB", np.full_like(depth, np.nan)),
    "NPHI": las.curves.get("NPHI", np.full_like(depth, np.nan)),
    "RT":   las.curves.get("RT",   np.full_like(depth, np.nan)),
}
units = {"GR": "gAPI", "RHOB": "g/cc", "NPHI": "v/v", "RT": "Ωm"}
bh_path = OUTPUT_DIR / "borehole_log_plot.png"
fig2 = plot_borehole(
    depth,
    curves,
    title=f"Well Log – {las.well_name}  |  {las.field_name}",
    units=units,
    output_path=str(bh_path),
    dpi=150,
)
print(f"  Borehole log plot → {bh_path}")


# ===========================================================================
# Summary
# ===========================================================================
print("\n" + "=" * 60)
print("  All modules executed successfully.")
print(f"  Output files saved to: ./{OUTPUT_DIR}/")
print("=" * 60)
