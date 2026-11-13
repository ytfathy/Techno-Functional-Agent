# Data Access for Users (BU / Inventory Org / Cost Org / Set)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Fusion security = user + role + data ("who can do what on which data"). Job roles like Procurement Requester, Buyer, Inventory Manager are data-scoped: the user also needs a **data assignment** (security context + value) for that role, e.g. Business Unit = US1 BU. Without it the user sees nothing or gets errors such as POR-2010674.

## Where in Fusion (FSM)
- Task **Manage Data Access for Users** (generic; MSCMM offering → Functional area **Users and Security**).
- Task **Manage Business Unit Data Access for Users** — Procurement offering → **Users and Security**.
- Task **Manage Inventory Organization Data Access for Users** — Facilities functional area; for new MSCMM installations ("not applicable in an upgraded environment").
- Task **Manage Reference Data Set Data Access for Users** — Enterprise Profile.
- GL: Manage Data Access Set Data Access for Users.
- Page: Manage Data Access for Users — radio **Users with Data Access** / **Users without Data Access**; Create (+) → Create Data Access for User dialog; one user at a time; rows can be copied.
- Alternative: Data Provisioning Rules auto-provision from work assignments.

## Security contexts (from docs)
- Financials: Business Unit, Data Access Set, Ledger, Asset Book, Control Budget, Intercompany Organization, Reference Data Set, Legal Entity.
- SCM: Inventory Organization, Reference Data Set, Cost Organization, Manufacturing Plant.
- Procurement: Business Unit.

## Prerequisites & dependencies
- User exists and **already has the role** (data assignment does not grant the role: "The role must be assigned to the user separately").
- Target BU / inventory org exists and is active (`business-units`).
- Procurement agents are separate: Manage Procurement Agents (not covered here).

## Key fields
| Field (UI label) | REST attribute (dataSecurities) | Meaning | Notes / typical value |
|---|---|---|---|
| User Name | `UserName` | Sign-in user name | Search by sign-in name |
| Role | `RoleNameCr` (name) / `RoleCommonName` (technical, 256) | Data-scoped job role | e.g. Procurement Requester |
| Security Context | `SecurityContext` (255) | Business unit / inventory org / ... | Doc example value `"Ledger"` |
| Security Context Value | `SecurityContextValue` (255), `SecurityContextValue2/3` for multi-part | The BU / org | Name vs code format UNVERIFIED |
| Active | `ActiveFlag` (default true) | | Deactivate instead of delete |
| (id) | `UserRoleDataAssignmentId` | Key | path param |

## Common mistakes
- Assigning data access for a role the user doesn't have → no effect.
- Using display name instead of sign-in user name.
- Inventory: using Manage Data Access for Users when the pod expects the Facilities task (new installs) or vice versa.
- Procurement requesters: BU must have Requisitioning enabled and be Active.

## Security note
- Data assignments widen what a user can see/transact → treat every create/PATCH as a security change: require explicit approval, log before/after, never bulk-grant.
- No DELETE on `dataSecurities`; revoke by PATCH `ActiveFlag=false`.
- The calling integration user needs privileges to manage data access (exact privilege not documented on the REST page → UNVERIFIED).

## Channel & exact technique
- Preferred channel: **A (REST)**.
- `/fscmRestApi/resources/11.13.18.05/dataSecurities` — POST (create; `Upsert-Mode` header), GET collection, GET/PATCH `/dataSecurities/{UserRoleDataAssignmentId}`. No DELETE.
- Doc example payload: `{"SecurityContext":"Ledger","SecurityContextValue":"...","RoleNameCr":"Financial Analyst","UserName":"..."}`. Response has LOV links for context values — use them to get valid values.
- Always `rest_describe` first; GET with `q=UserName='<u>'` before POST to avoid duplicates.
- D (UI) fallback: Manage Business Unit Data Access for Users (steps in 26D Procurement doc: + → user name, role, Business unit context, value → Save and Close → Done).

## How to verify
- `GET .../dataSecurities?q=UserName='<u>';RoleNameCr='<role>'&onlyData=true`
- UI: Users with Data Access, Security Context = Business unit, search by user.
- Functional: user signs in and creates a requisition in the BU.

## Sources
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/api-data-security-users.html — operations, no DELETE
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-datasecurities-post.html — attributes, example payload
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/faser/data-access.html — 3-way model, task names, security contexts by product, data provisioning rules
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fammi/manage-data-access-for-users.html — MSCMM > Users and Security > Manage Data Access for Users; inventory org task note
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html — Procurement > Users and Security > Manage Business Unit Data Access for Users steps
- https://docs.oracle.com/en/cloud/saas/financials/26d/fausf/set-up-data-access-to-business-units.html — Manage Reference Data Set Data Access for Users, Users with/without Data Access
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/Chunk437736635.html — BU data access via Manage Data Access for Users

## UNVERIFIED
- VERIFIED-ON-POD 2026-11-14 (read): BU rows look like `SecurityContext="Business unit"`, `SecurityContextValue="US1 Business Unit"` (BU name), `RoleNameCr` = role display name (e.g. "Accounts Payable Supervisor"), `RoleCommonName` = role code, `UserName` as stored (case varies). Reference data set rows use `SecurityContext="Reference data set"`.
- VERIFIED-ON-POD 2026-11-14 (write): POST `{"UserName","RoleNameCr","SecurityContext":"Business unit","SecurityContextValue":"<BU name>"}` worked for Supplier Manager and Buyer, but returned 400 "The value of the attribute Role isn't valid." for Procurement Requester and Procurement Application Administrator, even after the role showed in `userRoleDetails`. Sending **`RoleCommonName` (role code) instead of `RoleNameCr`** worked for both → always send `RoleCommonName`.
- VERIFIED-ON-POD: `q=UserName='X'` returns 0 rows even when rows exist; read back by `UserRoleDataAssignmentId IN (...)`. Role LOV for a user: `dataSecurities/{anyId}/child/userRoleDetails`.
- VERIFIED-ON-POD: `q=` uses `and` between conditions (`;` gives "unexpected expression token").
- UNVERIFIED: Privilege required to call `dataSecurities`.
- UNVERIFIED: Whether rows created via Manage Inventory Organization Data Access for Users are visible in `dataSecurities`.
