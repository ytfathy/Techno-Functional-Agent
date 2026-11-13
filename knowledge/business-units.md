# Business Units, Business Functions, BU Set Assignment

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
A business unit (BU) "performs one or many business functions that can be rolled up in a management hierarchy. A business unit can process transactions on behalf of many legal entities." BUs drive transaction processing, transactional data security (users get role + BU data access), reference data sharing (via default set) and management reporting.
Procurement model: a Procurement BU (procurement function) serves Requisitioning BUs (requisitioning function) and Sold-to/Payables BUs via service provider relationships.

## Where in Fusion (FSM)
- Offering: **Procurement** → Functional area: **Organization Structures** → Task: **Manage Business Unit** (confirmed 26D Procurement doc). Actions menu on the BU row → **Assign Business Functions**.
- Task: **Assign Business Unit Business Function** — scoped task: Scope column shows "Select" → Select Scope dialog → Business Unit → "Apply and Go to Task" (Financials offering, Organization Structures; Student Mgmt doc). Opens the Assign Business Unit Functions / Assign Business Functions page.
- Task: **Manage Business Unit Set Assignment** — Organization Structures (Financials offering); opens the Manage Set Assignments page. See `reference-data-sets.md`.
- Task: **Manage Business Unit Data Access for Users** — Procurement offering, Users and Security functional area. See `bu-data-access.md`.
- Rapid implementation alternative: **Create Chart of Accounts, Ledger, Legal Entities, and Business Units in Spreadsheet** (task list "Define Enterprise Structure for Procurement Rapid Implementation ..."). Also ESS **Configure Basic Enterprise Structure for Procurement** (creates a central Procurement BU as service provider, gives other BUs Requisitioning, one inventory org each; parameters "Centralized Procurement Business Unit Name", "Currency").

## Business functions (26D list)
Billing and revenue management · Collections management · Customer contract management · Customer payments · Expense management · Incentive compensation · Materials management · Payables invoicing · Payables payments · Procurement · Procurement contract management · Project accounting · Receiving · Requisitioning · Sales.

**Need primary ledger + default legal entity** (docs: "generate financial transactions and will require a primary ledger and a default legal entity"):
Billing and revenue management, Collections management, Customer payments, Expense management, Materials management, Payables invoicing, Project accounting, **Receiving**, **Requisitioning**.
Not in that list: Procurement, Procurement contract management, Payables payments, Sales, Customer contract management, Incentive compensation. (Student Mgmt doc nonetheless groups Payables Payment with functions needing ledger + LE — treat Payables Payments as "set ledger anyway".)
- "Each business unit can post transactions to a single primary ledger, but it can process transactions for many legal entities."
- Changing the primary ledger after setup is discouraged (different COA segments may corrupt data).

## Prerequisites & dependencies
- Before Create BU: reference data set for Default Set (`reference-data-sets`), optional Location (`locations`), optional Manager (person).
- Before Assign Business Function with ledger functions: primary ledger + legal entity (`legal-entities-ledgers`).
- After: Manage Business Unit Set Assignment (save!), Manage Business Unit Data Access for Users, Configure Procurement Business Function / Configure Requisitioning Business Function, Manage Service Provider Relationships, receiving/inventory orgs.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Name | `BusinessUnitName` (finBusinessUnitsLOV, read) | BU name | |
| Location | `LocationId` (read) | Optional HR location | |
| Manager | `ManagerId` (read) | Optional | |
| Active | `ActiveFlag` (read) | Active checkbox | Must be active for requisitioning |
| Default Set | — (see setIdAssignmentsBusinessUnit) | Default reference data set | "Create" in LOV makes a new set |
| Business function "Enabled" | — | Per-function checkbox on Assign Business Functions page | |
| Primary Ledger (Financial Reporting section) | `PrimaryLedgerId` (read) | | |
| Default Legal Entity (Financial Reporting section) | `LegalEntityId` (read) | | |
| (profit center) | `ProfitCenterFlag` (read) | BU is profit center under one LE | |

## Common mistakes
- User error POR-2010674 "You aren't assigned to a business unit that supports requisitioning": BU must be Active, have Requisitioning enabled, and the user needs BU data access for the role.
- Enabling Requisitioning/Receiving/Materials Management without primary ledger + default LE.
- Forgetting to open and save Manage Business Unit Set Assignment.
- Setting BU above legal entity level: "if you set up business units at a higher level than legal entities, your financial transactions may fail."
- Enabled checkbox must be changed BU by BU (no mass update in UI — community report, not docs).
- Supplier contracts: after creating a BU run ESS "Adopt Global Clauses for a New Business Unit".

## Channel & exact technique
- Preferred channel for **create BU / assign business function**: **D (UI)** — no documented writable REST resource for BUs or BU business functions; Business Unit is "not integration enabled" for HCM Data Loader.
  - `playbooks/create-business-unit.md`, `playbooks/assign-business-unit-business-function.md`
- **BU set assignment**: **A** via `setIdAssignmentsBusinessUnit` (see `reference-data-sets.md`).
- A (REST read-only):
  - `GET /fscmRestApi/resources/11.13.18.05/finBusinessUnitsLOV` — finders `PrimaryKey` (BusinessUnitId), `KeywordFinder` (SearchTerm), `IntentFinder` (Intent, SearchTerm), `ModuleIdFinder` (Intent, ModuleId, SearchTerm), `ServiceProviderFinder` (DownstreamFunctionId, Intent, ModuleId, SearchTerm, UpstreamFunctionId). Attributes: ActiveFlag, BusinessUnitId, BusinessUnitName, LegalEntityId, LocationId, ManagerId, PrimaryLedgerId, ProfitCenterFlag. All read-only.
  - `GET /fscmRestApi/resources/11.13.18.05/procurementBusinessUnitsLOV` — BUs where the **caller** is a procurement agent; attrs AgentAction, ProcurementBU, ProcurementBUId; default AgentAction MANAGE_PURCHASE_ORDERS. Security-filtered, not a master list.
  - `prjBusinessUnitsLOV`, `setIdAssignmentsBusinessUnitLOV` also read-only.
  - No `hcmBusinessUnitsLOV` found in HCM REST docs.
- B (FSM CSV): support for Manage Business Unit / Assign Business Unit Business Function not documented → UNVERIFIED. Runtime check: task Actions > Export to CSV File is disabled when a task doesn't support it.
- C: Rapid-implementation spreadsheet (above) — creation only, initial setup.

## How to verify
- `GET .../finBusinessUnitsLOV?q=BusinessUnitName='<name>'&onlyData=true` → ActiveFlag, PrimaryLedgerId, LegalEntityId.
- Business functions: no REST read documented → UI: Manage Business Unit > row > Actions > Assign Business Functions (Cancel after check). `ModuleIdFinder` can test if a BU appears for a function, but ModuleId values UNVERIFIED.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/business-functions.html — function list, ledger/LE requirement
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/Chunk437736635.html — BU concepts, primary ledger, security, Manage Data Access for Users
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html — Procurement > Organization Structures > Manage Business Unit; Actions > Assign Business Functions; POR-2010674
- https://docs.oracle.com/en/cloud/saas/project-management/26d/fapfm/creating-and-managing-a-business-unit-procedure.html — create BU steps, Assign BU Business Function steps, set assignment
- https://docs.oracle.com/en/cloud/saas/student-management/faism/assign-financials-business-unit-functions.html — scope selection, Financial Reporting section fields
- https://docs.oracle.com/en/cloud/saas/sales/fabus/define-business-units.html — Name, Manager, Location, Active, Default Set fields
- https://docs.oracle.com/en/cloud/saas/sales/fabus/define-business-units-assign-business-function-and-assign-ledger.html — Adopt Global Clauses note
- https://docs.oracle.com/en/cloud/saas/human-resources/fahdl/how-you-define-referenced-objects.html — BU not integration enabled for HDL; Organization Structures | Manage Business Unit
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-configure-basic-enterprise-structure-for-procurement.html — ESS Configure Basic Enterprise Structure for Procurement
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/enterprise-structure-for-procurement-rapid-implementation.html — rapid implementation spreadsheet task
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-finbusinessunitslov-get.html — finBusinessUnitsLOV
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-procurementbusinessunitslov-get.html — procurementBusinessUnitsLOV

## UNVERIFIED
- UNVERIFIED: No writable REST for creating BUs or assigning business functions in 26D (none found; absence not proven).
- UNVERIFIED: FSM Setup Task CSV support and TaskCodes for Manage Business Unit, Assign Business Unit Business Function, Manage Business Unit Set Assignment.
- UNVERIFIED: Functional area of Assign Business Unit Business Function and Manage Business Unit Set Assignment inside the Procurement offering (confirmed only for Financials offering).
- UNVERIFIED: Whether Payables Payments requires ledger + LE (26D list says no; Student Mgmt groups it with ledger functions).
- UNVERIFIED: ModuleId values per business function for `ModuleIdFinder`.
- UNVERIFIED: `requisitioningBusinessUnitsLOV` (named in 26A readiness only; 26D page not found).
- UNVERIFIED: Whether a business function can be disabled after transactions exist.
