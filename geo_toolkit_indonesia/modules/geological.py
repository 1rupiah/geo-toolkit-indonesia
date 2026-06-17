"""
Module 3: Geological Data
==========================
Readers for industry-standard well-log formats:
    - LAS 2.0 / 3.0  (Log ASCII Standard, via lasio)
    - CSV-based well-log tables (generic columnar format)

Functions:
    read_las(filepath, null_value)
    read_well_log(filepath, depth_col, value_cols, delimiter)
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import lasio
import numpy as np

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CurveInfo:
    """Metadata for a single LAS curve."""
    mnemonic: str
    unit: str
    description: str

    def __repr__(self) -> str:
        return f"Curve({self.mnemonic} [{self.unit}]: {self.description})"


@dataclass
class LASData:
    """
    Parsed LAS file container.

    Attributes
    ----------
    well_name : str
    field_name : str
    curves : dict[str, np.ndarray]
        Curve data keyed by mnemonic, nulls replaced with np.nan.
    curve_info : list[CurveInfo]
        Metadata per curve.
    depth : np.ndarray
        The depth curve (DEPT or DEPTH mnemonic).
    units : dict[str, str]
        Unit string per mnemonic.
    header : dict
        Full LAS header sections.
    """
    well_name: str
    field_name: str
    curves: Dict[str, np.ndarray]
    curve_info: List[CurveInfo]
    depth: np.ndarray
    units: Dict[str, str]
    header: dict
    filepath: str

    def summary(self) -> str:
        lines = [
            f"Well     : {self.well_name}",
            f"Field    : {self.field_name}",
            f"File     : {self.filepath}",
            f"Depth    : {self.depth.min():.2f} – {self.depth.max():.2f} m ({len(self.depth)} samples)",
            f"Curves   : {len(self.curves)}",
        ]
        for ci in self.curve_info:
            arr = self.curves.get(ci.mnemonic, np.array([]))
            valid = np.count_nonzero(~np.isnan(arr))
            lines.append(f"  {ci.mnemonic:<12} [{ci.unit:<6}]  {valid}/{len(arr)} valid – {ci.description}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "well_name": self.well_name,
            "field_name": self.field_name,
            "curves": {k: v.tolist() for k, v in self.curves.items()},
            "depth_range": [float(self.depth.min()), float(self.depth.max())],
            "num_samples": len(self.depth),
            "curve_mnemonics": list(self.curves.keys()),
        }


@dataclass
class WellLogData:
    """
    Parsed well-log CSV container.

    Attributes
    ----------
    depth : np.ndarray
    curves : dict[str, np.ndarray]
    columns : list[str]
    filepath : str
    num_rows : int
    """
    depth: np.ndarray
    curves: Dict[str, np.ndarray]
    columns: List[str]
    filepath: str
    num_rows: int

    def summary(self) -> str:
        lines = [
            f"File     : {self.filepath}",
            f"Rows     : {self.num_rows}",
            f"Depth    : {self.depth.min():.2f} – {self.depth.max():.2f}",
            f"Columns  : {', '.join(self.columns)}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "depth": self.depth.tolist(),
            "curves": {k: v.tolist() for k, v in self.curves.items()},
            "columns": self.columns,
            "num_rows": self.num_rows,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_las(
    filepath: Union[str, Path],
    null_value: float = -9999.25,
    encoding: str = "utf-8",
) -> LASData:
    """
    Read a LAS 2.0 or 3.0 file and return a structured LASData object.

    Parameters
    ----------
    filepath : str or Path
        Path to the .las file.
    null_value : float
        Null sentinel to replace with np.nan. Default: -9999.25.
    encoding : str
        File encoding. Default: "utf-8". Try "latin-1" for older files.

    Returns
    -------
    LASData
        Parsed well data with curves, depth array, header, and metadata.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file cannot be parsed as a valid LAS file.

    Examples
    --------
    >>> data = read_las("well_A.las")
    >>> print(data.summary())
    >>> gr = data.curves["GR"]
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"LAS file not found: {filepath}")
    if path.suffix.lower() not in (".las", ".LAS"):
        raise ValueError(f"Expected a .las file, got: {path.suffix}")

    try:
        las = lasio.read(str(path), encoding=encoding)
    except Exception as exc:
        raise ValueError(f"Failed to parse LAS file '{filepath}': {exc}") from exc

    # Extract curves, replace nulls with nan
    curves: Dict[str, np.ndarray] = {}
    curve_info: List[CurveInfo] = []
    units: Dict[str, str] = {}

    for curve in las.curves:
        arr = np.array(curve.data, dtype=float)
        arr[arr == null_value] = np.nan
        curves[curve.mnemonic] = arr
        curve_info.append(CurveInfo(
            mnemonic=curve.mnemonic,
            unit=curve.unit or "",
            description=curve.descr or "",
        ))
        units[curve.mnemonic] = curve.unit or ""

    # Identify depth curve
    depth_mnemonics = ["DEPT", "DEPTH", "MD", "TVD", "TDEP"]
    depth_key = next((m for m in depth_mnemonics if m in curves), None)
    if depth_key is None and curves:
        depth_key = list(curves.keys())[0]
    depth = curves.get(depth_key, np.array([]))

    # Extract header metadata
    well_name = _safe_header(las, "WELL", "Unknown Well")
    field_name = _safe_header(las, "FLD", "") or _safe_header(las, "FIELD", "Unknown Field")

    header = {
        "well": {k: str(v.value) for k, v in las.well.items()},
    }

    return LASData(
        well_name=well_name,
        field_name=field_name,
        curves=curves,
        curve_info=curve_info,
        depth=depth,
        units=units,
        header=header,
        filepath=str(path.resolve()),
    )


def read_well_log(
    filepath: Union[str, Path],
    depth_col: str = "DEPTH",
    value_cols: Optional[List[str]] = None,
    delimiter: str = ",",
    skip_rows: int = 0,
    null_value: float = -9999.25,
) -> WellLogData:
    """
    Read a CSV-based well-log file (tabular format) into a WellLogData object.

    Parameters
    ----------
    filepath : str or Path
        Path to the CSV / TSV / space-delimited well-log file.
    depth_col : str
        Name of the column to use as the depth axis. Default: "DEPTH".
    value_cols : list[str], optional
        Columns to load as curves. If None, all numeric columns are loaded.
    delimiter : str
        Column delimiter. Default: "," (comma). Use "\\t" for tab-delimited.
    skip_rows : int
        Number of header rows to skip before the column names row.
    null_value : float
        Numeric sentinel for missing data. Replaced with np.nan. Default: -9999.25.

    Returns
    -------
    WellLogData
        Contains depth array, curve dict, column list, and metadata.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    KeyError
        If depth_col is not found in the file.

    Examples
    --------
    >>> log = read_well_log("well_B.csv", depth_col="MD", value_cols=["GR", "RHOB"])
    >>> print(log.summary())
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Well log file not found: {filepath}")

    rows: List[dict] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for _ in range(skip_rows):
            next(fh, None)
        reader = csv.DictReader(fh, delimiter=delimiter)
        columns_raw = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError(f"No data rows found in '{filepath}'.")

    # Normalise column names: strip whitespace
    columns = [c.strip() for c in columns_raw]
    depth_col_norm = depth_col.strip()

    if depth_col_norm not in columns:
        raise KeyError(
            f"Depth column '{depth_col}' not found. Available columns: {columns}"
        )

    # Determine which columns to extract
    if value_cols is None:
        load_cols = [c for c in columns if c != depth_col_norm]
    else:
        load_cols = [c.strip() for c in value_cols if c.strip() in columns]

    def _parse(val: str) -> float:
        try:
            f = float(val)
            return np.nan if f == null_value else f
        except (ValueError, TypeError):
            return np.nan

    depth_arr = np.array([_parse(row.get(depth_col_norm, "")) for row in rows])

    curves: Dict[str, np.ndarray] = {}
    for col in load_cols:
        curves[col] = np.array([_parse(row.get(col, "")) for row in rows])

    return WellLogData(
        depth=depth_arr,
        curves=curves,
        columns=[depth_col_norm] + load_cols,
        filepath=str(path.resolve()),
        num_rows=len(rows),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_header(las: lasio.LASFile, key: str, default: str) -> str:
    try:
        return str(las.well[key].value).strip() or default
    except Exception:
        return default
