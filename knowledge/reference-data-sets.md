# Reference Data Sets (SetID) and Set Assignment

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Reference data sets ("SetID") partition shared setup data (payment terms, locations, departments, jobs, transaction types, etc.) so business units can share it or own it. A transaction filters LOVs to the set assigned to its BU (for that reference group) plus the Common Set.
- Docs: "Regardless of the business unit on a transaction, reference data assigned to the Common Set is always available, in addition to the reference data assigned to the set that corresponds to the business unit on the transaction."
- An **Enterprise** set is also predefined: "Define any reference data that affects your entire enterprise in this set."

## Where in Fusion (FSM)
- Create sets: Task **Manage Reference Data Sets** — Functional area **Enterprise Profile** (Financials offering per Student Mgmt/HCM docs; Sales offering also lists it). Page: click New → Set Code, Set Name, Description → Save and Close.
- Assign sets to a BU: Task **Manage Business Unit Set Assignment** — Functional area **Organization Structures** (Financials offering). Opens the **Manage Set Assignments** page; scope = business unit.
- Generic assignment page: "Manage Reference Data Set Assignments" (determinant type + determinant + reference group).
- Data access to sets: Task **Manage Reference Data Set Data Access for Users** (Enterprise Profile functional area).

## Concepts
- **Determinant type** (the partitioning key) — values from docs: Asset Book, Business Unit, Cost Organization, Project Unit, Reference Data Set.
- **Determinant (value)**: the specific BU / cost org / etc.
- **Reference group**: logical group of reference entities sharing one set assignment (e.g. all Sales Order Type tables). Predefined.
- **Sharing methods**: (1) one set only, no common values (e.g. Asset Prorate Conventions); (2) one set only, with common values — most common (e.g. Receivables Transaction Types); (3) multiple sets, no common values (e.g. Payables Payment Terms).
- **BU default set**: "When you assign reference data sets to business units, you assign a default reference data set to use for all reference data types for that business unit. You can override the set assignment for one or more data types."
- Default Set is chosen on the Create Business Unit page (can "Create" a new set from the LOV). The BU default set is assigned to each reference data object; **the assignment isn't complete until the Manage Business Unit Set Assignment record is saved**, even with no changes.
- Creating a new set does not change existing BU assignments; reassign per object via Manage Set Assignments.

## Prerequisites & dependencies
- Needs: nothing (sets are top of chain).
- Used by: `business-units` (Default Set), `locations` (Location Set), procurement/supplier site sharing, payment terms, etc.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Set Code | `SetCode` (setIdSets, string 30, not updatable) | Unique code | UI uppercases on save |
| Set Name | `SetName` (string 80) | Display name | |
| Description | `Description` (string 2000) | | |
| (internal) | `SetId` (int64) | Surrogate id | Needed by locationsV2 POST |
| Determinant Type | `DeterminantType` (setIdAssignmentsBusinessUnit, string 30) | Partition key type | BU code value UNVERIFIED |
| Determinant Value | `DeterminantValue` (int64) | BU id | |
| Reference Group | `ReferenceGroupName` (string 30) | Reference group | |
| Reference Data Set Code | `SetCode` / `SetId` | Assigned set | |
| (org) | `OrganizationCode` (240), `OrganizationId` (read-only) | Set ID organization | |

## Common mistakes
- Assuming BU set assignment is done after Create BU: must open and **save** Manage Business Unit Set Assignment.
- Putting shared data (e.g. locations) in a BU-specific set → invisible to other BUs. Use Common Set unless partitioning is intended.
- Changing set assignment after transactions exist — see FAQ "What happens if I override the set assignment?" (not read; behaviour UNVERIFIED).

## Channel & exact technique
- Preferred channel: **A (REST)** — Applications Common REST exposes write operations for both sets and BU set assignments.
- A (REST), base `/fscmRestApi/resources/11.13.18.05`:
  - `setIdSets`: GET collection (finders `PrimaryKey` [SetId], `SetCodeFinder` [SetCode]), GET item `/setIdSets/{SetId}`, POST (create/upsert, `Upsert-Mode` header), PATCH (`SetName`, `Description` updatable). No DELETE documented.
  - `setIdAssignmentsBusinessUnit`: GET / POST / PATCH / DELETE (`/{setIdAssignmentsBusinessUnit_Id}`). Finders: `AssignmentFinder` (DeterminantValue, ReferenceGroupName), `DeterminantFinder` (bindBusinessUnitCode), `PrimaryKey` (DeterminantType, DeterminantValue, OrganizationId, ReferenceGroupName), `ReferenceGroupFinder` (bindReferenceGroupName).
  - `setIdAssignmentsBusinessUnitLOV`: read-only GET.
  - Related (search index only): `setIdAssignmentsSet`, `setIdAssignmentsAssetBook`, `setIdReferenceGroups` — UNVERIFIED for 26D.
  - Always `rest_describe` first; payload `ReferenceGroupName` values must come from a GET of existing assignments.
- B (FSM CSV): FSM docs list "Application Reference Data Set" as ready-to-use setup data exported only if modified. TaskCode / CSV support per task UNVERIFIED.
- D (UI): Manage Reference Data Sets / Manage Business Unit Set Assignment — fallback only.

## How to verify
- `GET .../setIdSets?finder=SetCodeFinder;SetCode=<CODE>`
- `GET .../setIdAssignmentsBusinessUnit?finder=DeterminantFinder;bindBusinessUnitCode=<BU>` — one row per reference group with SetCode.
- UI: Manage Business Unit Set Assignment, scope = BU → check set per object.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/reference-data-sets.html — definition, common sets/subsets, Manage Reference Data Set Assignments page
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/reference-data-sets-and-sharing-methods.html — sharing methods, Enterprise set
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assignment-of-reference-data-sets-to-reference-objects.html — determinant types, determinant, reference groups
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-business-units-work-with-reference-data-sets.html — Common Set rule, default set + overrides
- https://docs.oracle.com/en/cloud/saas/project-management/26d/fapfm/creating-and-managing-a-business-unit-procedure.html — Default Set on BU create; set assignment must be saved
- https://docs.oracle.com/en/cloud/saas/student-management/faism/manage-your-reference-data-set.html — Manage Reference Data Sets task, Enterprise Profile, fields
- https://docs.oracle.com/en/cloud/saas/human-resources/fahdl/how-you-define-referenced-objects.html — Application Reference Data Set | Enterprise Profile | Manage Reference Data Sets
- https://docs.oracle.com/en/cloud/saas/financials/26d/fausf/set-up-data-access-to-business-units.html — Manage Reference Data Set Data Access for Users task
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-http-servername-fscmrestapi-resources-11.13.18.05-setidsets-get.html — setIdSets GET, finders, attributes
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-http-servername-fscmrestapi-resources-11.13.18.05-setidsets-post.html — setIdSets POST
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/api-set-id-assignments-business-unit.html — BU set assignment operations
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-http-servername-fscmrestapi-resources-11.13.18.05-setidassignmentsbusinessunit-post.html — POST attributes
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-http-servername-fscmrestapi-resources-11.13.18.05-setidassignmentsbusinessunit-get.html — finders
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/api-set-id-assignments-business-unit-list-values.html — LOV resource
- https://docs.oracle.com/en/cloud/saas/applications-common/25a/oafsm/key-information-about-setup-data-export-and-import-processes.html — Application Reference Data Set export note (25A)

## UNVERIFIED
- UNVERIFIED: Exact `DeterminantType` code for business unit in `setIdAssignmentsBusinessUnit` (e.g. `BU`) — read existing rows first.
- UNVERIFIED: Whether creating a BU auto-creates `setIdAssignmentsBusinessUnit` rows before the Manage Business Unit Set Assignment page is saved (doc implies assignment incomplete until saved).
- UNVERIFIED: Set codes of predefined Common and Enterprise sets (e.g. `COMMON`, `ENTERPRISE`).
- UNVERIFIED: Functional area of Manage Reference Data Sets / Manage Business Unit Set Assignment inside the **Procurement** offering.
- UNVERIFIED: FSM Setup Task CSV support + TaskCodes for Manage Reference Data Sets and Manage Business Unit Set Assignment.
- UNVERIFIED: Effects of overriding a set assignment after transactions exist.
- UNVERIFIED: 26D presence of `setIdAssignmentsSet`, `setIdReferenceGroups`, `setIdAssignmentsAssetBook`.
