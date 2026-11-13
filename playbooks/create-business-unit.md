# Playbook: Create Business Unit (Manage Business Unit)

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS
> Knowledge file: `knowledge/business-units.md`

## When to use
No documented writable REST for business units, BU is not HDL-enabled, and FSM CSV support for Manage Business Unit is unverified. UI is the only confirmed channel.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Name | Yes | US1 Business Unit | Request |
| Default Set | Yes | set code, e.g. US1_SET | `setIdSets?finder=SetCodeFinder;SetCode=` (create first via REST if new) |
| Location | No | location name | `locationsV2` |
| Manager | No | person | HCM |
| Active | Yes | checked | default |

## Pre-checks (read before write)
- Duplicate: `GET /fscmRestApi/resources/11.13.18.05/finBusinessUnitsLOV?q=BusinessUnitName='<name>'` must return 0 rows (LOV is security-filtered; also search on the Manage Business Units page).
- Default Set exists (`setIdSets`), Location exists and is active.
- Backup: screenshot of Manage Business Units search result to `backups/<date>/create-business-unit-before.png`.

## Navigation path
> VERIFIED-ON-POD 2026-11-14 (Claude browser pane, read-only): `<pod>/fscmUI/faces/FuseTaskListManagerTop` opens Setup and Maintenance directly (Navigator links sit in collapsed groups). "Search Tasks" box → `Manage Business Unit` → Enter → click the task link in the results table → "Manage Business Units" page: search fields Name / Location / Manager / Active, then Search. YT Business Unit showed Active ✓.
1. Navigator > My Enterprise > Setup and Maintenance
2. Setup: Procurement > Functional Area: Organization Structures > Task: Manage Business Unit   (or Search Tasks: "Manage Business Unit")
3. Manage Business Units page opens.

## Steps
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|
| 1 | Click | Create icon (or Actions > Create) | — |
| 2 | Type | Name | `<Name>` |
| 3 | Select (optional) | Location | `<Location>` |
| 4 | Select (optional) | Manager | `<Manager>` |
| 5 | Ensure checked | Active | checked |
| 6 | Select | Default Set | `<set code>` (list also offers Create to make a new set — avoid; create set via REST first) |
| 7 | Click | Save and Close | — |

## Save / submit
Save and Close → back on Manage Business Units. Confirmation message text not documented (record actual text here).

## Verification
- `GET .../finBusinessUnitsLOV?q=BusinessUnitName='<name>'&onlyData=true` → row with ActiveFlag true, LocationId.
- Screenshot `playbooks/screenshots/create-business-unit-after.png`.
- Next steps (separate actions): assign business functions (`assign-business-unit-business-function.md`), then **open and Save Manage Business Unit Set Assignment** (assignment not complete until saved; or use `setIdAssignmentsBusinessUnit` REST), then data access (`dataSecurities`). Supplier contracts users: run ESS "Adopt Global Clauses for a New Business Unit".

## Known UI differences / gotchas
- Sales offering requires profile HZ_ENABLE_MULTIPLE_BU_CRM = Yes to create extra BUs (Sales only).
- Older docs say location and default set must exist before creating the BU.
- (record pod differences here: date, env, change)

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html
- https://docs.oracle.com/en/cloud/saas/project-management/26d/fapfm/creating-and-managing-a-business-unit-procedure.html
- https://docs.oracle.com/en/cloud/saas/sales/fabus/define-business-units.html
- https://docs.oracle.com/en/cloud/saas/human-resources/gaagw/create-a-business-unit-for-oman.html
- https://docs.oracle.com/en/cloud/saas/sales/fabus/define-business-units-assign-business-function-and-assign-ledger.html
