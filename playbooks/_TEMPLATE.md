# Playbook: <task name>

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS | VERIFIED-ON-POD (date, env)
> Knowledge file: `knowledge/<area>.md`

## When to use
Why this needs the UI (no REST / no FSM CSV for this task).

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|

## Pre-checks (read before write)
- Read current state (REST or UI) and check for duplicates.
- Backup: screenshot of current values to `backups/<date>/<task>-before.png`.

## Navigation path
1. Navigator > My Enterprise > Setup and Maintenance
2. Setup: <Offering> > Functional Area: <area> > Task: <task>   (or Search Tasks: "<task>")
3. ...

## Steps
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|

## Save / submit
Which button, expected confirmation message.

## Verification
How to read back the result (REST query or screen) + screenshot `playbooks/screenshots/<task>-after.png`.

## Known UI differences / gotchas
- Record here every time the real screen differs from this playbook (date, env, what changed).

## Sources
- docs.oracle.com URL(s)
