# Users and role assignment (SCIM + HCM userAccounts)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Read Fusion users and their roles, and grant/revoke roles (e.g. give a buyer the Buyer job role, give AI_SCM_AGENT its roles). Data access (BU / inventory org scoping) is a separate setup.

## Where in Fusion (FSM)
- Security Console (Tools > Security Console): users, roles, role copy.
- Setup and Maintenance task **Manage Data Access for Users** — assign BU-scoped data access for roles (doc-referenced name).
- HCM: Manage Users / person record (users linked to persons).

## Prerequisites & dependencies
- Caller needs IT Security Manager (`ORA_FND_IT_SECURITY_MANAGER_JOB`) or equivalent for SCIM writes; userAccounts REST needs "Use REST Service - User Accounts" privileges (read-only aggregate: "Use REST Service - User Accounts Read Only").
- Role assignment does not grant data: roles that need BU/org context also need data access (see below).

## Key fields
### SCIM Users — `/hcmRestApi/scim/Users` (VERIFIED 26D)
Ops: POST, GET; GET/PUT/PATCH/DELETE `/Users/{id}`.
Query: `filter`, `attributes`, `count`, `startIndex` (1-based), `sortBy`, `sortOrder`.
Attributes: `id` (GUID, read-only), `schemas` (`urn:scim:schemas:core:2.0:User`), `userName`, `name{familyName,givenName}`, `displayName`, `emails[{value,type,primary}]`, `active`, `password` (write-only), `roles[{id,value,displayName,description}]` (read-only; `value` = role code, e.g. `ORA_PER_EMPLOYEE_ABSTRACT`), `urn:scim:schemas:extension:fa:2.0:faUser{userCategory,accountType,partyInformation[],workerInformation[{businessUnit,department,job,manager,personNumber}],assignServiceAdminRoles}`, `meta{created,lastModified,location}`.
```
GET /hcmRestApi/scim/Users?filter=userName eq "AI_SCM_AGENT"   (no attributes=…roles: the 2026-11-25 pod rejects it with 400 "Attribute roles is not a valid attribute"; the full user includes roles)
```
Response: `{"itemsPerPage":..,"startIndex":1,"Resources":[{...}]}`.

### SCIM Roles — `/hcmRestApi/scim/Roles` (VERIFIED 26D)
Ops: GET, GET `/Roles/{id}`, PATCH `/Roles/{id}`. Attributes: `id`, `name` (role code), `displayName`, `description`, `category`, `members[{value}]`, `schemas` (`urn:oracle:apps:scim:schemas:fa:1.0:Role`), `meta`.
```
GET /hcmRestApi/scim/Roles?filter=name eq "ORA_PO_BUYER_JOB"&attributes=id,name,displayName
```
(filter on `name` = role code: by schema, example not on page.)
Assign / revoke (204 No Content):
```
PATCH /hcmRestApi/scim/Roles/{roleId}
Content-Type: application/json
{"members":[{"value":"<user id GUID>","operation":"ADD"},
            {"value":"<user id GUID>","operation":"REMOVE"}]}
```
Also `POST /hcmRestApi/scim/Bulk`, GET `/Schemas`, `/ResourceTypes`. No `/Groups` resource in the 26D endpoint list.

### HCM userAccounts — `/hcmRestApi/resources/11.13.18.05/userAccounts` (VERIFIED, current HCM guide)
- GET collection, finders: `PrimaryKey` (UserId), `findByFinder` (GUID). Item key `{GUID}`. Attributes: `GUID, UserId, Username, PersonId, PersonNumber, SuspendedFlag, CredentialsEmailSentFlag, CreatedBy, CreationDate, LastUpdateDate, LastUpdatedBy`; child `userAccountRoles`.
- POST create user account; PATCH `/{GUID}`.
- Role assignment child: `POST /userAccounts/{GUID}/child/userAccountRoles` body `{"RoleId":5071}` or `RoleCode` (attributes `RoleCode` ≤240, `RoleId`, `UserRoleId`) → 201 with `UserRoleId, RoleId, RoleCode`. GET list; GET/DELETE `/child/userAccountRoles/{UserRoleId}`.
```
GET /hcmRestApi/resources/11.13.18.05/userAccounts?q=Username='AI_SCM_AGENT'&expand=userAccountRoles
```

### Data access
- Done in UI task Manage Data Access for Users (role + security context e.g. Business Unit / Inventory Organization). Procurement Requester gets implicit access to the BU of the primary assignment; other BUs must be granted explicitly. BU access aggregates across roles.
- Buyer also needs to be a **procurement agent** for the procurement BU (Manage Procurement Agents) — see procurement knowledge (UNVERIFIED here).
- No 26D REST resource for user data access found → channel D (UI) or B (FSM CSV, if the task supports it; check `setupTasks`).

### Verified on the TEST pod (2026-11-14)
- `rest_get('/hcmRestApi/scim/Users?filter=userName eq "x"')` works (client sends only SCIM params `count`/`startIndex`; filter stays in the path). `attributes=...,roles` → 400 "Attribute roles is not a valid attribute"; omit `attributes` and `roles` comes back by default.
- Role ids (SCIM GUID): Supplier Manager `1E6678139A59564AE9D9F5806B490691`, Buyer `E3A40F5AB1E590D7E040F00AC6466664`, Procurement Requester `EBEFF074FF40433DA0D522FFA352626D`, Procurement Application Administrator `9C8A3991A0CA40118958B20076F117B1`, IT Security Manager `EE7560D7E2B14CAF82166E53D36C1E69`.
- `hcm_impl` SCIM id `<user GUID>`; has IT Security Manager, no procurement roles. `userAccounts?q=Username='HCM_IMPL'` returns 0 rows (use SCIM instead).
- Demo pod `PRC_IMPL` has `PO_PROCUREMENT_APPLICATION_ADMIN_AIGENT` (custom) but not Supplier Manager/Buyer.

## Common mistakes
- Using SCIM `roles` attribute on PATCH Users to assign roles — roles are read-only on Users; assign via `PATCH /Roles/{id}` members or `userAccountRoles`.
- Using `RoleId` from SCIM (`id` is a GUID string) in `userAccountRoles` (expects numeric `RoleId`) — use `RoleCode` there.
- Forgetting data access → user sees nothing in the BU.
- Role provisioning is asynchronous in some flows (LDAP sync) — re-read after a short delay (UNVERIFIED timing).

## Channel & exact technique
- Preferred channel: A. Read: SCIM Users with only `filter=` (MCP tool `user_roles`). Assign (MCP tool `assign_roles`): `userAccountRoles` POST with `RoleCode` (one call, by code) or SCIM `PATCH /Roles/{id}`.
- Data access: D (playbook) unless a CSV task is found.

## How to verify
`GET /hcmRestApi/scim/Users/{id}?attributes=roles` or `userAccounts/{GUID}/child/userAccountRoles` contains the role code.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-hcmrestapi-scim-users-get.html — SCIM Users params/schema/example
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-hcmrestapi-scim-roles-get.html — SCIM Roles schema/example
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-hcmrestapi-scim-roles-id-patch.html — members ADD/REMOVE payload
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/rest-endpoints.html — SCIM endpoints list (Users, Roles, Bulk, Schemas, ResourceTypes)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Manage_Collections.html — SCIM filter operators/paging
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-useraccounts-get.html — userAccounts finders/attributes
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-useraccounts-guid-child-useraccountroles-post.html — userAccountRoles POST
- https://docs.oracle.com/en/cloud/saas/applications-common/24c/faser/procurement-requester-data-security.html — implicit BU access, Manage Data Access for Users

## UNVERIFIED
- HCM farws pages are the unversioned (current) guide, not /26d/ URLs.
- SCIM `filter=name eq "<code>"` on Roles (attribute exists; example not shown).
- No REST for data access assignments in 26D.
- Exact privilege names required to call SCIM PATCH / userAccountRoles POST.

## MCP tools (2026-11-25)
- `find_role(text)` — SCIM `Roles?filter=name co "x" or displayName co "x"`.
- `user_roles(user, filter_text)` — compact role list of any user.
- `assign_roles(user, [codes], remove=False)` — SCIM `PATCH /Roles/{id}` members ADD/REMOVE; skips held/not-held roles, backs up the user roles to `backups/<date>/` and re-reads to verify. High-impact (CLAUDE.md rule 6).
- `ensure_access(resource_path)` — maps a 403 resource to the roles that grant it (`security.ROLE_MAP`) and adds the missing ones to the agent user only (add-only; CLAUDE.md self-grant rule).
- `grant_data_access(user, role_code, context, [values])` — `dataSecurities` POST with `RoleCommonName`; contexts as stored: `Business unit` (BU name), `Inventory organization` (org code), `Reference data set`, cost organization.
