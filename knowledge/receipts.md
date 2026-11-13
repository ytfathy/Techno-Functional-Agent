# Receipts (Receiving against Purchase Orders)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Record receipt of goods/services against PO schedules (or ASN, transfer order, RMA, in-transit). Drives 3-way match (invoice vs PO vs receipt) and inventory/expense delivery. Receipts are created through the receiving open interface: the REST request lands in interface tables and is processed immediately or in background.

## Where in Fusion (FSM)
- UI: Supply Chain Execution > Receipts (Receive Expected Shipments). Offering Manufacturing and Supply Chain Materials Management (receiving parameters per inventory org; task names UNVERIFIED here).

## Prerequisites & dependencies
- Approved/open PO whose schedule has `ReceiptRequiredFlag` = true (3/4-way match) and ship-to organization = a receiving-enabled inventory org (receiving parameters set).
- Receiving employee (`EmployeeName`/`EmployeeId`).
- Receipt routing on the schedule: `ReceiptRoutingId` 1 standard (receive, then deliver), 2 inspection required, 3 direct delivery.
- INVENTORY destination: subinventory/locator (or item transaction defaults). EXPENSE destination with direct delivery: `DeliverToLocationId` mandatory.

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Receipt source | header & line `ReceiptSourceCode` | `VENDOR` for PO/ASN | mandatory; header default VENDOR |
| ASN type | `ASNType` | `STD` = plain receipt | default STD; ASN, ASBN |
| Organization | `OrganizationCode` / `OrganizationId` | receiving org | one required (header and line) |
| Supplier | `VendorName` / `VendorNumber` / `VendorId`, `VendorSiteCode` / `VendorSiteId` | | one supplier identifier required for PO receipt |
| Receiver | `EmployeeName` / `EmployeeId` | | one required |
| Business unit | `BusinessUnit` / `BusinessUnitId` | | |
| Receipt number | `ReceiptNumber`, `ShipmentNumber`, `ReceiptHeaderId` | | |
| Processing | `InsertAndProcessFlag` (default true), `SaveAndSubmitFlag` (default false), `GroupId`, `HeaderInterfaceId` | | |
| Status (read) | `ProcessingStatusCode` (PENDING/ERROR/SUCCESS), `ReturnStatus` (SUCCESS/ERROR sync; SUBMITTED/QUEUED async), `ReturnMessage` | | |
| Source doc | lines `SourceDocumentCode` | `PO` | mandatory (lookup RCV_SOURCE_DOCUMENT_TYPE) |
| Transaction | lines `TransactionType` | default `RECEIVE`; also DELIVER, ACCEPT, REJECT, TRANSFER, CORRECT, RETURN TO VENDOR ... | |
| Auto transact | lines `AutoTransactCode` | 26D: "Not applicable. Leave blank." | older docs used DELIVER for direct delivery |
| PO number | lines `DocumentNumber` | | mandatory |
| PO line | lines `DocumentLineNumber` | | mandatory |
| PO schedule | lines `DocumentShipmentLineNumber` | | mandatory for PO |
| PO distribution | lines `DocumentDistributionNumber` | | mandatory if multiple distributions |
| Item | `ItemNumber` / `ItemId` / `ItemDescription` | | one required; defaults from PO if blank |
| Qty / UOM | `Quantity`, `UnitOfMeasure` / `UOMCode` | | |
| Amount | `Amount`, `CurrencyCode` | | mandatory for fixed-price service lines |
| Legal entity | `SoldtoLegalEntity` | | |
| Destination | `Subinventory`, `Locator`/`LocatorId`, `DeliverToLocationCode`/`DeliverToLocationId`, `DeliverToPersonName`/`DeliverToPersonId` | | |
| Date | `TransactionDate` | default now; no future dates | |
| Source | `InterfaceSourceCode` | default `REST` | |

Line children: `lotItemLots`, `lotSerialItemLots`, `serialItemSerials`, `processingErrors`, `transactionAttachments`, `transactionDFF`, `inventoryStripingDFF`, `ASNLineAttachments`, `ASNLineDFF`, `ASNPackingUnits`.

## Common mistakes
- Schedule not receivable: PO not approved/open, `ReceiptRequiredFlag` false (2-way), or org not a receiving org.
- Wrong `DocumentShipmentLineNumber` (schedule number, not line id).
- Missing subinventory/locator for INVENTORY DELIVER, or `DeliverToLocationId` for EXPENSE direct delivery.
- Future `TransactionDate`.
- Treating HTTP 201 as success: check `ReturnStatus`/`ProcessingStatusCode` and `processingErrors`.
- Sending POST with `ProcessingStatusCode` filled (must be blank).

## Channel & exact technique
- Preferred: A (REST). Receipts have no FBDI in the Procurement FBDI guide (SCM receiving import not researched: UNVERIFIED).
- Book: REST API for Oracle Fusion Cloud SCM (`fasrp`). Base `/fscmRestApi/resources/11.13.18.05`.

### Resources
- `receivingReceiptRequests`: POST `/receivingReceiptRequests` (create receipts/ASN); GET `/receivingReceiptRequests`, GET/PATCH/DELETE `/receivingReceiptRequests/{HeaderInterfaceId}`; collection action POST `/receivingReceiptRequests/action/submitForApproval`. Children: `lines` (Requests for Receiving Transactions) at `/receivingReceiptRequests/{HeaderInterfaceId}/child/lines`, `attachments`, `DFF`.
- `receivingReceiptExpectedShipmentLines` (what can be received): GET `/receivingReceiptExpectedShipmentLines`, GET `/receivingReceiptExpectedShipmentLines/{receivingReceiptExpectedShipmentLinesUniqID}`. Finders: `findLines;bindPONumber=,bindOrganizationCode=,bindSupplier=,bindItemNumber=,bindFromDate=,bindToDate=,bindASNNumber=,...`, `includeClosedOrCanceledPOs;bindIncludeClosedPOs=,bindIncludeCanceledPOs=,bindOrganizationCode=,bindOrganizationId=`, `PrimaryKey;DocumentLineId=,SourceDocumentCode=`. `q`: `OrganizationCode`, `PONumber`, `POLineNumber`, `POLineLocationId` (not `POScheduleNumber`, `AvailableQuantity`).
- `receivingReceiptTransactionRequests`: post-receipt transactions (deliver, inspect, correct, return) — exists (26A page), details not read: UNVERIFIED for 26D.

### Create receipt against a PO schedule (payload constructed from 26D attribute names; no PO example readable on 26D page)
`POST /receivingReceiptRequests`, `Content-Type: application/json`
```json
{
  "ReceiptSourceCode": "VENDOR",
  "ASNType": "STD",
  "OrganizationCode": "M1",
  "VendorName": "Tall Manufacturing",
  "VendorSiteCode": "New York",
  "BusinessUnit": "Vision Operations",
  "EmployeeName": "Furey,Clare",
  "lines": [{
    "ReceiptSourceCode": "VENDOR",
    "SourceDocumentCode": "PO",
    "TransactionType": "RECEIVE",
    "OrganizationCode": "M1",
    "DocumentNumber": "1005151",
    "DocumentLineNumber": 1,
    "DocumentShipmentLineNumber": 1,
    "Quantity": 2,
    "UnitOfMeasure": "Each"
  }]
}
```
Response: `HeaderInterfaceId`, `ReturnStatus`, `ReturnMessage`, `ReceiptNumber` (when processed), line `processingErrors`.

## How to verify
1. Before: `GET /receivingReceiptExpectedShipmentLines?finder=findLines;bindPONumber=<PO>,bindOrganizationCode=<ORG>` → line present, `AvailableQuantity` > 0, take `POLineNumber`, `POScheduleNumber`.
2. After POST: response `ReturnStatus` = SUCCESS (sync). If ERROR/QUEUED: `GET /receivingReceiptRequests/{HeaderInterfaceId}?expand=lines` and `GET .../child/lines/{id}/child/processingErrors` (exact child path UNVERIFIED; use expand).
3. Re-run expected-lines query → `AvailableQuantity` reduced; PO schedule received quantity updated (attribute name on PO schedule UNVERIFIED).
4. UI: Receipts > Review Receipts.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/api-inventory-management-receiving-receipt-requests.html — endpoints
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-receivingreceiptrequests-post.html — header/line attributes, children, status fields
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-receivingreceiptexpectedshipmentlines-get.html — expected shipment lines, finders
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseorders-post.html — schedule receipt controls (ReceiptRequiredFlag, ReceiptRoutingId, InspectionRequiredFlag)

## UNVERIFIED
- Verbatim PO receipt example (26D page examples not readable; payload constructed).
- Whether header `ReceiptSourceCode` should be `VENDOR` or `SUPPLIER` (doc text lists both in different places; line value list says VENDOR).
- Child path for `processingErrors` and response field `ReceiptNumber` presence.
- `receivingReceiptTransactionRequests` details for 26D; receiving FBDI; FSM receiving parameter task names.
- `submitForApproval` action purpose/parameters.
