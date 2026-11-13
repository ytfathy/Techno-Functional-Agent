# Credentials setup form — design (approved 2026-11-14)

## Intent
The pod URL and password change from time to time. At the start of every session the user wants a small screen where they type the instance URL, username and password, instead of editing `.env.*` by hand.

## Goals / non-goals / anti-goals
- Goal: one form in the Claude browser pane; saves to `.env.<profile>`; tests the connection; agent reloads the profile.
- Non-goals: activity monitoring, an in-page chat, browser SSO sign-in (stays manual). All three were dropped by the user.
- Anti-goal: the password ever passing through Claude, chat, logs or the page after submit.

## Constraints
- Claude cannot read `.env*` (denied in `.claude/settings.json`).
- No new dependencies: Python stdlib + `python-dotenv` (already used).
- Local only: bind `127.0.0.1`.

## Approaches
- **Local form in the Claude browser pane (picked)**: user asked for an interface; the pane sits next to the chat.
- Terminal prompt (`getpass`): simpler, but not an interface.
- Editing `.env` by hand: the current state the user wants to leave.

## Design
- `scripts/setup_env.py`: stdlib `http.server` on `127.0.0.1:8765`.
  - GET `/`: form with profile (from existing `.env.*`, default `test`), URL and username prefilled from that profile, password empty (never sent to the page).
  - POST `/save`: updates only `ORACLE_BASE_URL`, `ORACLE_USERNAME`, `ORACLE_PASSWORD` (empty password = keep current) with `dotenv.set_key`; creates the profile from `.env.example` if missing. URL must be `https://`. Then one test GET with a fresh `FusionClient`; page shows "Connected" or the HTTP error. Password is never printed, logged or echoed.
  - POST `/keep`: no change, just "Keep current".
  - A one-time token in the form blocks cross-site posts.
- `.claude/launch.json`: config `oracle-setup` → `.venv\Scripts\python.exe scripts/setup_env.py`, port 8765.
- `CLAUDE.md`: at session start, `preview_start("oracle-setup")`, wait for the user, then `switch_environment(<profile>)` + `env_info`.

## Left to the builder
Page styling, exact test endpoint (a cheap GET such as `finBusinessUnitsLOV?limit=1`).
