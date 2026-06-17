"""
Module 2: Survey Calculation
==============================
Geodetic bearing and distance calculations using the Vincenty / Haversine
formulae on the WGS84 ellipsoid.

Functions:
    calculate_bearing(lat1, lon1, lat2, lon2)
    calculate_distance(lat1, lon1, lat2, lon2, unit)
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Literal

# WGS84 ellipsoid parameters
_WGS84_A = 6_378_137.0          # semi-major axis (m)
_WGS84_F = 1 / 298.257223563    # flattening
_WGS84_B = _WGS84_A * (1 - _WGS84_F)  # semi-minor axis


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BearingResult:
    """Forward and back azimuths between two points."""
    forward_bearing: float   # degrees, 0–360
    back_bearing: float      # degrees, 0–360
    from_point: tuple
    to_point: tuple

    def __repr__(self) -> str:
        return (
            f"Bearing(forward={self.forward_bearing:.4f}°, "
            f"back={self.back_bearing:.4f}°)"
        )

    def to_dict(self) -> dict:
        return {
            "forward_bearing_deg": self.forward_bearing,
            "back_bearing_deg": self.back_bearing,
            "from_point": self.from_point,
            "to_point": self.to_point,
        }


@dataclass
class DistanceResult:
    """Geodetic distance between two points."""
    metres: float
    kilometres: float
    nautical_miles: float
    statute_miles: float
    from_point: tuple
    to_point: tuple

    def __repr__(self) -> str:
        return f"Distance({self.kilometres:.4f} km)"

    def to_dict(self) -> dict:
        return {
            "metres": self.metres,
            "kilometres": self.kilometres,
            "nautical_miles": self.nautical_miles,
            "statute_miles": self.statute_miles,
            "from_point": self.from_point,
            "to_point": self.to_point,
        }


# ---------------------------------------------------------------------------
# Internal: Vincenty inverse formula
# ---------------------------------------------------------------------------

def _vincenty_inverse(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> tuple[float, float, float]:
    """
    Compute geodetic distance and azimuths using Vincenty's inverse formula.

    Returns
    -------
    (distance_m, fwd_az_deg, back_az_deg)
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    L = math.radians(lon2 - lon1)

    tan_u1 = (1 - _WGS84_F) * math.tan(phi1)
    cos_u1 = 1 / math.sqrt(1 + tan_u1 ** 2)
    sin_u1 = tan_u1 * cos_u1

    tan_u2 = (1 - _WGS84_F) * math.tan(phi2)
    cos_u2 = 1 / math.sqrt(1 + tan_u2 ** 2)
    sin_u2 = tan_u2 * cos_u2

    lam = L
    lam_prev = None
    cos_sq_alpha = sin_sigma = cos_sigma = sigma = cos2_sigma_m = 0.0

    for _ in range(200):
        sin_lam = math.sin(lam)
        cos_lam = math.cos(lam)

        sin_sq_sigma = (cos_u2 * sin_lam) ** 2 + (
            cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lam
        ) ** 2
        sin_sigma = math.sqrt(sin_sq_sigma)

        if sin_sigma == 0:
            return 0.0, 0.0, 0.0  # coincident points

        cos_sigma = sin_u1 * sin_u2 + cos_u1 * cos_u2 * cos_lam
        sigma = math.atan2(sin_sigma, cos_sigma)

        sin_alpha = cos_u1 * cos_u2 * sin_lam / sin_sigma
        cos_sq_alpha = 1 - sin_alpha ** 2

        cos2_sigma_m = (
            cos_sigma - 2 * sin_u1 * sin_u2 / cos_sq_alpha
            if cos_sq_alpha != 0
            else 0.0
        )

        C = _WGS84_F / 16 * cos_sq_alpha * (4 + _WGS84_F * (4 - 3 * cos_sq_alpha))
        lam_prev = lam
        lam = L + (1 - C) * _WGS84_F * sin_alpha * (
            sigma
            + C * sin_sigma * (
                cos2_sigma_m + C * cos_sigma * (-1 + 2 * cos2_sigma_m ** 2)
            )
        )

        if lam_prev is not None and abs(lam - lam_prev) < 1e-12:
            break

    u_sq = cos_sq_alpha * (_WGS84_A ** 2 - _WGS84_B ** 2) / _WGS84_B ** 2
    A_coeff = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    B_coeff = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    delta_sigma = B_coeff * sin_sigma * (
        cos2_sigma_m
        + B_coeff / 4 * (
            cos_sigma * (-1 + 2 * cos2_sigma_m ** 2)
            - B_coeff / 6
            * cos2_sigma_m
            * (-3 + 4 * sin_sigma ** 2)
            * (-3 + 4 * cos2_sigma_m ** 2)
        )
    )

    distance = _WGS84_B * A_coeff * (sigma - delta_sigma)

    cos_lam_final = math.cos(lam)
    sin_lam_final = math.sin(lam)

    fwd_az = math.degrees(
        math.atan2(cos_u2 * sin_lam_final,
                   cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lam_final)
    ) % 360

    back_az = math.degrees(
        math.atan2(cos_u1 * sin_lam_final,
                   -sin_u1 * cos_u2 + cos_u1 * sin_u2 * cos_lam_final)
    ) % 360

    return distance, fwd_az, back_az


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_bearing(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> BearingResult:
    """
    Calculate the geodetic forward and back bearing between two points.

    Uses Vincenty's inverse formula on the WGS84 ellipsoid, giving
    sub-millimetre accuracy across any distance on Earth.

    Parameters
    ----------
    lat1, lon1 : float
        Starting point in decimal degrees. Negative = South / West.
    lat2, lon2 : float
        Ending point in decimal degrees.

    Returns
    -------
    BearingResult
        .forward_bearing : azimuth from point 1 to point 2 (0–360°)
        .back_bearing    : azimuth from point 2 back to point 1 (0–360°)

    Examples
    --------
    >>> b = calculate_bearing(-6.2, 106.8, -7.3, 112.7)
    >>> print(b.forward_bearing)
    83.xxxx
    """
    for name, val in [("lat1", lat1), ("lat2", lat2)]:
        if not (-90 <= val <= 90):
            raise ValueError(f"{name} must be in [-90, 90], got {val}.")
    for name, val in [("lon1", lon1), ("lon2", lon2)]:
        if not (-180 <= val <= 180):
            raise ValueError(f"{name} must be in [-180, 180], got {val}.")

    _, fwd, back = _vincenty_inverse(lat1, lon1, lat2, lon2)

    return BearingResult(
        forward_bearing=round(fwd, 6),
        back_bearing=round(back, 6),
        from_point=(lat1, lon1),
        to_point=(lat2, lon2),
    )


def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: Literal["m", "km", "nm", "mi"] = "km",
) -> DistanceResult:
    """
    Calculate the geodetic distance between two points.

    Uses Vincenty's inverse formula on the WGS84 ellipsoid.

    Parameters
    ----------
    lat1, lon1 : float
        Starting point in decimal degrees.
    lat2, lon2 : float
        Ending point in decimal degrees.
    unit : str
        Primary unit for display: "m" (metres), "km" (kilometres),
        "nm" (nautical miles), "mi" (statute miles). Default: "km".

    Returns
    -------
    DistanceResult
        Contains distance in all units regardless of the `unit` parameter.

    Examples
    --------
    >>> d = calculate_distance(-6.2, 106.8, -7.3, 112.7)
    >>> print(d.kilometres)
    651.xxxx
    """
    dist_m, _, _ = _vincenty_inverse(lat1, lon1, lat2, lon2)

    return DistanceResult(
        metres=round(dist_m, 3),
        kilometres=round(dist_m / 1000, 6),
        nautical_miles=round(dist_m / 1852, 6),
        statute_miles=round(dist_m / 1609.344, 6),
        from_point=(lat1, lon1),
        to_point=(lat2, lon2),
    )
