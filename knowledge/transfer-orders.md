# Transfer Orders (setup and creation through Supply Requests)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- A transfer order moves material between orgs (interorg) or between subinventories (intraorg). Demand and supply sit in one document.
- Destination type is **INVENTORY** or **EXPENSE**.
- Transfer orders are created by **Supply Chain Orchestration** from a supply request (`SupplyType=TRANSFER`). Sources: Inventory (min-max), Planning, Self-Service Procurement (internal material transfer requisitions) or an external system.

## Where in Fusion (FSM)
All tasks are in Offering: Manufacturing and Supply Chain Materials Management.

| Task | Functional area | Requirement |
|---|---|---|
| Manage Interorganization Parameters | Inventory Management | Required. Enable Transfer Order Required |
| Manage Intersubinventory Parameters | Inventory Management | Only for intra-org |
| Manage Subinventories and Locators | Inventory Management | Optional. Cancel Backorders at destination subinventory |
| Manage Transit Times | **Carriers and Transit Times** | Required. Set the Default Shipping Method there |
| Manage Shipping Parameters | **Shipping** | Required. Enforce Shipping Method |
| Manage Receiving Profile Options | Receiving | Optional |

Internal material transfers from requisitions also need:
- Procurement feature opt-in "Internal Material Transfers"
- Configure Requisitioning Business Function: "Enable supply availability for internal transfers"
- Locations assigned to orgs
- Shipping method assigned to orgs on Edit Carriers
- On-hand stock with cost

## Prerequisites & dependencies
- Source and destination orgs and subinventories with locations.
- Interorg parameters (`shipping-networks.md`).
- Transit times with a shipping method.
- Carrier shipping method assigned to the orgs (`carriers.md`).
- Item with `TransferOrdersEnabledFlag`, assigned to both orgs.
- Transfer price: Supply Chain Financial Orchestration (cost-based when both orgs are in the same BU).

## Key fields (supply request, transfer type)
| Field | REST attribute (`supplyRequests` header / `supplyRequestLines`) | Notes |
|---|---|---|
| Batch | `InterfaceBatchNumber` (req, header and line) | |
| Source app | `SupplyOrderSource` (req) | lookup `ORA_DOS_SUPPLY_ORDER_SOURCE` (DOO, INV, YPS...). The doc example uses "EXT" |
| Interface source | `InterfaceSourceCode` | example "EXT" |
| Status | `SupplyRequestStatus` (req) | example "NEW" |
| Request date | `SupplyRequestDate` (req) | |
| Reference number | `SupplyOrderReferenceNumber` / `SupplyOrderReferenceLineNumber` | caller's own keys |
| Trusted source | `TrustedSource` (marked req) | 1 trusted Oracle app, 0 external |
| Process now | `ProcessRequestFlag` | example "Y" |
| Supply type | line `SupplyType` (req) | **`TRANSFER`** (lookup `ORA_DOS_SUPPLY_ORDER_TYPE`) |
| Orgs | `SourceOrganizationCode`/`Id`, `DestinationOrganizationCode`/`Id` | |
| Subinventories | `SourceSubinventoryCode`, `DestinationSubinventoryCode` | |
| Destination type | `DestinationTypeCode` | `INVENTORY` / `EXPENSE` |
| Item / qty | `ItemNumber`/`ItemId`, `Quantity` (req), `UOMCode` (req) | |
| Dates | `NeedByDate`, `RequestedShipDate` | |
| Ship method | `CarrierId`/`CarrierCode`, `ShipModeOfTransport`, `ShipClassOfService` | |
| People | `PreparerEmail`, `DeliverToRequesterEmail` | |
| Line status | `ProcessStatus` (marked req) | |
| Result | `TransferOrderHeaderNumber`, `TransferOrderHeaderId`, `TransferOrderLineNumber` | read back |

## Common mistakes
- No interorg parameter row, or Transfer Order Required not set.
- No transit time or default ship method while Enforce Shipping Method is on, so no TO is created.
- Item not transfer-order enabled or not assigned to the destination org.
- Expecting `POST /transferOrders`. **It does not exist.** That resource is GET/PATCH only.

## Channel & exact technique
- Preferred channel: **A (REST)** through `supplyRequests`.
- A:
  - Create: `POST /fscmRestApi/resources/11.13.18.05/supplyRequests`, with lines nested in `supplyRequestLines`.
  - `GET|PATCH .../supplyRequests/{SupplyOrderReferenceNumber}`.
  - Children: `supplyRequestLines` (POST/PATCH; sub-children `distributionDetails`, `errorMessages`, `transferCostRequestDetails`, `supplyRequestLinesXferDFF`, `supplyLinesIntStrpDFF`), `supplyOrderLines` (read: `transferSupply`, `buySupply`, `makeSupply`, `atpSupply`), `supplyRequestsXferDFF`.
  - Read/update TOs:
    - `GET /transferOrders`, `GET|PATCH /transferOrders/{HeaderId}`.
    - Children `transferOrderLines` (GET/PATCH) with `transferOrderDistributions`, `transferOrderLineDFFs`, `inventoryAttributesDFF`, `transferLineItemSubstitutes`; header child `transferOrderHeaderDFFs`.
    - Finders `FindByTransferOrderDetails` (pTransferOrder, pSourceOrganization, pDestinationOrganization, pItemNumber, pLineNumber, pLineStatus, pScheduledShipDate, pTransactionOrigin), `FindByShippingBatch` (pBatch).
  - Receiving views: `transferOrdersForReceiving`, `transferOrderLinesForReceiving` (GET).
  - Doc example payload: `{"InterfaceSourceCode":"EXT","InterfaceBatchNumber":"batch09","SupplyRequestStatus":"NEW","SupplyRequestDate":"...","SupplyOrderSource":"EXT","SupplyOrderReferenceNumber":"0009","ProcessRequestFlag":"Y","supplyRequestLines":[{"InterfaceBatchNumber":"batch09","SupplyOrderReferenceLineNumber":"00091","DestinationOrganizationCode":"M1","SourceOrganizationCode":"M2","DestinationSubinventoryCode":"Stores","SourceSubinventoryCode":"Stores","ItemNumber":"..","InterfaceSourceCode":"EXT","SupplyOrderSource":"EXT","NeedByDate":"...","Quantity":10,"UOMCode":"Ea","DestinationTypeCode":"INVENTORY","SupplyType":"TRANSFER"}]}`
- D (UI): Inventory Management > Manage Transfer Orders (view/edit).

## How to verify
- `GET supplyRequests/{ref}?expand=supplyRequestLines` and check `ProcessStatus`, `errorMessages`, `TransferOrderHeaderNumber`.
- Then `GET transferOrders?finder=FindByTransferOrderDetails;pTransferOrder=<num>`.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-supplyrequests-post.html — attributes, lookups, example payload
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-transferorders-get.html — finders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-transferorders-headerid-patch.html — PATCH
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — no POST on transferOrders, children
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implementing-manufacturing-and-supply-chain-materials-management.pdf — ch. 3 Internal Material Transfers: setup task table, interorg/intersub params, shipping method setup, IMT prerequisites

## UNVERIFIED
- The "transfer order parameters" name in the request has no separate FSM task in 26D docs. The setup is the task set above.
- Valid `SupplyOrderSource` / `InterfaceSourceCode` for an external integration ("EXT" appears only in the example). Check the lookup.
- Whether `TrustedSource` and line `ProcessStatus` must be sent on create. They are marked required, but the doc example omits them.
- FBDI for transfer orders (not researched).
