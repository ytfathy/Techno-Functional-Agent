# Purchase Agreements (Blanket & Contract)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Blanket purchase agreement (BPA): negotiated prices/lines with a supplier, released via POs (catalog/requisition sourcing). Contract purchase agreement (CPA): terms without lines, referenced by PO lines. Both are enabled for client requisitioning BUs through business-unit access.

## Where in Fusion (FSM)
- UI: Procurement > Purchase Agreements (Create Agreement, Manage Agreements).
- Setup: document styles, procurement BF, approval rules (UNVERIFIED task names).

## Prerequisites & dependencies
- Procurement BU, buyer (agent), supplier + site + assignment, document style, line types, categories/items, requisitioning BUs to grant access.

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Procurement BU | `ProcurementBUId` (req) / `ProcurementBU` | owner BU | |
| Buyer | `BuyerId` (req) / `Buyer` | | |
| Style | `DocumentStyleId` (req) / `DocumentStyle` | | |
| Document type | `DocumentTypeCode` (req, max 25) | blanket vs contract | values (e.g. BLANKET / CONTRACT) UNVERIFIED |
| Supplier / site | `Supplier`/`SupplierId`, `SupplierSite`/`SupplierSiteId` | | |
| Currency | `CurrencyCode` | | |
| Amount | `AgreementAmount` | agreed amount | |
| Dates | `StartDate`, `EndDate` | yyyy-MM-dd | |
| Description | `Description` | | |
| Line | lines `LineNumber` (req), `LineTypeId` (req), `LineType` | | |
| Item / desc / category | `Item`/`ItemId`, `Description`, `Category`/`CategoryCode`/`CategoryId` | | |
| UOM / price | `UOM`/`UOMCode`, `Price`, `Amount`, `AgreementAmount`, `AgreementQuantity`, `PriceLimit` | | |
| BU access | businessUnitAccess `RequisitioningBU`/`RequisitioningBUId`, `OrderLocallyFlag`, `PurchasingSite`/`PurchasingSiteId`, `ShipToLocation`(Id/Code), `BillToBU`/`BilltoBUId`, `BillToLocation`(Id), `EnabledFlag` | | note casing `BilltoBUId` |

## Common mistakes
- No `businessUnitAccess` row for the requisitioning BU → agreement not usable for that BU's requisitions.
- Purchasing site for the requisitioning BU has no supplier-site assignment.
- Cancel/close agreements via FBDI: not supported → use REST (`cancel`, `finallyClose`).
- BPA FBDI: >10,000 lines per import not supported; notification controls cannot be imported.
- Adding lines via FBDI: header action UPDATE, line action ADD (new line number) or SYNC.

## Channel & exact technique
- Preferred: A (REST `draftPurchaseAgreements` + `submit`) for few agreements; `purchaseAgreementImportRequests` REST or C (FBDI) for bulk.
- Base `/fscmRestApi/resources/11.13.18.05`; items `application/vnd.oracle.adf.resourceitem+json` / `application/json`; actions `application/vnd.oracle.adf.action+json`.

### draftPurchaseAgreements (create/edit drafts and change orders)
- `/draftPurchaseAgreements` GET, POST; `/draftPurchaseAgreements/{draftPurchaseAgreementsUniqID}` GET, PATCH, DELETE
- Actions (POST `.../{id}/action/<name>`): `submit`, `validateDocument`, `withdraw`, `transferAuthoring`, `cancelChangeOrder`, `deleteChangeOrder`, `addContractTerms`, `removeContractTerms`, `applyLatestTemplate`, `changeContractSource`, `downloadLinesResources`, `viewPDF`, `viewMasterContract`, `eSign`; collection `/draftPurchaseAgreements/action/suggestCategory`.
- Children: `lines` (`/child/lines[/{AgreementLineId}]` GET POST PATCH DELETE; line action `undoChanges`; line children `attachments`, `DFF`, `itemAttributes`, `priceBreaks`), `businessUnitAccess` (`[/{businessUnitAccessUniqID}]` GET POST PATCH DELETE), `attachments`, `contractDocuments`, `supportingDocuments`, `DFF`, `notificationControls`, `templateUsages`.
- Submit docs example: `POST /draftPurchaseAgreements/300100650403840/action/submit` body `{"bypassApprovalsFlag": true}` or `{"validateBeforeSubmitFlag": true}` → `{"result":"SUCCESS"}`.
- Create payload (constructed; no readable docs example):
```json
{
  "ProcurementBUId": 204, "BuyerId": 100010026863783, "DocumentStyleId": 1, "DocumentTypeCode": "BLANKET",
  "SupplierId": 254, "SupplierSiteId": 32, "CurrencyCode": "USD", "StartDate": "2026-12-01", "Description": "Test BPA",
  "lines": [{"LineNumber": 1, "LineType": "Goods", "Description": "Test item", "Category": "Paper", "UOMCode": "Ea", "Price": 10}],
  "businessUnitAccess": [{"RequisitioningBUId": 204, "OrderLocallyFlag": false}]
}
```

### purchaseAgreements (approved; read + actions)
- `/purchaseAgreements` GET; `/purchaseAgreements/{purchaseAgreementsUniqID}` GET.
- Actions: `cancel`, `cancelChangeOrder`, `createProposal`, `communicatePurchaseAgreement`, `duplicate`, `finallyClose`, `freeze`, `unfreeze`, `hold`, `removeHold`, `renegotiate`, `manageCatalogAdminAuthoring`, `generateHighlights`, `viewPDF`, `viewMasterContract`.
- Children: `lines` (with `attachments`, `DFF`, `itemAttributes`, `priceBreaks`, `lifecycleDetails`), `businessUnitAccess`, `attachments`, `contractDocuments`, `DFF`, `notificationControls`, `lifecycleDetails`, `supportingDocuments`, `templateUsages`.
- Change order on an approved agreement: via draftPurchaseAgreements (pattern assumed same as PO; UNVERIFIED).
- Also: `/purchaseAgreementLines` GET (flat line search); `/purchaseAgreementAcknowledgments` GET/PATCH.

### purchaseAgreementImportRequests (REST bulk import)
- `POST /purchaseAgreementImportRequests` → `InterfaceHeaderId`; children `/child/lines` (+ `/child/itemAttributes`, `/child/priceBreaks`, `/child/translationItemAttributes`), `/child/businessUnitAccess`; action `POST /purchaseAgreementImportRequests/{InterfaceHeaderId}/action/importPurchaseAgreements`. Attributes not read: UNVERIFIED.

### C (FBDI)
| Type | Template | Control files / tables | UCM | Process |
|---|---|---|---|---|
| Blanket | `POBlanketPurchaseAgreementImportTemplate.xlsm` | `PoHeadersInterfaceBlanket.ctl`, `PoLinesInterfaceBlanket.ctl`, `PoLineLocationsInterfaceBlanket.ctl` (price breaks), `PoGAOrgAssignInterfaceBlanket.ctl` (BU access), `PoAttrValuesInterfaceBlanket.ctl`, `PoAttrValuesTlpInterfaceBlanket.ctl` / `PO_HEADERS_INTERFACE`, `PO_LINES_INTERFACE`, `PO_LINE_LOCATIONS_INTERFACE`, `PO_GA_ORG_ASSIGN_INTERFACE`, `PO_ATTR_VALUES_INTERFACE`, `PO_ATTR_VALUES_TLP_INTERFACE` | `prc/blanketPurchaseAgreement/import` | Import Blanket Purchase Agreements (FBDI page) / "Import Blanket Agreements" (playbook) |
| Contract | `POContractPurchaseAgreementImportTemplate.xlsm` | `PoHeadersInterfaceContract.ctl`, `PoGAOrgAssignInterfaceContract.ctl` / `PO_HEADERS_INTERFACE`, `PO_GA_ORG_ASSIGN_INTERFACE` | `prc/contractPurchaseAgreement/import` | Import Contract Purchase Agreements / "Import Contract Agreements" |
- ESS job paths/parameters: UNVERIFIED.

## How to verify
- `GET /purchaseAgreements?q=...` (agreement number attribute name UNVERIFIED; use `rest_describe`) → status open/approved.
- `GET /purchaseAgreements/{id}/child/businessUnitAccess` → requisitioning BU enabled.
- Functional: requisition line sourced to the agreement; `requisitionProcessingRequests` with `SourceAgreement` creates PO.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html — draftPurchaseAgreements, purchaseAgreements, purchaseAgreementImportRequests, purchaseAgreementLines, acknowledgments
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseagreements-post.html — required arrays, header/line/businessUnitAccess attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-draftpurchaseagreements-draftpurchaseagreementsuniqid-action-submit-post.html — submit
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/blanketpurchaseagreementsimport-3119.html, contractpurchaseagreementsimport-3120.html — FBDI
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fainp/integration-playbooks-for-procurement.pdf — FBDI constraints, REST guidance

## UNVERIFIED
- `DocumentTypeCode` values for blanket vs contract.
- Agreement number attribute name for `q` on purchaseAgreements.
- Agreement change-order flow via draftPurchaseAgreements PATCH.
- purchaseAgreementImportRequests attributes and action parameters.
- Exact scheduled-process display name (two variants in docs) and ESS job paths.
