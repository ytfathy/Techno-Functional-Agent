# Shipping Execution (setup, pick wave release, pick confirm, ship confirm)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL

## Business purpose
- Outbound fulfilment of sales orders / transfer orders: pick release (pick wave) -> pick confirm -> (pack) -> ship confirm -> inventory issue + order status update.
- Setup is per ship-from inventory organization. Rules (release sequence, pick slip grouping, ship confirm, release rule) drive how lines are released and processed.
- Affected: warehouse, shipping agents, order managers (backorders), billing (shipped quantity).

## Where in Fusion (FSM)
- Offering: **Manufacturing and Supply Chain Materials Management**
- Functional area: **Shipping** (use Show: All Tasks)
- Tasks, in the order Oracle lists them (all required per the guide):
  1. Manage Release Sequence Rules
  2. Manage Ship Confirm Rules
  3. Manage Shipping Cost Types
  4. Manage Transportation Schedules
  5. Manage Shipping Exceptions
  6. Manage Default Packing Configurations
  7. Manage Shipping Zones
  8. Manage Shipping Parameters (per ship-from organization)
  9. Manage Pick Wave Release Rules
- Common tasks (shared): Manage Shipping Value Sets, Manage Shipping Descriptive Flexfields, Manage Shipping Lookups, Manage Shipping Document Sequences.
- **Manage Pick Slip Grouping Rules**: Offering MSCM, functional area **Inventory Management** (not Shipping).
- Document job sets: functional area **Manufacturing Master Data**, task **Manage Enterprise Scheduler Job Definitions and Job Sets for Financial, Supply Chain Management, and Related Applications** -> tab Manage Job Sets -> Actions > Create. Job set assignment is done by task **Manage Shipping Document Job Set Rules** (Shipping area; only visible after opt-in "Manage and Distribute Shipping Documents" - from search snippet of 25B/23D docs) and **Shipping Document Output Preferences**.
- Scope when opening: Manage Shipping Parameters asks for the inventory organization (ship-from org).
- Redwood pages exist for Shipping Parameters, Pick Wave Release Rules, Release Sequence Rules, Ship Confirm Rules, Pick Slip Grouping Rules, Document Job Set Rules (25A/25B readiness); the classic pages stay available.
- CSV export/import (Setup Task CSV) for these tasks: UNVERIFIED. Use `fsm_find_task` on the pod.

## Prerequisites & dependencies
- Inventory organization (shipping enabled), subinventories (pick-from + staging), locators if used -> `inventory-organizations.md`, `subinventories-locators.md`.
- Items assigned to the org, with on-hand stock (reservations/allocation) -> `items-item-classes.md`.
- Carriers + shipping methods assigned to orgs -> `carriers.md`; transit times / interorg for transfer orders -> `shipping-networks.md`, `transfer-orders.md`.
- Document sequence categories (packing slip, bill of lading, commercial invoice) for Shipping Parameters.
- Release sequence rule + pick slip grouping rule + ship confirm rule + document job set must exist BEFORE the pick wave release rule that references them.
- Upstream demand: sales order scheduled into the ship-from org (`order-management.md`) or transfer order.
- Depends on this: Order Management Ship task (fulfilment), receivables billing, costing.

## Key fields
Manage Shipping Parameters (UI label; table in "Considerations for Managing Shipping Parameters"):
| Field (UI label) | REST attribute (`shippingParameters`) | Meaning | Notes / typical value |
|---|---|---|---|
| (organization) | `OrganizationId`, `OrganizationCode` | Ship-from org | finder `PrimaryKey;OrganizationId=` |
| Appending Limit | not in the REST attribute list I saw | Do Not Append / Start of Staging / End of Staging | UI only (UNVERIFIED in REST) |
| Packing Slip / Bill of Lading / Commercial Invoice Document Sequence Category | n/a | numbering of documents | BoL defaults to preseeded `ONT:1` |
| Consolidate Backordered Lines | n/a | merge backordered split lines | only unassigned, unpacked |
| Enable Carrier Manifesting | n/a | send open shipments to manifesting system | packing happens before |
| Pick Release Batch Size | n/a | lines per batch | default 50; >999 treated as 999 |
| Reservation Behavior for Integration to External Systems | `WmsReservationBehavior` (likely) | what goes to 3PL/WMS | UNVERIFIED mapping |
| Trade Compliance Screening Method | `TradeComplianceMethod`/`TradeComplianceMethodCode` | None / Pick confirm / User initiated | |
| Shipping Tolerance Behavior | n/a | line closes at Under Tolerance or Requested Quantity | |
| Create Shipments | `CreateShipmentsFlag` | auto assign released lines to shipment | |
| Automatically Pack | `AutomaticallyPackFlag`, `EnforcePackingFlag` | | |
| Enforce Ship Method / Ship Set | `EnforceShipMethodFlag`, `EnforceShipSetFlag` | | |
| Auto ship on pick confirm | `AutoShipOnPickConfirmFlag` | | |
| Quick ship | `QuickShipEnabledFlag`, `QuickShipSubinventory`, `QuickShipLocator`/`Id` | needed for the `confirm` REST action (see below) | |
| Staging | `StagingSubinventory`, `StagingLocator`/`Id` | | |
| Shipment grouping | `GroupByCustomerFlag`, `GroupByFOBFlag`, `GroupByFreightTermsFlag`, `GroupByShipMethodFlag`, `ShipmentCreationCriteria(Code)` | | |
| LPN | `LPNEnabledFlag`, `LPNControl` (only non-read-only), `LPNReuseAllowedFlag` | | |
| UOM classes | `WeightUOMClass`, `VolumeUOMClass` | | |
| Overshipment / Undershipment Tolerance for Transfer Orders | n/a | % | |

Pick wave release rule (`releaseRules`; `ReleaseRule` required, `StartDateActive` non-nullable):
| Field | REST attribute | Notes |
|---|---|---|
| Name | `ReleaseRule` (req, max 60), `ReleaseRuleId` | |
| Effective | `StartDateActive` (non-nullable), `EndDateActive` | UTC only, no time zone stored |
| Ship-from org | `ShipFromOrganizationId`/`Code`/`Name` | |
| Demand selection | `OrderNumber`, `OrderId`, `OrderTypeCode`, `SourceOrderTypeCode`, `CustomerId`, `ShipToLocationId`, `ShipSetName`, `ItemNumber`, `InventoryItemId`, `CatalogId`, `CategoryId`, `ShipMethodCode`, `ShipmentPriorityCode`, `DestinationTypeCode`, `ZoneId`, `GeographyId`, `From/ToRequestedDate`, `From/ToScheduledShipDate` (and `Start/End...Days/Hours` offsets) | |
| Fulfilment | `PickFromSubinventory`, `PickFromLocatorId`, `ReleaseSubinventory`, `ReleaseLocatorId`, `StagingSubinventory`, `StagingLocatorId` | |
| Processing | `ReleaseSequenceRuleId`, `PickSlipGroupingRuleId`, `ShipConfirmRuleId`, `DocumentSetId`, `JobSetName`, `AutoPickConfirmFlag`, `CreateShipmentsFlag`, `AutomaticallyPackFlag`, `AppendShipmentsFlag`, `IncludeAssignedLinesFlag`, `AutoShipOnPickConfirmFlag`, `PriorReservationsFlag`, `ShipmentCreationCriteriaCode`, `TradeComplianceMethod` | |
| Status | `ReleaseStatusCode` (default `E`) | |

## Common mistakes
- Rule created before its release sequence / pick slip grouping / ship confirm rules or job set exist.
- Release rule dates entered in local time (stored as UTC only).
- Ship confirm via REST `.../action/confirm`: doc says it ship confirms the **quick-ship eligible** lines for an org **enabled for quick ship**. For normal ship confirm use the pick release rule's Ship Confirm Rule + Create Shipments, or the `shipmentTransactionRequests` flow.
- `pickWaves` POST: `ReleaseStatusCode` is `nullable:false`; example body in doc is illustrative (value "Y" not documented).
- Pick release batch size < 1000 can create more shipments than expected.
- Pick slip grouping rule is in Inventory Management, not Shipping: easy to miss.
- No stock / no reservation -> lines backordered at release. Check `ShipmentLinesBackordered` in the pick wave response.
- Running several Schedule Pick Wave instances in parallel (doc recommends one at a time).

## Channel & exact technique
- Preferred channel for transactions: **A (REST)**. Master/setup rules: A for release rules and read of shipping parameters; B/D for the rest (no REST found for sequence rules, ship confirm rules, pick slip grouping rules, document job sets).
- A (REST), base `/fscmRestApi/resources/11.13.18.05/`. Always `rest_describe` first.
  - `shippingParameters` GET only seen (finder `PrimaryKey;OrganizationId`; `q=OrganizationCode='M1'`; pass `fields`, else only links). Write support UNVERIFIED (only `LPNControl` not read-only).
  - `releaseRules`: GET all / POST (create) documented. Other methods UNVERIFIED. Child: `DFF`.
  - `pickWaves`: GET all, POST create, GET one `/{BatchId}`, PATCH `/{BatchId}` = release. Child `DFF`. Create: `ReleaseRule`/`ReleaseRuleId` (use a rule), `ShipFromOrganizationCode`/`Id`, `ReleaseMode` (`ONLINE` immediate | `CONCURRENT` scheduled), `PickReleaseFlag`, `ReleaseStatusCode` (req), optional overrides (`CreateShipmentsFlag`, `AutoPickConfirmFlag`, `AutoShipOnPickConfirmFlag`, `PickFromSubinventory`, `StagingSubinventory`, `ShipmentCreationCriteriaCode`...). Response counters: `ShipmentLinesReleased/Picks/PickSlips/Backordered/Staged/Shipped...`, `ReturnStatus`, `ReturnMessage`. Release existing wave: PATCH with `PickReleaseFlag`, `ReleaseMode`, `ReleaseLocatorId`, `ResendFlag`, `SubmitOutboundShipmentRequestFlag`.
  - Eligible orders LOV: `pickReleaseEligibleOrdersLOV` (GET). Other LOVs: `shipmentSetsLOV`, `shippingCustomersLOV`, `shippingShipMethodsLOV`, `shippingPackingUnitsLOV`, `shippingPickSlipGroupingRulesLOV`, `shippingProjectsLOV`, `transportationShipmentsLOV`.
  - `shipmentLines` GET: finders `PrimaryKey;ShipmentLine`, `findByShipment;bindOrganizationId,bindShipmentName`, `findByNoDemandReservation`, `findByShipmentAttributes`. Query attrs: `ShipmentLine`, `Shipment`, `PickWave`, `PickWaveId`, `LineStatus(Code)`, `SourceOrder`, `Order`, `OrganizationId/Code`, `RequestedQuantity`, `PickedQuantity`, `ShippedQuantity`. Children: `attachments`, `costs`, `inventoryStripingDFF`, `lineDFF`, `lotAttributeDFF`, `lotStandardDFF`, `notes`.
  - `shipmentLineChangeRequests` (POST only; media `application/vnd.oracle.adf.action+json`, body `{"details":[{"ShipmentLine":"..."}]}`): actions `/action/pickRelease`, `assign`, `unassign`, `autoCreate` (create shipments), `autoPack`, `pack`, `unpack`, `stage`, `confirm` (quick-ship ship confirm), `backorderLine`, `backorderAll`, `backorderLineFromLPN`, `split`, `splitToMultipleLines`, `generateShipmentRequest` (body `pickBatchName`), `checkTradeCompliance`, `changeTransportationPlan`, `loadAssignments`, `rePackLPN`, `resetIntegrationStatus`, `resetQuickshipStatus`, `resetWeightVolume`, `submitForApproval`, `cycleCount`, `cycleCountAll`, `cycleCountLineFromLPN`. Base POST (`ActionCode=UpdateAttributes`, `shipmentLines[]` with `ShipmentLine`, `ShippedQuantity`, `Subinventory`, `Locator`, `Lot`, `TrackingNumber`, `serials[]`...) updates attributes.
  - `pickTransactions` POST = **pick confirm**: required `TransactionHeaderId`; `pickLines[]` required `PickSlip`, `PickSlipLine`; `PickedQuantity`, `SubinventoryCode`, `LocatorId`, lots in `lotItemLots`/`lotSerialItemLots`, serials in `serialItemSerials`; `RollbackAllLinesOnError` default `Y`; `OverpickAndMoveFlag`. Also `interfacedPickTransactions` (create/delete) and `openPickLines` / `inventoryPickLines` (GET) to find pick slip lines.
  - `shipmentTransactionRequests` (external WMS/3PL ship confirm): POST body `ActionCode` in `CreateAndConfirmShipment` | `ShipmentCreate` | `ShipmentUpdate`; `shipments[]` (`PlannedFlag` required in schema; `Shipment`, `ShipFromOrganizationCode`, `Carrier`, `ModeOfTransportCode`, `ServiceLevelCode`, weights/volumes) -> `outerPackingUnits[]` -> `innerPackingUnits[]` -> `packedLines[]` (`ShipmentLine`, `ShippedQuantity`, `ShippedQuantityUOM`, `lots[]`), or `unpackedLines[]` (`ShipmentLine`, `Subinventory`, `Locator`, `ShippedQuantity`). Response `TransactionId`, `TransactionStatusCode` `AP`. Then run ESS **Perform Shipping Transactions**, GET by `finder=findByAttributes;Shipment=...` (`expand=all` shows `errors`).
- B (FSM CSV): TaskCode lookup via `fsm_find_task` on names above; CSV support UNVERIFIED.
- C (FBDI/ESS):
  - **Perform Shipping Transaction Import**: template `PerformShippingTransactionImportTemplate.xlsm`, UCM account `scm/performShippingTransaction/import`, object owner Shipment, interface tables `WSH_NEW_DEL_INTERFACE`, `WSH_DEL_DETAILS_INTERFACE`, `WSH_FREIGHT_COSTS_INTERFACE`, `INV_LPN_INTERFACE`, `INV_TRANSACTION_LOTS_INTERFACE`, `INV_SERIAL_NUMBERS_INTERFACE`; control files `WshNewDelInterface.ctl`, `InvLpnInterface.ctl`, `WshShipmentLineInterface.ctl`, `InvTransactionLotsInterface.ctl`, `InvSerialNumbersInterface.ctl`, `WshFreightCostsInterface.ctl`. CSV names inside the zip not stated (convention = control file base name): UNVERIFIED. Process: Load Interface File for Import, then **Perform Shipping Transactions** (param `Shipment`, optional; privilege `WSH_PERFORM_SHIPMENT_TRANSACION_PRIV`; only lines Ready to Release / Backordered).
  - **Shipment Request Import** template exists (`shipmentrequestimport-3275.html`): details UNVERIFIED.
  - ESS **Schedule Pick Wave** (param **Release Rule** required; Pick Wave Prefix, Actual Ship Date, Number of Child Processes optional; privilege `WSH_SCHEDULE_PICK_WAVE_PRIV`). Detailed log profile `ORA_WSH_PICK_RELEASE_ESS_DETAIL_LOGGING`=Y. The Create Pick Wave UI and the `pickWaves` REST resource are the interactive equivalents. Names "Release Sales Orders for Picking" / "Interface Trip Stop" are legacy and were NOT found in 26D docs.
  - Other shipping ESS seen in doc index (25x/26A, details UNVERIFIED): Generate Shipment Request, Create Shipments, Close Shipments, Manage Shipment Interface, Purge Shipping Interface, Send Shipment Advice, Send Manifest Request, Receive Shipment Request, Apply Document Job Set Rules and Output Preferences (runs automatically at pick release / ship confirm), Process Staged Pick Transactions (only after a pickTransactions timeout).
- D (UI): Shipping work area: Pick Wave (Create Pick Wave / Release), Pick Slips, Shipments / Ship Confirm. No playbook yet.

## Roles
- Shipping Manager (job role): inherits duties Pick Waves Management, Shipment Management, Shipping Administration, Shipping Agent, Create Pick Wave Using Responsive Shipping, Ship Goods Using Responsive Shipping, Upload data for Shipping Transaction Import, Upload data for Shipment Request Import. Code `ORA_WSH_SHIPPING_MANAGER_JOB` is in `access-and-roles.md` but not shown on the 26D role page: UNVERIFIED.
- Shipping Agent (job role): Shipment Processing, Ship Goods Using Responsive Shipping. Code not on page: UNVERIFIED.

## How to verify
- `GET pickWaves/{BatchId}` counters; `GET shipmentLines?q=PickWaveId=<id>&fields=ShipmentLine,Item,LineStatus,PickedQuantity,ShippedQuantity`.
- Line status moves Ready to Release -> Released to Warehouse -> Staged -> Shipped (status names UNVERIFIED for 26D).
- Scheduled Processes log/output for Schedule Pick Wave / Perform Shipping Transactions.
- Sales order line status "Shipped" in Order Management.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/set-up-shipping.html — task list and order
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/considerations-for-managing-shipping-parameters.html — shipping parameters
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/pick-wave-release-rules.html and .../considerations-for-pick-wave-release-rules.html — release rules
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/pick-slip-grouping-rules.html — pick slip grouping, functional area
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/how-you-set-up-shipping-document-job-sets.html — job sets
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-shippingparameters-get.html — shippingParameters
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-releaserules-post.html — releaseRules
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-pickwaves-post.html and op-pickwaves-batchid-patch.html — pickWaves
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/api-inventory-management-pick-waves.html — pickWaves endpoints
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/api-inventory-management-shipment-line-change-requests.html — action list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-shipmentlinechangerequests-action-pickrelease-post.html, ...-action-confirm-post.html, op-shipmentlinechangerequests-post.html — action bodies
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-shipmentlines-get.html — shipmentLines
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-picktransactions-post.html — pick confirm
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-shipmenttransactionrequests-post.html and use_case_integrate_shipment_request_shipment_confirmation_processes_external_systems.html — shipment transaction flow
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — LOV resources, inventoryPickLines
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faspc/schedule-pick-wave.html and perform-shipping-transactions.html — ESS
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/performshippingtransactionimport-3274.html — FBDI
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fammm/Shipping_Agent_job_roles.html; https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fammm/Shipping_Manager_job_roles.html — roles

## UNVERIFIED
- 26D content of Manage Release Sequence Rules and Manage Ship Confirm Rules pages (only Redwood readiness notes / task names seen; fields not read).
- Fields of the pick slip grouping rule (criteria list), release sequence rule criteria.
- TaskCodes and Setup Task CSV support for all shipping tasks.
- REST write support for `shippingParameters` and methods beyond POST/GET on `releaseRules`.
- Mapping of UI Shipping Parameter fields (Appending Limit, Pick Release Batch Size, etc.) to REST attributes.
- CSV file names inside the Perform Shipping Transaction Import zip; Shipment Request Import details.
- Role codes `ORA_WSH_SHIPPING_MANAGER_JOB`, Shipping Agent code.
- Accepted values of `ReleaseStatusCode` for `pickWaves` (lookup `WSH_BACKORDERS_FLAG`).
- Exact ESS job path/package for Schedule Pick Wave and Perform Shipping Transactions (only display names confirmed).
- "Release Sales Orders for Picking" and "Interface Trip Stop" as 26D processes: not found.
