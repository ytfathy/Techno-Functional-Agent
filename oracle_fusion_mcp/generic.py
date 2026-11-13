"""Generic REST tools: work on ANY Fusion business object, so the agent is never limited to shortcuts."""
from __future__ import annotations

import difflib
from typing import Any

from .client import FusionError, audit, get_client, guard_prod, redact, strip_links

STD_ACTIONS = {"get", "create", "update", "delete", "replace", "describe", "upsert"}
_describe_cache: dict[str, dict] = {}


# ---------------------------------------------------------------- path helpers

def _segments(path: str) -> list[str]:
    return [s for s in path.split("?")[0].strip("/").split("/") if s]


def collection_of(path: str) -> str:
    """'suppliers/1/child/sites/2' -> 'suppliers/1/child/sites' ; collection paths unchanged."""
    segs = _segments(path)
    head = segs[: segs.index("resources") + 2] if "resources" in segs else []  # keep /xxRestApi/resources/<ver>
    body = segs[len(head):]
    if len([s for s in body if s != "child"]) % 2 == 0:  # ends with a record key
        body = body[:-1]
    out = "/".join(head + body)
    return "/" + out if path.startswith("/") else out


def resource_name(path: str) -> str:
    return _segments(collection_of(path))[-1]


def q_str(value: str) -> str:
    """Quote a value for a q= RowMatch expression."""
    return "'" + str(value).replace("'", "''") + "'"


# ---------------------------------------------------------------- describe

def _split(path: str) -> tuple[list[str], list[str]]:
    """-> (prefix segments up to /resources/<ver>, collection names along the path)."""
    segs = _segments(collection_of(path))
    head = segs[: segs.index("resources") + 2] if "resources" in segs else []
    body = [s for s in segs[len(head):] if s != "child"]
    return head, body[0::2]


def _describe_raw(path: str) -> dict:
    """Describe of the ROOT resource: Fusion nests full child descriptors inside it
    (describing a child URL with a parent key does not work)."""
    head, names = _split(path)
    root = "/".join(head + names[:1])
    root = "/" + root if path.startswith("/") else root
    key = f"{get_client().base}|{root}"
    if key not in _describe_cache:
        _describe_cache[key] = get_client().request("GET", f"{root}/describe")
    return _describe_cache[key]


def _node_for(data: dict, path: str) -> dict:
    """Walk root -> child -> grandchild following the collection names in path."""
    resources = data.get("Resources", {}) if isinstance(data, dict) else {}
    _, names = _split(path)
    node = resources.get(names[0]) or next(iter(resources.values()), {})
    for name in names[1:]:
        node = (node.get("children") or {}).get(name, {})
    return node


def _attr_line(a: dict) -> str:
    flags = [f for f, on in (("mandatory", a.get("mandatory")), ("read-only", a.get("updatable") is False),
                             ("lov", "lov" in a)) if on]
    return f"{a.get('name')}:{a.get('type', '?')}" + (f" [{', '.join(flags)}]" if flags else "")


def summarize_node(name: str, node: dict) -> dict:
    coll, item = node.get("collection", {}) or {}, node.get("item", {}) or {}
    return {
        "resource": name,
        "title": node.get("title"),
        "attributes": [_attr_line(a) for a in node.get("attributes", [])],
        "children": sorted((node.get("children") or {}).keys()),
        "finders": [f"{f.get('name')}({', '.join(x.get('name', '') for x in f.get('attributes', []))})" for f in coll.get("finders", [])],
        "custom_actions": [
            {"name": a.get("name"), "parameters": [p.get("name") for p in a.get("parameters", [])]}
            for a in coll.get("actions", []) + item.get("actions", []) if a.get("name") not in STD_ACTIONS
        ],
    }


def rest_describe(resource_path: str, raw: bool = False) -> dict:
    """Read a REST resource's real metadata (attributes, children, finders, custom actions).
    ALWAYS call this before building a payload. resource_path is relative to /fscmRestApi/resources/11.13.18.05/
    (e.g. 'suppliers', 'suppliers/123/child/sites') or absolute (e.g. '/hcmRestApi/resources/11.13.18.05/locationsV2')."""
    try:
        data = _describe_raw(resource_path)
    except FusionError as e:
        return e.to_dict()
    return data if raw else summarize_node(resource_name(resource_path), _node_for(data, resource_path))


def validate_payload(path: str, payload: dict, creating: bool) -> tuple[list[str], list[str]]:
    """Check payload field names against describe. Returns (errors, warnings)."""
    try:
        node = _node_for(_describe_raw(path), path)
    except FusionError as e:
        return [], [f"describe unavailable (HTTP {e.status}): field names NOT verified"]
    errors: list[str] = []
    warnings: list[str] = []

    def check(data: dict, n: dict, prefix: str) -> None:
        attrs = {a.get("name"): a for a in n.get("attributes", [])}
        children = n.get("children") or {}
        if not attrs:
            return
        for k, v in data.items():
            if k in attrs:
                if not creating and attrs[k].get("updatable") is False:
                    warnings.append(f"{prefix}{k}: read-only attribute, Oracle will reject or ignore it")
                continue
            if k in children and isinstance(v, list):
                for i, row in enumerate(v):
                    if isinstance(row, dict):
                        check(row, children[k], f"{prefix}{k}[{i}].")
                continue
            close = difflib.get_close_matches(k, list(attrs) + list(children), n=3)
            errors.append(f"{prefix}{k}: not a field of this resource" + (f" (did you mean {', '.join(close)}?)" if close else ""))
        if creating:
            missing = [a for a, d in attrs.items() if d.get("mandatory") and d.get("updatable") is not False and a not in data]
            if missing:
                warnings.append(f"{prefix or 'payload'}: mandatory per describe but not sent (may default): {', '.join(missing)}")

    check(payload, node, "")
    return errors, warnings


# ---------------------------------------------------------------- reads

def rest_get(resource_path: str, q: str = "", fields: str = "", expand: str = "", finder: str = "",
             order_by: str = "", limit: int = 25, offset: int = 0, all_pages: bool = False,
             max_rows: int = 2000, total_results: bool = False) -> dict:
    """Read records from any Fusion REST resource (collection or single record).
    q: filter, e.g. "Supplier LIKE 'Nile%'" or "BusinessUnitName='Egypt Operations'".
    fields: comma list to keep output small. expand: child names or 'all'. finder: 'FinderName;Attr=Val'.
    all_pages=True follows hasMore up to max_rows."""
    try:
        return strip_links(get_client().get(resource_path, q=q or None, fields=fields or None, expand=expand or None,
                                            finder=finder or None, order_by=order_by or None, limit=limit,
                                            offset=offset, all_pages=all_pages, max_rows=max_rows,
                                            total_results=total_results))
    except FusionError as e:
        return e.to_dict()


# ---------------------------------------------------------------- writes

def _ids(result: Any) -> dict:
    if not isinstance(result, dict):
        return {}
    return {k: v for k, v in result.items()
            if isinstance(v, (str, int)) and (k.endswith("Id") or k.endswith("Number") or k in ("ReqstId", "ProcessId"))}


def write(operation: str, method: str, path: str, payload: Any, *, dry_run: bool, confirm_prod: str = "",
          validate: bool = True, creating: bool = False, headers: dict | None = None, extra_preview: dict | None = None) -> dict:
    """Shared write path: field check -> preview (dry run) -> PROD guard -> send -> audit."""
    client = get_client()
    preview: dict[str, Any] = {"env": client.env_name, "operation": operation, "method": method,
                               "url": client.url(path), "payload": redact(payload), **(extra_preview or {})}
    if validate and isinstance(payload, dict) and payload:
        errors, warnings = validate_payload(path, payload, creating)
        preview["field_check"] = {"errors": errors, "warnings": warnings}
        if errors:
            return {"blocked": True, "reason": "Unknown field names per describe. Fix the payload; never guess.", **preview}
    if dry_run:
        return {"dry_run": True, **preview}
    guard_prod(confirm_prod)
    try:
        if method == "ACTION":
            result = client.request("POST", path, json_body=payload or {},
                                    headers={"Content-Type": "application/vnd.oracle.adf.action+json"})
        else:
            result = client.request(method, path, json_body=payload, headers=headers)
    except FusionError as e:
        audit({"event": "error", **preview, "error": e.to_dict()})
        return {**e.to_dict(), "operation": operation}
    result = strip_links(result)
    audit({"event": "write", **preview, "ids": _ids(result)})
    return {"ok": True, "env": client.env_name, "operation": operation, "url": preview["url"], "ids": _ids(result), "result": result}


def rest_create(resource_path: str, payload: dict, dry_run: bool = True, confirm_prod: str = "") -> dict:
    """POST a new record to a collection (e.g. 'suppliers/123/child/sites'). Field names are checked against
    describe first. dry_run=True (default) returns the exact endpoint + payload without sending."""
    return write("create", "POST", resource_path, payload, dry_run=dry_run, confirm_prod=confirm_prod, creating=True)


def create_checked(path: str, payload: dict, *, dup_q: str = "", dup_path: str = "", extra: dict | None = None,
                   dry_run: bool = True, confirm_prod: str = "", allow_duplicate: bool = False) -> dict:
    """Shortcut helper: merge extra fields, drop empty values, block on duplicates (read before write), then create."""
    payload = {k: v for k, v in {**payload, **(extra or {})}.items() if v not in (None, "")}
    if dup_q and not allow_duplicate:
        found = rest_get(dup_path or path, q=dup_q, limit=5)
        if found.get("error"):
            return {"blocked": True, "reason": "Duplicate check failed; fix the query or pass allow_duplicate=True after checking manually.", "error": found}
        if found.get("items"):
            return {"blocked": True, "reason": "Possible duplicate already exists.", "duplicates": found["items"]}
    return rest_create(path, payload, dry_run=dry_run, confirm_prod=confirm_prod)


def rest_update(resource_path: str, payload: dict, dry_run: bool = True, confirm_prod: str = "") -> dict:
    """PATCH an existing record (path must end with its key, e.g. 'suppliers/123'). Send only changed fields."""
    return write("update", "PATCH", resource_path, payload, dry_run=dry_run, confirm_prod=confirm_prod)


def rest_action(resource_path: str, action_name: str, payload: dict | None = None, dry_run: bool = True,
                confirm_prod: str = "") -> dict:
    """Invoke a custom action on a record, e.g. ('draftPurchaseOrders/300100...', 'submit').
    Find valid action names and parameters with rest_describe(...)['custom_actions']."""
    path = f"{resource_path.rstrip('/')}/action/{action_name}"
    return write(f"action:{action_name}", "ACTION", path, payload or {}, dry_run=dry_run, confirm_prod=confirm_prod, validate=False)


def rest_delete(resource_path: str, user_explicitly_requested: bool = False, dry_run: bool = True,
                confirm_prod: str = "") -> dict:
    """DELETE a record. Refused unless the user explicitly asked for a delete in this conversation.
    Prefer inactivation / end-dating via rest_update."""
    if not user_explicitly_requested:
        return {"blocked": True, "reason": "No deletes unless the user explicitly asks. Prefer inactivation/end-dating."}
    return write("delete", "DELETE", resource_path, None, dry_run=dry_run, confirm_prod=confirm_prod, validate=False)


def rest_batch(parts: list[dict], dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Send several operations in one ADF batch request (bulk mode). Each part:
    {"id": "row1", "path": "/suppliers", "operation": "create" | "update" | "get", "payload": {...}}."""
    from .client import FSCM

    bad = [p.get("id") for p in parts if not {"id", "path", "operation"} <= set(p)]
    if bad:
        return {"blocked": True, "reason": f"parts missing id/path/operation: {bad}"}
    return write("batch", "POST", f"{FSCM}/", {"parts": parts}, dry_run=dry_run, confirm_prod=confirm_prod,
                 validate=False, headers={"Content-Type": "application/vnd.oracle.adf.batch+json"},
                 extra_preview={"part_count": len(parts)})
