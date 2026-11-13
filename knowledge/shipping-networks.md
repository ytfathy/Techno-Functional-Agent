# Shipping Networks (Interorganization Parameters) and Intersubinventory Parameters

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- Interorganization parameters define the **shipping network** between a source (from) and a destination (to) inventory org. They control:
  - the transfer type (**Direct** or **In transit**)
  - the receipt routing for in-transit transfers
  - whether a **transfer order is required**
  - expense-destination receipt requirement and routing
  - backorder cancellation
- No row between two orgs means no interorg transfer or transfer order between them.
- Intersubinventory parameters do the same for transfers between subinventories inside one org.

## Where in Fusion (FSM)
- Offering: Manufacturing and Supply Chain Materials Management. Functional area: **Inventory Management**. Task: **Manage Interorganization Parameters**.
- Same offering/area. Task: **Manage Intersubinventory Parameters**.

## Prerequisites & dependencies
- Both inventory orgs exist and have locations.
- For transfer orders also: transit times between locations (Manage Transit Times) and shipping methods assigned to orgs (carriers). See `carriers.md` and `transfer-orders.md`.
- Depends on this: transfer orders, internal material transfers (requisitions), interorg transfers.

## Key fields
| Field (UI label) | REST attribute (`interOrganizationParameters`) | Meaning | Notes |
|---|---|---|---|
| From organization | `FromOrganizationId` (req) / `FromOrganizationCode` | source | |
| To organization | `ToOrganizationId` (req) / `ToOrganizationCode` | destination | |
| Inventory destination transfer type | `IntransitType` (`IntransitTypeMeaning`) | Direct or In transit | default "1"; code meanings UNVERIFIED |
| Inventory destination receipt routing | UNVERIFIED (no explicit attribute; likely the routing attrs below) | Standard / Direct / Inspection | |
| Transfer order required | `TransferOrderRequiredFlag` | | default false |
| Expense destination receipt required | `ManualReceiptExpenseFlag` | | default false |
| Expense destination receipt routing | `ExpenseDestReceiptRouting` / `ExpenseDestinationRoutingMeaning`, `RoutingHeaderId` / `RoutingHeader` | | |
| Cancel backorders (inventory / expense) | `FillKillInvToLookup`, `FillKillExpToLookup` | default `ORG_LEVEL` | |
| Distance | `ToOrganizationDistance`, `DistanceUOMCode` | | |

Intersubinventory (`interSubinventoryParameters`):
- Required: `OrganizationId`, `DestinationTypeCode` (inventory / expense), `StartDate`.
- UI fields: destination subinventory, source subinventory (or All), receipt required at expense destination, transfer type, receipt routing.

## Common mistakes
- Only one direction defined. Each From/To pair is its own row; define the reverse if needed.
- Enforce Shipping Method = Yes in shipping parameters but no default shipping method on the transit time. Then the transfer order is not created ("Transit times weren't found...").
- Expense destination without "receipt required". The TO is then considered received and delivered at shipment.

## Channel & exact technique
- Preferred channel: **A (REST)**.
- A:
  - `GET|POST /fscmRestApi/resources/11.13.18.05/interOrganizationParameters`; `GET|PATCH|DELETE .../interOrganizationParameters/{InterorganizationParametersId}`. Child `DFF`.
  - `GET|POST /interSubinventoryParameters`; `GET|PATCH|DELETE .../{IntersubParametersId}`. Child `DFF`.
- D (UI): Manage Interorganization Parameters.
- REST for transit times or "Manage Transit Times": none found in the 26D SCM REST endpoint list (UNVERIFIED). Use the UI task Offering MSCMM > Carriers and Transit Times > **Manage Transit Times**.

## How to verify
- `GET interOrganizationParameters?q=FromOrganizationCode='A';ToOrganizationCode='B'`
- Functional test: create a transfer order (`transfer-orders.md`).

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-interorganizationparameters-post.html — attributes, required fields
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-intersubinventoryparameters-post.html — intersubinventory required fields
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — methods
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implementing-manufacturing-and-supply-chain-materials-management.pdf — ch. 3 Internal Material Transfers: interorg and intersubinventory parameters, shipping method setup, setup task table (Manage Transit Times in Carriers and Transit Times)

## UNVERIFIED
- Code values for `IntransitType` (1 = direct? 2 = in transit?) and the attribute that holds inventory-destination receipt routing.
- REST resource for transit times.
- FSM CSV support for Manage Interorganization Parameters.
