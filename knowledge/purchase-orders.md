# Purchase Orders (draft, open, change orders)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Standard PO: header (procurement BU, buyer, supplier/site, style, currency) → lines (item/description, category, qty, UOM, price) → schedules (ship-to org/location, dates, receipt/inspection/match controls) → distributions (charge account, deliver-to, requester). Drafts (incomplete / change orders) live in `draftPurchaseOrders`; approved/open orders are read and acted on via `purchaseOrders`. A change to an open PO is a change order created through `draftPurchaseOrders`.

## Where in Fusion (FSM)
- UI: Procurement > Purchase Orders (Create Order, Manage Orders, Process Requisitions).
- Setup: Configure Procurement Business Function, Manage Procurement Agents (buyer), Manage Purchasing Document Styles, Document Approvals (task names UNVERIFIED here).

## Prerequisites & dependencies
- Procurement BU serving the requisitioning/sold-to BU; buyer = procurement agent with access to the BU; document style (`DocumentStyleId`, "Purchase Order" style id 1 in examples).
- Supplier + site (purchasing purpose) + assignment for the requisitioning BU.
- Ship-to inventory organization (schedule `ShipToOrganization` is required), locations, charge account (distribution `POChargeAccount`; PO Variance Account is also validated on submit).
- Approvals rules for PO (or `bypassApprovalsFlag`).

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Procurement BU | `ProcurementBUId` (req) / `ProcurementBU` | | |
| Requisitioning BU | `RequisitioningBUId` / `RequisitioningBU` | | |
| Buyer | `BuyerId` (req) / `Buyer` | | `BuyerEmail` = PO email sender |
| Document style | `DocumentStyleId` (req) / `DocumentStyle` | | |
| Supplier / Site / Contact | `Supplier`/`SupplierId`, `SupplierSite`/`SupplierSiteId`, `SupplierContact`/`SupplierContactId` | | |
| Currency | `CurrencyCode` | | |
| Bill-to | `BillToBU`, `BillToLocation`(Id), `DefaultShipToLocation`(Id) | | |
| Terms | `PaymentTerms`/`PaymentTermsId` | | |
| Description / notes | `Description`, `NoteToSupplier`, `NoteToReceiver`, `NoteToAuthorizer` | | |
| Communication | `SupplierCommunicationMethod`, `SupplierEmailAddress` | | |
| Order / status | `OrderNumber`, `Status`/`StatusCode`, `POHeaderId` | read | |
| Change order | `ChangeOrderDescription`, `ChangeOrderInitiatingParty` (BUYER / REQUESTER / SUPPLIER), `ChangeOrderNumber`, `ChangeOrderStatusCode` (INCOMPLETE ...), `ChangeOrderTypeCode` | | |
| Line | lines `LineNumber`, `LineType`, `LineTypeId` (all req) | | "Goods" |
| Item / desc | `Item`/`ItemId`, `Description` | | |
| Category | `Category` / `CategoryCode` / `CategoryId` | | |
| Qty / UOM / price | `Quantity`, `UOM`/`UOMCode`, `Price`, `Amount` | | |
| Schedule | schedules `ScheduleNumber`, `Quantity` | | |
| Ship-to | `ShipToOrganization`/`ShipToOrganizationId`/`ShipToOrganizationCode`, `ShipToLocation`/`ShipToLocationCode` | | |
| Dates | `RequestedDeliveryDate`, `PromisedDeliveryDate` | | |
| Destination | `DestinationType` / `DestinationTypeCode` | | EXPENSE / INVENTORY |
| Receipt controls | `ReceiptRequiredFlag`, `InspectionRequiredFlag`, `ReceiptRoutingId` (1 standard, 2 inspection, 3 direct delivery), `ReceiptCloseTolerancePercent` | | |
| Invoice controls | `MatchApprovalLevel`/`MatchApprovalLevelCode` (2/3/4-way), `InvoiceMatchOptionCode` (P order, R receipt, C consumption), `InvoiceCloseTolerancePercent` | | |
| Distribution | distributions `DistributionNumber`, `Quantity`, `POChargeAccount`, `DeliverToLocation`/`DeliverToLocationCode`, `Requester`/`RequesterId`, `BudgetDate` | | |

Schema "required" arrays (26D, verbatim): header `BuyerId`, `DocumentStyleId`, `ProcurementBUId`; line `LineNumber`, `LineType`, `LineTypeId`; schedule `InspectionRequiredFlag`, `InvoiceCloseTolerancePercent`, `InvoiceMatchOptionCode`, `POHeaderId`, `POLineId`, `ReceiptCloseTolerancePercent`, `ReceiptRequiredFlag`, `ReceiptRoutingId`, `ScheduleNumber`, `ShipToOrganization`, `ShipToOrganizationId`; distribution `DistributionNumber`, `POHeaderId`. Many of these are defaulted by the server when created as nested children (parent IDs, controls from setup) — expectation, UNVERIFIED; `rest_describe` before writing.

## Common mistakes
- Distribution qty sum ≠ schedule qty; missing PO Charge Account / PO Variance Account (exact validate-before-submit messages in docs).
- Supplier site has no assignment for the requisitioning BU.
- Buyer not set up as procurement agent for the procurement BU.
- Expecting `purchaseOrders` to accept POST/PATCH: it is read + actions only. Create/modify through `draftPurchaseOrders`.
- Updating an open PO via FBDI: not supported (only add lines → creates change order); cancel/update via REST.
- PO referencing a requisition must go through `requisitionProcessingRequests`, not FBDI or draftPurchaseOrders POST.
- Change order via requester intent returns no data if a pending change order exists, PO is closed/cancelled/frozen, etc.

## Channel & exact technique
- Preferred: A (REST). C (FBDI Import Orders) for bulk loads of new POs only.
- Base `/fscmRestApi/resources/11.13.18.05`. Items `application/vnd.oracle.adf.resourceitem+json` (schema also `application/json`); actions `application/vnd.oracle.adf.action+json`, response `application/vnd.oracle.adf.actionresult+json` → `{"result":"SUCCESS"}`.
- Action call forms seen in 26D docs (both): (a) POST `.../{id}/action/<name>` with flat body `{"param": value}` (schema form; draftPurchaseAgreements submit example); (b) POST item URL `.../{id}` with `{"name":"<name>","parameters":[{"param":"value"}]}` (examples on PO cancel/close/communicate, draft PO submit). Prefer (a).

### draftPurchaseOrders
- `/draftPurchaseOrders` GET, POST; `/draftPurchaseOrders/{draftPurchaseOrdersUniqID}` GET, PATCH, DELETE
- Header actions (POST `.../{id}/action/<name>`): `submit`, `validateDocument`, `withdraw`, `calculateTaxAndAccounting`, `checkFunds`, `applyDiscount`, `updateAllLines`, `distributeProjectCosts`, `processRequesterChanges`, `cancelChangeOrder`, `deleteChangeOrder`, `addContractTerms`, `removeContractTerms`, `applyLatestTemplate`, `changeContractSource`, `viewPDF`, `viewMasterContract`, `eSign`; collection `/draftPurchaseOrders/action/suggestCategory`.
- Children: `lines` (`/child/lines[/{POLineId}]` GET POST PATCH DELETE; line actions `duplicate`, `rebuildAccounts`, `recalculatePrice`), `lines/{POLineId}/child/schedules[/{schedulesUniqID}]` (GET POST PATCH DELETE; action `rebuildAccounts`), `.../schedules/{schedulesUniqID}/child/distributions[/{distributionsUniqID}]` (GET POST PATCH DELETE; action `rebuildAccounts`), plus `attachments`, `DFF`, `globalDFFs`, `specialHandlingDFF`, `projectDFF` (distribution), `configurationComponents` (line), `contractDocuments`, `supportingDocuments`, `templateUsages`, `summaryAttributes`.
- Finders: `PrimaryKey;POHeaderId=`, `findByIntent;Intent=ProcurementRequester`.
- Submit: `POST /draftPurchaseOrders/{id}/action/submit`, params `bypassApprovalsFlag`, `validateBeforeSubmitFlag`, `defaultTaxAttributesFlag`, `requestFundsOverrideFlag` (booleans). Docs examples: `{"name":"submit"}`; `{"name":"submit","parameters":[{"bypassApprovalsFlag":"true"}]}`; `{"name":"submit","parameters":[{"validateBeforeSubmitFlag":"true"}]}` → plain-text error lines if invalid.
- Create payload (no docs example readable on 26D page; constructed from schema names):
```json
{
  "ProcurementBUId": 204, "BuyerId": 100010026863783, "DocumentStyleId": 1,
  "SupplierId": 254, "SupplierSiteId": 32, "CurrencyCode": "USD", "Description": "P2P test",
  "lines": [{
    "LineNumber": 1, "LineType": "Goods", "Description": "Test item", "Category": "Paper",
    "Quantity": 2, "UOMCode": "Ea", "Price": 10,
    "schedules": [{
      "ScheduleNumber": 1, "Quantity": 2, "ShipToOrganizationCode": "M1", "ShipToLocationCode": "M1-LOC",
      "RequestedDeliveryDate": "2026-12-01", "DestinationTypeCode": "EXPENSE",
      "distributions": [{"DistributionNumber": 1, "Quantity": 2, "POChargeAccount": "01-000-7110-0000-000"}]
    }]
  }]
}
```

### purchaseOrders (open/approved; read + actions)
- `/purchaseOrders` GET; `/purchaseOrders/{purchaseOrdersUniqID}` GET. No POST/PATCH.
- Header actions (POST `.../{id}/action/<name>`): `acknowledge`, `cancel`, `close`, `communicate`, `communicateOnePurchaseOrder`, `duplicate`, `freeze`, `unfreeze`, `hold`, `removeHold`, `renumberPO`, `reopen`, `submit`, `viewPDF`, `viewMasterContract`, `generateHighlights`.
  - `close`: `closeAction` = `closeForReceiving` | `closeForInvoicing` | `close` | `finallyClose`; `closeReason`. Finally close = `close` with `closeAction:"finallyClose"` (no separate action at header).
  - `cancel`: `cancellationReason`, `initiatingParty` (buyer/requester/supplier), `cancelUnfulfilledDemandFlag`, `communicationMethod`, `email`, `CCEmail`, `BCCEmail`, `fax`, `requiredAcknowledgment`, `acknowledgeWithinDays`. Example `{"name":"cancel","parameters":[{"cancellationReason":"No longer required"},{"initiatingParty":"buyer"}]}`.
  - `communicate`: B2B re-communication only; `forceCommunicationFlag`, `changeOrderNumber`.
  - `communicateOnePurchaseOrder`: email/fax/print; `communicationMethod` (email|fax|print), `email`, `cc`, `bcc`, `fax`, `preferredLanguage`.
- Line action: `/purchaseOrders/{id}/child/lines/{POLineId}/action/close`. Schedule actions: `.../child/lines/{POLineId}/child/schedules/{schedulesUniqID}/action/close|firm|unfirm|reopen`.
- Children (read): `lines`, `lines/schedules`, `schedules/distributions`, `attachments`, `DFF`, `globalDFFs`, `specialHandlingDFF`, `contractDocuments`, `supportingDocuments`, `templateUsages`, `projectDFF`.
- Finders: `PrimaryKey;POHeaderId=`, `findByIntent;Intent=<APUser|POUser|LOBUser>,POHeaderId=`. `q` on `OrderNumber`, `POHeaderId`, `FundsStatus`, `PendingResponseRole`.

### Change orders (no separate resource in 26D)
1. (requester) check: `GET /draftPurchaseOrders?q=POHeaderId=<id>&finder=findByIntent;Intent=ProcurementRequester` (empty items = cannot change).
2. Create: `PATCH /draftPurchaseOrders/{POHeaderId}` (`application/vnd.oracle.adf.resourceitem+json`):
   requester `{"ChangeOrderDescription":"change order","ChangeOrderInitiatingParty":"REQUESTER","lines":[{"POLineId":300100185839441,"Quantity":15}]}`;
   buyer `{"ChangeOrderInitiatingParty":"Buyer","ChangeOrderDescription":"Create a buyer change order from REST"}` → `ChangeOrderStatusCode` INCOMPLETE, `ChangeOrderNumber` "1".
3. Submit: `POST /draftPurchaseOrders/{POHeaderId}/action/submit` (or `{"name":"submit"}` to item URL).
- Discard: `cancelChangeOrder` / `deleteChangeOrder` actions on draftPurchaseOrders.

### C (FBDI) — Import Orders
- Template `POPurchaseOrderImportTemplate.xlsm`; control files `PoHeadersInterfaceOrder.ctl`, `PoLinesInterfaceOrder.ctl`, `PoLineLocationsInterfaceOrder.ctl`, `PoDistributionsInterfaceOrder.ctl`; tables `PO_HEADERS_INTERFACE`, `PO_LINES_INTERFACE`, `PO_LINE_LOCATIONS_INTERFACE`, `PO_DISTRIBUTIONS_INTERFACE`; UCM `prc/purchaseOrder/import`; scheduled process `Import Orders`.
- Playbook: create POs (incomplete or open), add lines (Update action → change order if open), ≤10,000 distributions per document, expense & inventory destinations only, no reprocessing of a failed batch (reload), update/cancel → REST, progress payments → REST, requisition-referenced POs → requisitionProcessingRequests. Privilege: Import Purchase Order.
- ESS job path / parameters: UNVERIFIED.

## How to verify
- `GET /purchaseOrders?q=OrderNumber='<num>'&fields=POHeaderId,OrderNumber,Status,StatusCode` → open/approved.
- `GET /draftPurchaseOrders?q=POHeaderId=<id>` → shows pending change order with `ChangeOrderStatusCode`.
- Schedules: `GET /purchaseOrders/{id}/child/lines/{POLineId}/child/schedules` → `ReceiptRequiredFlag`, `MatchApprovalLevel`.
- UI: Manage Orders → status Open; Document History shows communicate/change actions.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html — draftPurchaseOrders/purchaseOrders paths, actions, children
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseorders-post.html — required arrays and attributes (header/line/schedule/distribution)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseorders-get.html — finders, q attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseorders-draftpurchaseordersuniqid-action-submit-post.html — submit params/examples
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-get.html — PO finders
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-purchaseordersuniqid-action-close-post.html — close/finallyClose
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-purchaseordersuniqid-action-cancel-post.html — cancel
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-purchaseordersuniqid-action-communicate-post.html — B2B communicate
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-purchaseordersuniqid-action-communicateonepurchaseorder-post.html — email/fax/print communicate
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/use-case_create_change_order_on_po_as_prc_requester.html — requester change order
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/use-case_Add_Attachment_to_Approved_PO_as_Buyer.html — buyer change order
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/purchaseordersimport-3121.html — FBDI
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fainp/integration-playbooks-for-procurement.pdf — FBDI vs REST guidance

## UNVERIFIED
- Full create payload (no readable docs example on the 26D page); which schema-"required" schedule/distribution fields the server defaults.
- `Status`/`StatusCode` values (OPEN, INCOMPLETE, PENDING APPROVAL...) and whether queryable on purchaseOrders.
- `{purchaseOrdersUniqID}` == `POHeaderId` (docs use POHeaderId in change-order URLs for draftPurchaseOrders).
- Whether `communicateOnePurchaseOrder` is needed in the P2P test or communication happens automatically after approval (depends on supplier site communication method).
- Import Orders ESS job path and parameters.
