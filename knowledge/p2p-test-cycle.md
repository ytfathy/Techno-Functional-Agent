# P2P Test Cycle (Requisition → Approval → PO → Communicate → Receipt → Invoice match)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
End-to-end smoke test that proves a BU's procurement setup works: requisitioning BF, approvals, supplier/site/assignment, buyer/agent, document style, PO approval, communication, receiving, and (optionally) AP matching. Each step has a read-back so failures point to the broken setup.

## Where in Fusion (FSM)
Not an FSM task. Uses: Procurement > Purchase Requisitions, Purchase Orders (Process Requisitions, Manage Orders), Supply Chain Execution > Receipts, Payables > Invoices.

## Prerequisites & dependencies
- See `suppliers.md`, `requisitions.md`, `purchase-orders.md`, `receipts.md`.
- Test user = employee with Procurement Requester (owns the requisition — REST only lets the preparer submit) and a buyer who is a procurement agent for the procurement BU. One integration user may hold both if it has an HR person record.
- Supplier site: purchasing + pay purposes, assignment for the requisitioning BU, communication method (EMAIL for a visible communicate step).
- Approval rules (or plan to approve manually / bypass on PO submit).

## Key fields
| Step | ID to carry forward | Read-back attribute |
|---|---|---|
| Requisition | `RequisitionHeaderId`, line `RequisitionLineId` | `DocumentStatusCode` |
| Processing request | `RequestHeaderId` | action `result` text contains PO number |
| PO | `POHeaderId`, `OrderNumber` | `Status`/`StatusCode` |
| Receipt | `HeaderInterfaceId`, `ReceiptNumber` | `ReturnStatus`, `ProcessingStatusCode` |

## Common mistakes
- Submitting the requisition with a user other than the preparer (REST restriction).
- Line without a suggested supplier/site and no sourcing → buyer must assign supplier in `requisitionProcessingRequests` (`Supplier`, `SupplierSite`).
- Expecting `processRequest` to give an approved PO: it creates a **draft PO in Incomplete status**; you must submit it.
- Schedule with `ReceiptRequiredFlag` false → no receipt possible (2-way match).
- Polling too fast: approvals are asynchronous (BPM); poll with backoff.

## Channel & exact technique
Channel A (REST). Base `/fscmRestApi/resources/11.13.18.05`. Items `application/vnd.oracle.adf.resourceitem+json`; actions `application/vnd.oracle.adf.action+json` POSTed to `.../{id}/action/<name>` with flat parameter body.

1. **Create requisition** (as preparer) — `POST /purchaseRequisitions` with header `RequisitioningBUId`, `PreparerId`, one line (`LineNumber`, `LineTypeCode`, `CategoryName`, `ItemDescription`, `UOM`, `Quantity`, `Price`, `CurrencyCode`, `DestinationTypeCode`=EXPENSE, `DestinationOrganizationId`, `RequesterId`, `DeliverToLocationId`, `RequestedDeliveryDate`, optional `Supplier`/`SupplierSite`) and `distributions` [`DistributionNumber`, `Quantity`, `CurrencyAmount`]. Verify: 201, `RequisitionHeaderId`.
2. **Submit** — `POST /purchaseRequisitions/{id}/action/submitRequisition` body `{}` → `{"result":"SUCCESS"}`. Failure → read `getApprovalWorkflowStatus`, check charge account / funds.
3. **Approval** — poll `GET /purchaseRequisitions/{id}?fields=Requisition,DocumentStatus,DocumentStatusCode` until approved; `POST .../action/retrieveCurrentApprovers` or `getApprovalWorkflowStatus` to see who blocks. Then `GET /purchaseRequisitions/{id}/child/lines?fields=RequisitionLineId,LineNumber`.
4. **Requisition → PO** (buyer) — `POST /requisitionProcessingRequests` (`Content-Type: application/json`):
   `{"ProcurementBU":"<BU>","RequisitioningBU":"<BU>","Type":"New Order","Supplier":"<supplier>","SupplierSite":"<site>","lines":[{"RequisitionLineId":<id>}]}` → `RequestHeaderId`.
   Then `POST /requisitionProcessingRequests/{RequestHeaderId}/action/processRequest` body `{}` or `{"bypassWarningsFlag": true}` → `{"result":"The document (Purchase Order) 1005151 was created."}` (draft, Incomplete). Errors come back as text lines (e.g. supplier/site mismatch, document style vs purchase basis). Existing order: `"Type":"Existing Order","POHeaderId":<id>`; agreement: `"SourceAgreement":"<num>"`.
   - Alternative (no requisition): `POST /draftPurchaseOrders` directly (see purchase-orders.md).
   - Auto-create by approval (requisition lines sourced to an agreement converted automatically without buyer) depends on setup: UNVERIFIED.
5. **Submit PO** — find it: `GET /draftPurchaseOrders?q=OrderNumber='1005151'` → id; optional `POST /draftPurchaseOrders/{id}/action/submit` `{"validateBeforeSubmitFlag": true}` to see errors, then `{}` or `{"bypassApprovalsFlag": true}` (test only, needs privilege — UNVERIFIED which). Verify `GET /purchaseOrders?q=OrderNumber='1005151'&fields=POHeaderId,OrderNumber,Status` → open.
6. **Communicate** — automatic on approval per supplier site communication method (expected; UNVERIFIED). Manual: `POST /purchaseOrders/{id}/action/communicateOnePurchaseOrder` `{"communicationMethod":"email","email":"<test address>"}` (sends a real email — confirm with user). B2B re-send: `.../action/communicate` `{"forceCommunicationFlag": true}`.
7. **Receipt** — `GET /receivingReceiptExpectedShipmentLines?finder=findLines;bindPONumber=1005151,bindOrganizationCode=<ORG>` → line available; `POST /receivingReceiptRequests` with header `ReceiptSourceCode`=VENDOR, `ASNType`=STD, `OrganizationCode`, `VendorName`, `VendorSiteCode`, `EmployeeName`, and line `SourceDocumentCode`=PO, `TransactionType`=RECEIVE, `DocumentNumber`, `DocumentLineNumber`, `DocumentShipmentLineNumber`, `Quantity`, `UnitOfMeasure`. Verify `ReturnStatus`=SUCCESS and expected-line `AvailableQuantity` reduced.
8. **Invoice match (optional)** — Payables `invoices` REST (Financials) matching PO/receipt: not researched here, UNVERIFIED. Verify in UI: Payables > Invoices, match to receipt, validation status.

## How to verify
Each step above has its read-back. Final pass criteria: requisition approved, PO open (status Open), communicated (Document History), receipt created (receipt number), expected-shipment quantity consumed.

Typical failures → setup to check:
| Symptom | Likely cause |
|---|---|
| Req submit FAILURE / no charge account | preparer HR assignment lacks default expense account |
| Req stuck pending approval | approval rules / approver missing |
| processRequest: supplier/site different / not valid | site not assigned to requisitioning BU, or purchasing purpose off |
| processRequest: purchase basis not supported on style | document style |
| PO submit: distribution sum ≠ schedule qty; PO Charge/Variance Account missing | account derivation setup |
| Buyer not found / no access | procurement agent setup for procurement BU |
| No expected shipment line | PO not open, `ReceiptRequiredFlag` false, wrong org |
| Receipt ERROR | subinventory/locator/deliver-to missing, future date |

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/use_case_manage_requisitions_by_users.html — requisition create/submit rules
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaserequisitions-purchaserequisitionsuniqid-action-submitrequisition-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaserequisitions-purchaserequisitionsuniqid-action-getapprovalworkflowstatus-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-requisitionprocessingrequests-post.html — request header/lines + examples
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-requisitionprocessingrequests-requisitionprocessingrequestsuniqid-action-processrequest-post.html — processRequest (creates draft PO / incomplete change order)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseorders-draftpurchaseordersuniqid-action-submit-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-purchaseordersuniqid-action-communicateonepurchaseorder-post.html
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-receivingreceiptexpectedshipmentlines-get.html
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-receivingreceiptrequests-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fainp/integration-playbooks-for-procurement.pdf — requisition-to-PO via requisitionProcessingRequests

## UNVERIFIED
- Requisition approved status code value.
- Automatic PO creation (auto-create / bypass buyer) behaviour and setup.
- Automatic communication on approval; privilege needed for `bypassApprovalsFlag`.
- Invoice match REST (Financials invoices resource) — not researched.
- Payload of step 7 (constructed, see receipts.md).
