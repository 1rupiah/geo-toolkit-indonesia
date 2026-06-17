"""
Module 4: GIS Export
=====================
Export geoscience data to standard GIS interchange formats.

Supported formats:
    - GeoJSON (RFC 7946) – compatible with QGIS, ArcGIS, MapboxGL, Leaflet
    - KML 2.2            – compatible with Google Earth, QGIS

Functions:
    to_geojson(features, output_path, properties_list)
    to_kml(features, output_path, name, description)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree as ET
from xml.dom import minidom


# ---------------------------------------------------------------------------
# Data class for a GIS feature
# ---------------------------------------------------------------------------

@dataclass
class GeoFeature:
    """
    A single geographic feature for export.

    Parameters
    ----------
    geometry_type : str
        "Point", "LineString", "Polygon", "MultiPoint", "MultiLineString".
    coordinates : list
        GeoJSON-style coordinate structure.
        Point          : [lon, lat] or [lon, lat, elev]
        LineString     : [[lon, lat], ...]
        Polygon        : [[[lon, lat], ...]]  (first ring = exterior)
    properties : dict, optional
        Arbitrary key-value metadata (name, well_id, depth, etc.)
    """
    geometry_type: str
    coordinates: list
    properties: Dict[str, Any] = field(default_factory=dict)

    VALID_TYPES = {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString"}

    def __post_init__(self):
        if self.geometry_type not in self.VALID_TYPES:
            raise ValueError(
                f"geometry_type must be one of {self.VALID_TYPES}, "
                f"got '{self.geometry_type}'."
            )

    def to_geojson_feature(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": self.geometry_type,
                "coordinates": self.coordinates,
            },
            "properties": self.properties,
        }


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def point_feature(
    latitude: float,
    longitude: float,
    elevation: Optional[float] = None,
    **properties,
) -> GeoFeature:
    """Create a Point GeoFeature from lat/lon."""
    coords = [longitude, latitude] if elevation is None else [longitude, latitude, elevation]
    return GeoFeature(geometry_type="Point", coordinates=coords, properties=dict(properties))


def linestring_feature(
    points: List[Tuple[float, float]],
    **properties,
) -> GeoFeature:
    """Create a LineString GeoFeature from a list of (lat, lon) tuples."""
    coords = [[lon, lat] for lat, lon in points]
    return GeoFeature(geometry_type="LineString", coordinates=coords, properties=dict(properties))


def polygon_feature(
    points: List[Tuple[float, float]],
    **properties,
) -> GeoFeature:
    """
    Create a Polygon GeoFeature from a list of (lat, lon) tuples.
    The ring is automatically closed if not already.
    """
    coords = [[lon, lat] for lat, lon in points]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return GeoFeature(geometry_type="Polygon", coordinates=[coords], properties=dict(properties))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def to_geojson(
    features: Union[GeoFeature, List[GeoFeature]],
    output_path: Optional[Union[str, Path]] = None,
    indent: int = 2,
) -> dict:
    """
    Export one or more GeoFeature objects to a GeoJSON FeatureCollection.

    Parameters
    ----------
    features : GeoFeature or list[GeoFeature]
        Features to include in the collection.
    output_path : str or Path, optional
        If provided, writes the GeoJSON to this file. Returns the dict
        regardless.
    indent : int
        JSON indentation for the output file. Default: 2.

    Returns
    -------
    dict
        A valid GeoJSON FeatureCollection dict (RFC 7946).

    Examples
    --------
    >>> pts = [point_feature(-6.2, 106.8, name="Jakarta"),
    ...        point_feature(-7.3, 112.7, name="Surabaya")]
    >>> geojson = to_geojson(pts, "cities.geojson")
    """
    if isinstance(features, GeoFeature):
        features = [features]

    collection = {
        "type": "FeatureCollection",
        "features": [f.to_geojson_feature() for f in features],
    }

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(collection, fh, indent=indent, ensure_ascii=False)

    return collection


def to_kml(
    features: Union[GeoFeature, List[GeoFeature]],
    output_path: Optional[Union[str, Path]] = None,
    document_name: str = "GeoToolkit Indonesia Export",
    document_description: str = "Generated by GeoToolkit Indonesia",
    name_property: str = "name",
    description_property: str = "description",
) -> str:
    """
    Export one or more GeoFeature objects to a KML 2.2 document.

    Parameters
    ----------
    features : GeoFeature or list[GeoFeature]
        Features to export.
    output_path : str or Path, optional
        If provided, writes the KML to this file. Returns the string
        regardless.
    document_name : str
        KML <Document> name element.
    document_description : str
        KML <Document> description element.
    name_property : str
        Feature property key to use as the KML <name> for each Placemark.
        Default: "name".
    description_property : str
        Feature property key to use as the KML <description>.

    Returns
    -------
    str
        Pretty-printed KML XML string.

    Examples
    --------
    >>> kml_str = to_kml(pts, "export.kml", document_name="Indonesia Wells")
    """
    if isinstance(features, GeoFeature):
        features = [features]

    kml_ns = "http://www.opengis.net/kml/2.2"
    root = ET.Element("kml", xmlns=kml_ns)
    doc = ET.SubElement(root, "Document")
    ET.SubElement(doc, "name").text = document_name
    ET.SubElement(doc, "description").text = document_description

    for feat in features:
        pm = ET.SubElement(doc, "Placemark")
        ET.SubElement(pm, "name").text = str(
            feat.properties.get(name_property, feat.geometry_type)
        )
        desc_val = feat.properties.get(description_property, "")
        if not desc_val:
            # Build a simple HTML table from all properties
            rows = "".join(
                f"<tr><td><b>{k}</b></td><td>{v}</td></tr>"
                for k, v in feat.properties.items()
            )
            desc_val = f"<table>{rows}</table>"
        ET.SubElement(pm, "description").text = desc_val

        _add_kml_geometry(pm, feat)

    raw_xml = ET.tostring(root, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(raw_xml).toprettyxml(indent="  ")
    # Remove redundant first line from minidom
    pretty_lines = pretty.splitlines()[1:]
    kml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(pretty_lines)

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(kml_str)

    return kml_str


# ---------------------------------------------------------------------------
# Internal KML geometry builder
# ---------------------------------------------------------------------------

def _coords_to_kml(coords_list: list, altitude: float = 0) -> str:
    """Convert a flat list of [lon, lat] or [lon, lat, elev] to KML coord string."""
    parts = []
    for c in coords_list:
        lon, lat = c[0], c[1]
        elev = c[2] if len(c) > 2 else altitude
        parts.append(f"{lon},{lat},{elev}")
    return " ".join(parts)


def _add_kml_geometry(parent: ET.Element, feat: GeoFeature) -> None:
    """Append the appropriate KML geometry element to parent."""
    gt = feat.geometry_type
    coords = feat.coordinates

    if gt == "Point":
        geom = ET.SubElement(parent, "Point")
        lon, lat = coords[0], coords[1]
        elev = coords[2] if len(coords) > 2 else 0
        ET.SubElement(geom, "coordinates").text = f"{lon},{lat},{elev}"

    elif gt == "LineString":
        geom = ET.SubElement(parent, "LineString")
        ET.SubElement(geom, "tessellate").text = "1"
        ET.SubElement(geom, "coordinates").text = _coords_to_kml(coords)

    elif gt == "Polygon":
        geom = ET.SubElement(parent, "Polygon")
        ET.SubElement(geom, "tessellate").text = "1"
        outer = ET.SubElement(geom, "outerBoundaryIs")
        ring = ET.SubElement(outer, "LinearRing")
        ET.SubElement(ring, "coordinates").text = _coords_to_kml(coords[0])
        for inner_ring in coords[1:]:
            inner = ET.SubElement(geom, "innerBoundaryIs")
            lr = ET.SubElement(inner, "LinearRing")
            ET.SubElement(lr, "coordinates").text = _coords_to_kml(inner_ring)

    elif gt == "MultiPoint":
        multi = ET.SubElement(parent, "MultiGeometry")
        for pt in coords:
            p = ET.SubElement(multi, "Point")
            lon, lat = pt[0], pt[1]
            elev = pt[2] if len(pt) > 2 else 0
            ET.SubElement(p, "coordinates").text = f"{lon},{lat},{elev}"

    elif gt == "MultiLineString":
        multi = ET.SubElement(parent, "MultiGeometry")
        for line in coords:
            ls = ET.SubElement(multi, "LineString")
            ET.SubElement(ls, "tessellate").text = "1"
            ET.SubElement(ls, "coordinates").text = _coords_to_kml(line)
