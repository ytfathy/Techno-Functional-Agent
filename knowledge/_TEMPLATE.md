# <Area name>

> Release: 26D · Last researched: YYYY-MM-DD · Status: VERIFIED | PARTIAL | UNVERIFIED

## Business purpose
What this setup/object is for, in consultant terms. Who is affected.

## Where in Fusion (FSM)
- Offering: e.g. Procurement
- Functional area: e.g. Procurement Foundation
- Task name(s): e.g. Configure Procurement Business Function
- Scope / parameters asked when opening the task (e.g. "Select Procurement BU")

## Prerequisites & dependencies
What must exist first (link to `dependencies.md` nodes). What depends on this.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|

## Common mistakes
- ...

## Channel & exact technique
- Preferred channel: A | B | C | D (and why)
- A (REST): `GET/POST /fscmRestApi/resources/11.13.18.05/<resource>` — child resources, actions, finders. Always `rest_describe` first.
- B (FSM CSV): TaskCode `...`, business object codes, export criteria.
- C (FBDI/ESS): template name, CSV file name(s), UCM account, import job path, parameters.
- D (UI): `playbooks/<file>.md`

## How to verify
Read-back query / screen to check / functional test.

## Sources
- <docs.oracle.com URL> — what was taken from it

## UNVERIFIED
- Items that could not be confirmed from official 26D docs.
