# Channel C — FBDI + ESS via ERP Integrations REST (erpintegrations)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL (erpintegrations payloads/finders VERIFIED; FBDI template/UCM/process names VERIFIED; ESS job paths and submit-argument order UNVERIFIED)

## Business purpose
Bulk-load master/transaction data (suppliers, sites, POs, agreements, requisitions, items, receipts) when no REST create exists or volume is high. Flow: build CSVs from the FBDI xlsm template → zip → upload to UCM (WebCenter Content) account → "Load Interface File for Import" → product import job → read output/log.

## Where in Fusion (FSM)
- UI equivalent: Tools > File Import and Export (upload to account) + Tools > Scheduled Processes.
- ESS job definitions (to read package/name/params): Setup and Maintenance > Application Extensions functional area > **Manage Enterprise Scheduler Job Definitions and Job Sets for Financial, Supply Chain Management, and Related Applications** > Manage Job Definitions > select > Edit (read only, Cancel).

## Prerequisites & dependencies
- Agent user needs import privileges of the object (see table) + FSCM Load Interface Administration duty (Load Interface File for Import, Manage File Import and Export, Access FSCM Integration Rest Service) — inherited by Buyer and Supplier Manager/Administrator per 26D Security Reference.
- Referenced master data must exist (BU, supplier, items, locations, buyers…).

## Key fields — erpintegrations attributes (all strings)
| Attribute | Meaning |
|---|---|
| `OperationName` | operation: `importBulkData`, `uploadFileToUCM`, `submitESSJobRequest`, `exportBulkData`, (GET) `getESSJobStatus`, `getESSExecutionDetails`, `downloadESSJobExecutionDetails`, `getDocumentIdsForFilePrefix`, `getDocumentForDocumentId` |
| `DocumentContent` | base64 file content (zip) |
| `FileName` | file name, e.g. `PozSuppliersInt_123.zip` |
| `ContentType` | `"zip"` in all examples |
| `DocumentAccount` | UCM account, `$`-suffixed form: `fin$/payables$/import$` → for suppliers `prc$/supplier$/import$` |
| `DocumentId` | UCM doc id (returned by uploadFileToUCM) |
| `JobName` | `"<job package path>,<job definition name>"` (importBulkData / exportBulkData) |
| `ParameterList` | comma-separated submit args for JobName; `#NULL` for null |
| `JobPackageName` / `JobDefName` / `ESSParameters` | submitESSJobRequest equivalents |
| `CallbackURL` | `#NULL` if none |
| `NotificationCode` | 2 digits: 1st 1=email 2=bell 3=both; 2nd 0=always 1=success 2=failure; `#NULL` = none. Only for loadAndImportData, ImportBulkData, ExportBulkData, extractAndPurge |
| `JobOptions` | e.g. `"InterfaceDetails=1,ImportOption=Y ,PurgeOption = Y,ExtractFileType=ALL"` |
| `ReqstId` | ESS request id (response) |
| `RequestStatus` | job status (getESSJobStatus) or JSON string tree (getESSExecutionDetails) |
| `FileType` | `LOG`, `OUT`, or both if empty (REST page); example uses `ALL`. SOAP doc: `Log`/`Out`/`All` |
| `StatusCode`, `LoadRequestId`, `ProcessName`, `Comments` | other |

## Common mistakes
- `DocumentAccount` without `$`: REST examples use `fin$/payables$/import$`; FBDI pages list `prc/supplier/import` → convert each segment to `seg$`.
- Wrong `ParameterList` order: it is the job's submit.argument1..N order, NOT the UI order; blanks must be `#NULL` (or empty).
- Expecting importBulkData `ReqstId` to be the import job: it is the **first job in the job list = Load Interface File for Import**; the product import runs as child — check with `ESSExecutionDetailsRF`.
- Running the import twice on same Batch ID without purge.
- Exceeding volume: supplier import advises batches ≤20,000 records; requisition import Maximum Batch Size ≤2500.

## Channel & exact technique
Endpoint: `POST|GET /fscmRestApi/resources/11.13.18.05/erpintegrations`, Content-Type `application/vnd.oracle.adf.resourceitem+json` (doc curl) / `application/json` (schema).

### 1. uploadFileToUCM (VERIFIED)
```json
POST /erpintegrations
{"OperationName":"uploadFileToUCM","DocumentContent":"<b64 zip>","DocumentAccount":"prc$/supplier$/import$",
 "ContentType":"zip","FileName":"PozSuppliersInt.zip","DocumentId":null}
```
→ `DocumentId` (e.g. "10621").

### 2a. submitESSJobRequest (VERIFIED)
```json
{"OperationName":"submitESSJobRequest",
 "JobPackageName":"oracle/apps/ess/financials/commonModules/shared/common/interfaceLoader",
 "JobDefName":"InterfaceLoaderController",
 "ESSParameters":"<importProcessId>,<DocumentId>,N,N"}
```
→ `ReqstId`. `InterfaceLoaderController` = Load Interface File for Import. Example ESSParameters `"1,10420,N,N"`: arg1 = import process (numeric id of the target import process, per doc example), arg2 = UCM DocumentId. Meaning of args 3–4 and the numeric id per object: UNVERIFIED.

### 2b. importBulkData = upload + load + import in one call (VERIFIED)
```json
{"OperationName":"importBulkData","DocumentContent":"<b64 zip>","ContentType":"zip","FileName":"X.zip",
 "DocumentAccount":"prc$/supplier$/import$",
 "JobName":"<package path>,<job def>","ParameterList":"<args of the import job>",
 "CallbackURL":"#NULL","NotificationCode":"10","JobOptions":"InterfaceDetails=1,ImportOption=Y ,PurgeOption = Y,ExtractFileType=ALL"}
```
→ `ReqstId` (Load Interface File for Import request). Doc AP example: `JobName "oracle/apps/ess/financials/payables/invoices/transactions,APXIIMPT"`. Doc generic example: `JobName "oracle/apps/ess/financials/commonModules/shared/common/interfaceLoader,InterfaceLoaderController"`, `ParameterList "1,7584,N,N"`. `InterfaceDetails` value per object: UNVERIFIED.

### 3. Status — getESSJobStatus (VERIFIED)
```
GET /erpintegrations?finder=ESSJobStatusRF;requestId=14557
```
→ `items[0].RequestStatus` e.g. `"SUCCEEDED"`.
Full tree: `GET /erpintegrations?finder=ESSExecutionDetailsRF;requestId=14557` → `RequestStatus` is a JSON **string**: `{"JOBS":{"JOBNAME","JOBPATH","REQUESTID","STATUS","CHILD":[{...}]}}` — parse with json.loads.
Status values: documented UI statuses (26D): Blocked, Canceled*, Canceling, Completed, Error*, Error Auto-Retry, Error Manual Recovery, Expired*, Finished*, Hold, Paused, Pending Validation, Ready, Retrying, Running, Schedule Ended, Succeeded*, Validation Failed*, Wait, Warning* (*final). REST string seen: `SUCCEEDED`. Treat terminal as {`SUCCEEDED`,`WARNING`,`ERROR`,`CANCELLED`,`EXPIRED`,`FINISHED`,`VALIDATION_FAILED`} — upper-case spellings other than SUCCEEDED UNVERIFIED.

### 4. Output/log — downloadESSJobExecutionDetails (VERIFIED)
```
GET /erpintegrations?finder=ESSJobExecutionDetailsRF;requestId=14557,fileType=ALL
```
→ `items[0].DocumentContent` = base64 zip of `<requestId>.log` + output files. Run on the **import job's** request id (child from ESSExecutionDetailsRF) to get the import report.

### Other finders (VERIFIED)
- `DocumentIdsByFilePrefixRF;filePrefix=..,docAccount=..,comment=..` → `DocumentId`, `FileName` (docAccount example `fin%2FgeneralLedger%2Fimport`).
- `DocumentRF;docId=233799` → `DocumentContent`.
- `PrimaryKey;OperationName=..`.
- exportBulkData output lands in UCM as `ExportBulkData_<JobName>_<RequestId>.zip` — poll DocumentIdsByFilePrefixRF, then DocumentRF.

### Purge interface (VERIFIED example, AR)
```json
{"OperationName":"submitESSJobRequest","JobPackageName":"oracle/apps/ess/financials/commonModules/shared/common/interfaceLoader",
 "JobDefName":"InterfaceLoaderPurge","ESSParameters":"59,XXXXX,,,Y,ORA_FBDI"}
```
(59 = import process id for AR customers in that example; XXXXX = Load Interface File request id). Returns 204.

### SCM / Procurement FBDI objects (26D)
Template base URL: `https://www.oracle.com/webfolder/technetwork/docs/fbdi-26d/fbdi/xlsm/<Template>.xlsm`, control files `.../fbdi-26d/fbdi/controlfiles/<ctl>`. CSV name inside zip = control file base name + `.csv` (convention; UNVERIFIED — generated by the xlsm "Generate CSV File" button; never rename).

| Object | Template | Control files (→ CSV) | UCM account (REST form) | Import process (UI name) | Interface tables | Key privileges |
|---|---|---|---|---|---|---|
| Suppliers | SupplierImportTemplate.xlsm | PozSuppliersInt.ctl | prc/supplier/import (`prc$/supplier$/import$`) | Import Suppliers | POZ_SUPPLIERS_INT | POZ_IMPORT_SUPPLIER_PRIV |
| Supplier addresses | SupplierAddressImportTemplate.xlsm | PozSupAddressesInt.ctl | prc/supplier/import | Import Supplier Addresses | POZ_SUP_ADDRESSES_INT | POZ_IMPORT_SUPPLIER_PRIV |
| Supplier sites | SupplierSiteImportTemplate.xlsm | PozSupplierSitesInt.ctl, PozSupThirdPartyInt.ctl | prc/supplier/import | Import Supplier Sites | POZ_SUPPLIER_SITES_INT, POZ_SUP_THIRDPARTY_INT | POZ_IMPORT_SUPPLIER_PRIV |
| Site assignments | SupplierSiteAssignmentImportTemplate.xlsm | PozSiteAssignmentsInt.ctl | prc/supplier/import | Import Supplier Site Assignments | POZ_SITE_ASSIGNMENTS_INT | POZ_IMPORT_SUPPLIER_PRIV |
| Supplier contacts | SupplierContactImportTemplate.xlsm | PozSupContactsInt.ctl, PozSupContactAddressesInt.ctl | prc/supplier/import | Import Supplier Contacts | POZ_SUP_CONTACTS_INT, POZ_SUP_CONTACT_ADDRESSES_INT | POZ_IMPORT_SUPPLIER_PRIV |
| Purchase orders | POPurchaseOrderImportTemplate.xlsm | PoHeadersInterfaceOrder.ctl, PoLinesInterfaceOrder.ctl, PoLineLocationsInterfaceOrder.ctl, PoDistributionsInterfaceOrder.ctl | prc/purchaseOrder/import (`prc$/purchaseOrder$/import$`) | Import Orders | PO_HEADERS_INTERFACE, PO_LINES_INTERFACE, PO_LINE_LOCATIONS_INTERFACE, PO_DISTRIBUTIONS_INTERFACE | PO_IMPORT_PURCHASE_ORDER_PRIV (+PO_BYPASS_PURCHASE_ORDER_APPROVAL_PRIV) |
| Blanket agreements | POBlanketPurchaseAgreementImportTemplate.xlsm | PoHeadersInterfaceBlanket.ctl, PoLinesInterfaceBlanket.ctl, PoLineLocationsInterfaceBlanket.ctl, PoGAOrgAssignInterfaceBlanket.ctl, PoAttrValuesInterfaceBlanket.ctl, PoAttrValuesTlpInterfaceBlanket.ctl | prc/blanketPurchaseAgreement/import | Import Blanket Agreements | PO_HEADERS_INTERFACE, PO_LINES_INTERFACE, PO_LINE_LOCATIONS_INTERFACE, PO_GA_ORG_ASSIGN_INTERFACE, PO_ATTR_VALUES_INTERFACE, PO_ATTR_VALUES_TLP_INTERFACE | PO_IMPORT_BLANKET_PURCHASE_AGREEMENT_PRIV |
| Contract agreements | POContractPurchaseAgreementImportTemplate.xlsm | PoHeadersInterfaceContract.ctl, PoGAOrgAssignInterfaceContract.ctl | prc/contractPurchaseAgreement/import | Import Contract Agreements | PO_HEADERS_INTERFACE, PO_GA_ORG_ASSIGN_INTERFACE | PO_IMPORT_CONTRACT_PURCHASE_AGREEMENT_PRIV |
| Requisitions | RequisitionImportTemplate.xlsm | PorReqHeadersInterfaceAll.ctl, PorReqLinesInterfaceAll.ctl, PorReqDistsInterfaceAll.ctl | prc/requisition/import | Load Interface File for Import → Import Requisitions | POR_REQ_HEADERS_INTERFACE_ALL, POR_REQ_LINES_INTERFACE_ALL, POR_REQ_DISTS_INTERFACE_ALL | POR_IMPORT_REQUISITION_PRIV, POR_IMPORT_APPROVED_REQUISITION_PRIV |
| Items | ItemImportTemplate.xlsm | EgpSystemItemsInterface.ctl, EgpItemRevisionsInterface.ctl, EgpItemCategoriesInterface.ctl, EgoItemAssociationsIntf.ctl, EgpItemRelationshipsIntf.ctl, EgoItemIntfEffb.ctl, EgoItemIntfEfftl.ctl, EgoItemRevisionIntfEffb.ctl, EgoItemRevisionIntfEfftl.ctl, EgoItemSupplierIntfEffb.ctl, EgoItemSupplierIntfEfftl.ctl, EgoStyleVariantAttrvsIntf.ctl, EgpTradingPartnerItemsIntf.ctl, EgpOrgAssociationsIntf.ctl | scm/item/import (`scm$/item$/import$`) | Item Import Job (Load Interface File: Import Process = "Item Import") | EGP_SYSTEM_ITEMS_INTERFACE, … | UNVERIFIED |
| Receipts | ReceivingReceiptImportTemplate.xlsm | RcvHeadersInterface.ctl, RcvTransactionsInterface.ctl, RcvLotsInterface.ctl, RcvSerialNumbersInterface.ctl, RcvLpnInterface.ctl | scm/receivingReceipt/import | Manage Receiving Transactions | RCV_HEADERS_INTERFACE, RCV_TRANSACTIONS_INTERFACE, INV_TRANSACTION_LOTS_INTERFACE, INV_SERIAL_NUMBERS_INTERFACE, INV_LPN_INTERFACE | UNVERIFIED |

Import job parameters (UI order, 26D Scheduled Processes reference):
- **Import Suppliers / Supplier Sites / Site Assignments / Contacts / Addresses**: 1 Import Options (New | Rejected | All), 2 Report Exceptions Only (Yes/No), 3 Batch ID. (Addresses/site-assignments pages not fetched; assumed same — UNVERIFIED.)
- **Import Orders**: 1 Procurement BU*, 2 Default Buyer*, 3 Create or Update Item (Yes/No), 4 Approval Action* (Do Not Approve | Submit for Approval | Bypass Approval), 5 Import Source, 6 Batch ID, 7 Default Requisitioning BU*, 8 Communicate Orders (Yes/No).
- **Import Blanket Agreements**: 1 Procurement BU*, 2 Default Buyer*, 3 Create or Update Item, 4 Approval Action, 5 Import Source, 6 Batch ID, 7 Communicate Agreements.
- **Import Contract Agreements**: 1 Procurement BU*, 2 Default Buyer*, 3 Approval Action, 4 Import Source, 5 Batch ID, 6 Communicate Agreements.
- **Import Requisitions**: Import Source, Import Batch ID, Maximum Batch Size (≤2500, default 2500), Requisitioning BU*, Group By* (Item|Buyer|Category|Location|Supplier|None), Next Requisition Number, Initiate Approval after Requisition Import* (Yes/No, default No), Error Processing* (All|Partial, default All).
(* required). Submit-argument values are usually IDs/codes, not display names — UNVERIFIED; read job definition parameters before building `ParameterList`.

### VERIFIED-ON-POD 2026-11-14 (26D) — Import Supplier Sites via importBulkData
- `JobName "/oracle/apps/ess/prc/poz/supplierImport,ImportSupplierSites"`, `ParameterList "NEW,N,<BatchId>"` (Import Options, Report Exceptions Only, Batch ID), `DocumentAccount prc$/supplier$/import$`, no `JobOptions` → works. Log echoes "Import Options: NEW / Report Exceptions Only: N / Batch Id: …".
- Request chain: load `ReqstId` (Load Interface File for Import, children Transfer File + Load File to Interface) → **separate** next request = Import Supplier Sites (not a child in `ESSExecutionDetailsRF`) → next = "Upload Interface Error and Job Output File to UCM". Find the import by scanning `ReqstId+1…` with `ESSJobStatusRF`/`ESSExecutionDetailsRF`.
- **CSV column order = control file order, NOT the template sheet order.** `PozSupplierSitesInt.ctl` starts with `IMPORT_ACTION`; `BATCH_ID` sits after `INVOICE_CHANNEL` (template shows "Batch ID" first). Wrong order → SQL*Loader "Rejected - Error on table POZ_SUPPLIER_SITES_INT, column IMPORT_ACTION", parent load = ERROR, rows deleted (`DeleteOnLoadFailure=Y`). The SQL*Loader log (`<loadChildId>.log`) prints the ctl field order — use it. `fbdi_build_zip` (sheet order) is therefore WRONG for templates whose macro reorders columns; also openpyxl cannot open the 26D supplier xlsm (bad stylesheet) → read sheet XML with zipfile.
- Import as `hcm_impl` (Supplier Manager role, NOT a procurement agent) succeeded: the import does not need procurement-agent BU access, while REST `POST .../sites` returns 403 for the same user. REST reads of the site stay empty for that user.

ESS job paths (NOT on docs.oracle.com — resolve at runtime from Manage Job Definitions):
- Supplier imports (VERIFIED for sites; others same package per community sources): `/oracle/apps/ess/prc/poz/supplierImport` with `ImportSuppliers`, `ImportSupplierAddresses`, `ImportSupplierSites`, `ImportSupplierSiteAssignments`, `ImportSupplierContacts`.
- Others (Import Orders, Blanket, Contract, Requisitions, supplier sites/contacts/addresses/assignments, Item Import, Manage Receiving Transactions): unknown.

Preferred technique for the MCP: `uploadFileToUCM` → `submitESSJobRequest` InterfaceLoaderController (load) → poll → `submitESSJobRequest` with the product import job → poll → `ESSJobExecutionDetailsRF` on the import request. Use `importBulkData` once the JobName/ParameterList for that object is confirmed in the pod.

## How to verify
- `ESSExecutionDetailsRF` tree: every STATUS = SUCCEEDED.
- Download import output (`fileType=ALL`) → exception report has 0 rejected rows.
- Read back via business REST (e.g. `suppliers?q=Supplier='...'`, `purchaseOrders?q=OrderNumber=...`).

## Sources
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-erpintegrations-post.html — POST attributes, importBulkData/uploadFileToUCM/submitESSJobRequest/exportBulkData/purge examples, NotificationCode, FileType text
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-erpintegrations-get.html — finders + variables
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-erpintegrations-operationname-get.html — ESSJobStatusRF / ESSExecutionDetailsRF / ESSJobExecutionDetailsRF / DocumentIdsByFilePrefixRF / DocumentRF example requests and responses
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Importing_Financials_Data.html — importBulkData with InterfaceLoaderController "1,7584,N,N"
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Export_Financials_Data_without_Using_Callback.html — ExportBulkData UCM file naming + polling
- https://docs.oracle.com/en/cloud/saas/financials/25d/oeswf/Chunk782013506.html — (25D SOAP) notificationCode digit table, importBulkData result = first job id, downloadESSJobExecutionDetails fileType Log/Out/All, paramList #NULL rule
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/toc.htm and pages importsuppliers-3129, importsupplieraddresses-3125, importsuppliersites-3132, importsuppliersiteassignments-3131, importsuppliercontacts-3128, purchaseordersimport-3121, blanketpurchaseagreementsimport-3119, contractpurchaseagreementsimport-3120, importrequisitions-3124 (.html) — templates, ctl files, UCM accounts, process names, tables
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/item-3182.html and receivingreceiptimport-3261.html — item and receipt FBDI
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/load-data-into-tables.html — manual FBDI flow
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/view-details-about-predefined-scheduled-processes.html — where to read job definitions
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/import-suppliers.html, import-supplier-sites.html, import-supplier-contacts.html, import-orders.html, import-blanket-agreements.html, import-contract-agreements.html, import-requisitions-0.html — parameters and privileges
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/statuses-of-scheduled-processes.html — status list and final statuses
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faipr/load-data-from-oracle-webcenter-to-interface-tables.html — Load Interface File for Import params (Import Process, Data File)

## UNVERIFIED
- ESS job package/definition names for every SCM/Procurement import (only third-party source for ImportSuppliers).
- Numeric "import process" id used as arg1 of InterfaceLoaderController per object; meaning of args 3–4 (`N,N`).
- Submit-argument order/values (IDs vs names) for each import job's ParameterList.
- CSV file names inside the zip (assumed = ctl base name + .csv).
- Upper-case REST spellings of statuses other than `SUCCEEDED`.
- `InterfaceDetails` JobOptions value for each SCM/Procurement object.
- Privileges for Item Import and Manage Receiving Transactions.
- Supplier Addresses / Site Assignments import parameters (not fetched; assumed same as Import Suppliers).
