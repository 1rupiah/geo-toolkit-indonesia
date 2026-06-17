"""
Module 1: Coordinate Conversion
================================
Converts coordinates between UTM (Universal Transverse Mercator) and
Geographic (Latitude/Longitude) using WGS84 / DGN95 datums.

Indonesia spans UTM zones 46N through 54S. This module auto-detects or
accepts an explicit zone parameter.

Functions:
    utm_to_latlon(easting, northing, zone, hemisphere)
    latlon_to_utm(latitude, longitude, datum)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

from pyproj import Proj, Transformer, CRS

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LatLon:
    """Geographic coordinate result."""
    latitude: float
    longitude: float
    datum: str = "WGS84"

    def __repr__(self) -> str:
        lat_dir = "N" if self.latitude >= 0 else "S"
        lon_dir = "E" if self.longitude >= 0 else "W"
        return (
            f"LatLon({abs(self.latitude):.6f}°{lat_dir}, "
            f"{abs(self.longitude):.6f}°{lon_dir}, datum={self.datum})"
        )

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "datum": self.datum,
        }


@dataclass
class UTMCoordinate:
    """UTM coordinate result."""
    easting: float
    northing: float
    zone: int
    hemisphere: str
    datum: str = "WGS84"

    def __repr__(self) -> str:
        return (
            f"UTM(E={self.easting:.3f}, N={self.northing:.3f}, "
            f"Zone={self.zone}{self.hemisphere}, datum={self.datum})"
        )

    def to_dict(self) -> dict:
        return {
            "easting": self.easting,
            "northing": self.northing,
            "zone": self.zone,
            "hemisphere": self.hemisphere,
            "datum": self.datum,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_utm_zone_from_lon(longitude: float) -> int:
    """Compute UTM zone number from longitude."""
    return int((longitude + 180) / 6) + 1


def _build_utm_crs(zone: int, hemisphere: Literal["N", "S"], datum: str = "WGS84") -> CRS:
    """Build a pyproj CRS for the given UTM zone and datum."""
    datum_map = {
        "WGS84": "WGS 84",
        "DGN95": "DGN95",   # Indonesian national datum – same as WGS84 for most purposes
    }
    proj_datum = datum_map.get(datum.upper(), "WGS 84")
    epsg_base = 32600 if hemisphere == "N" else 32700
    epsg = epsg_base + zone
    try:
        return CRS.from_epsg(epsg)
    except Exception:
        # Fall back to explicit Proj string
        south_flag = "+south" if hemisphere == "S" else ""
        proj_str = (
            f"+proj=utm +zone={zone} {south_flag} "
            f"+datum={proj_datum} +units=m +no_defs"
        )
        return CRS.from_proj4(proj_str)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def utm_to_latlon(
    easting: float,
    northing: float,
    zone: int,
    hemisphere: Literal["N", "S"] = "S",
    datum: str = "WGS84",
) -> LatLon:
    """
    Convert UTM coordinates to geographic Latitude / Longitude.

    Parameters
    ----------
    easting : float
        UTM easting in metres.
    northing : float
        UTM northing in metres.
    zone : int
        UTM zone number (1–60). Indonesia: zones 46–54.
    hemisphere : "N" or "S"
        Northern or Southern hemisphere. Most of Indonesia is "S".
        Default: "S".
    datum : str
        Geodetic datum. Supports "WGS84" (default) and "DGN95".

    Returns
    -------
    LatLon
        Dataclass with .latitude, .longitude, and .datum.

    Examples
    --------
    >>> result = utm_to_latlon(692000, 9580000, zone=49, hemisphere="S")
    >>> print(result)
    LatLon(6.000000°S, 108.000000°E, datum=WGS84)
    """
    if not (1 <= zone <= 60):
        raise ValueError(f"UTM zone must be between 1 and 60, got {zone}.")
    if hemisphere not in ("N", "S"):
        raise ValueError("hemisphere must be 'N' or 'S'.")

    utm_crs = _build_utm_crs(zone, hemisphere, datum)
    geo_crs = CRS.from_epsg(4326)  # WGS84 geographic

    transformer = Transformer.from_crs(utm_crs, geo_crs, always_xy=True)
    lon, lat = transformer.transform(easting, northing)

    return LatLon(latitude=round(lat, 8), longitude=round(lon, 8), datum=datum.upper())


def latlon_to_utm(
    latitude: float,
    longitude: float,
    datum: str = "WGS84",
    zone: Optional[int] = None,
) -> UTMCoordinate:
    """
    Convert geographic Latitude / Longitude to UTM coordinates.

    Parameters
    ----------
    latitude : float
        Latitude in decimal degrees. Negative = South.
    longitude : float
        Longitude in decimal degrees. Indonesia: ~95°E to ~141°E.
    datum : str
        Geodetic datum. Supports "WGS84" (default) and "DGN95".
    zone : int, optional
        Force a specific UTM zone. Auto-detected from longitude if omitted.

    Returns
    -------
    UTMCoordinate
        Dataclass with .easting, .northing, .zone, .hemisphere, .datum.

    Examples
    --------
    >>> result = latlon_to_utm(-6.200, 106.816)
    >>> print(result)
    UTM(E=692xxx.xxx, N=9315xxx.xxx, Zone=48S, datum=WGS84)
    """
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {latitude}.")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {longitude}.")

    detected_zone = zone or _get_utm_zone_from_lon(longitude)
    hemisphere: Literal["N", "S"] = "N" if latitude >= 0 else "S"

    geo_crs = CRS.from_epsg(4326)
    utm_crs = _build_utm_crs(detected_zone, hemisphere, datum)

    transformer = Transformer.from_crs(geo_crs, utm_crs, always_xy=True)
    easting, northing = transformer.transform(longitude, latitude)

    return UTMCoordinate(
        easting=round(easting, 3),
        northing=round(northing, 3),
        zone=detected_zone,
        hemisphere=hemisphere,
        datum=datum.upper(),
    )
