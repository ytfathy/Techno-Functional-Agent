"""Bulk mode helpers: read Excel/CSV input, write per-row result reports to reports/."""
from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path

from openpyxl import Workbook, load_workbook

from .client import ROOT, redact


def bulk_read_file(file_path: str, sheet: str = "", header_row: int = 1, max_rows: int = 5000) -> dict:
    """Read an .xlsx or .csv file into rows (list of dicts keyed by header). Use before validating a bulk load."""
    p = Path(file_path)
    if not p.is_absolute():
        p = ROOT / p
    if p.suffix.lower() == ".csv":
        with open(p, newline="", encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f) if any(v not in (None, "") for v in r.values())]
        cols = list(rows[0].keys()) if rows else []
    else:
        wb = load_workbook(p, read_only=True, data_only=True)
        ws = wb[sheet] if sheet else wb.worksheets[0]
        values = list(ws.iter_rows(min_row=header_row, values_only=True))
        cols = [str(c).strip() if c is not None else f"col{i + 1}" for i, c in enumerate(values[0])] if values else []
        rows = [dict(zip(cols, r)) for r in values[1:] if any(v not in (None, "") for v in r)]
        wb.close()
    return {"file": str(p), "columns": cols, "count": len(rows), "truncated": len(rows) > max_rows,
            "rows": [{"_row": i + header_row + 1, **r} for i, r in enumerate(rows[:max_rows])]}


def bulk_write_report(name: str, rows: list[dict]) -> dict:
    """Write a result report (one row per input row: status, IDs, errors) to reports/<name>-<timestamp>.xlsx.
    Secret/bank fields are masked."""
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-") or "report"
    out = ROOT / "reports" / f"{safe}-{dt.datetime.now():%Y%m%d-%H%M%S}.xlsx"
    out.parent.mkdir(exist_ok=True)
    rows = redact(rows)
    cols: list[str] = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    wb = Workbook()
    ws = wb.active
    ws.title = "results"
    ws.append(cols)
    for r in rows:
        ws.append([str(v) if isinstance(v, (dict, list)) else v for v in (r.get(c) for c in cols)])
    wb.save(out)
    return {"report": str(out), "rows": len(rows)}


TOOLS = [bulk_read_file, bulk_write_report]
