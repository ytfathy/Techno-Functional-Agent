# Technical reporting: OTBI and BICC (extract)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL (no 26D-specific OTBI web-service page for Fusion; SCM subject-area list is the 26C book; BICC SOAP is the 26C book)

## Business purpose
- OTBI: real-time, security-trimmed ad hoc analyses/dashboards on logical subject areas (no SQL on tables). For managers/analysts and quick checks.
- BICC: bulk, scheduled extraction of Fusion data (PVO data stores) to files in WebCenter Content (UCM) or OCI Object Storage for data warehouses. Oracle labels it legacy; 26D Procurement/SCM playbooks say it is being replaced by the Data Extraction tool (separate guide "Data Extraction Tool", REST incl. extractSchedules). OTBI/BIP is NOT recommended for bulk integration (26D SCM playbook).

## Where in Fusion (FSM)
- OTBI/BICC are not FSM setup tasks. OTBI: Navigator > Tools > Reports and Analytics / Analytics catalog. BICC console: `https://<pod>/biacm` (path not on the pages read: UNVERIFIED) with Manage Offerings and Data Stores, Manage Extract Schedules, Manage Jobs.
- Security Console task for roles (Setup and Maintenance > Security Console).

## Prerequisites & dependencies
- OTBI access = duty roles whose names include "Transaction Analysis Duty" (they secure both the subject area and the BI Catalog folder). An analysis fails if the user cannot access ALL subject areas it uses. Data security (BU, org) applies via the user's data roles (`bu-data-access.md`).
- BICC: external storage (UCM or OCI: user OCID, namespace, bucket, API signing key) configured in the BICC console; global extract data stores selected.

## Key fields
### OTBI subject areas (names; all end with "Real Time")
Procurement (26C Procurement subject-areas book): `Procurement - Implemented Change Orders Real Time`, `Procurement - Pending Change Orders Real Time`, `Procurement - Procure To Pay Real Time`, `Procurement - Purchasing Agreements Real Time`, `Procurement - Purchasing Real Time`, `Procurement - Requisitions Real Time`, `Procurement - Spend Real Time`.
- `Procurement - Purchasing Real Time`: duty `Purchase Order Transaction Analysis Duty`; job roles Buyer, Category Manager, Procurement Contract Administrator, Procurement Manager, Purchase Analysis; granularity PO line / schedule / distribution; time dimension = PO Version Document Date; example metric Ordered Quantity.
SCM (26C SCM book; 26D list not checked): Inventory: `Inventory - Inventory ABC Real Time`, `Inventory - Inventory Balance Real Time`, `Inventory - Inventory Cycle Count Real Time`, `Inventory - Inventory Supply Real Time`, `Inventory - Inventory Transactions Real Time`, `Inventory - Inventory Transfer Order Real Time`, `Inventory Organization Real Time`. Receiving: `Receiving - Purchase Receipts Real Time`, `Receiving - Receipts Real Time`, `Receiving - Transactions Real Time`, `Receiving - Unordered Receipts Real Time`, `Receiving - Interorganization Receipts Real Time`, `Receiving - In-Transit Shipments Real Time`, `Receiving - In-Transit Advanced Shipment Notifications Real Time`, `Receiving - In-Transit Interorganization Inventory Transfers Real Time`. Order Management: `Order Management - Order Headers / Order Lines / Order Holds / Price Adjustments / Process Instances Real Time`. Product Management (item): e.g. `Product Management - Item Revisions Real Time`, `... - Structures Real Time`, `... - Item Catalog Category Hierarchy Real Time`, `... - Trading Partner Item Real Time`. Costing: e.g. `Costing - Receipt Accounting Real Time`, `Costing - Standard Cost Real Time`, `Costing - Period Inventory Valuation Real Time`, `Costing - Landed Costs Real Time`. Shipping: `Shipping Real Time`. Other: `Supply Chain Financial Orchestration Real Time`, `Supply Chain Orchestration - Supply Order/Supply Request Real Time`, `Supply Chain Planning Real Time`, `Security - Roles and Privileges Real Time`, `OTBI Usage Real Time`.

### Roles
| Role | Use | Code |
|---|---|---|
| BI Consumer Role | run analyses; OTBI "Transaction Analysis Duty" roles inherit it | UNVERIFIED |
| BI Author Role | create/edit analyses | UNVERIFIED |
| BI Administrator Role | superuser; dashboards, permissions | UNVERIFIED |
| `BIACM_ADMIN` (custom abstract role, category "BI - Abstract Roles") | BICC console access; members: ESS Administrator Role + `ORA_ASM_APPLICATION_IMPLEMENTATION_ADMIN_ABSTRACT` | exact code `BIACM_ADMIN` (created by you in Security Console) |
| BI Administrator role | alternative way to get BICC console access (26C page) | UNVERIFIED code |
| `BICC_UCM_CONTENT_ADMIN` | access to extract files in UCM (from search summary of 26A guide) | UNVERIFIED (page not opened) |

### Analyses / logical SQL
- Create: Navigator > Reports and Analytics > Create > Analysis (BI Author Role), pick subject area, columns, filters, save under `/Shared Folders/Custom/...` (not under predefined folders). Same Custom-folder rule as BIP (`tech-bi-publisher.md`).
- Logical SQL shape (BI Server presentation layer): `SELECT "<Folder>"."<Column>" s_1 FROM "Procurement - Purchasing Real Time" WHERE ... FETCH FIRST 100 ROWS ONLY`. Exact folder/column names must be read from the subject area on the pod (the docs page for Purchasing lists no folder names). Syntax details UNVERIFIED for Fusion.

### Running an analysis by web service
- Generic Oracle BI EE web services (not Fusion-specific docs): `SAWSessionService.logon(String name, String password)` returns sessionID; `logoff(String sessionID)`. `XmlViewService.executeSQLQuery(sql, outputFormat, executionOptions, sessionID)` returns rows; if more than one page, call `fetchNext`. WSDL on BI EE: `http://<host>/analytics/saw.dll?WSDL` (11g also `.../analytics/saw.dll/wsdl/v6`). Whether a Fusion pod exposes `/analytics/saw.dll` to external callers with basic auth: UNVERIFIED. executeSQLQuery argument details (executionOptions fields, outputFormat values) not read from the doc: UNVERIFIED.
- Documented, supported alternative for Fusion: wrap the report in BIP (data model with SQL, or analysis-as-data-source) and call `ExternalReportWSSService.runReport` (see `tech-bi-publisher.md`). "Analysis as BIP data source" is UNVERIFIED here.

### BICC
- Model: Offering (e.g. Procurement / SCM areas) -> Data Stores (View Objects, ExtractPVOs) -> Jobs -> Schedules -> external storage (UCM / OCI Object Storage). Use entity-specific ExtractPVOs; OTBI reporting PVOs are available but can cause performance problems for integration.
- Defaults/limits (26C/26B Procurement playbook): timeout 10 h per VO extract (Manage Offerings and Data Stores > Actions > Job Setting > Extract preference); extract only needed columns (default all); broker mode recommended (Flex VOs keep BI server mode); put data extracts and primary-key (deleted records) extracts in separate jobs; prune time controls incremental window; cleanup with `BICC Delete Expired UCM Files` job; not real time; no row-condition filtering; BICC cannot extract Analytics Publisher reports (use BIPJobType custom ESS job + `downloadEssJobExecutionDetails` / `exportBulkData`).
- Data store names: sample from Oracle SOAP page: `CrmAnalyticsAM.PartiesAnalyticsAM.Location`. Procurement/SCM data store names (Purchasing, Self Service Procurement) are listed in "Extract Data Stores for Procurement" (page `.../procurement/24c/oadpr/PorBiccExtractAMOverview.html`) and SCM "Extract Data Stores" book; names NOT captured -> read on the BICC console or the pages. Known doc name: `Inventory Organization Parameters` extract PVO (SCM 24D `oadsc/InvOrgParametersExtractPVO.html`).
- Programmatic run (SOAP, confirmed 26C):
  - Endpoint: `POST https://<pod>/bi/ess/esswebservice` (WSDL `?wsdl`). Header: WS-Security UsernameToken (Username, Password PasswordText, Nonce, Created) + `wsu:Timestamp` Created/Expires (fresh each call, else "Security Token Is Not Valid").
  - `sch:submitRequest`: `sch:description`; `sch:jobDefinitionId` {`typ:name`=`BICloudConnectorJobDefinition`, `typ:packageName`=`oracle.apps.ess.biccc`, `typ:type`=`JOB_DEFINITION`}; `sch:application`=`oracle.biacm`; `sch:requestedStartTime` (empty = now); `sch:requestParameters` of `typ:parameter` {`typ:dataType` STRING, `typ:name`, `typ:scope`, `typ:value`}:
    - `SYS_className` = `oracle.esshost.impl.CloudAdaptorJobImpl`
    - `SYS_application` = `BI Cloud Adaptor`
    - `EXTRACT_JOB_TYPE` = `VO_EXTRACT` | `PRIMARY_KEY_EXTRACT` | `VO_AND_PK_EXTRACT`
    - `DATA_STORE_LIST` = comma list (omit -> global list enabled in BICC)
    - `EXTERNAL_STORAGE_LIST` = storage name (e.g. `storage1`)
    - optional: `STARTED_NOTIFICATION`, `SUCCESS_NOTIFICATION`, `FAILURE_NOTIFICATION` (true/false), `MAIL_TO_ADDRESSES`, `FILE_EXPIRY_DAYS`, `FILE_SPLIT_SIZE` (unit MB vs GB differs between doc versions), `EXTRACT_COMPRESS_TYPE` (`zip`|`gzip`)
  - Response `requestId`; poll `getRequestState` / `getRequestDetail` with `sch:requestId`.
  - Generic ESS REST also exists: `POST /ess/rest/scheduler/v1/requests` (`jobDefinitionId`, `application`, `requestParameters[{name,paramType,value}]`, `schedule.recurrences[].icalString`). Whether it accepts the BICC job: UNVERIFIED.

## Common mistakes
- Using OTBI/BICC for transactional integrations; OTBI analysis mixing subject areas the user is not entitled to -> whole analysis fails.
- Saving analyses in predefined folders (lost on upgrade).
- BICC: stale WS-Security timestamp; extracting all columns; combining data and PK extracts in one job; leaving the 10 h timeout for huge first loads.
- Assuming subject-area folder/column names: read them from the pod.

## Channel & exact technique
- Preferred channel: OTBI analysis authoring = D (UI only; no documented REST for creating analyses). Running data via report = A-like SOAP `runReport` (BIP). BICC run = C-like SOAP to `/bi/ess/esswebservice` (job `BICloudConnectorJobDefinition`); BICC setup (storage, data stores, schedules) = D in BICC console.
- A: none for OTBI. B: none. C: BICC output files in UCM are fetched like ESS exports (UCM `GET_FILE`, `documentId`).
- D: BICC console / Reports and Analytics (playbook to be recorded on first use).

## How to verify
- OTBI: open analysis, Results tab returns rows; run as a user with the duty role to test security. BICC: `getRequestState` = success, file appears in UCM (search by extract job) or OCI bucket; BICC console Manage Jobs shows record counts.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26c/faopb/toc.htm - Procurement subject area names
- https://docs.oracle.com/en/cloud/saas/procurement/26c/faopb/Procurement-Purchasing-Real-Time-SA-402.html - Purchasing subject area detail
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faosm/toc.htm - SCM subject areas (26C)
- https://docs.oracle.com/en/cloud/saas/applications-common/26c/faser/oracle-fusion-transactional-business-intelligence-security.html - OTBI security (duty roles, catalog permissions)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fassc/business-intelligence-roles-explained.html - BI role names
- https://docs.oracle.com/en/cloud/saas/applications-common/26c/biacc/soap-api.html - BICC SOAP envelope and parameters
- https://docs.oracle.com/en/cloud/saas/applications-common/26c/biacc/provision-a-user-with-access-to-bicc.html - BIACM_ADMIN role
- https://docs.oracle.com/en/cloud/saas/procurement/26c/fainp/prc-business-intelligence-cloud-connector.html and .../26b/fainp/ss-business-intelligence-cloud-connector-bicc.html - BICC settings, limits, destinations
- https://docs.oracle.com/en/cloud/saas/applications-common/25d/farca/op-ess-rest-scheduler-v1-requests-post.html - ESS REST
- https://docs.oracle.com/middleware/1221/biee/BIEIT/methods.htm and https://docs.oracle.com/cd/E28280_01/bi.1111/e16364/methods.htm - generic BI EE SAWSessionService/XmlViewService (not Fusion-specific)

## UNVERIFIED
1. OTBI web-service access (`/analytics/saw.dll`, XmlViewService.executeSQLQuery argument details) on Fusion 26D pods.
2. Role codes for BI Consumer/Author/Administrator; `BICC_UCM_CONTENT_ADMIN` (only from a search summary).
3. 26D SCM subject-area list (26C used) and folder/column names inside subject areas.
4. BICC console URL path; Procurement/SCM data store (PVO) names; ESS REST acceptance of the BICC job.
5. Analysis-as-BIP-data-source and logical SQL syntax on Fusion.
6. FILE_SPLIT_SIZE unit (MB vs GB across doc versions).
7. Data Extraction tool REST details (only existence confirmed).
