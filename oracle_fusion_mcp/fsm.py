"""Channel B — FSM Setup Task CSV export/import. knowledge/channel-b-fsm-csv.md."""
from __future__ import annotations

import base64
import datetime as dt
import re
from pathlib import Path

from .client import ROOT, FusionError, audit, get_client
from .generic import q_str, rest_get, write

KINDS = {"export": ("setupTaskCSVExports", "SetupTaskCSVExportProcess", "SetupTaskCSVExportProcessResult"),
         "import": ("setupTaskCSVImports", "SetupTaskCSVImportProcess", "SetupTaskCSVImportProcessResult")}


def _first(child) -> dict:
    """First row of a child collection in a POST response: a list (docs) or {"items": [...]} (seen on the pod)."""
    if isinstance(child, dict):
        child = child.get("items") or [child]
    return (child or [{}])[0]


def fsm_find_task(name: str) -> dict:
    """Find a setup task's TaskCode by (part of) its name and whether it supports CSV export/import
    (CSVExportImportSupportedFlag = Y -> channel B possible)."""
    return rest_get("setupTasks", q=f"TaskName LIKE {q_str('%' + name + '%')}",
                    fields="TaskCode,TaskName,AvailableFlag,ExportImportSupportedFlag,CSVExportImportSupportedFlag", limit=25)


def fsm_export(task_code: str, criteria: list[dict] | None = None) -> dict:
    """Start a CSV export (also the backup before a change). criteria (optional, scope), e.g.
    [{"BusinessObjectCode": "...", "AttributeSet": "Set1", "AttributeName": "...", "AttributeValue": "..."}].
    Returns ProcessId; then poll fsm_status and fetch the zip with fsm_download. Read-only for setup data."""
    body: dict = {"TaskCode": task_code, "SetupTaskCSVExportProcess": [{"TaskCode": task_code}]}
    if criteria:
        body["SetupTaskCSVExportCriteria"] = [{"TaskCode": task_code, **c} for c in criteria]
    try:
        res = get_client().request("POST", "setupTaskCSVExports", json_body=body)
    except FusionError as e:
        return e.to_dict()
    pid = _first(res.get("SetupTaskCSVExportProcess")).get("ProcessId")
    audit({"event": "fsm_export", "task_code": task_code, "process_id": pid, "criteria": criteria})
    return {"task_code": task_code, "process_id": pid}


def fsm_status(task_code: str, process_id: int, kind: str = "export") -> dict:
    """Poll an FSM CSV export/import process. kind: export | import. Done when completed=True;
    result StatusCode: COMPLETED | COMPLETED_WARNINGS | COMPLETED_ERRORS."""
    coll, proc, result = KINDS[kind]
    base = f"{coll}/{task_code}/child/{proc}/{process_id}"
    try:
        p = get_client().request("GET", base)
    except FusionError as e:
        return e.to_dict()
    done = str(p.get("ProcessCompletedFlag")).lower() in ("true", "y")
    out = {"process_id": process_id, "completed": done, "process": {k: v for k, v in p.items() if k != "links"}}
    if done:
        try:
            out["result"] = {k: v for k, v in get_client().request("GET", f"{base}/child/{result}/{process_id}").items() if k != "links"}
        except FusionError as e:
            out["result"] = e.to_dict()
    return out


def fsm_download(task_code: str, process_id: int, kind: str = "export", what: str = "FileContent") -> dict:
    """Save an FSM process file to backups/<YYYY-MM-DD>/. what: FileContent (export zip) | ProcessLog |
    ProcessResultsReport | ProcessResultsSummaryReport | CSVTemplateReport."""
    coll, proc, result = KINDS[kind]
    path = f"{coll}/{task_code}/child/{proc}/{process_id}/child/{result}/{process_id}/enclosure/{what}"
    try:
        data = get_client().download(path)
    except FusionError as e:
        return e.to_dict()
    ext = ".zip" if data[:2] == b"PK" else ".txt"
    out = ROOT / "backups" / f"{dt.date.today():%Y-%m-%d}" / f"{re.sub(r'[^A-Za-z0-9_-]', '_', task_code)}-{kind}-{process_id}-{what}{ext}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {"saved": str(out), "bytes": len(data)}


def fsm_import(task_code: str, zip_path: str, dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Import a (modified) setup task CSV zip. ALWAYS fsm_export first (backup). Poll with fsm_status(kind='import')
    and read the log with fsm_download(kind='import', what='ProcessLog')."""
    p = Path(zip_path)
    p = p if p.is_absolute() else ROOT / p
    content = base64.b64encode(p.read_bytes()).decode()
    body = {"TaskCode": task_code,
            "SetupTaskCSVImportProcess": [{"TaskCode": task_code, "SourceTargetDiffOkFlag": "N", "FileContent": content}]}
    res = write("fsm_import", "POST", "setupTaskCSVImports", body, dry_run=dry_run, confirm_prod=confirm_prod,
                validate=False, extra_preview={"zip": str(p)})
    if res.get("ok"):
        res["process_id"] = _first(res["result"].get("SetupTaskCSVImportProcess")).get("ProcessId")
    return res


TOOLS = [fsm_find_task, fsm_export, fsm_status, fsm_download, fsm_import]
