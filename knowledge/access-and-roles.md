# Access for the agent user AI_SCM_AGENT (roles, data access, OAuth)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL (most role codes VERIFIED from 26D OTBI/Security references; 2 codes UNVERIFIED; OAuth: client credentials NOT supported for fscmRestApi)

## Business purpose
Define the minimum role set and data access for a dedicated integration user that the MCP server uses to read and configure SCM/Procurement setup and to run imports.

## Where in Fusion (FSM)
- Security Console: create user `AI_SCM_AGENT` (or via SCIM), assign roles.
- Setup and Maintenance > Manage Data Access for Users: BU / inventory org contexts.
- Procurement: Manage Procurement Agents (agent access per procurement BU) — UNVERIFIED detail.
- IAM identity domain (OCI console): confidential application for OAuth.

## Prerequisites & dependencies
- BUs, inventory orgs exist before data access can be granted.
- For CSV export/import: `ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT`.

## Key fields
| Role name | Role code | Type | Why the agent needs it | Unlocks |
|---|---|---|---|---|
| Application Implementation Consultant | `ORA_ASM_APPLICATION_IMPLEMENTATION_CONSULTANT_JOB` | Job | full access to all offering opt-in and setup tasks | FSM tasks, setupTasks, features, CSV export/import (with role below) |
| Export Import Functional Setups User | `ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT` | Abstract | required to submit setup CSV export/import by API and read codes | setupTaskCSVExports/Imports, setupOfferingCSV* |
| Procurement Application Administrator | `ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB` (verified on TEST pod via SCIM 2026-11-14) | Job | procurement setup tasks (BU functions, agents, styles…), Import Supplier, supplier upload duty | procurement FSM tasks, Import Supplier |
| Supplier Administrator | `ORA_POZ_SUPPLIER_ADMINISTRATOR_ABSTRACT` | Abstract | supplier profile + user provisioning, Import Supplier, FSCM Load Interface Administration | suppliers REST, Import Suppliers FBDI, erpintegrations (Access FSCM Integration Rest Service) |
| Supplier Manager | `ORA_POZ_SUPPLIER_MANAGER_ABSTRACT` | Abstract | create/merge supplier, spend authorization, Manage Supplier by Web Service, Load Interface File for Import | suppliers REST writes, supplier FBDI |
| Buyer | `ORA_PO_BUYER_JOB` | Job | create/change POs & agreements; Import PO/BPA/CPA/Requisition; FSCM Load Interface Administration | purchaseOrders, purchaseAgreements, draftPurchaseOrders REST; PO/BPA/CPA/Req FBDI |
| Procurement Manager | `ORA_PO_PROCUREMENT_MANAGER_JOB` | Job | Manage Procurement Agent, buyer assignment rules, ASL; inherits Buyer | procurement agents, ASL |
| Category Manager | `ORA_PON_CATEGORY_MANAGER_JOB` | Job | category/sourcing management | sourcing, category data |
| Inventory Manager | `ORA_INV_INVENTORY_MANAGER_JOB` | Job | inventory transactions, replenishment, counts; inventory setup | inventory REST |
| Warehouse Manager | `ORA_INV_WAREHOUSE_MANAGER_JOB` | Job | warehouse operations | inventory/receiving REST |
| Shipping Manager | `ORA_WSH_SHIPPING_MANAGER_JOB` | Job | outbound shipping exceptions/setup | shipping REST |
| Receiving Specialist (optional) | `ORA_CMF_RECEIVING_SPECIALIST_JOB` | Job | fiscal document receiving (Brazil-type) — only if needed | — |
| Product Data Steward (optional, items) | `ORA_EGI_PRODUCT_DATA_STEWARD_JOB` | Job | item creation / Item Import | items REST, Item FBDI |
| Integration Specialist | `ORA_FND_INTEGRATION_SPECIALIST_JOB` | Job | integration of enterprise systems; ERP Integration REST endpoints | erpintegrations |
| Human Resource Specialist (only if locations/HCM needed) | `ORA_PER_HUMAN_RESOURCE_SPECIALIST_JOB` | Job | locations, worker data | locationsV2 etc. |
| Procurement Requester | `ORA_POR_PROCUREMENT_REQUESTER_ABSTRACT` (verified on TEST pod via SCIM 2026-11-14) | Abstract | create requisitions (p2p test) | purchaseRequisitions |
| Employee | `ORA_PER_EMPLOYEE_ABSTRACT` | Abstract | self-service base; inherits Procurement Requester | — |
| IT Security Manager (only if SCIM role assignment in scope) | `ORA_FND_IT_SECURITY_MANAGER_JOB` | Job | users/roles admin | SCIM Users/Roles PATCH, userAccountRoles |

Notes from 26D Security Reference for Procurement (oapcm):
- Buyer: Purchase Order Administration duty → Import Purchase Order; Upload data for Purchase Orders for Import; Import Requisition, Import Approved Requisition, Import Blanket/Contract Purchase Agreement; FSCM Load Interface Administration → Load Interface File for Import, Load File to Interface, Manage File Import and Export, Transfer File, Access FSCM Integration Rest Service.
- Supplier Manager: Create/Import/Merge Supplier, Maintain Supplier/Site/Contact/Payment, Manage Supplier by Web Service, File Import and Export, Load Interface File for Import.
- Procurement Application Administrator: Setup and Maintain Applications, Execute Setup Tasks, Import Supplier, Upload data for Supplier Import, several procurement scheduled processes.
- Procurement Manager: Manage Buyer Assignment Rules, Manage Procurement Agent, ASL, Functional Setups, FSCM Load Interface Administration.

### Data access requirements
- Business Unit context for procurement roles (Buyer, Procurement Manager, Category Manager, Supplier Manager/Admin, Procurement App Admin, Procurement Requester): Manage Data Access for Users, one row per role per BU. Requester gets implicit primary-assignment BU only.
- Inventory Organization context for Inventory/Warehouse/Shipping/Receiving roles (UNVERIFIED context names).
- Procurement agent record for the agent user (needs a person/worker record) in each procurement BU with actions (Manage Purchase Orders, Manage Agreements, Manage Suppliers…) — UNVERIFIED (not researched in this pass).
- Least privilege: grant only the BUs/orgs in scope of the project.

### OAuth for Fusion REST (IAM identity domain)
- **Client Credentials grant works only for Spectra services (`/api/...`)**, NOT for `/fscmRestApi`, `/hcmRestApi` (incl. SCIM), `/crmRestApi`. For those use **JWT User Assertion** (non-interactive, on behalf of a user — fits AI_SCM_AGENT), Authorization Code, or Authorization Code + PKCE. Basic auth remains possible (not covered by this page).
- Confidential app steps (doc): Identity domain > Integrated applications > Add application > Confidential Application > name > Submit > OAuth configuration > Edit OAuth > "Configure this application as a client now" > tick grant type (for Fusion REST: JWT assertion; client credentials only for Spectra) > Client type **Trusted** > Import Certificate (alias = JWT `kid`) > Token issuance policy: Authorized resources = specific > Add resources > Add scope (select the Fusion Applications resource app; scope = `<resource primary audience><resource scope>`) > Activate > note Client ID.
- Token: `POST https://<identity domain URL>/oauth2/v1/token`, `Content-Type: application/x-www-form-urlencoded;charset=UTF-8`; client-credentials body (Spectra): `grant_type=client_credentials&scope=<scope>&client_id=<id>&client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer&client_assertion=<signed JWT>`. Response `{"access_token":"...","token":"Bearer","expires_in":3600}`. IDCS URLs from `https://idcs-<id>.identity.oraclecloud.com/.well-known/idcs-configuration`.
- JWT user assertion: grant type `urn:ietf:params:oauth:grant-type:jwt-bearer` with `assertion=<user JWT, sub=AI_SCM_AGENT>` — exact parameters UNVERIFIED (section exists, body not extracted).
- Call: `Authorization: Bearer <access_token>`.
- Roles can also be granted to the OAuth client app itself in Security Console (Application Extensions page) — "Manage Roles in Custom OAuth Client Applications".

## Common mistakes
- Picking client credentials for fscmRestApi → 401.
- Assigning job roles without data access → empty results / "no access to BU".
- Over-granting IT Security Manager when user admin is not in scope.

## Channel & exact technique
- Preferred: A (SCIM / userAccountRoles) to assign roles if IT Security Manager is granted; else manual Security Console (D).
- Data access: D (UI) — no REST found.

## How to verify
- `GET /hcmRestApi/scim/Users?filter=userName eq "AI_SCM_AGENT"&attributes=roles` lists all codes above.
- Smoke calls: `GET /fscmRestApi/resources/11.13.18.05/setupTasks?limit=1`, `GET /erpintegrations?finder=ESSJobStatusRF;requestId=1` (auth OK even if no row), a BU-scoped GET (e.g. purchaseOrders?limit=1) returns rows.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/Buyer-JR-133.html — ORA_PO_BUYER_JOB
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/Category-Manager-JR-132.html — ORA_PON_CATEGORY_MANAGER_JOB
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/Procurement-Manager-JR-135.html — ORA_PO_PROCUREMENT_MANAGER_JOB
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/Supplier-Administrator-JR-137.html — ORA_POZ_SUPPLIER_ADMINISTRATOR_ABSTRACT
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/Supplier-Manager-JR-138.html — ORA_POZ_SUPPLIER_MANAGER_ABSTRACT
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/Application-Implementation-Consultant-JR-2.html — ORA_ASM_APPLICATION_IMPLEMENTATION_CONSULTANT_JOB
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faopb/IT-Security-Manager-JR-1.html — ORA_FND_IT_SECURITY_MANAGER_JOB
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faosm/Inventory-Manager-JR-186.html, Warehouse-Manager-JR-185.html, Shipping-Manager-JR-194.html, Receiving-Specialist-JR-207.html, Product-Data-Steward-JR-190.html — SCM codes
- https://docs.oracle.com/en/cloud/paas/access-governance/oncai/ — ORA_FND_INTEGRATION_SPECIALIST_JOB, ORA_PER_HUMAN_RESOURCE_SPECIALIST_JOB (not 26D-specific)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-hcmrestapi-scim-users-get.html — ORA_PER_EMPLOYEE_ABSTRACT in example
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/oafsm/automate-export-and-import-of-csv-file-packages.html — ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapcm/toc.htm and Buyer_job_roles.html, Supplier_Manager_job_roles.html, Supplier_Administrator_job_roles.html, Procurement_Manager_job_roles.html, Procurement_Application_Administrator_job_roles.html — role types and privileges
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/configure_oauth.html — OAuth grant types per API family, confidential app steps, token request
- https://docs.oracle.com/en/cloud/saas/applications-common/24c/faser/procurement-requester-data-security.html — implicit BU access

## UNVERIFIED
- RESOLVED 2026-11-14: `ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB` exists on the pod (SCIM Roles).
- RESOLVED 2026-11-14: `ORA_POR_PROCUREMENT_REQUESTER_ABSTRACT` exists on the pod (SCIM Roles). Integration Specialist, HR Specialist and Functional Setups User codes also confirmed there.
- Integration Specialist / HR Specialist codes come from an Oracle Access Governance doc, not the 26D Security Reference.
- Data security context names for SCM roles; procurement agent requirements for the agent user.
- JWT user assertion token request parameters.
- Whether a dedicated "Supply Chain Application Administrator" role should replace the SCM job roles for setup (not researched).
