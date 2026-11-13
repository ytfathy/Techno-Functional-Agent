# Line Types (Manage Line Types)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
A line type tells Fusion whether a requisition or PO line is quantity-based goods, a fixed-price service, rate-based, or a credit line. It defaults the purchase basis, product type, UOM, category, match approval level, invoice match option and receipt close tolerance. Line types default from Configure Requisitioning BF (req lines), can be restricted per document style, and drive retroactive pricing eligibility: only purchase basis Goods is repriced.

## Where in Fusion (FSM)
- Offering: Procurement
- Functional area: Procurement Foundation (UNVERIFIED; no 26D topic names the task)
- Task name: **Manage Line Types** (UNVERIFIED exact name in 26D docs)

## Prerequisites & dependencies
- UOMs and purchasing categories exist (for the default category and UOM).
- Dependents: Configure Requisitioning BF Line Type, Configure Procurement BF Line Type (UNVERIFIED), document style `lineTypes` child, requisition/PO lines (`LineTypeCode` e.g. `Goods`, `Fixed Price Services`).

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Line Type | `LineType` (required, 30) | Name | e.g. Goods |
| Code | `LineTypeCode` (required, 30) | Alternate key (`LINE_TYPE_CODE`, "used as alternate key for setup migrator") | e.g. `2WAYR` |
| Description | `LineTypeDescription` (required, 240) | | |
| Purchase Basis | `PurchaseBasis` / `PurchaseBasisCode` (default `GOODS`) | Goods (quantity) vs Services (amount/fixed price) | Example shows code `GOODS` with meaning "Quantity". Credit lines use Amount |
| Matching basis | table `MATCHING_BASIS` (not null) | Quantity vs amount matching | **Not exposed** in REST. Likely derived from purchase basis (UNVERIFIED) |
| Product Type | `ProductType` / `ProductTypeCode` (default `GOODS`) | Defaults Product Type on PO schedules | Goods / Services |
| Default Category | `DefaultCategoryId` (POST), `DefaultCategory`/`DefaultCategoryCode` (LOV) | | |
| Default UOM | `DefaultUOMCode` | | |
| Match Approval Level | `DefaultMatchApprovalLevelCode` | 2-Way / 3-Way / 4-Way | Code values UNVERIFIED |
| Invoice Match Option | `DefaultInvoiceMatchOption` / `DefaultInvoiceMatchOptionCode` | Order / Receipt | Table `MATCH_OPTION` P/R |
| Receipt Close Tolerance Percent | `DefaultReceiptCloseTolerancePercent` | | Credit types = 100 |
| Credit | `CreditLineFlag` (default false) | Line type usable for credit lines | LOV exposes it as `CreditFlag` |
| End Date | `EndDate` | Inactive after this date | |
| Receipt required | table `RECEIVING_FLAG` | Default receipt required | **Not exposed** in REST. UI label UNVERIFIED |
| Inspection required | table `INSPECTION_REQUIRED_FLAG` | | Not in REST |
| Outside processing | table `OUTSIDE_OPERATION_FLAG` | OSP line type | Not in REST |
| DFF | child `DFF` (`__FLEX_Context`) | Purchasing Line Types DFF (PO_LINE_TYPES) | |

Delivered examples:
- **Goods**: quantity, UOM, unit price.
- **Fixed Price Services**: amount. Received and matched by amount.
- **Rate Based Services**: quantity × rate.

Credit line types default to Purchase Basis Amount, Product Type Services, Match Approval Level 2 Way, Invoice Match Option Order, and Receipt Close Tolerance 100. No receipts are allowed, and Accrue on Receipt is No.

## Common mistakes
- Creating a Services (amount) line type and expecting retroactive pricing. Only Goods is repriced.
- A style with Line Types = Specified that omits the new line type, so the line type is not selectable.
- Relying on REST to set receipt required, inspection or OSP flags. These aren't exposed, so use the UI.

## Channel & exact technique
- Preferred channel: **A (REST)** for name, code, basis, product type, defaults and credit flag. **D (UI)** for receipt required, inspection required and outside processing.
- A (REST): `GET/POST /fscmRestApi/resources/11.13.18.05/purchasingLineTypes`, `GET/PATCH .../purchasingLineTypes/{LineTypeId}`. Child `DFF`. No DELETE: end-date the line type instead.
- Read LOV: `GET /fscmRestApi/resources/11.13.18.05/purchasingLineTypesLOV`, finders `PrimaryKey;LineTypeId`, `findActiveLineTypes;CurrentDate`, `findByDocumentStyle;DocumentType,StyleId`.
- Example POST: `{"LineType":"2WAYR","LineTypeCode":"2WAYR","LineTypeDescription":"2-Way match to receipt","CreditLineFlag":false,"ProductTypeCode":"GOODS","PurchaseBasisCode":"GOODS"}`
- B (FSM CSV): UNVERIFIED. The `LINE_TYPE_CODE` comment ("alternate key for setup migrator") suggests CSV/migration support, but this is not confirmed.
- D (UI): no playbook yet.

## How to verify
- `GET purchasingLineTypes?q=LineTypeCode='<code>'`
- `purchasingLineTypesLOV?finder=findByDocumentStyle;DocumentType=...,StyleId=...`
- Create a req/PO line with the line type.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/examples-of-purchase-order-line-types.html — Goods / Fixed Price Services / Rate Based Services
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-you-create-purchase-order-lines-with-negative-amounts.html — credit line type defaults
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchasing-line-types.html — operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchasinglinetypes-post.html — attributes, required fields, example
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchasinglinetypeslov-get.html — LOV attributes and finders
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/initiate-retroactive-price-update.html — only Goods purchase basis repriced
- https://docs.oracle.com/en/cloud/saas/procurement/25d/oedmp/polinetypesb-16748.html — PO_LINE_TYPES_B columns (25D; 26D page not reachable)

## UNVERIFIED
- The FSM task name "Manage Line Types" and its functional area in 26D.
- UI labels for receipt required, inspection required, outside processing and matching basis, and whether matching basis is user-settable.
- Code values for `DefaultMatchApprovalLevelCode` and `DefaultInvoiceMatchOptionCode`.
- PurchaseBasisCode values other than `GOODS` (e.g. `SERVICES`/`TEMP LABOR`).
- FSM Setup Task CSV support and TaskCode.
