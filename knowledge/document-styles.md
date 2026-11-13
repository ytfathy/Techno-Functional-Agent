# Document Styles (Manage Document Styles)

> Release: 26D · Last researched: 2026-11-14 · Status: VERIFIED (REST) / PARTIAL (UI labels)

## Business purpose
Reusable purchasing document styles turn procurement features on or off per style. Disabled features are hidden on the document; for example, no price break region when price breaks aren't allowed. A style can be limited to purchase bases and line types, and it renames the document types (PO / Blanket / Contract display names) to match company conventions. Complex work (progress payments, retainage, work confirmation), outside processing, consignment, configuration ordering and credit lines are all enabled per style. New documents default to the "Standard Style" display name for each document type.

## Where in Fusion (FSM)
- Offering: Procurement
- Functional area: Procurement Foundation
- Task name: **Manage Document Styles**
- Privilege: Manage Purchasing Document Style (Procurement Application Administrator)
- No scope prompt (global, not per BU)

## Prerequisites & dependencies
- Line types exist if Line Types = Specified.
- Feature opt-ins where relevant: complex work / progress payments, outside processing (Manufacturing), "Create Purchase Order Lines with Negative Amounts" for credit line types.
- Work confirmation search needs Oracle Search indexes `fa-prc-po` and `fa-prc-wc` (index definition and initial ingest ESS).
- Dependents: Group Requisitions (style is a grouping key), POs, BPAs, CPAs, `purchasingLineTypesLOV` finder `findByDocumentStyle`.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Name | `StyleName` (required) | Unique style name | |
| Description | `StyleDescription` | | |
| Status | `Status` / `StatusCode` (required) | Active / Inactive | Code example: `ACTIVE` |
| Purchase Bases: Goods / Services / Both | `QuantityPurchaseBasisEnabledFlag`, `AmountPurchaseBasisEnabledFlag` | Allowed purchase bases | REST key shows `PURCHASE_BASES,GOODS` / `SERVICES` |
| Line Types: All / Specified | `LineTypeAllowed` / `LineTypeAllowedCode` (required) | All line types, or only those listed | Code example `ALL`. Child `lineTypes` (`LineTypeId`, `EnabledFlag`) when Specified |
| Outside Processing Enabled | `OutsideProcessingEnabledFlag` | OSP items | Mutually exclusive with Consignment Terms and Configuration Ordering. Can't be disabled once used |
| Consignment Terms Enabled | `ConsignmentTermsEnabledFlag` | Consignment agreements | Mutually exclusive (see above) |
| Configuration Ordering Enabled | `ConfigurationOrderingEnabledFlag` | Configured items | Mutually exclusive (see above) |
| Progress Payments Enabled | `ProgressPaymentEnabledFlag` | Complex work: pay items and progress payment schedules | Delivered alternative: **Complex Work Style** |
| Retainage Enabled | `RetainageEnabledFlag` | Retainage on complex work | User-defined styles only |
| Work Confirmation | `WorkConfirmationEnabledFlag` | Work confirmations | Can be enabled on Complex Work Style only if no receipts exist for its POs |
| Credit Line Types Enabled | `CreditLineTypesEnabledFlag` | Allows credit (negative/zero amount) lines | Can't be disabled after enabling. Incompatible with consignment, configuration ordering, OSP and complex work |
| Purchase Order: Display Name | `StandardDocumentStyleTypeDisplayName` | PO name shown to users | |
| Blanket Purchase Agreement: enabled + Display Name | `BlanketDocumentStyleTypeEnabledFlag`, `BlanketDocumentStyleTypeDisplayName` | Use the style for BPAs | |
| Price Breaks Allowed (BPA) | `PriceBreaksEnabledFlag` | Price break region on BPA | |
| Contract Purchase Agreement: enabled + Display Name | `ContractDocumentStyleTypeEnabledFlag`, `ContractDocumentStyleTypeDisplayName` | Use the style for CPAs | |
| (read-only) | `StyleId`, `StyleType`, Created/LastUpdate* | | |

Delivered styles: **Standard Style** (the default for new documents), **Complex Work Style**, and **Outside Processing Style** (read-only: Goods, Line Types All, OSP enabled, with OSP PO/BPA/CPA display names and BPA price breaks Yes).

## Common mistakes
- Trying to edit the delivered Outside Processing Style. Create a new style instead.
- Enabling two of OSP / Consignment / Configuration Ordering together. Not allowed.
- Enabling Credit Line Types on a style used for complex work. Not allowed, and it can't be undone.
- Line Types = Specified with no `lineTypes` rows, so no usable line types.
- Assuming progress payment, retainage or OSP flags can be toggled later. OSP can't be disabled once documents use the style. Older-release docs say complex payment flags lock after save (UNVERIFIED for 26D).

## Channel & exact technique
- Preferred channel: **A (REST)**. A full create/read/update resource exists in 26D.
- A (REST):
  - `GET /fscmRestApi/resources/11.13.18.05/purchasingDocumentStyles` (finder `PrimaryKey;StyleId=`)
  - `GET /fscmRestApi/resources/11.13.18.05/purchasingDocumentStyles/{purchasingDocumentStylesUniqID}`
  - `POST /fscmRestApi/resources/11.13.18.05/purchasingDocumentStyles`. Required: `StyleName`, `StatusCode`, `Status`, `LineTypeAllowedCode`, `LineTypeAllowed`. `Upsert-Mode` header is supported.
  - `PATCH /fscmRestApi/resources/11.13.18.05/purchasingDocumentStyles/{purchasingDocumentStylesUniqID}`
  - Child: `GET/POST .../purchasingDocumentStyles/{purchasingDocumentStylesUniqID}/child/lineTypes`, `GET .../child/lineTypes/{lineTypesUniqID}`. No PATCH or DELETE on the child.
  - No DELETE on styles; inactivate via `StatusCode`.
  - The UniqID is a composite key. Use the `self` href from GET, not `StyleId`.
  - LOV: `GET /fscmRestApi/resources/11.13.18.05/purchasingDocumentStylesLOV`, finders `PrimaryKey;StyleId`, `findByDocumentType;DocumentSubtype,EnabledFlag,StatusCode`, `findAgreementStylesByStatus;EnabledFlag,StatusCode`. Attributes include `StyleId`, `StyleName`, `DisplayName`, `DocumentSubtype`, `EnabledFlag`, `PriceBreaksFlag`, `OutsideProcessingEnabledFlag`, `ConsignmentTermsEnabledFlag`, `ConfigurationOrderingEnabledFlag`, `EnabledFeature`.
- Example create body (from docs): `{"StyleName":"...","StatusCode":"ACTIVE","QuantityPurchaseBasisEnabledFlag":true,"AmountPurchaseBasisEnabledFlag":true,"LineTypeAllowedCode":"ALL","ProgressPaymentEnabledFlag":false,"StandardDocumentStyleTypeDisplayName":"..."}`
- B (FSM CSV): TaskCode UNVERIFIED.
- D (UI): `playbooks/document-styles.md` (fallback).

## How to verify
- `GET purchasingDocumentStyles?q=StyleName='<name>'&expand=lineTypes`
- `purchasingDocumentStylesLOV?finder=findByDocumentType;DocumentSubtype=STANDARD,EnabledFlag=true,StatusCode=ACTIVE` (subtype values UNVERIFIED)
- Create a PO with the style and check that hidden or visible regions match.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/document-style-options.html — purpose, BPA/CPA styles, hidden features
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-s-a-document-style.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/define-a-document-style-for-outside-processing.html — UI labels (Purchase Bases, Line Types All/Specified, Outside Processing Enabled, Display Name, sections), mutual exclusivity
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-review-the-delivered-document-style-for-outside.html — delivered OSP style
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/enable-progress-payment-schedules.html — Progress Payments Enabled, Complex Work Style
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-retainage.html — Retainage Enabled, privilege
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/enable-work-confirmation.html — work confirmation, search indexes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-you-create-purchase-order-lines-with-negative-amounts.html — Credit Line Types Enabled
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-purchasing-document-header-defaults-work.html — "Standard Style" default
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchasing-document-styles.html — operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchasingdocumentstyles-get.html — attributes, lineTypes child
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchasingdocumentstyles-post.html — required attributes, example
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchasing-document-styles-line-types.html — child operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchasingdocumentstyleslov-get.html — LOV and finders

## UNVERIFIED
- Exact UI label for Work Confirmation and Credit Line Types on the Create Document Style page. The work confirmation doc page itself says to set "Progress Payments Enabled".
- An "Advances" option for Fusion styles. Only EBS docs mention it; it is not in the 26D REST attributes, so it probably doesn't exist.
- Whether complex payment flags are locked after the first save in 26D.
- `DocumentSubtype` code values for the LOV finder (e.g. STANDARD / BLANKET / CONTRACT; inferred from the REST composite key).
- FSM Setup Task CSV support and TaskCode for Manage Document Styles.
