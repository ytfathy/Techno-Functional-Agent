# Technical reporting: BI Publisher (Analytics Publisher) in Fusion

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL (docs.oracle.com has no Fusion-specific page for the SOAP envelope, CatalogService in Fusion, BIP REST in Fusion, or BI role codes; those are UNVERIFIED. Table pages read were 25C/25D/26B/26D, see Sources.)

## Business purpose
Pixel-perfect / data-extract reports on Fusion transactional tables (SQL data model + layout), exposed as (a) catalog report, (b) scheduled process (ESS job of type BIPJobType), (c) SOAP-callable report returning base64 output. Used by a SCM technical consultant for: ad hoc extracts the REST API cannot filter, open-PO / receipts / on-hand reports, outbound interface files (via bursting + ESS), data validation after FBDI loads.

## Where in Fusion (FSM)
- Offering: any (task must be enabled at offering level: feature "Enterprise Scheduler Job Definitions and Job Sets").
- Functional area: Application Extensions
- Task name(s): `Manage Enterprise Scheduler Job Definitions and Job Sets` (tab Manage Job Definitions). Report authoring itself is in the BI Publisher UI (Navigator > Tools > Reports and Analytics > Browse Catalog), not FSM.
- CSV export/import of this task: UNVERIFIED (not found; treat as channel D / ESS UI).

## Prerequisites & dependencies
- User needs BI roles (below) to author; data model SQL runs against data source `ApplicationDB_FSCM` (Financials/SCM/Procurement) (11g Fusion edition guide; confirm in the data model editor on the pod).
- Catalog: put custom content in `/Shared Folders/Custom/<Family>/<Product>/...`. Predefined catalog content cannot be modified or have permissions changed; changes outside `/Shared/Custom` (or new folders under `/Shared`) are lost on upgrade. "Customize" copies a seeded report to Custom with the same hierarchy but NOT its permissions - reapply them.
- Report-level permissions go to Application Roles or users: Read, Execute, Write, Delete, Change Permissions, Set Ownership, Run Publisher Report, Schedule Publisher Report, View Publisher Output.
- Scheduled-process registration needs the report first (data model .xdm + report .xdo + layout) -> then job definition -> then Run privilege assigned to a role in Security Console.

## Key fields
### Roles (BI)
| Role (as named by Oracle) | Meaning | Role code |
|---|---|---|
| BI Consumer Role | run reports | UNVERIFIED (no code on docs page) |
| BI Author Role (inherits Consumer) | create/edit reports | UNVERIFIED |
| BI Administrator Role (superuser; inherits Author) | admin, catalog permissions; needed to create/edit data models in BIP per Fusion docs; test envs only | UNVERIFIED |
| BI Publisher Data Model Developer Role | create/edit BIP data models; inherited by Application Developer -> Application Implementation Consultant job roles | UNVERIFIED |
Caution (Oracle): BI Author/Data Model Developer allow arbitrary SQL against the data source; do not give to PROD users.
Verify codes on the pod: `rest_get` on the roles resource or Security Console > Roles search "BI ". Do not guess.

### ESS job definition (BIPJobType) - fields from Oracle
| Field (UI) | Value |
|---|---|
| Display Name | name users see in Schedule New Process |
| Name | alphanumeric only, no spaces/special chars (e.g. `AtkEssPrograms1`) |
| Job Application Name | `FscmEss` for Financial/SCM; `CrmEss`; `EarHcmEss` |
| Enable submission from Enterprise Manager | leave cleared |
| Job Type | `BIPJobType` (only type allowed when creating new) |
| Default Output Format | default format at submit |
| Report ID | catalog path under Shared Folders incl. extension: `Custom/<Family>/<Product>/<Report File Name>.xdo` |
| Enable submission from Scheduled Processes | leave selected |
| Parameters subtab | must match data model params and ORDER (11g/12c-era note; keep same order) |
| User Properties subtab | do not edit; `EXT_PortletContainerWebModule` auto-created |
Bursting job: report must have a bursting definition. Security: save creates privilege `RUN_<JOBNAME UPPER>` (e.g. `RUN_MYPROCESS1`, "Run My Process"); assign it to a role in Security Console.

### Data model / layout / bursting concepts (BIP guides; general product behaviour)
| Item | Notes |
|---|---|
| Data model | SQL data sets; parameters (text/menu/date), LOV via SQL, triggers (schedule trigger = SQL; no rows -> job skipped), bursting definition. Query Timeout property per data model; keep below system SQL timeout; queries > 600 s risk stuck threads -> schedule them |
| Layouts | RTF template, Excel template, eText (output formats pdf, html, excel, xlsx, csv, xml etc.; allowed values depend on template type) |
| Bursting query columns | KEY, TEMPLATE (layout name, not file), LOCALE, OUTPUT_FORMAT, DEL_CHANNEL, PARAMETER1..PARAMETER10 (EMAIL, FTP, FILE, WebDAV channels use them differently) |

## Common mistakes
- Report ID without `.xdo` or with leading `/Shared Folders/` (Oracle example starts at the folder inside Shared Folders: `Custom/...xdo`).
- Saving custom work in a predefined folder -> blocked / lost at upgrade.
- ESS job parameter order differs from data model order.
- Using `runReport` synchronously for big/slow reports -> timeouts; use ESS BIPJobType + `exportBulkData` / UCM instead (Oracle guidance: sync only for short-running, small reports; response is base64, MTOM not supported).
- Forgetting to grant the `RUN_` privilege / catalog Execute permission -> job not visible or fails.
- Seeded report customization loses permissions.

## Channel & exact technique
- Preferred channel: for RUNNING reports: A-like SOAP (below) for small output, or C (ESS `exportBulkData` on a BIPJobType job, via `ess_*`) for large. For CREATING catalog objects: `CatalogService` SOAP upload (UNVERIFIED in Fusion) else D (BIP UI). For registering the ESS job: D (task UI), no documented REST/CSV.
- Auth: HTTP basic over HTTPS is the normal Fusion pattern; Oracle's page only says protected services take credentials in the SOAP header, public services in the body (header format not given -> UNVERIFIED).

### Web services (endpoint paths confirmed by Oracle Integration doc)
| Service | Op | Path (append to pod host) | Credentials |
|---|---|---|---|
| ExternalReportWSSService (protected; recommended for synchronous BI report) | `runReport` | `/xmlpserver/services/ExternalReportWSSService?wsdl` | SOAP header |
| ReportService (public) | `runReport` | `/xmlpserver/services/v2/ReportService?wsdl` | in body (`userID`,`password`) |
| ScheduleReportWSSService (protected) | `getDocumentData` | `/xmlpserver/services/ScheduleReportWSSService?wsdl` | SOAP header |
| ScheduleService (public) | `getDocumentData` | `/xmlpserver/services/v2/ScheduleService?wsdl` | in body |
| CatalogService (v2) | see below | `/xmlpserver/services/v2/CatalogService?wsdl` (path from standard BIP; not on a Fusion page: UNVERIFIED) | in body (`userID`,`password`) |

### runReport request fields (ReportRequest data type, BIP Developer Guide)
| Field | Type / notes |
|---|---|
| `reportAbsolutePath` | string, e.g. `/Custom/Procurement/OpenPO.xdo` (Oracle example: `/HR Manager/HR Reports/Employee Listing.xdo`) |
| `attributeFormat` | string: pdf, html, excel, xlsx, csv, xml, ... (depends on template; `xml` for data) |
| `attributeLocale` | string, e.g. `fr-FR` / `en-US` |
| `attributeTemplate` | string, layout name e.g. `Employeelisting.rtf` |
| `attributeCalendar`, `attributeTimeZone`, `attributeUILocale` | optional |
| `sizeOfDataChunkDownload` | int; `-1` = return everything in one response (required if flattenXML true or no chunking wanted) |
| `flattenXML` | boolean (Analyzer for Excel) |
| `parameterNameValues` | ParamNameValues -> `listOfParamNameValues` -> array of ParamNameValue {`name`, `values` (ArrayOfString), `multiValuesAllowed`, `dataType`, `UIType`, ...} |
| `byPassCache`, `reportData`, `reportRawData`, `reportOutputPath`, `dynamicDataSource`, `XDOPropertyList` | optional |
Response ReportResponse: `reportBytes` (byte[] -> base64 in SOAP), `reportContentType` (e.g. application/pdf, text/xml, application/vnd.ms-excel), `reportFileID`, `reportLocale`, `metaDataList`. When `sizeOfDataChunkDownload` != -1, use `reportFileID` with `downloadReportDataChunk`.
Public `runReport(ReportRequest, userID, password)`; in-session variant `runReportInSession(ReportRequest, bipSessionToken)`. Also `getReportParameters(ReportRequest,...)` returns ParamNameValues (use to discover param names/defaults).

SOAP 1.2 envelope for ExternalReportWSSService: field names above are documented; the exact wrapper element names/namespace (`pub:runReport` / `pub:reportRequest` / `pub:appParams`, namespace `http://xmlns.oracle.com/oxp/service/PublicReportService`) are NOT on a docs.oracle.com Fusion page -> UNVERIFIED. Always fetch `GET <pod>/xmlpserver/services/ExternalReportWSSService?wsdl` and copy element names from it before building the envelope. Parse `reportBytes` base64 -> decode (xml/csv/pdf).
Skeleton to adapt after reading the WSDL (UNVERIFIED shape):
```xml
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:pub="http://xmlns.oracle.com/oxp/service/PublicReportService">
 <soap:Header/>
 <soap:Body><pub:runReport><pub:reportRequest>
  <pub:attributeFormat>xml</pub:attributeFormat>
  <pub:attributeLocale>en-US</pub:attributeLocale>
  <pub:reportAbsolutePath>/Custom/Procurement/OpenPO.xdo</pub:reportAbsolutePath>
  <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
  <pub:flattenXML>false</pub:flattenXML>
  <pub:parameterNameValues><pub:item><pub:name>P_BU</pub:name><pub:values><pub:item>US1 BU</pub:item></pub:values></pub:item></pub:parameterNameValues>
 </pub:reportRequest><pub:appParams/></pub:runReport></soap:Body>
</soap:Envelope>
```

### CatalogService operations (BIP 12c Developer Guide; Fusion availability UNVERIFIED)
All take trailing `userID, password` (or `bipSessionToken` in the `...InSession` variants).
| Operation | Signature (args) | Notes |
|---|---|---|
| `uploadObject` | `String uploadObject(reportObjectAbsolutePathURL, objectType, objectZippedData, userID, password)` | `objectZippedData` = zipped object bytes (base64 in SOAP). objectType valid: `xdm` (data model), `xdo` (report), `xsb` (sub-template), `xss` (style template). Files are packaged as `.xdmz` / `.xdoz`; Oracle's objectType list does NOT contain `xdmz`/`xdoz` (the z is the zip extension). If the pod rejects `xdm`, try what the WSDL/enum shows |
| `createObject` | `(folderAbsolutePathURL, objectName, objectType, objectDescription, objectData, userID, password)` | objectData bytes |
| `getFolderContents` | `CatalogContents getFolderContents(folderAbsolutePath, userID, password)` | returns `catalogContents` array of ItemData |
| `downloadObject` | `byte[] downloadObject(reportAbsolutePath, userID, password)` | zipped object |
| `deleteObject` | `boolean deleteObject(reportObjectAbsolutePath, userID, password)` | no deletes without user request |
| `createFolder` | `String createFolder(folderAbsolutePath, userID, password)` | e.g. `/Custom/Procurement/` |
| `copyObject` | `(srcOjectAbsolutePath, destObjectAbsolutePath, newName, ...)` | param name has a typo in docs; use WSDL |
| `objectExist`, `getObjectInfo`, `getObject(path, locale)`, `renameObject(path,newName)`, `updateObject(path, objectData)` | | `getObjectInfo` returns CatalogObjectInfo: objectName, objectAbsolutePath, objectType, objectSubType, owner, accessPermissions, creationDate, lastModifiedDate |

### BIP REST API
`/xmlpserver/services/rest/v1/reports/{reportPath}/run` (POST, JSON ReportRequest, report path URL-encoded), `GET /reports/{reportPath}` (definition), `/reports/{reportPath}/sampleData` exist in the standalone BI Publisher 12.2.1.4 and Oracle Analytics docs. NOT documented for Fusion Applications 26D -> UNVERIFIED on Fusion; prefer SOAP.

### Registering a BIP report as an ESS job
1. D: Setup and Maintenance > `Manage Enterprise Scheduler Job Definitions and Job Sets` > Manage Job Definitions > Create; fill fields in the table above; Save and Close.
2. Security Console: give `RUN_<NAME>` privilege to a role; give role catalog Execute/Schedule permission on the report.
3. Run via ESS: `POST /ess/rest/scheduler/v1/requests` (REST for Common Features; body `jobDefinitionId` (metadata id e.g. `JobDefinition://oracle/apps/ess/custom/<Path>/<Name>`: pattern UNVERIFIED for custom jobs), `application`, `requestParameters[{name,paramType,value}]`, optional `schedule.recurrences[].icalString`, `callbackSubscription`) or ErpIntegrationService `submitESSJobRequest` / `exportBulkData` (jobName = path;name, `jobOptions` `EnableEvent=Y` raises ExportBulkDataEvent with `documentId`; fetch file from UCM with `GET_FILE`). Large reports: configure report delivery to UCM/FTP and use exportBulkData.

## SQL: tables/views documented in Oracle "Tables and Views" books
(Schema FUSION; owners PO, POR, POZ, RCV, INV, EGP. Pages read were 25C/25D/26B/26D, columns may differ in 26D: check with `SELECT *` first.)
| Table | PK | Key columns |
|---|---|---|
| PO_HEADERS_ALL (PO.) | PO_HEADER_ID | SEGMENT1 (doc no; not unique alone), TYPE_LOOKUP_CODE, PRC_BU_ID, REQ_BU_ID, SOLDTO_LE_ID, VENDOR_ID, VENDOR_SITE_ID, DOCUMENT_STATUS, CURRENCY_CODE, AGENT_ID, APPROVED_FLAG, START_DATE, END_DATE, BLANKET_TOTAL_AMOUNT, CREATION_DATE, LAST_UPDATE_DATE. Unique: SEGMENT1+TYPE_LOOKUP_CODE+(SOLDTO_LE_ID for STANDARD else PRC_BU_ID) |
| PO_LINES_ALL | PO_LINE_ID | UNVERIFIED columns (only FK from other pages: referenced by PO_LINE_LOCATIONS_ALL.PO_LINE_ID) |
| PO_LINE_LOCATIONS_ALL | LINE_LOCATION_ID | PO_HEADER_ID, PO_LINE_ID, SHIPMENT_NUM, QUANTITY, QUANTITY_RECEIVED, QUANTITY_BILLED, QUANTITY_CANCELLED, NEED_BY_DATE, PROMISED_DATE, SHIP_TO_ORGANIZATION_ID, SCHEDULE_STATUS, CANCEL_FLAG, SHIPMENT_CLOSED_DATE, CLOSED_FOR_RECEIVING_DATE, CLOSED_FOR_INVOICE_DATE, CLOSED_REASON (no CLOSED_CODE) |
| PO_DISTRIBUTIONS_ALL | - | exists (FK from RCV_TRANSACTIONS.PO_DISTRIBUTION_ID); columns UNVERIFIED |
| POZ_SUPPLIERS | VENDOR_ID | SEGMENT1 (supplier number), PARTY_ID (-> HZ_PARTIES), VENDOR_TYPE_LOOKUP_CODE, START_DATE_ACTIVE, END_DATE_ACTIVE, CREATION_SOURCE, PARENT_VENDOR_ID, ONE_TIME_FLAG, DENIED_PARTY_FLAG, SUPPLIER_LOCKED_FLAG. ENABLED_FLAG is OBSOLETE: use dates |
| POR_REQUISITION_HEADERS_ALL (POR.) | REQUISITION_HEADER_ID | REQUISITION_NUMBER, PREPARER_ID, REQ_BU_ID, DESCRIPTION, DOCUMENT_STATUS, LIFECYCLE_STATUS, SUBMISSION_DATE, APPROVED_DATE, SOLDTO_LE_ID, APPROVAL_INSTANCE_ID, CREATION_DATE |
| POR_REQUISITION_LINES_ALL | - | joins on REQUISITION_HEADER_ID; columns UNVERIFIED |
| RCV_TRANSACTIONS (RCV.) | TRANSACTION_ID | TRANSACTION_TYPE, TRANSACTION_DATE, QUANTITY, UOM_CODE, PRIMARY_QUANTITY, PO_HEADER_ID, PO_LINE_ID, PO_LINE_LOCATION_ID, PO_DISTRIBUTION_ID, SHIPMENT_HEADER_ID, SHIPMENT_LINE_ID, ORGANIZATION_ID, VENDOR_ID, VENDOR_SITE_ID, SUBINVENTORY, LOCATOR_ID, INSPECTION_STATUS_CODE, ACCRUAL_STATUS_CODE, PO_UNIT_PRICE, CURRENCY_CODE, AMOUNT, QUANTITY_BILLED, PARENT_TRANSACTION_ID. Rows never updated; net after corrections via RCV_SUPPLY |
| EGP_SYSTEM_ITEMS_B (EGP.) | INVENTORY_ITEM_ID + ORGANIZATION_ID | ITEM_NUMBER, PRIMARY_UOM_CODE, INVENTORY_ITEM_STATUS_CODE, APPROVAL_STATUS, ENABLED_FLAG, PURCHASING_ITEM_FLAG, PURCHASING_ENABLED_FLAG. No description column: use EGP_SYSTEM_ITEMS_TL (columns UNVERIFIED) |
| INV_ONHAND_QUANTITIES_DETAIL (INV.) | ONHAND_QUANTITIES_ID | ORGANIZATION_ID, INVENTORY_ITEM_ID, SUBINVENTORY_CODE, LOCATOR_ID, LOT_NUMBER, PRIMARY_TRANSACTION_QUANTITY, OWNING_TYPE, OWNING_ENTITY_ID, CREATE_TRANSACTION_ID (-> INV_MATERIAL_TXNS.TRANSACTION_ID) |
| INV_ORG_PARAMETERS (INV.) | ORGANIZATION_ID | ORGANIZATION_CODE, MASTER_ORGANIZATION_ID, BUSINESS_UNIT_ID, LEGAL_ENTITY_ID, ITEM_DEFINITION_ORG_ID, SCHEDULE_ID, LOT_NUMBER_GENERATION, SERIAL_NUMBER_GENERATION |
| HR_ALL_ORGANIZATION_UNITS_F, FUN_ALL_BUSINESS_UNITS_V, INV_MATERIAL_TXNS | - | referenced as FK targets on other pages; own pages NOT read: columns UNVERIFIED |
Example (open PO schedules, from Oracle page; open_quantity is a derived expression):
`SELECT pll.line_location_id, pll.po_header_id, pll.quantity - NVL(pll.quantity_received,0) - NVL(pll.quantity_cancelled,0) open_qty FROM po.po_line_locations_all pll WHERE pll.shipment_closed_date IS NULL AND NVL(pll.cancel_flag,'N')='N'`
Always filter by BU (`PRC_BU_ID`, `REQ_BU_ID`, `BUSINESS_UNIT_ID`) and date for performance.

## How to verify
- GET the WSDL (HTTP 200, lists operations); `getFolderContents` on `/Custom` returns the uploaded object; `runReport` with `attributeFormat=xml` returns well-formed XML in `reportBytes`; Scheduled Processes shows the job and ESS request state; `ess_status` for submitted job.

## Sources
- https://docs.oracle.com/en/cloud/paas/application-integration/soap-adapter/call-oracle-fusion-applications-business-intelligence-publisher-report-services.html - ExternalReportWSSService/ScheduleReportWSSService/ReportService/ScheduleService paths, protected vs public, base64, MTOM, ESS+UCM pattern (exportBulkData, EnableEvent=Y, ExportBulkDataEvent, GET_FILE)
- https://docs.oracle.com/middleware/12212/bip/BIPDV/datatypes.htm - ReportRequest, ParamNameValue(s), CatalogObjectInfo fields
- https://docs.oracle.com/en/cloud/paas/analytics-cloud/acspd/to_reportrequest.html and .../to_reportresponse.html - sizeOfDataChunkDownload=-1, flattenXML; ReportResponse reportBytes/reportContentType/reportFileID/reportLocale
- https://docs.oracle.com/middleware/12212/bip/BIPDV/reportservice.htm - runReport signature, getReportParameters
- https://docs.oracle.com/middleware/12212/bip/BIPDV/catalogservice.htm - CatalogService operations and objectType values
- https://docs.oracle.com/middleware/bi12214/bip/BIPAP/op-v1-reports-reportpath-run-post.html - BIP REST (standalone product)
- https://docs.oracle.com/en/cloud/saas/sales/facaa/create-job-definitions-to-run-reports-as-scheduled-processes.html - BIPJobType job definition fields, RUN_ privilege
- https://docs.oracle.com/en/cloud/saas/human-resources/faucf/job-definitions.html - task/functional area, job types
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/faacc/manage-predefined-catalog-permission.html - /Shared/Custom rule
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fassc/business-intelligence-roles-explained.html - BI role names and hierarchy
- https://docs.oracle.com/en/cloud/saas/applications-common/26c/faser/oracle-fusion-transactional-business-intelligence-security.html - catalog permission types
- https://docs.oracle.com/en/cloud/saas/applications-common/25d/farca/op-ess-rest-scheduler-v1-requests-post.html - ESS REST submit
- https://docs.oracle.com/en/cloud/saas/procurement/26b/oedmp/poheadersall-4375.html (PO_HEADERS_ALL); https://docs.oracle.com/en/cloud/saas/procurement/26d/oedmp/polinelocationsall-23987.html (PO_LINE_LOCATIONS_ALL); .../procurement/25d/oedmp/pozsuppliers-23042.html; .../procurement/25c/oedmp/porrequisitionheadersall-3438.html; .../supply-chain-and-manufacturing/25c/oedsc/rcvtransactions-8872.html; .../egpsystemitemsb-4717.html; .../invonhandquantitiesdetail-6062.html; .../invorgparameters-26911.html (all under https://docs.oracle.com/en/cloud/saas/) - columns
- https://docs.oracle.com/cd/E24001_01/bi.1111/e18862/T527073T555155.htm and https://docs.oracle.com/cd/E29542_01/bi.1111/e22258/add_burst_def.htm - data model, ApplicationDB_FSCM, bursting query columns (older releases)

## UNVERIFIED
1. Exact SOAP 1.2 envelope (namespace/wrapper element names) and WSS header format for ExternalReportWSSService on Fusion 26D: read from `?wsdl`.
2. CatalogService path/availability on Fusion pods (`/xmlpserver/services/v2/CatalogService`), and whether a WSS-secured variant exists.
3. BIP REST API on Fusion 26D.
4. Role codes for BI Consumer / Author / Administrator / Data Model Developer.
5. FSM CSV export/import support for the job definition task.
6. Columns of PO_LINES_ALL, PO_DISTRIBUTIONS_ALL, POR_REQUISITION_LINES_ALL, EGP_SYSTEM_ITEMS_TL, INV_MATERIAL_TXNS, HR_ALL_ORGANIZATION_UNITS_F, FUN_ALL_BUSINESS_UNITS_V.
7. Table pages used were 25C/25D/26B (PO_LINE_LOCATIONS_ALL is 26D): 26D column differences not checked.
8. `jobDefinitionId` metadata pattern for custom BIPJobType jobs; data source name `ApplicationDB_FSCM` (from 11g Fusion doc).
9. Whether upload objectType accepts `xdm`/`xdo` zipped vs `xdmz`/`xdoz` on Fusion.
