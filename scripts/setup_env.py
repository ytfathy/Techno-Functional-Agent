"""Local form (127.0.0.1 only) to set the pod URL / username / password in .env.<profile> and test them.

Run: .venv\\Scripts\\python.exe scripts/setup_env.py   (or preview_start "oracle-setup")
The password is written to the .env file only: never printed, logged, or sent back to the page.
"""
from __future__ import annotations

import html
import re
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oracle_fusion_mcp.client import FusionClient, FusionError  # noqa: E402

PROFILE_RE = re.compile(r"^[a-z0-9_-]{1,20}$")


def _env_path(root: Path, profile: str) -> Path:
    if not PROFILE_RE.match(profile or ""):
        raise ValueError("Profile must be letters/digits/_/- (e.g. test).")
    return root / f".env.{profile}"


def save_profile(root: Path, profile: str, url: str, username: str, password: str) -> None:
    """Write URL/username (and password unless empty) into .env.<profile>; create it from .env.example if missing."""
    path = _env_path(root, profile)
    url, username = (url or "").strip(), (username or "").strip()
    if not re.match(r"^https://[^\s/]+\.[^\s/]+", url):
        raise ValueError("URL must start with https:// and contain the pod host.")
    if not username:
        raise ValueError("Username is required.")
    if not path.exists():
        path.write_text((root / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
        if profile in ("dev", "test", "prod"):
            set_key(path, "ORACLE_ENV_NAME", profile.upper(), quote_mode="never")
    set_key(path, "ORACLE_BASE_URL", url, quote_mode="never")
    set_key(path, "ORACLE_USERNAME", username, quote_mode="never")
    if password:
        set_key(path, "ORACLE_PASSWORD", password, quote_mode="always")  # quoted: passwords may hold # or spaces


def test_connection(root: Path, profile: str) -> tuple[bool, str]:
    """One cheap GET with the saved profile. Returns (ok, message without secrets)."""
    cfg = {k: (v or "") for k, v in dotenv_values(_env_path(root, profile)).items()}
    cfg["_profile"] = profile
    try:
        FusionClient(cfg).get("finBusinessUnitsLOV", limit=1)
    except FusionError as e:
        return False, f"HTTP {e.status}: {e.to_dict().get('hint') or e.to_dict().get('message') or 'failed'}"
    except Exception as e:  # network / DNS / bad URL
        return False, f"{type(e).__name__}: {e}"
    return True, f"Connected: {cfg.get('ORACLE_ENV_NAME') or profile.upper()} · {cfg.get('ORACLE_RELEASE', '')} · {cfg.get('ORACLE_USERNAME')}"


def render_form(root: Path, profile: str, token: str, note: str, ok: bool | None = None) -> str:
    cfg = dotenv_values(root / f".env.{profile}") if (root / f".env.{profile}").exists() else {}
    profiles = sorted({p.name[5:] for p in root.glob(".env.*") if p.name != ".env.example"} | {profile})
    e = lambda s: html.escape(s or "", quote=True)  # noqa: E731
    opts = "".join(f'<option{" selected" if p == profile else ""}>{e(p)}</option>' for p in profiles)
    color = {True: "var(--ok)", False: "var(--bad)"}.get(ok, "var(--muted)")
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oracle connection</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--fg:#1d2330;--muted:#5b6475;--line:#d6dae1;--acc:#c74634;--ok:#1a7f37;--bad:#b42318}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14171c;--card:#1d2128;--fg:#e8eaee;--muted:#9aa3b2;--line:#323844;--ok:#4ac26b;--bad:#ff7b72}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;padding:16px;box-sizing:border-box}}
form{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:24px;width:100%;max-width:440px;box-sizing:border-box}}
h1{{font-size:18px;margin:0 0 16px}} label{{display:block;font-size:13px;color:var(--muted);margin:12px 0 4px}}
input,select{{width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit}}
.row{{display:flex;gap:8px;margin-top:20px}} button{{flex:1;padding:9px;border-radius:6px;border:1px solid var(--line);font:inherit;cursor:pointer;background:var(--bg);color:var(--fg)}}
button.primary{{background:var(--acc);border-color:var(--acc);color:#fff}} .note{{margin-top:16px;color:{color};min-height:1.4em}}
</style></head><body><form method="post" action="/save">
<h1>Oracle connection</h1><input type="hidden" name="token" value="{e(token)}">
<label for="p">Profile</label><select id="p" name="profile" onchange="location='/?profile='+this.value">{opts}</select>
<label for="u">Instance URL</label><input id="u" name="url" type="url" required placeholder="https://xxxx.fa.ocs.oraclecloud.com" value="{e(cfg.get('ORACLE_BASE_URL'))}">
<label for="n">Username</label><input id="n" name="username" required autocomplete="username" value="{e(cfg.get('ORACLE_USERNAME'))}">
<label for="w">Password</label><input id="w" name="password" type="password" autocomplete="current-password" placeholder="{'unchanged — leave empty to keep' if cfg.get('ORACLE_PASSWORD') else ''}">
<div class="row"><button class="primary" type="submit">Save &amp; test</button><button type="submit" formaction="/keep" formnovalidate>Keep current</button></div>
<div class="note" role="status">{e(note)}</div></form></body></html>"""


class Handler(BaseHTTPRequestHandler):
    token = secrets.token_urlsafe(16)
    root = ROOT

    def _send(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args) -> None:  # no request logging (POST bodies hold the password)
        pass

    def do_GET(self) -> None:
        q = parse_qs(self.path.partition("?")[2])
        profile = (q.get("profile") or ["test"])[0]
        if not PROFILE_RE.match(profile):
            profile = "test"
        self._send(200, render_form(self.root, profile, self.token, ""))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        f = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True).items()}
        profile = f.get("profile", "test") if PROFILE_RE.match(f.get("profile", "")) else "test"
        if not secrets.compare_digest(f.get("token", ""), self.token):
            return self._send(403, "Forbidden")
        if self.path == "/keep":
            ok, msg = test_connection(self.root, profile) if (self.root / f".env.{profile}").exists() else (False, "No profile yet.")
            print(f"KEEP profile={profile} ok={ok}", flush=True)
            return self._send(200, render_form(self.root, profile, self.token, ("Kept. " + msg), ok))
        try:
            save_profile(self.root, profile, f.get("url", ""), f.get("username", ""), f.get("password", ""))
        except ValueError as e:
            return self._send(200, render_form(self.root, profile, self.token, str(e), False))
        ok, msg = test_connection(self.root, profile)
        print(f"SAVED profile={profile} ok={ok}", flush=True)  # status only; the agent reads this, never the values
        self._send(200, render_form(self.root, profile, self.token, ("Saved. " + msg), ok))


def main(port: int = 8765) -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"oracle-setup on http://127.0.0.1:{port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
