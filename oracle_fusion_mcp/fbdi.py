"""Channel C — FBDI + ESS via erpintegrations. knowledge/channel-c-fbdi-ess.md."""
from __future__ import annotations

import base64
import csv
import datetime as dt
import io
import json
import re
import zipfile
from pathlib import Path

from openpyxl import load_workbook

from .client import ROOT, FusionError, get_client
from .generic import write

WORK = ROOT / "fbdi" / "work"


def _abs(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else ROOT / path


def _ucm_account(account: str) -> str:
    """'prc/supplier/import' -> 'prc$/supplier$/import$' (REST form)."""
    return account if "$" in account else "/".join(f"{s}$" for s in account.strip("/").split("/"))


def _header(ws) -> tuple[int, list[str]]:
    """FBDI sheets have instructions on top: the header is the fullest row among the first 12."""
    rows = list(ws.iter_rows(min_row=1, max_row=12, values_only=True))
    idx = max(range(len(rows)), key=lambda i: sum(v not in (None, "") for v in rows[i])) if rows else 0
    cols = [str(v).strip().lstrip("*").strip() if v is not None else "" for v in (rows[idx] if rows else [])]
    while cols and not cols[-1]:
        cols.pop()
    return idx + 1, cols


def fbdi_template_columns(xlsm_path: str, sheet: str = "") -> dict:
    """Read column order from an official FBDI .xlsm template (download it for the pod's release into
    fbdi/templates/ after asking the user). sheet empty = all data sheets."""
    wb = load_workbook(_abs(xlsm_path), read_only=True, keep_vba=False)
    sheets = [wb[sheet]] if sheet else [ws for ws in wb.worksheets if "instruction" not in ws.title.lower()]
    out = {ws.title: _header(ws)[1] for ws in sheets}
    wb.close()
    return {"template": xlsm_path, "sheets": out}


def _csv_name(sheet: str) -> str:
    """'POZ_SUPPLIERS_INT' -> 'PozSuppliersInt.csv' (FBDI macro convention)."""
    return "".join(p.capitalize() for p in re.split(r"[_\s]+", sheet) if p) + ".csv"


def fbdi_build_zip(xlsm_path: str, data: dict[str, list[dict]], zip_name: str,
                   csv_names: dict[str, str] | None = None) -> dict:
    """Build the FBDI zip the way the template macro does: one header-less CSV per sheet, columns in template order.
    data: {sheet_title: [ {column_header: value, ...}, ... ]}; column headers as in the template (leading * ignored).
    Unknown keys are reported, not silently dropped."""
    cols_by_sheet = fbdi_template_columns(xlsm_path)["sheets"]
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"{re.sub(r'[^A-Za-z0-9_-]', '_', zip_name)}.zip"
    problems, files = [], {}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for sheet, rows in data.items():
            cols = cols_by_sheet.get(sheet)
            if cols is None:
                problems.append(f"sheet {sheet!r} not in template; sheets: {list(cols_by_sheet)}")
                continue
            unknown = sorted({k for r in rows for k in r} - set(cols))
            if unknown:
                problems.append(f"{sheet}: unknown columns {unknown}")
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            for r in rows:
                w.writerow(["" if r.get(c) is None else r.get(c) for c in cols])
            name = (csv_names or {}).get(sheet) or _csv_name(sheet)
            z.writestr(name, buf.getvalue())
            files[name] = len(rows)
    if problems:
        out.unlink(missing_ok=True)
        return {"blocked": True, "problems": problems}
    return {"zip": str(out), "files": files}


def fbdi_import(zip_path: str, document_account: str, job_name: str, parameter_list: str,
                notification_code: str = "10", job_options: str = "", dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Upload an FBDI zip and run Load Interface File + the import job in one call (importBulkData).
    document_account e.g. 'prc/supplier/import'; job_name '<package path>,<job definition>' (read the exact path from
    'Manage Enterprise Scheduler Job Definitions…' — not published in docs); parameter_list comma list, #NULL for empty.
    job_options: optional, e.g. 'InterfaceDetails=<id>,ImportOption=Y,PurgeOption=Y,ExtractFileType=ALL' — the
    InterfaceDetails id is per object; empty = not sent. Returns ReqstId of the load job -> ess_status / ess_output."""
    p = _abs(zip_path)
    body = {"OperationName": "importBulkData", "DocumentContent": base64.b64encode(p.read_bytes()).decode(),
            "ContentType": "zip", "FileName": p.name, "DocumentAccount": _ucm_account(document_account),
            "JobName": job_name, "ParameterList": parameter_list, "CallbackURL": "#NULL",
            "NotificationCode": notification_code}
    if job_options:
        body["JobOptions"] = job_options
    return write("fbdi_import", "POST", "erpintegrations", body, dry_run=dry_run, confirm_prod=confirm_prod, validate=False)


def ess_submit(job_package_name: str, job_def_name: str, ess_parameters: str = "", dry_run: bool = True,
               confirm_prod: str = "") -> dict:
    """Submit any scheduled process (ESS job). ess_parameters: comma list in the job's parameter order (#NULL = empty)."""
    body = {"OperationName": "submitESSJobRequest", "JobPackageName": job_package_name, "JobDefName": job_def_name,
            "ESSParameters": ess_parameters}
    return write("ess_submit", "POST", "erpintegrations", body, dry_run=dry_run, confirm_prod=confirm_prod, validate=False)


def ess_status(request_id: int, details: bool = True) -> dict:
    """Status of a scheduled process (SUCCEEDED, ERROR, WARNING, RUNNING…). details=True adds the child job tree."""
    c = get_client()
    try:
        st = c.get("erpintegrations", finder=f"ESSJobStatusRF;requestId={request_id}", limit=1)
        out = {"request_id": request_id, "status": ((st.get("items") or [{}])[0]).get("RequestStatus")}
        if details:
            d = c.get("erpintegrations", finder=f"ESSExecutionDetailsRF;requestId={request_id}", limit=1)
            raw = ((d.get("items") or [{}])[0]).get("RequestStatus")
            try:
                out["jobs"] = json.loads(raw) if isinstance(raw, str) else raw
            except ValueError:
                out["jobs"] = raw
        return out
    except FusionError as e:
        return e.to_dict()


def ess_output(request_id: int, file_type: str = "ALL") -> dict:
    """Download the log/output of a scheduled process to reports/ess-<id>.zip and return the first part of each
    log/text file (to read errors)."""
    try:
        d = get_client().get("erpintegrations", finder=f"ESSJobExecutionDetailsRF;requestId={request_id},fileType={file_type}", limit=1)
    except FusionError as e:
        return e.to_dict()
    content = ((d.get("items") or [{}])[0]).get("DocumentContent")
    if not content:
        return {"request_id": request_id, "message": "no output available (yet)"}
    data = base64.b64decode(content)
    out = ROOT / "reports" / f"ess-{request_id}-{dt.datetime.now():%Y%m%d-%H%M%S}.zip"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    previews = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for n in z.namelist():
            if n.lower().endswith((".log", ".txt", ".out", ".csv")):
                previews[n] = z.read(n).decode("utf-8", "replace")[:3000]
    return {"saved": str(out), "files": list(previews) or None, "previews": previews}


TOOLS = [fbdi_template_columns, fbdi_build_zip, fbdi_import, ess_submit, ess_status, ess_output]
