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

from xml.etree import ElementTree as ET

from .client import ROOT, FusionError, get_client
from .generic import write

WORK = ROOT / "fbdi" / "work"


def _abs(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else ROOT / path


def _ucm_account(account: str) -> str:
    """'prc/supplier/import' -> 'prc$/supplier$/import$' (REST form)."""
    return account if "$" in account else "/".join(f"{s}$" for s in account.strip("/").split("/"))


_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _xlsx_sheets(path: Path) -> dict[str, list[list[str]]]:
    """Read the first 12 rows of every sheet straight from the xlsx/xlsm XML (openpyxl fails on Oracle's
    26D templates: bad stylesheet)."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).findall("p:Relationship", _NS)}
        out = {}
        for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", _NS):
            target = rels[s.get(f"{{{_NS['r']}}}id")].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            rows = []
            for row in ET.fromstring(z.read(target)).iter(f"{{{_NS['m']}}}row"):
                if len(rows) == 12:
                    break
                cells = {}
                for c in row.findall("m:c", _NS):
                    col = re.match(r"[A-Z]+", c.get("r", "A")).group()
                    idx = sum((ord(ch) - 64) * 26 ** i for i, ch in enumerate(reversed(col))) - 1
                    v = c.find("m:v", _NS)
                    if c.get("t") == "s" and v is not None:
                        cells[idx] = shared[int(v.text)]
                    elif c.get("t") == "inlineStr":
                        cells[idx] = "".join(t.text or "" for t in c.iter(f"{{{_NS['m']}}}t"))
                    elif v is not None:
                        cells[idx] = v.text or ""
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)] if cells else [])
            out[s.get("name")] = rows
    return out


def fbdi_template_columns(xlsm_path: str, sheet: str = "") -> dict:
    """Read the column LABELS of an official FBDI .xlsm template (to understand fields; download the template for
    the pod's release into fbdi/templates/ after asking the user). NOTE: the CSV order is the control-file order,
    not this sheet order — build files with fbdi_ctl_columns + fbdi_build_zip."""
    out = {}
    for name, rows in _xlsx_sheets(_abs(xlsm_path)).items():
        if (sheet and name != sheet) or (not sheet and "instruction" in name.lower()) or not rows:
            continue
        header = max(rows, key=lambda r: sum(bool(str(v).strip()) for v in r))  # fullest of the first 12 rows
        cols = [str(v).strip().strip("*").strip() for v in header]  # required marker: '*Name' or 'Name *'
        while cols and not cols[-1]:
            cols.pop()
        out[name] = cols
    return {"template": xlsm_path, "sheets": out}


def fbdi_ctl_columns(file_path: str) -> dict:
    """Column order of an FBDI CSV, from Oracle's SQL*Loader control file (.ctl, e.g. downloaded with the user's OK
    from .../fbdi-26d/fbdi/controlfiles/<name>.ctl into fbdi/templates/) or from the SQL*Loader .log of a load
    (ess_output of the 'Load File to Interface' child). Columns filled by EXPRESSION/CONSTANT are not in the CSV."""
    text = _abs(file_path).read_text(encoding="utf-8", errors="replace")
    if re.search(r"Column Name\s+Position", text):  # SQL*Loader log: one line per field, FIRST/NEXT = read from file
        cols = re.findall(r"^\s*\"?(\w+)\"?\s+(?:FIRST|NEXT)\s", text, re.M)
    else:
        body = text[text.index("(", text.upper().index("INTO TABLE")) + 1:]
        fields, depth, cur = [], 0, ""
        for ch in body:  # split on top-level commas until the closing parenthesis of the field list
            if ch == "(":
                depth += 1
            elif ch == ")":
                if depth == 0:
                    break
                depth -= 1
            if ch == "," and depth == 0:
                fields.append(cur)
                cur = ""
            else:
                cur += ch
        fields.append(cur)
        cols = [f.split()[0].strip('"') for f in (x.strip() for x in fields)
                if f and not re.search(r"\b(EXPRESSION|CONSTANT|RECNUM|SEQUENCE|SYSDATE)\b", f, re.I)]
    return {"file": file_path, "count": len(cols), "columns": cols}


def fbdi_build_zip(data: dict[str, list[dict]], zip_name: str, columns: dict[str, list[str] | str]) -> dict:
    """Build an FBDI zip: one header-less CSV per file, columns in CONTROL-FILE order.
    data: {"PozSupplierSitesInt.csv": [{"IMPORT_ACTION": "CREATE", "VENDOR_NAME": "...", ...}, ...]} — keys are the
    ctl column names. columns: per CSV, either an explicit ordered list or the path of the .ctl / SQL*Loader .log
    to read the order from. Unknown keys are reported, never silently dropped."""
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"{re.sub(r'[^A-Za-z0-9_-]', '_', zip_name)}.zip"
    problems, files = [], {}
    order = {}
    for name in data:
        spec = columns.get(name)
        if spec is None:
            problems.append(f"{name}: no column order given (pass a list or a .ctl/.log path in columns)")
        else:
            order[name] = spec if isinstance(spec, list) else fbdi_ctl_columns(spec)["columns"]
            unknown = sorted({k for r in data[name] for k in r} - set(order[name]))
            if unknown:
                problems.append(f"{name}: unknown columns {unknown}")
    if problems:
        return {"blocked": True, "problems": problems}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, rows in data.items():
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            for r in rows:
                w.writerow(["" if r.get(c) is None else r.get(c) for c in order[name]])
            z.writestr(name, buf.getvalue())
            files[name] = {"rows": len(rows), "columns": len(order[name])}
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


LOADER_JOBS = ("load interface file", "transfer file", "load file to interface", "upload interface error",
               "interfaceloader")


def fbdi_import_job(load_request_id: int, look_ahead: int = 6) -> dict:
    """After fbdi_import: find the product import job (e.g. Import Supplier Sites). Oracle submits it as a SEPARATE
    request after the load (usually load ReqstId + 1), not as a child. Scans the next request ids and returns their
    names/statuses; import_request_id = first one that is not a loader/upload job. On a shared pod other users' jobs
    can sit in between, so check the job name."""
    chain, found = [], None
    for rid in range(load_request_id + 1, load_request_id + 1 + look_ahead):
        st = ess_status(rid)
        if st.get("error"):
            continue
        jobs = st.get("jobs") if isinstance(st.get("jobs"), dict) else {}
        name = (jobs.get("JOBS") or {}).get("JOBNAME") or ""
        chain.append({"request_id": rid, "job": name, "status": st.get("status")})
        if found is None and name and not any(k in name.lower() for k in LOADER_JOBS):
            found = rid
    return {"load_request_id": load_request_id, "import_request_id": found, "next_requests": chain}


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


TOOLS = [fbdi_template_columns, fbdi_ctl_columns, fbdi_build_zip, fbdi_import, fbdi_import_job, ess_submit,
         ess_status, ess_output]
