# Playbook: Assign Business Unit Business Function

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS
> Knowledge file: `knowledge/business-units.md`

## When to use
No documented REST to read or write BU business functions; FSM CSV support unverified. UI only.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Business Unit | Yes | US1 Business Unit | `finBusinessUnitsLOV` |
| Functions to enable | Yes | Requisitioning, Procurement, Receiving, Materials Management, Payables Invoicing | Request |
| Primary Ledger | If any ledger function | US Primary Ledger | `ledgersLOV` (primary, not ledger set) |
| Default Legal Entity | If any ledger function | US1 Legal Entity | `legalEntitiesLOV?finder=LedgerFinder;LedgerId=` |

Ledger functions (need Primary Ledger + Default Legal Entity): Billing and Revenue Management, Collections Management, Customer Payments, Expense Management, Materials Management, Payables Invoicing, Project Accounting, Receiving, Requisitioning.

## Pre-checks (read before write)
- BU exists and Active (`finBusinessUnitsLOV`).
- If ledger functions requested: ledger is Primary and LE is assigned to it (`legalEntitiesLOV` LedgerFinder).
- Read current state: Manage Business Unit > row > Actions > Assign Business Functions → screenshot `backups/<date>/assign-bu-function-before.png` → Cancel.
- Never uncheck an enabled function unless explicitly requested.

## Navigation path
Option 1 (scoped task):
1. Navigator > My Enterprise > Setup and Maintenance
2. Setup: Procurement > Functional Area: Organization Structures > Task: Assign Business Unit Business Function (or Search Tasks: "Assign Business Unit Business Function")
3. Scope column shows "Select" → click Select → Select Scope dialog → Business Unit: choose `<BU>` (Select and Add if not listed) → Apply and Go to Task.

Option 2 (from BU list):
1. Setup: Procurement > Organization Structures > Manage Business Unit
2. Search BU, select row > Actions > Assign Business Functions.

## Steps
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|
| 1 | Check | Enabled checkbox in Business Unit Functions table, row per function | each requested function |
| 2 | Select | Primary Ledger (Financial Reporting section) | `<ledger>` |
| 3 | Select | Default Legal Entity (Financial Reporting section) | `<LE>` |
| 4 | Click | Save and Close | — |

## Save / submit
Save and Close. Docs: "The enabled business functions are now assigned to your business unit." Exact confirmation/error text not documented (record here).

## Verification
- Reopen via Option 2 and check boxes + ledger/LE; screenshot `playbooks/screenshots/assign-business-unit-business-function-after.png`, then Cancel.
- `GET .../finBusinessUnitsLOV?finder=PrimaryKey;BusinessUnitId=<id>` → PrimaryLedgerId, LegalEntityId populated.
- Requisitioning: user with BU data access can open a requisition (no POR-2010674).
- Follow-ups: Configure Requisitioning Business Function / Configure Procurement Business Function, Manage Service Provider Relationships, Manage Business Unit Set Assignment (save).

## Known UI differences / gotchas
- Page title varies in docs: "Assign Business Functions" vs "Assign Business Unit Functions".
- Primary ledger change after transactions is discouraged (COA mismatch).
- One BU per page; no mass update.
- (record pod differences here: date, env, change)

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/business-functions.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html
- https://docs.oracle.com/en/cloud/saas/project-management/26d/fapfm/creating-and-managing-a-business-unit-procedure.html
- https://docs.oracle.com/en/cloud/saas/student-management/faism/assign-financials-business-unit-functions.html
