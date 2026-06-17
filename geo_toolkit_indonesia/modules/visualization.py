"""
Module 5: Visualization
========================
Publication-quality plots for survey lines and borehole/well-log data.

Functions:
    plot_survey_line(points, title, output_path, show)
    plot_borehole(depth, curves, title, output_path, show)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server / CI environments
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
import numpy as np

# ---------------------------------------------------------------------------
# Styling constants (McKinsey-style clean theme)
# ---------------------------------------------------------------------------

_PALETTE = {
    "primary":    "#0A2F5A",   # deep navy
    "secondary":  "#1565C0",   # medium blue
    "accent":     "#F57C00",   # amber
    "grid":       "#E0E0E0",   # light grey
    "background": "#FAFAFA",
    "text":       "#212121",
    "text_light": "#616161",
    "line":       "#1565C0",
    "waypoint":   "#F57C00",
    "curves": [
        "#1565C0", "#C62828", "#2E7D32", "#6A1B9A",
        "#E65100", "#00838F", "#4E342E", "#283593",
    ],
}

_FONT = {
    "family": "sans-serif",
    "title":  14,
    "label":  10,
    "tick":    8,
    "annot":   7,
}


def _apply_base_style(ax: plt.Axes) -> None:
    """Apply consistent clean styling to an Axes object."""
    ax.set_facecolor(_PALETTE["background"])
    ax.grid(True, color=_PALETTE["grid"], linewidth=0.6, linestyle="-", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#BDBDBD")
    ax.spines["bottom"].set_color("#BDBDBD")
    ax.tick_params(labelsize=_FONT["tick"], colors=_PALETTE["text_light"])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plot_survey_line(
    points: List[Tuple[float, float]],
    title: str = "Survey Line",
    point_labels: Optional[List[str]] = None,
    output_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize: Tuple[float, float] = (10, 8),
    dpi: int = 150,
) -> plt.Figure:
    """
    Plot a geographic survey line with labelled waypoints.

    Parameters
    ----------
    points : list of (lat, lon) tuples
        Survey stations in decimal degrees.
    title : str
        Plot title. Default: "Survey Line".
    point_labels : list[str], optional
        Labels for each point. Auto-numbered if None.
    output_path : str or Path, optional
        Save the figure to this path (.png, .pdf, .svg supported).
    show : bool
        Display the figure interactively. Default: False.
    figsize : tuple
        Figure size in inches. Default: (10, 8).
    dpi : int
        Output resolution. Default: 150.

    Returns
    -------
    matplotlib.figure.Figure

    Examples
    --------
    >>> pts = [(-6.2, 106.8), (-6.5, 107.2), (-7.0, 107.8)]
    >>> fig = plot_survey_line(pts, title="Seismic Line A", output_path="line_a.png")
    """
    if len(points) < 2:
        raise ValueError("At least 2 points are required to draw a survey line.")

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    labels = point_labels or [f"SP{i+1:03d}" for i in range(len(points))]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor("white")
    _apply_base_style(ax)

    # Survey line
    ax.plot(
        lons, lats,
        color=_PALETTE["line"],
        linewidth=2.0,
        solid_capstyle="round",
        solid_joinstyle="round",
        zorder=2,
        label="Survey Line",
    )

    # Direction arrow at midpoint
    if len(points) >= 2:
        mid = len(points) // 2
        dx = lons[mid] - lons[mid - 1]
        dy = lats[mid] - lats[mid - 1]
        ax.annotate(
            "",
            xy=(lons[mid], lats[mid]),
            xytext=(lons[mid] - dx * 0.01, lats[mid] - dy * 0.01),
            arrowprops=dict(arrowstyle="->", color=_PALETTE["secondary"], lw=1.5),
            zorder=3,
        )

    # Waypoints
    ax.scatter(
        lons, lats,
        s=60, color=_PALETTE["waypoint"],
        edgecolors="white", linewidths=1.0,
        zorder=4,
    )

    # Start / end markers
    ax.scatter(lons[0],  lats[0],  s=120, color="#2E7D32", marker="^",
               edgecolors="white", linewidths=1.0, zorder=5, label="Start")
    ax.scatter(lons[-1], lats[-1], s=120, color="#C62828", marker="s",
               edgecolors="white", linewidths=1.0, zorder=5, label="End")

    # Labels
    lat_range = max(lats) - min(lats) or 0.01
    lon_range = max(lons) - min(lons) or 0.01
    offset_lat = lat_range * 0.025
    offset_lon = lon_range * 0.015

    for i, (lat, lon, lbl) in enumerate(zip(lats, lons, labels)):
        ax.text(
            lon + offset_lon, lat + offset_lat, lbl,
            fontsize=_FONT["annot"],
            color=_PALETTE["text"],
            fontweight="bold" if i in (0, len(points) - 1) else "normal",
            path_effects=[pe.withStroke(linewidth=2, foreground="white")],
            zorder=6,
        )

    # Compute total distance in km (simple Euclidean approximation for label)
    total_km = _approx_line_length_km(lats, lons)

    ax.set_title(title, fontsize=_FONT["title"], fontweight="bold",
                 color=_PALETTE["primary"], pad=14)
    ax.set_xlabel("Longitude (°E)", fontsize=_FONT["label"], color=_PALETTE["text"])
    ax.set_ylabel("Latitude (°)", fontsize=_FONT["label"], color=_PALETTE["text"])

    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f°"))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f°"))

    # Info box
    info = (
        f"Stations : {len(points)}\n"
        f"Total length ≈ {total_km:.2f} km\n"
        f"Lat range : {min(lats):.4f}° – {max(lats):.4f}°\n"
        f"Lon range : {min(lons):.4f}° – {max(lons):.4f}°"
    )
    ax.text(
        0.02, 0.98, info,
        transform=ax.transAxes,
        fontsize=_FONT["annot"],
        verticalalignment="top",
        color=_PALETTE["text_light"],
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor=_PALETTE["grid"], alpha=0.85),
    )

    ax.legend(loc="lower right", fontsize=_FONT["annot"], framealpha=0.85)

    _add_branding(fig)
    fig.tight_layout()

    if output_path:
        _save_figure(fig, output_path, dpi)
    if show:
        plt.show()

    return fig


def plot_borehole(
    depth: Union[np.ndarray, List[float]],
    curves: Dict[str, Union[np.ndarray, List[float]]],
    title: str = "Borehole Log",
    units: Optional[Dict[str, str]] = None,
    output_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    figsize_per_track: Tuple[float, float] = (3.0, 10.0),
    dpi: int = 150,
    depth_label: str = "Depth (m)",
    invert_depth: bool = True,
) -> plt.Figure:
    """
    Plot a multi-track borehole / well-log display.

    Each curve in `curves` gets its own vertical track, sharing a common
    depth axis on the left. The layout mirrors standard petrophysical log
    displays (GR | RHOB | NPHI | RT | etc.).

    Parameters
    ----------
    depth : array-like
        Depth values (metres). Typically MD or TVD.
    curves : dict[str, array-like]
        Curve name → data array. Must match length of `depth`.
    title : str
        Plot title. Default: "Borehole Log".
    units : dict[str, str], optional
        Curve name → unit string (e.g. {"GR": "gAPI", "RHOB": "g/cc"}).
    output_path : str or Path, optional
        Save the figure to this path.
    show : bool
        Display interactively. Default: False.
    figsize_per_track : tuple
        Width × height per track in inches. Default: (3.0, 10.0).
    dpi : int
        Output resolution. Default: 150.
    depth_label : str
        Y-axis label. Default: "Depth (m)".
    invert_depth : bool
        Invert Y-axis so depth increases downward. Default: True.

    Returns
    -------
    matplotlib.figure.Figure

    Examples
    --------
    >>> depth = np.arange(0, 2000, 0.5)
    >>> curves = {"GR": np.random.rand(4000)*150, "RHOB": np.random.rand(4000)+1.8}
    >>> fig = plot_borehole(depth, curves, title="Well-A", output_path="well_a.png")
    """
    depth = np.asarray(depth, dtype=float)
    n_tracks = len(curves)
    if n_tracks == 0:
        raise ValueError("At least one curve must be provided.")

    units = units or {}
    curve_names = list(curves.keys())
    total_width = figsize_per_track[0] * n_tracks + 1.0  # +1 for depth track
    fig_height = figsize_per_track[1]

    fig = plt.figure(figsize=(total_width, fig_height), dpi=dpi)
    fig.patch.set_facecolor("white")

    # GridSpec: col 0 = depth axis, col 1..n = curve tracks
    gs = GridSpec(1, n_tracks + 1, figure=fig, width_ratios=[0.6] + [1.0] * n_tracks,
                  wspace=0.0)

    # ---- Depth axis (leftmost panel) ----
    ax_depth = fig.add_subplot(gs[0, 0])
    ax_depth.set_facecolor(_PALETTE["background"])
    ax_depth.set_xlim(0, 1)
    ax_depth.xaxis.set_visible(False)
    ax_depth.set_ylabel(depth_label, fontsize=_FONT["label"], color=_PALETTE["text"])
    ax_depth.tick_params(labelsize=_FONT["tick"], colors=_PALETTE["text_light"])
    ax_depth.spines["top"].set_visible(False)
    ax_depth.spines["right"].set_visible(False)
    ax_depth.spines["bottom"].set_visible(False)
    ax_depth.spines["left"].set_color("#BDBDBD")
    if invert_depth:
        ax_depth.set_ylim(np.nanmax(depth), np.nanmin(depth))
    else:
        ax_depth.set_ylim(np.nanmin(depth), np.nanmax(depth))
    ax_depth.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.0f}"))
    ax_depth.grid(True, color=_PALETTE["grid"], linewidth=0.4, axis="y", zorder=0)

    # ---- Curve tracks ----
    axes = []
    for i, name in enumerate(curve_names):
        arr = np.asarray(curves[name], dtype=float)
        color = _PALETTE["curves"][i % len(_PALETTE["curves"])]
        unit_str = units.get(name, "")
        track_label = f"{name}\n[{unit_str}]" if unit_str else name

        ax = fig.add_subplot(gs[0, i + 1], sharey=ax_depth)
        _apply_base_style(ax)
        ax.spines["left"].set_visible(False)

        # Fill area between curve and left edge for GR-like tracks
        valid_mask = ~np.isnan(arr)
        if valid_mask.any():
            x_vals = arr[valid_mask]
            y_vals = depth[valid_mask]
            ax.plot(x_vals, y_vals, color=color, linewidth=0.8, zorder=2)
            ax.fill_betweenx(y_vals, x_vals, np.nanmin(x_vals),
                             alpha=0.12, color=color, zorder=1)

        # Track header
        ax.set_title(track_label, fontsize=_FONT["label"] - 1,
                     color=color, fontweight="bold", pad=6)
        ax.tick_params(labelleft=False, labelsize=_FONT["tick"])
        ax.xaxis.set_tick_params(labelsize=_FONT["tick"], labelcolor=_PALETTE["text_light"])

        # Stat annotation
        if valid_mask.any():
            stat_txt = (
                f"min: {np.nanmin(arr):.2f}\n"
                f"max: {np.nanmax(arr):.2f}\n"
                f"avg: {np.nanmean(arr):.2f}"
            )
            ax.text(
                0.98, 0.01, stat_txt,
                transform=ax.transAxes,
                fontsize=_FONT["annot"] - 1,
                ha="right", va="bottom",
                color=_PALETTE["text_light"],
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor=_PALETTE["grid"], alpha=0.8),
            )

        axes.append(ax)

    fig.suptitle(title, fontsize=_FONT["title"], fontweight="bold",
                 color=_PALETTE["primary"], y=1.01)

    _add_branding(fig)
    fig.tight_layout()

    if output_path:
        _save_figure(fig, output_path, dpi)
    if show:
        plt.show()

    return fig


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _approx_line_length_km(lats: list, lons: list) -> float:
    """Very fast great-circle approximation (adequate for label display)."""
    R = 6371.0
    total = 0.0
    for i in range(1, len(lats)):
        dlat = np.radians(lats[i] - lats[i - 1])
        dlon = np.radians(lons[i] - lons[i - 1])
        a = (np.sin(dlat / 2) ** 2
             + np.cos(np.radians(lats[i - 1]))
             * np.cos(np.radians(lats[i]))
             * np.sin(dlon / 2) ** 2)
        total += R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return total


def _save_figure(fig: plt.Figure, output_path: Union[str, Path], dpi: int) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=dpi, bbox_inches="tight",
                facecolor="white", edgecolor="none")


def _add_branding(fig: plt.Figure) -> None:
    """Add a subtle footer branding."""
    fig.text(
        0.99, 0.005,
        "GeoToolkit Indonesia v1.0",
        ha="right", va="bottom",
        fontsize=6,
        color="#BDBDBD",
        fontstyle="italic",
    )
