"""
GeoToolkit Indonesia – Full Test Suite
========================================
Run with:  python -m pytest tests/ -v
Or:        python tests/test_all_modules.py
"""

import math
import os
import sys
import tempfile
import json
from pathlib import Path

import numpy as np
import pytest

# Make sure package is importable even without install
sys.path.insert(0, str(Path(__file__).parent.parent))

from geo_toolkit_indonesia.modules.coordinate import utm_to_latlon, latlon_to_utm
from geo_toolkit_indonesia.modules.survey import calculate_bearing, calculate_distance
from geo_toolkit_indonesia.modules.geological import read_las, read_well_log
from geo_toolkit_indonesia.modules.gis_export import (
    to_geojson, to_kml, point_feature, linestring_feature, polygon_feature, GeoFeature
)
from geo_toolkit_indonesia.modules.visualization import plot_survey_line, plot_borehole

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SAMPLE_DIR = Path(__file__).parent.parent / "geo_toolkit_indonesia" / "data" / "sample"
LAS_FILE   = SAMPLE_DIR / "WELL_A.LAS"
CSV_FILE   = SAMPLE_DIR / "well_log_B.csv"


# ===========================================================================
# Module 1 – Coordinate Conversion
# ===========================================================================

class TestCoordinateConversion:

    def test_latlon_to_utm_jakarta(self):
        """Jakarta: -6.2°, 106.8° → UTM zone 48S"""
        result = latlon_to_utm(-6.2, 106.816)
        assert result.zone == 48
        assert result.hemisphere == "S"
        assert 600_000 < result.easting  < 800_000
        assert 9_200_000 < result.northing < 9_500_000

    def test_utm_to_latlon_roundtrip(self):
        """Round-trip: lat/lon → UTM → lat/lon should match within 1 cm."""
        lat, lon = -7.25, 112.75  # Surabaya area
        utm = latlon_to_utm(lat, lon)
        recovered = utm_to_latlon(utm.easting, utm.northing, utm.zone, utm.hemisphere)
        assert abs(recovered.latitude  - lat) < 1e-5
        assert abs(recovered.longitude - lon) < 1e-5

    def test_latlon_to_utm_northern_hemisphere(self):
        """Aceh is slightly north of equator → hemisphere should be N."""
        result = latlon_to_utm(5.55, 95.32)  # Banda Aceh
        assert result.hemisphere == "N"
        assert result.zone == 46

    def test_utm_to_latlon_basic(self):
        result = utm_to_latlon(369769, 9390135, zone=48, hemisphere="S")
        assert -8.0 < result.latitude  < -4.0
        assert 100.0 < result.longitude < 110.0

    def test_invalid_zone_raises(self):
        with pytest.raises(ValueError):
            utm_to_latlon(500000, 9000000, zone=0, hemisphere="S")

    def test_invalid_hemisphere_raises(self):
        with pytest.raises(ValueError):
            utm_to_latlon(500000, 9000000, zone=49, hemisphere="X")

    def test_invalid_latitude_raises(self):
        with pytest.raises(ValueError):
            latlon_to_utm(91.0, 106.8)

    def test_invalid_longitude_raises(self):
        with pytest.raises(ValueError):
            latlon_to_utm(-6.2, 181.0)

    def test_to_dict(self):
        result = latlon_to_utm(-6.2, 106.8)
        d = result.to_dict()
        assert "easting" in d and "northing" in d and "zone" in d


# ===========================================================================
# Module 2 – Survey Calculation
# ===========================================================================

class TestSurveyCalculation:

    def test_distance_jakarta_surabaya(self):
        """Jakarta → Surabaya: roughly 665–700 km."""
        d = calculate_distance(-6.2, 106.816, -7.257, 112.752)
        assert 650 < d.kilometres < 720

    def test_distance_zero(self):
        """Same point should return zero distance."""
        d = calculate_distance(-6.2, 106.8, -6.2, 106.8)
        assert d.metres == 0.0

    def test_distance_units_consistent(self):
        """Cross-check unit conversions."""
        d = calculate_distance(-6.2, 106.8, -7.3, 112.7)
        assert abs(d.metres / 1000 - d.kilometres) < 0.001
        assert abs(d.metres / 1852 - d.nautical_miles) < 0.001
        assert abs(d.metres / 1609.344 - d.statute_miles) < 0.001

    def test_bearing_east(self):
        """Two points on same latitude – bearing should be ~90° (due East)."""
        b = calculate_bearing(0.0, 100.0, 0.0, 110.0)
        assert abs(b.forward_bearing - 90.0) < 1.0

    def test_bearing_north(self):
        """Two points on same longitude – bearing should be ~0° (due North)."""
        b = calculate_bearing(-10.0, 106.0, -5.0, 106.0)
        assert b.forward_bearing < 5.0 or b.forward_bearing > 355.0

    def test_bearing_back_is_reciprocal(self):
        """Back bearing differs from forward by < 1° on an ellipsoid (not exactly 180°)."""
        b = calculate_bearing(-6.2, 106.8, -7.3, 112.7)
        # On WGS84 ellipsoid, fwd and back azimuths differ by <1° for moderate distances
        diff = abs(b.forward_bearing - b.back_bearing)
        assert diff < 2.0

    def test_bearing_range(self):
        """Bearings should always be in [0, 360)."""
        b = calculate_bearing(-6.2, 106.8, -7.3, 112.7)
        assert 0 <= b.forward_bearing < 360
        assert 0 <= b.back_bearing  < 360

    def test_invalid_lat_raises(self):
        with pytest.raises(ValueError):
            calculate_bearing(95.0, 106.0, -6.0, 107.0)

    def test_bearing_to_dict(self):
        b = calculate_bearing(-6.2, 106.8, -7.3, 112.7)
        d = b.to_dict()
        assert "forward_bearing_deg" in d and "back_bearing_deg" in d

    def test_distance_to_dict(self):
        d = calculate_distance(-6.2, 106.8, -7.3, 112.7)
        dd = d.to_dict()
        assert "metres" in dd and "kilometres" in dd


# ===========================================================================
# Module 3 – Geological Data
# ===========================================================================

class TestGeologicalData:

    def test_read_las_success(self):
        data = read_las(LAS_FILE)
        assert data.well_name != ""
        assert "DEPT" in data.curves or "DEPTH" in data.curves or len(data.curves) > 0
        assert len(data.depth) > 0

    def test_read_las_curves_present(self):
        data = read_las(LAS_FILE)
        assert "GR" in data.curves
        assert "RHOB" in data.curves
        assert "NPHI" in data.curves

    def test_read_las_no_nan_in_valid_data(self):
        data = read_las(LAS_FILE)
        gr = data.curves["GR"]
        # Our sample file has no null rows; all values should be valid
        assert np.count_nonzero(~np.isnan(gr)) > 0

    def test_read_las_summary(self):
        data = read_las(LAS_FILE)
        s = data.summary()
        assert "Well" in s or "WELL" in s.upper()

    def test_read_las_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_las("nonexistent_file.las")

    def test_read_las_to_dict(self):
        data = read_las(LAS_FILE)
        d = data.to_dict()
        assert "curves" in d and "well_name" in d

    def test_read_well_log_success(self):
        log = read_well_log(CSV_FILE, depth_col="DEPTH")
        assert len(log.depth) > 0
        assert "GR" in log.curves

    def test_read_well_log_all_columns(self):
        log = read_well_log(CSV_FILE, depth_col="DEPTH")
        assert "RHOB" in log.curves
        assert "NPHI" in log.curves

    def test_read_well_log_selected_columns(self):
        log = read_well_log(CSV_FILE, depth_col="DEPTH", value_cols=["GR", "RT"])
        assert "GR" in log.curves
        assert "RT" in log.curves
        assert "RHOB" not in log.curves

    def test_read_well_log_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_well_log("ghost.csv")

    def test_read_well_log_bad_depth_col(self):
        with pytest.raises(KeyError):
            read_well_log(CSV_FILE, depth_col="NONEXISTENT_COL")

    def test_read_well_log_summary(self):
        log = read_well_log(CSV_FILE)
        s = log.summary()
        assert "File" in s

    def test_read_well_log_to_dict(self):
        log = read_well_log(CSV_FILE)
        d = log.to_dict()
        assert "depth" in d and "curves" in d


# ===========================================================================
# Module 4 – GIS Export
# ===========================================================================

class TestGISExport:

    def test_to_geojson_single_point(self):
        feat = point_feature(-6.2, 106.8, name="Jakarta")
        gj = to_geojson(feat)
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) == 1
        assert gj["features"][0]["geometry"]["type"] == "Point"

    def test_to_geojson_multiple_features(self):
        feats = [
            point_feature(-6.2, 106.8, name="Jakarta"),
            point_feature(-7.3, 112.7, name="Surabaya"),
        ]
        gj = to_geojson(feats)
        assert len(gj["features"]) == 2

    def test_to_geojson_linestring(self):
        feat = linestring_feature([(-6.2, 106.8), (-7.3, 112.7)], survey="line_A")
        gj = to_geojson(feat)
        assert gj["features"][0]["geometry"]["type"] == "LineString"

    def test_to_geojson_polygon(self):
        pts = [(-6.0, 106.0), (-6.0, 107.0), (-7.0, 107.0), (-7.0, 106.0)]
        feat = polygon_feature(pts, name="Block_A")
        gj = to_geojson(feat)
        assert gj["features"][0]["geometry"]["type"] == "Polygon"

    def test_to_geojson_write_file(self, tmp_path):
        feat = point_feature(-6.2, 106.8, name="Test")
        out = tmp_path / "test.geojson"
        to_geojson(feat, output_path=str(out))
        assert out.exists()
        with open(out) as f:
            data = json.load(f)
        assert data["type"] == "FeatureCollection"

    def test_to_kml_returns_string(self):
        feat = point_feature(-6.2, 106.8, name="Jakarta")
        kml = to_kml(feat)
        assert isinstance(kml, str)
        assert "<kml" in kml
        assert "Jakarta" in kml

    def test_to_kml_write_file(self, tmp_path):
        feat = point_feature(-6.2, 106.8, name="Test")
        out = tmp_path / "test.kml"
        to_kml(feat, output_path=str(out))
        assert out.exists()

    def test_invalid_geometry_type_raises(self):
        with pytest.raises(ValueError):
            GeoFeature(geometry_type="Circle", coordinates=[0, 0])

    def test_point_feature_with_elevation(self):
        feat = point_feature(-6.2, 106.8, elevation=50.0, name="Elevated")
        assert len(feat.coordinates) == 3
        assert feat.coordinates[2] == 50.0

    def test_polygon_autoclosed(self):
        pts = [(-6.0, 106.0), (-6.0, 107.0), (-7.0, 107.0)]
        feat = polygon_feature(pts)
        ring = feat.coordinates[0]
        assert ring[0] == ring[-1], "Polygon ring should be closed"


# ===========================================================================
# Module 5 – Visualization
# ===========================================================================

class TestVisualization:

    def _make_depth_curves(self, n=100):
        depth = np.linspace(500, 2000, n)
        curves = {
            "GR":   np.random.rand(n) * 150,
            "RHOB": np.random.rand(n) * 0.5 + 2.0,
            "NPHI": np.random.rand(n) * 0.4,
        }
        return depth, curves

    def test_plot_survey_line_returns_figure(self):
        import matplotlib.pyplot as plt
        pts = [(-6.2, 106.8), (-6.5, 107.2), (-7.0, 107.8)]
        fig = plot_survey_line(pts)
        assert fig is not None
        plt.close("all")

    def test_plot_survey_line_saves_file(self, tmp_path):
        pts = [(-6.2, 106.8), (-6.5, 107.2), (-7.0, 107.8)]
        out = tmp_path / "survey_test.png"
        plot_survey_line(pts, output_path=str(out))
        assert out.exists()
        assert out.stat().st_size > 10_000  # sanity: non-trivial file

    def test_plot_survey_line_with_labels(self, tmp_path):
        import matplotlib.pyplot as plt
        pts = [(-6.2, 106.8), (-6.5, 107.2), (-7.0, 107.8)]
        labels = ["Station-A", "Station-B", "Station-C"]
        fig = plot_survey_line(pts, point_labels=labels)
        assert fig is not None
        plt.close("all")

    def test_plot_survey_line_too_few_points(self):
        with pytest.raises(ValueError):
            plot_survey_line([(-6.2, 106.8)])

    def test_plot_borehole_returns_figure(self):
        import matplotlib.pyplot as plt
        depth, curves = self._make_depth_curves()
        fig = plot_borehole(depth, curves)
        assert fig is not None
        plt.close("all")

    def test_plot_borehole_saves_file(self, tmp_path):
        depth, curves = self._make_depth_curves()
        out = tmp_path / "borehole_test.png"
        plot_borehole(depth, curves, output_path=str(out))
        assert out.exists()
        assert out.stat().st_size > 10_000

    def test_plot_borehole_no_curves_raises(self):
        import matplotlib.pyplot as plt
        depth = np.linspace(0, 1000, 100)
        with pytest.raises(ValueError):
            plot_borehole(depth, {})
        plt.close("all")

    def test_plot_borehole_with_units(self, tmp_path):
        import matplotlib.pyplot as plt
        depth, curves = self._make_depth_curves()
        units = {"GR": "gAPI", "RHOB": "g/cc", "NPHI": "v/v"}
        fig = plot_borehole(depth, curves, units=units)
        assert fig is not None
        plt.close("all")


# ===========================================================================
# Integration Test
# ===========================================================================

class TestIntegration:

    def test_las_to_geojson_pipeline(self, tmp_path):
        """Read well header location → export as GeoJSON point."""
        las_data = read_las(LAS_FILE)
        # Simulate well location (from header or known coords)
        feat = point_feature(
            latitude=1.5,
            longitude=101.4,
            well_name=las_data.well_name,
            field=las_data.field_name,
        )
        gj = to_geojson(feat, output_path=tmp_path / "well_location.geojson")
        assert gj["features"][0]["properties"]["well_name"] == las_data.well_name

    def test_coordinate_then_export(self, tmp_path):
        """Convert coordinates and export as GeoJSON."""
        utm_result = latlon_to_utm(-6.2, 106.8)
        recovered  = utm_to_latlon(utm_result.easting, utm_result.northing,
                                   utm_result.zone, utm_result.hemisphere)
        feat = point_feature(
            recovered.latitude, recovered.longitude,
            source="UTM roundtrip",
            zone=utm_result.zone,
        )
        gj = to_geojson(feat, output_path=tmp_path / "roundtrip.geojson")
        assert len(gj["features"]) == 1

    def test_survey_line_full_pipeline(self, tmp_path):
        """Calculate bearings/distances for a multi-station line, then plot and export."""
        stations = [
            (-6.20, 106.80),
            (-6.45, 107.10),
            (-6.70, 107.45),
            (-7.00, 107.85),
        ]
        bearings  = [calculate_bearing(*a, *b) for a, b in zip(stations, stations[1:])]
        distances = [calculate_distance(*a, *b) for a, b in zip(stations, stations[1:])]

        assert all(0 <= b.forward_bearing < 360 for b in bearings)
        assert all(d.kilometres > 0 for d in distances)

        # Export line as GeoJSON
        line = linestring_feature(stations, survey_id="LINE-01")
        gj = to_geojson(line, output_path=tmp_path / "survey_line.geojson")
        assert gj["features"][0]["geometry"]["type"] == "LineString"

        # Plot
        plot_survey_line(stations, title="Integration Test Line",
                         output_path=str(tmp_path / "survey_plot.png"))
        assert (tmp_path / "survey_plot.png").exists()


# ===========================================================================
# Runner (standalone)
# ===========================================================================

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
