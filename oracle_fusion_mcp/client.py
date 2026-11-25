"""Oracle Fusion REST client: env profiles, auth, retries, pagination, errors, batch, audit log."""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
REST_VERSION = "11.13.18.05"
FSCM = f"/fscmRestApi/resources/{REST_VERSION}"
HCM = f"/hcmRestApi/resources/{REST_VERSION}"

ERROR_CODE_RE = re.compile(r"\b[A-Z]{2,4}-\d{4,8}\b")
SECRET_KEY_RE = re.compile(
    r"password|passwd|secret|token|authorization|bankaccount|bank_account|accountnumber|account_number"
    r"|iban|swift|routing|cardnumber|card_number",
    re.I,
)
RETRY_STATUS = {429, 502, 503, 504}
STATUS_HINTS = {
    400: "Oracle rejected the payload: read the message/codes, fix the field values (use rest_describe), do not resend unchanged.",
    401: "Authentication failed: check the username/password or OAuth client in the active .env profile.",
    403: "Signed in but not authorized: the agent user lacks a role/privilege or data access (BU / inventory org) for this "
         "resource. Run ensure_access(<this resource path>) to see and (per the CLAUDE.md self-grant rule) add the missing role.",
    404: "Resource path or record ID not found: check the path with rest_describe / rest_get.",
    409: "Conflict: the record changed or already exists. Re-read it before retrying.",
}


class FusionError(Exception):
    """An HTTP error returned by Fusion, with Oracle message codes (POZ-, PO-, INV-...) extracted."""

    def __init__(self, status: int, message: str, codes: list[str], url: str, body: Any = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status, self.message, self.codes, self.url, self.body = status, message, codes, url, body

    def to_dict(self) -> dict:
        return {
            "error": True,
            "status": self.status,
            "message": self.message,
            "oracle_codes": self.codes,
            "url": self.url,
            "hint": STATUS_HINTS.get(self.status, "See knowledge/error-codes.md for the Oracle codes."),
        }


def parse_error(resp: httpx.Response) -> FusionError:
    text = resp.text or ""
    msg = text.strip()
    try:
        body = resp.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        details = body.get("o:errorDetails") or []
        parts = [d.get("detail") for d in details if isinstance(d, dict) and d.get("detail")]
        msg = "; ".join(parts) or body.get("detail") or body.get("title") or msg
    return FusionError(resp.status_code, str(msg)[:2000], sorted(set(ERROR_CODE_RE.findall(text))), str(resp.request.url), body)


# ---------------------------------------------------------------- redaction + audit

def redact(obj: Any) -> Any:
    """Mask secret/bank values and shorten huge strings (base64 files) before logging or showing."""
    if isinstance(obj, dict):
        return {k: ("***" if SECRET_KEY_RE.search(str(k)) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    if isinstance(obj, str) and len(obj) > 2000:
        return obj[:120] + f"...<{len(obj)} chars>"
    return obj


def log_dir() -> Path:
    return Path(os.getenv("ORACLE_AGENT_LOG_DIR") or ROOT / "logs")


def audit(event: dict) -> None:
    """Append one record to logs/audit-YYYY-MM-DD.jsonl (secrets masked)."""
    d = log_dir()
    d.mkdir(parents=True, exist_ok=True)
    rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), **redact(event)}
    with open(d / f"audit-{dt.date.today():%Y-%m-%d}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def strip_links(obj: Any) -> Any:
    """Drop ADF 'links' arrays: they are noise for the agent."""
    if isinstance(obj, dict):
        return {k: strip_links(v) for k, v in obj.items() if k != "links"}
    if isinstance(obj, list):
        return [strip_links(x) for x in obj]
    return obj


# ---------------------------------------------------------------- profiles

def load_profile(name: str) -> dict[str, str]:
    path = ROOT / f".env.{name.lower()}"
    if not path.exists():
        raise FileNotFoundError(f"No profile {path.name}. Copy .env.example to {path.name} and fill it in.")
    cfg = {k: (v or "") for k, v in dotenv_values(path).items()}
    cfg["_profile"] = name.lower()
    return cfg


class FusionClient:
    def __init__(self, cfg: dict[str, str], transport: httpx.BaseTransport | None = None):
        self.cfg = cfg
        u = urlsplit((cfg.get("ORACLE_BASE_URL") or "").strip())
        self.base = f"{u.scheme}://{u.netloc}" if u.scheme and u.netloc else ""  # pod root only; drops UI paths like /fscmUI/...
        self.http = httpx.Client(timeout=httpx.Timeout(180, connect=20), transport=transport)
        self._token: str | None = None
        self._token_exp = 0.0

    # -- identity
    @property
    def env_name(self) -> str:
        return (self.cfg.get("ORACLE_ENV_NAME") or self.cfg.get("_profile") or "").upper()

    @property
    def is_prod(self) -> bool:
        return self.env_name == "PROD"

    def info(self) -> dict:
        return {
            "profile": self.cfg.get("_profile"),
            "env": self.env_name,
            "base_url": self.base,
            "release": self.cfg.get("ORACLE_RELEASE"),
            "auth_mode": self.cfg.get("ORACLE_AUTH_MODE") or "basic",
            "user": self.cfg.get("ORACLE_USERNAME") if (self.cfg.get("ORACLE_AUTH_MODE") or "basic") == "basic" else self.cfg.get("ORACLE_CLIENT_ID"),
        }

    def url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        if not self.base:
            raise RuntimeError("ORACLE_BASE_URL is empty in the active .env profile.")
        if path.startswith("/"):
            return self.base + path
        return f"{self.base}{FSCM}/{path}"

    # -- auth
    def _auth(self) -> dict[str, str]:
        mode = (self.cfg.get("ORACLE_AUTH_MODE") or "basic").lower()
        if mode == "basic":
            user, pwd = self.cfg.get("ORACLE_USERNAME"), self.cfg.get("ORACLE_PASSWORD")
            if not user or not pwd:
                raise RuntimeError("ORACLE_USERNAME / ORACLE_PASSWORD missing in the active .env profile.")
            return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pwd}".encode()).decode()}
        if mode == "oauth":
            if not self._token or time.time() > self._token_exp - 60:
                r = self.http.post(
                    self.cfg["ORACLE_OAUTH_TOKEN_URL"],
                    data={"grant_type": "client_credentials", "scope": self.cfg.get("ORACLE_SCOPE", "")},
                    auth=(self.cfg["ORACLE_CLIENT_ID"], self.cfg["ORACLE_CLIENT_SECRET"]),
                )
                if r.status_code != 200:
                    raise parse_error(r)
                j = r.json()
                self._token, self._token_exp = j["access_token"], time.time() + int(j.get("expires_in", 3600))
            return {"Authorization": f"Bearer {self._token}"}
        raise RuntimeError(f"Unknown ORACLE_AUTH_MODE {mode!r} (expected basic | oauth)")

    # -- core request
    def request(self, method: str, path: str, *, params: dict | None = None, json_body: Any = None,
                headers: dict | None = None, retries: int = 3) -> Any:
        url = self.url(path)
        h = {"REST-Framework-Version": self.cfg.get("ORACLE_REST_FRAMEWORK_VERSION") or "4", **self._auth(), **(headers or {})}
        if json_body is not None:
            h.setdefault("Content-Type", "application/json")
        body = json.dumps(json_body) if json_body is not None else None
        safe_to_repeat = method.upper() in ("GET", "HEAD")
        for attempt in range(retries + 1):
            # auth goes on every call; a reused session cookie keeps OLD role grants (seen on pod: 403 after a grant)
            self.http.cookies.clear()
            try:
                resp = self.http.request(method, url, params=params, content=body, headers=h)
            except httpx.ConnectError:  # never reached Oracle: safe to retry any method
                if attempt == retries:
                    raise
                time.sleep(2 ** attempt)
                continue
            except httpx.TimeoutException:
                # a timed-out write may still have been applied: never resend it blindly
                if not safe_to_repeat or attempt == retries:
                    raise
                time.sleep(2 ** attempt)
                continue
            if attempt < retries and resp.status_code in RETRY_STATUS and (safe_to_repeat or resp.status_code in (429, 503)):
                ra = resp.headers.get("Retry-After", "")
                time.sleep(int(ra) if ra.isdigit() else 2 ** attempt)
                continue
            if resp.status_code >= 400:
                raise parse_error(resp)
            if not resp.content:
                return {"status": resp.status_code}
            ctype = resp.headers.get("content-type", "")
            if "json" in ctype:
                return resp.json()
            if "html" in ctype:  # a sign-in / SSO / UI page, never a REST answer
                raise FusionError(resp.status_code, "Got an HTML page instead of JSON: wrong base URL or an SSO login page.",
                                  [], str(resp.request.url))
            return {"status": resp.status_code, "text": resp.text[:5000]}
        raise RuntimeError("unreachable")

    # -- reads
    def get(self, path: str, *, q: str | None = None, fields: str | None = None, expand: str | None = None,
            finder: str | None = None, order_by: str | None = None, limit: int = 25, offset: int = 0,
            all_pages: bool = False, max_rows: int = 2000, total_results: bool = False) -> Any:
        if "/scim/" in path:  # SCIM rejects ADF params (onlyData/limit/offset); put filter=/attributes= in the path
            path, _, qs = path.partition("?")  # httpx drops a path query string when params= is given
            return self.request("GET", path, params={**dict(httpx.QueryParams(qs)), "count": limit, "startIndex": offset + 1})
        params = {"q": q, "fields": fields, "expand": expand, "finder": finder, "orderBy": order_by,
                  "limit": limit, "offset": offset, "onlyData": "true",
                  "totalResults": "true" if total_results else None}
        params = {k: v for k, v in params.items() if v not in (None, "")}
        data = self.request("GET", path, params=params)
        if not (all_pages and isinstance(data, dict) and "items" in data):
            return data
        items = list(data["items"])
        while data.get("hasMore") and len(items) < max_rows:
            params["offset"] = params.get("offset", 0) + len(data["items"])
            data = self.request("GET", path, params=params)
            if not data.get("items"):
                break
            items.extend(data["items"])
        return {"count": len(items), "hasMore": bool(data.get("hasMore")), "items": items[:max_rows]}

    def download(self, path: str) -> bytes:
        """GET a binary enclosure (zip/log). Returns raw bytes (base64 text is decoded)."""
        resp = self.http.get(self.url(path), headers=self._auth())
        if resp.status_code >= 400:
            raise parse_error(resp)
        data = resp.content
        if data[:2] != b"PK":  # some enclosures come back base64-encoded
            try:
                return base64.b64decode(data, validate=True)
            except ValueError:
                pass
        return data

    def soap(self, path: str, envelope: str, timeout: float = 300, soap11: bool = False) -> ET.Element:
        """POST a SOAP envelope (1.2 by default; soap11=True for BIP v2 services). Returns the parsed response root.
        HTTP errors and SOAP Faults raise FusionError with the fault text. Never retried (may be a write)."""
        self.http.cookies.clear()
        ctype = {"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": '""'} if soap11 else \
            {"Content-Type": "application/soap+xml; charset=UTF-8"}
        resp = self.http.post(self.url(path), content=envelope.encode("utf-8"), timeout=timeout,
                              headers={**self._auth(), **ctype})
        text = resp.text
        if resp.status_code >= 400 or "Fault>" in text[:5000]:
            m = re.search(r"<(?:\w+:)?(?:Text|faultstring)[^>]*>(.*?)</", text, re.S)
            raise FusionError(resp.status_code, (m.group(1) if m else text[:500]).strip(),
                              sorted(set(ERROR_CODE_RE.findall(text))), str(resp.request.url))
        return ET.fromstring(resp.content)

    # -- writes (callers must apply dry-run / PROD guard first; see generic.write)
    def action(self, item_path: str, name: str, params: dict | None = None) -> Any:
        return self.request("POST", f"{item_path.rstrip('/')}/action/{name}", json_body=params or {},
                            headers={"Content-Type": "application/vnd.oracle.adf.action+json"})

    def batch(self, parts: list[dict]) -> Any:
        return self.request("POST", f"{FSCM}/", json_body={"parts": parts},
                            headers={"Content-Type": "application/vnd.oracle.adf.batch+json"})


# ---------------------------------------------------------------- session state

_state: dict[str, Any] = {"client": None, "mode": "confirm", "off": False}


def get_client() -> FusionClient:
    if _state["off"]:
        raise RuntimeError("Agent is off (disconnected). Run /agent on (switch_environment) to reconnect.")
    if _state["client"] is None:
        _state["client"] = FusionClient(load_profile(os.getenv("ORACLE_PROFILE", "test")))
    return _state["client"]


def set_client(client: FusionClient | None) -> None:
    _state["client"] = client
    if client is not None:
        _state["off"] = False


def disconnect() -> None:
    """Close the HTTP session and block every Fusion call until switch_environment()."""
    if _state["client"] is not None:
        _state["client"].http.close()
    _state.update(client=None, off=True, mode="confirm")


def get_mode() -> str:
    return _state["mode"]


def set_mode(mode: str) -> str:
    mode = mode.lower().strip()
    if mode not in ("confirm", "auto"):
        raise ValueError("mode must be 'confirm' or 'auto'")
    if mode == "auto" and get_client().is_prod:
        raise PermissionError("auto mode is not allowed on PROD. Staying in confirm mode.")
    _state["mode"] = mode
    return mode


def switch_environment(name: str) -> FusionClient:
    client = FusionClient(load_profile(name))
    set_client(client)
    if client.is_prod:
        _state["mode"] = "confirm"
    return client


def guard_prod(confirm_prod: str) -> None:
    if get_client().is_prod and confirm_prod.strip() != "CONFIRM PROD":
        raise PermissionError("Target environment is PROD. The user must type exactly 'CONFIRM PROD'; pass it as confirm_prod.")
