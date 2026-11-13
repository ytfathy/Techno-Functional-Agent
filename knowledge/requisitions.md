# Purchase Requisitions

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Internal request for goods/services. Header (requisitioning BU, preparer) → lines (item/description, category, qty, UOM, price, destination, deliver-to, requester) → distributions (charge account, qty/amount). Submitted for approval (BPM/AMX); approved lines are then processed by a buyer (or automatically) into a PO via Requisition Processing Requests.

## Where in Fusion (FSM)
- UI: Procurement > Purchase Requisitions (Self Service Procurement).
- Setup prerequisites live in FSM offering Procurement: Configure Requisitioning Business Function, Manage Requisition Approvals (task names not re-verified here: UNVERIFIED).

## Prerequisites & dependencies
- Requisitioning BU with requisitioning business function; preparer is an employee with access to that BU and the Procurement Requester role (`POR_MANAGE_REQUISITION_PRIV` "Manage Requisition").
- Preparer HR assignment with default expense account (charge account is generated on submit from HR record).
- Deliver-to location, destination org (inventory org for INVENTORY lines), purchasing category, UOM, currency.
- Supplier + site + assignment for the client BU if the supplier is suggested on the line.

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Requisitioning BU | `RequisitioningBUId` (req) / `RequisitioningBU` | | |
| Preparer | `PreparerId` (req) / `PreparerEmail` | | must equal personId of the REST caller |
| Description | `Description` | max 240 | |
| Externally managed | `ExternallyManagedFlag` | | false for normal approval |
| Justification | `Justification` | | |
| Status | `DocumentStatus` / `DocumentStatusCode` | read, queryable | values e.g. APPROVED / PENDING_APPROVAL / INCOMPLETE: UNVERIFIED |
| Requisition number | `Requisition` | read, queryable | |
| Line | lines `LineNumber` (req) | | |
| Line type | `LineTypeCode` / `LineTypeId` | | "Goods" in docs example |
| Item / description | `Item`/`ItemId`, `ItemDescription` | | |
| Category | `CategoryName` / `CategoryId` | | |
| Qty / UOM | `Quantity`, `UOM` / `UOMCode` | | |
| Price | `Price` (supplier currency) / `UnitPrice` (buyer currency), `CurrencyCode` | | |
| Need-by | `RequestedDeliveryDate` | date | |
| Destination | `DestinationTypeCode` | EXPENSE / INVENTORY | |
| Deliver-to | `DeliverToLocationId` / `DeliverToLocationCode`, `DestinationOrganizationId` / `DestinationOrganizationCode` | | |
| Requester | `RequesterId` / `RequesterEmail` | | |
| Suggested supplier | `Supplier`, `SupplierSite`, `SupplierSiteId` | | |
| Suggested procurement BU | `SuggestedProcurementBU` / `SuggestedPrcBUId` | | no `ProcurementBU` on lines |
| Source type | `SourceTypeCode` | default `EXTERNAL` | |
| Distribution | distributions `DistributionNumber`, `Quantity`, `CurrencyAmount` | | charge account attribute names not read: UNVERIFIED |

## Common mistakes
- Creating the requisition as one user and submitting/viewing as another: REST only lets the preparer (PreparerId = caller personId) view/update/submit. `POR_VIEW_REQUISITIONS_ALL` does not help through REST.
- Caller lacks access to the requisitioning BU, or lacks the privilege for the line type (e.g. deliver-to different from HR location).
- No default expense account on the preparer's assignment → charge account not generated on submit.
- Distribution quantities not summing to line quantity.
- Using the requisition GET to read someone else's requisitions: use finder `ViewAccessibleRequisitionDetailsFinder` with the view-all privilege.

## Channel & exact technique
- Preferred channel: A (REST) for test/low volume; C (FBDI) for bulk or approved-requisition import.
- Base `/fscmRestApi/resources/11.13.18.05`. Items: `application/vnd.oracle.adf.resourceitem+json` (docs; the use case typo shows `vnd.vision`). Actions: `application/vnd.oracle.adf.action+json`.

### Resource paths
- `/purchaseRequisitions` GET, POST; `/purchaseRequisitions/{purchaseRequisitionsUniqID}` GET, PATCH, DELETE
- `/purchaseRequisitions/{id}/child/lines[/{linesUniqID}]` GET, POST, PATCH, DELETE
- `/purchaseRequisitions/{id}/child/lines/{linesUniqID}/child/distributions[/{RequisitionDistributionId}]` GET, POST, PATCH, DELETE
- Other children: header `attachments`, `DFF`, `specialHandlingDFF`, `summaryAttributes` (only with a finder); line `attachments`, `DFF`, `specialHandlingDFF`, `informationTemplates` (not used), `configurationComponents`; distribution `DFF`, `projectDFF`.
- Header actions (POST `/purchaseRequisitions/{id}/action/<name>`): `submitRequisition`, `getApprovalWorkflowStatus`, `retrieveCurrentApprovers`, `withdraw`, `cancel`, `calculateTaxAndAccounting`, `calculateTax`, `checkFunds`, `checkActionEligibility`, `createDefaultDistributions`, `deriveChargeAccount`, `distributeProjectCosts`, `viewPDF`, `copyLine`, `copyLinesFromRequisition`, `processPunchoutShoppingCart`, `retrieveSourceDocumentAndTransferPrice`, `retrieveTransferPriceAndTax`, `splitLine`, `updateAllLines`.
- Collection actions (POST `/purchaseRequisitions/action/<name>`): `generatePayloadForCreation`, `initiateApproverCheckout`, `parseAndValidatePunchoutCart`, `reassignRequisitions`, `reassignBuyer`, `replaceRequisitionLine`, `returnLines`, `suggestCategory`.
- Line actions (POST `.../child/lines/{linesUniqID}/action/<name>`): `calculateTaxAndAccounting`, `calculateTax`, `cancel`, `deriveChargeAccount`, `retrieveTransferPriceAndTax`, `withdraw`.
- Finders (GET `?finder=<name>;<var>=<val>`): `PrimaryKey;RequisitionHeaderId=`, `InternallyManagedRequisitionsFinder;bindPreparerId=`, `ViewAccessibleRequisitionDetailsFinder;bindRequisitionHeaderId=`, `ActiveRequisitionInPreferredBUFinder;PreferenceType=,RequisitioningBUId=,SysEffectiveDate=`.
- `q` queryable: `Requisition`, `RequisitionHeaderId`, `DocumentStatus`, `DocumentStatusCode`, `PreparerId`, `Preparer`, `RequisitioningBUId`, `RequisitioningBU`, `ActiveRequisitionFlag`, `CreationDate`, ...

### Create (docs use-case payload)
`POST /purchaseRequisitions`
```json
{
  "RequisitioningBUId": 204,
  "PreparerId": 100100004256726,
  "ExternallyManagedFlag": false,
  "Description": "Office Supplies",
  "lines": [{
    "LineNumber": 1, "LineTypeCode": "Goods", "CategoryName": "Paper",
    "ItemDescription": "Notebook - 100 Pages", "UOM": "Each", "Quantity": 1, "Price": 4.99,
    "CurrencyCode": "USD", "DestinationTypeCode": "EXPENSE", "DestinationOrganizationId": 204,
    "RequesterId": 100100004256726, "DeliverToLocationId": 204, "RequestedDeliveryDate": "2021-09-15",
    "distributions": [{"DistributionNumber": 1, "CurrencyAmount": 4.99, "Quantity": 1}]
  }]
}
```
Response: requisition in incomplete status; take `RequisitionHeaderId` / self link for `{purchaseRequisitionsUniqID}`.

### Submit
`POST /purchaseRequisitions/{purchaseRequisitionsUniqID}/action/submitRequisition`, `Content-Type: application/vnd.oracle.adf.action+json`
- Flat body per 26D schema: `{}` or `{"requestFundsOverrideFlag": false}` (params: `approverCheckoutFlowFlag`, `options`, `requestFundsOverrideFlag`).
- Use-case form (POST to item URL): `{"name":"submitRequisition","parameters":[]}`.
- Response `{"result":"SUCCESS"}` or `FAILURE`. Approval is bypassed if externally managed or approver details are supplied. Submit triggers tax calc and charge-account generation.

### Approval status
- Poll `GET /purchaseRequisitions/{id}?fields=Requisition,DocumentStatus,DocumentStatusCode` until approved.
- Detail: `POST /purchaseRequisitions/{id}/action/getApprovalWorkflowStatus` body `{}` → `{"result":{...}}` (map of strings; content UNVERIFIED). Current approvers: `retrieveCurrentApprovers`.

### C (FBDI)
- Template `RequisitionImportTemplate.xlsm`; control files `PorReqHeadersInterfaceAll.ctl`, `PorReqLinesInterfaceAll.ctl`, `PorReqDistsInterfaceAll.ctl`; tables `POR_REQ_HEADERS_INTERFACE_ALL`, `POR_REQ_LINES_INTERFACE_ALL`, `POR_REQ_DISTS_INTERFACE_ALL`; UCM `prc/requisition/import`; processes Load Interface File for Import → Import Requisitions.
- Playbook: default max batch size 2,500 lines; to import as approved give document status Approved + approver email; draft requisitions max 500 lines; user preferences not applied.

## How to verify
- GET requisition → `DocumentStatusCode` approved (exact code UNVERIFIED), `Requisition` number.
- GET `.../child/lines?fields=RequisitionLineId,LineNumber,...` → `RequisitionLineId` needed for requisitionProcessingRequests.
- UI: Manage Requisitions → status Approved; Process Requisitions shows the line for the buyer.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html — all requisition paths, actions, children
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaserequisitions-post.html — required arrays and attribute names
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaserequisitions-get.html — finders, q attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaserequisitions-purchaserequisitionsuniqid-action-submitrequisition-post.html — submit params/media type
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaserequisitions-purchaserequisitionsuniqid-action-getapprovalworkflowstatus-post.html — approval status action
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/use_case_manage_requisitions_by_users.html — create/update/view/submit payloads and ownership rules
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/importrequisitions-3124.html — FBDI
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fainp/integration-playbooks-for-procurement.pdf — requisition import best practices

## UNVERIFIED
- `DocumentStatusCode` values (APPROVED, PENDING_APPROVAL, INCOMPLETE, REJECTED...).
- Distribution charge-account attribute names (e.g. `ChargeAccount`).
- Content of the `getApprovalWorkflowStatus` result map.
- FSM task names for requisitioning setup.
- Whether `{purchaseRequisitionsUniqID}` equals `RequisitionHeaderId` (use self link to be safe).
