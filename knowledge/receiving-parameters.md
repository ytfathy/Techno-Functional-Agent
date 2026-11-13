# Receiving Parameters

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
These are org-level receiving defaults. They must be set before receipts can be recorded in an inventory org. They cover:
- receipt routing
- date and quantity tolerances
- ASN control
- ship-to exception
- substitute / unordered receipts
- blind receiving
- receipt numbering
- RMA validation
- return shipping documents

PO-level tolerances override the org-level ones.

## Where in Fusion (FSM)
- Offering: Manufacturing and Supply Chain Materials Management. Functional area: **Receiving**. Task: **Manage Receiving Parameters**. Select the organization.
- Related: Manage Receiving Profile Options (Receiving). The "Redwood Self-Service Receiving Pages Enabled" profile.

## Prerequisites & dependencies
- An inventory org exists.
- Depends on this: PO receipts, ASN receipts, transfer order receipts, RMA receipts, self-service receiving. Self-service receiving needs Generation = Automatic and Type = Numeric.

## Key fields
| Field (UI label) | REST attribute (`receivingParameters`, read) | Meaning / options |
|---|---|---|
| Ship-to Exception Action | `ShipToExceptionAction` / `EnforceShipToLocationCode` | None / Reject / Warning |
| ASN Control Action | `ASNControlAction` / `ReceiptASNExistsCode` | None / Reject / Warning |
| Early / Late Receipt Tolerance in Days | `EarlyReceiptToleranceInDays`, `LateReceiptToleranceInDays` | |
| Receipt Days Exceed Action | `ReceiptExceedDaysAction` / `ReceiptDaysExceptionCode` | None / Reject / Warning |
| Over-Receipt Action | `OverReceiptAction` / `QuantityRcvExceptionCode` | None / Reject / Warning |
| Over-Receipt Tolerance (%) | `OverReceiptTolerance` | |
| Receipt Routing | `ReceiptRouting` / `ReceivingRoutingId` | Direct Delivery / Standard Receipt / Inspection Required |
| Allow substitute receipts | `AllowSubstituteReceipts` / `AllowSubstituteReceiptsCode` | |
| Allow unordered receipts | `AllowUnorderedReceipts` / `AllowUnorderedReceiptsCode` | |
| Enforce blind receiving | `EnforceBlindReceiving` / `BlindReceivingCode` | |
| Print receipt traveler | `PrintReceiptTraveler` / `PrintReceiptTravelerCode` | |
| Include closed POs for receipt | `IncludeClosedPurchaseOrdersForReceipt` / `IncludeClosedPOReceipt` | |
| Allow routing override | `AllowRoutingOverride` / `AllowRoutingOverrideCode` | |
| Process all lines together | `ProcessAllLinesTogether`, `ProcessASNLinesTogether` | |
| Print shipping docs for returns to suppliers / drop ship / RMA | `PrintShippingDocumentsForReturnsToSuppliers`, `IntfReturnsToShipping`, `IntfDropshipsToShipping`, `IntfRmasToShipping` | |
| Allow defaulting of lots and serials from ASN / TO | `AllowDefaultingOfLotsAndSerialNumbersFromASNFlag`, `...FromTransferOrderFlag` | |
| Receipt number Generation | `ReceiptNumberGeneration` / `UserDefinedReceiptNumberCode` | Automatic / Manual |
| Receipt number Type | `ReceiptNumberType` / `ManualReceiptNumberType` | Numeric / Alphanumeric |
| Next Number | `NextReceiptNumber` | |
| RMA Receipt Routing | `RMAReceiptRouting` / `RMAReceiptRoutingId` | |
| RMA Validate Lots / Serials | `RMALotValidation` / `EnforceRMALotNumber`, `RMASerialNumbersValidation` / `EnforceRMASerialNumbers` | Restricted / Restricted with warning / Unrestricted |
| Delivery required for expense / PAR locations | `DeliveryRequiredForExpenseLocations`, `DeliveryRequiredForPARLocations` | |

## Common mistakes
- Automatic numbering with Alphanumeric type. Automatic only generates numeric numbers.
- Changing from alphanumeric to numeric when alphanumeric receipts exist. This is not allowed.
- Expecting org tolerances to win over PO-schedule tolerances. The PO level overrides the org.
- Brazil (fiscal document) orgs: some parameters are forced (Standard routing, no unordered receipts, print return docs).

## Channel & exact technique
- Preferred channel: **D (UI)** for create/update. **REST is read-only** for this setup.
- A (read): `GET /fscmRestApi/resources/11.13.18.05/receivingParameters`, `GET .../receivingParameters/{receivingParametersUniqID}`. Finders: `PrimaryKey` (OrganizationId), `findByOrganization` (bindOrganizationCode, bindOrganizationId). No POST/PATCH in 26D.
- B (FSM CSV): UNVERIFIED.
- D (UI): Manage Receiving Parameters, then select the org, then the tabs/regions General, Receipt Number, RMA. Write a playbook `playbooks/manage-receiving-parameters.md` when needed.

## How to verify
`GET receivingParameters?finder=findByOrganization;bindOrganizationCode=<ORG>`

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-receivingparameters-get.html — attributes, finders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — GET only
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implementing-manufacturing-and-supply-chain-materials-management.pdf — ch. 9 Receiving: General / Receipt Number / RMA parameter options, Brazil defaults, tolerance examples

## UNVERIFIED
- The exact mapping of UI label to REST attribute for pairs like `ShipToExceptionAction` vs `EnforceShipToLocationCode` (meaning vs code). Inferred from names.
- FSM Setup CSV support for Manage Receiving Parameters.
- Whether receiving parameters are auto-created with defaults when an inventory org is created.
