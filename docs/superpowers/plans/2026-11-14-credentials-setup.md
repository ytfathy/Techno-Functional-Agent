# Credentials Setup Form Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local form in the Claude browser pane that saves the pod URL / username / password to `.env.<profile>` and tests the connection.

**Architecture:** One stdlib `http.server` script; pure helpers (`save_profile`, `test_connection`) are unit-tested, the HTTP handler stays thin. Launched via `.claude/launch.json`; `CLAUDE.md` tells the agent to open it at session start.

**Tech Stack:** Python 3.14 stdlib, `python-dotenv`, existing `oracle_fusion_mcp.client.FusionClient`, pytest + respx.

**Spec:** `docs/superpowers/specs/2026-11-14-credentials-setup-design.md`

## Global Constraints
- Bind `127.0.0.1:8765` only.
- Write only `ORACLE_BASE_URL`, `ORACLE_USERNAME`, `ORACLE_PASSWORD`; empty password = keep current.
- URL must start with `https://`.
- Password never printed, logged, echoed in HTML, or returned to the page.
- No new dependencies. Not a git repo: no commit steps.

## Review Focus
- Empty password on save → existing password kept (test in Task 1).
- Profile file missing → created from `.env.example` (test in Task 1).
- `http://` or junk URL → rejected, file unchanged (test in Task 1).
- Wrong password → page shows "HTTP 401", not a traceback (test in Task 1).
- Cross-site POST without the form token → 403 (handler check, Task 1).

---

### Task 1: `scripts/setup_env.py` + tests

**Files:**
- Create: `scripts/setup_env.py`
- Test: `tests/test_setup_env.py`

**Interfaces:**
- Produces: `save_profile(root: Path, profile: str, url: str, username: str, password: str) -> None` (raises `ValueError` on bad URL/profile); `test_connection(root: Path, profile: str) -> tuple[bool, str]`; `main(port: int = 8765)`.

- [ ] **Step 1: Write failing tests** — `test_save_keeps_password_when_empty`, `test_save_creates_from_example`, `test_save_rejects_http_url` (file content unchanged), `test_connection_reports_401` (respx 401 → `(False, "HTTP 401 …")`), `test_password_never_in_page` (rendered form for a profile with password `S3cret!` does not contain it).
- [ ] **Step 2: Run** `.venv\Scripts\python.exe -m pytest tests/test_setup_env.py -q` → FAIL (module missing).
- [ ] **Step 3: Implement** helpers with `dotenv.set_key(..., quote_mode="never")`; `test_connection` builds `FusionClient(load_profile-equivalent from root)` and GETs `finBusinessUnitsLOV?limit=1`; handler: GET `/` form, POST `/save`, POST `/keep`, token check.
- [ ] **Step 4: Run** full suite → all pass.

### Task 2: Wire-up

**Files:**
- Create: `.claude/launch.json` (`oracle-setup`, `.venv\Scripts\python.exe` `scripts/setup_env.py`, port 8765)
- Modify: `CLAUDE.md` (session-start rule), `README.md` (one line), `PROGRESS.md`

- [ ] **Step 1:** `preview_start("oracle-setup")` → form renders in the pane with URL/username prefilled, password empty.
