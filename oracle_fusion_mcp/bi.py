"""Technical consultant — BI Publisher reporting & SQL analysis via BIP SOAP services.
knowledge/tech-bi-publisher.md. Needs a BI role on the agent user (BI Consumer to run, BI Author to deploy)."""
from __future__ import annotations

import base64
import csv
import datetime as dt
import io
import re
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from .client import ROOT, FusionError, audit, get_client, guard_prod, redact

REPORT_SVC = "/xmlpserver/services/ExternalReportWSSService"
PUB = "http://xmlns.oracle.com/oxp/service/PublicReportService"
SOAP12 = "http://www.w3.org/2003/05/soap-envelope"


def _envelope(ns: str, body: str) -> str:
    return (f'<soap:Envelope xmlns:soap="{SOAP12}" xmlns:pub="{ns}"><soap:Header/>'
            f"<soap:Body>{body}</soap:Body></soap:Envelope>")


def _params_xml(params: dict | None) -> str:
    items = []
    for name, value in (params or {}).items():
        values = value if isinstance(value, list) else [value]
        vals = "".join(f"<pub:item>{escape(str(v))}</pub:item>" for v in values)
        items.append(f"<pub:item><pub:name>{escape(name)}</pub:name><pub:values>{vals}</pub:values></pub:item>")
    return f"<pub:parameterNameValues>{''.join(items)}</pub:parameterNameValues>" if items else ""


def _save(name: str, data: bytes, ext: str) -> str:
    out = ROOT / "reports" / f"{re.sub(r'[^A-Za-z0-9_-]+', '-', name).strip('-') or 'report'}-{dt.datetime.now():%Y%m%d-%H%M%S}.{ext}"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    return str(out)


def run_report_bytes(report_path: str, params: dict | None = None, fmt: str = "csv") -> bytes:
    body = (f"<pub:runReport><pub:reportRequest><pub:attributeFormat>{escape(fmt)}</pub:attributeFormat>"
            f"<pub:flattenXML>false</pub:flattenXML>{_params_xml(params)}"
            f"<pub:reportAbsolutePath>{escape(report_path)}</pub:reportAbsolutePath>"
            f"<pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload></pub:reportRequest>"
            f"<pub:appParams></pub:appParams></pub:runReport>")
    root = get_client().soap(REPORT_SVC, _envelope(PUB, body))
    node = next((e for e in root.iter() if e.tag.endswith("reportBytes")), None)
    if node is None or not (node.text or "").strip():
        raise FusionError(200, "runReport returned no reportBytes (empty report or wrong path)", [], REPORT_SVC)
    return base64.b64decode(node.text)


def bi_run_report(report_path: str, params: dict | None = None, fmt: str = "csv", preview_rows: int = 30) -> dict:
    """Run any BI Publisher report (catalog path, e.g. '/Custom/AI_SCM_AGENT/SupplierAudit.xdo') via
    ExternalReportWSSService.runReport. params: {"P_BU": "US1 Business Unit", "P_LIST": ["a", "b"]}.
    fmt: csv | xlsx | pdf | xml | html. The full output is saved to reports/; csv/xml return a masked preview."""
    try:
        data = run_report_bytes(report_path, params, fmt)
    except FusionError as e:
        return e.to_dict()
    name = report_path.rsplit("/", 1)[-1].replace(".xdo", "")
    out: dict = {"report": report_path, "bytes": len(data)}
    if fmt == "csv":
        rows = redact(list(csv.DictReader(io.StringIO(data.decode("utf-8-sig", "replace")))))
        out.update(saved=_save_rows(name, rows), row_count=len(rows), columns=list(rows[0]) if rows else [],
                   preview=rows[:preview_rows])
    else:  # shortcut: pdf/xlsx/xml cannot be masked column-wise; saved as returned
        out["saved"] = _save(name, data, fmt)
        if fmt == "xml":
            out["preview"] = data.decode("utf-8", "replace")[:3000]
    audit({"event": "bi_run_report", "report": report_path, "params": params, "format": fmt, "saved": out["saved"]})
    return out


def _save_rows(name: str, rows: list[dict]) -> str:
    """Save already-masked rows as CSV in reports/ (never raw bank/secret values)."""
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return _save(name, buf.getvalue().encode("utf-8"), "csv")


# ---------------------------------------------------------------- catalog (BIP v2 CatalogService, SOAP 1.1)
# shortcut: path /xmlpserver/services/v2/CatalogService is the standard BIP path (UNVERIFIED on Fusion); check ?wsdl.
CATALOG_SVC = "/xmlpserver/services/v2/CatalogService"
V2 = "http://xmlns.oracle.com/oxp/service/v2"
SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"


def _v2_call(op: str, fields: str) -> ET.Element:
    """v2 services take userID/password in the body: built here only, never logged or returned."""
    cfg = get_client().cfg
    creds = f"<v2:userID>{escape(cfg.get('ORACLE_USERNAME', ''))}</v2:userID><v2:password>{escape(cfg.get('ORACLE_PASSWORD', ''))}</v2:password>"
    env = (f'<soapenv:Envelope xmlns:soapenv="{SOAP11}" xmlns:v2="{V2}"><soapenv:Header/><soapenv:Body>'
           f"<v2:{op}>{fields}{creds}</v2:{op}></soapenv:Body></soapenv:Envelope>")
    return get_client().soap(CATALOG_SVC, env, soap11=True)


def bi_catalog_list(folder: str = "/Custom") -> dict:
    """List BI Publisher catalog objects in a folder (reports .xdo, data models .xdm, sub-folders)."""
    try:
        root = _v2_call("getFolderContents", f"<v2:folderAbsolutePath>{escape(folder)}</v2:folderAbsolutePath>")
    except FusionError as e:
        return e.to_dict()
    items = []
    for item in root.iter():
        vals = {c.tag.split("}")[-1]: (c.text or "") for c in item}
        if "absolutePath" in vals:
            items.append({k: vals.get(k) for k in ("absolutePath", "type", "displayName", "lastModified")})
    return {"folder": folder, "count": len(items), "items": items}


def bi_deploy_object(local_file: str, target_path: str, object_type: str, dry_run: bool = True,
                     confirm_prod: str = "") -> dict:
    """Upload a BIP object to the catalog (CatalogService.uploadObject). local_file: an exported .xdmz (data model) or
    .xdoz (report) zip; object_type: xdm | xdo | xsb | xss; target_path e.g. '/Custom/AI_SCM_AGENT/SupplierAudit.xdo'.
    Custom content belongs only under /Custom. A pod write: dry run first, then the user's yes."""
    from pathlib import Path

    if object_type not in ("xdm", "xdo", "xsb", "xss"):
        return {"blocked": True, "reason": "object_type must be xdm | xdo | xsb | xss"}
    if not target_path.startswith(("/Custom/", "/Shared Folders/Custom/")):
        return {"blocked": True, "reason": "custom BI content must go under /Custom (never overwrite seeded reports)"}
    p = Path(local_file) if Path(local_file).is_absolute() else ROOT / local_file
    preview = {"env": get_client().env_name, "operation": "bi_deploy_object", "target": target_path,
               "object_type": object_type, "file": str(p), "bytes": p.stat().st_size}
    if dry_run:
        return {"dry_run": True, **preview}
    guard_prod(confirm_prod)
    fields = (f"<v2:reportObjectAbsolutePathURL>{escape(target_path)}</v2:reportObjectAbsolutePathURL>"
              f"<v2:objectType>{object_type}</v2:objectType>"
              f"<v2:objectZippedData>{base64.b64encode(p.read_bytes()).decode()}</v2:objectZippedData>")
    try:
        _v2_call("uploadObject", fields)
    except FusionError as e:
        audit({"event": "error", **preview, "error": e.to_dict()})
        return e.to_dict()
    audit({"event": "write", **preview})
    return {"ok": True, **preview}


# ---------------------------------------------------------------- ad-hoc SQL analysis
# One generic "SQL runner" report (playbooks/bi-sql-runner.md) takes the query base64-encoded in P_SQL_B64 and returns
# DBMS_XMLGEN XML. Created once per pod with the user's OK: it can read any table the BI data source can read.
SQL_BLOCK = re.compile(r"\b(insert|update|delete|merge|drop|alter|create|grant|revoke|truncate|execute|exec|begin|declare|"
                       r"commit|rollback|dbms_\w+|utl_\w+|into)\b", re.I)


def check_select(sql: str) -> str:
    """Return a clean single SELECT/WITH statement or raise ValueError."""
    s = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S).strip().rstrip(";").strip()
    if not re.match(r"(?is)^(select|with)\b", s):
        raise ValueError("only SELECT / WITH queries are allowed")
    if ";" in s:
        raise ValueError("one statement only")
    m = SQL_BLOCK.search(s)
    if m:
        raise ValueError(f"keyword {m.group(0)!r} is not allowed in analysis SQL")
    return s


def bi_sql(sql: str, max_rows: int = 500, runner_path: str = "") -> dict:
    """Read-only analysis SQL against Fusion tables/views (e.g. PO_HEADERS_ALL, POZ_SUPPLIERS_V, RCV_TRANSACTIONS,
    INV_ONHAND_QUANTITIES_DETAIL, EGP_SYSTEM_ITEMS_B — see knowledge/tech-bi-publisher.md). SELECT/WITH only; DML/DDL/
    PL/SQL blocked; rows capped. Runs through the SQL runner report (ORACLE_BI_SQL_REPORT in the profile, default
    /Custom/AI_SCM_AGENT/SQL_RUNNER.xdo). Results are masked and saved to reports/."""
    try:
        clean = check_select(sql)
    except ValueError as e:
        return {"blocked": True, "reason": str(e)}
    wrapped = f"SELECT * FROM ({clean}) WHERE ROWNUM <= {int(max_rows)}"
    path = runner_path or get_client().cfg.get("ORACLE_BI_SQL_REPORT") or "/Custom/AI_SCM_AGENT/SQL_RUNNER.xdo"
    try:
        data = run_report_bytes(path, {"P_SQL_B64": base64.b64encode(wrapped.encode()).decode()}, "xml")
    except FusionError as e:
        d = e.to_dict()
        d["hint"] = f"Is the SQL runner deployed at {path}? See playbooks/bi-sql-runner.md. " + (d.get("hint") or "")
        return d
    rows = _xml_rows(data)
    rows = redact(rows)
    audit({"event": "bi_sql", "sql": wrapped[:2000], "rows": len(rows)})
    return {"row_count": len(rows), "capped": len(rows) >= max_rows, "columns": list(rows[0]) if rows else [],
            "saved": _save_rows("sql", rows), "preview": rows[:30]}


def _xml_rows(data: bytes) -> list[dict]:
    """Runner output: <DATA_DS><G_1><RESULT_XML>&lt;ROWSET&gt;&lt;ROW&gt;…</RESULT_XML></G_1></DATA_DS>
    (the DBMS_XMLGEN document may also come back already parsed as child elements)."""
    root = ET.fromstring(data)
    holder = next((e for e in root.iter() if e.tag.upper().endswith("RESULT_XML")), None)
    inner = ET.fromstring(holder.text) if holder is not None and (holder.text or "").strip().startswith("<") else root
    return [{c.tag: (c.text or "") for c in row} for row in inner.iter("ROW")]


TOOLS = [bi_run_report, bi_sql, bi_catalog_list, bi_deploy_object]
