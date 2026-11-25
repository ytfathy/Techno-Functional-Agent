# Inventory Transactions (misc, transfers, cycle count, physical inventory, min-max, ABC)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL

## Business purpose
Moves and adjusts stock: miscellaneous issue/receipt, subinventory transfer, interorganization transfer, account alias issue/receipt, cycle counts, physical inventory, min-max replenishment, ABC classification (drives cycle count frequency). Each transaction updates on-hand, then is costed and accounted by Cost Accounting (`cost-management.md`). Affects warehouse, finance, planners.

## Where in Fusion (FSM)
- Offering: **Manufacturing and Supply Chain Materials Management**. Functional area: **Inventory Management** (select All Tasks).
- Setup tasks (26D overview page): **Manage Subinventories and Locators**, **Manage Interorganization Parameters**, **Manage Account Aliases**, **Manage Transaction Source Types**, **Manage Transaction Reasons**, **Manage Item Transaction Defaults**, **Manage Material Statuses**, **Manage Intersubinventory Parameters**, **Manage ABC Classes**, **Manage ABC Classification Sets**, **Manage ABC Assignment Groups**, **Manage Inventory Profile Options**, **Manage Inventory Lookups**, **Manage Inventory Account Alias Key Flexfield** (must be defined for inventory to operate), **Manage Inventory Locator Key Flexfield** (must be defined).
- Transaction types: defined on the "Manage Inventory Transaction Sources and Types" page (26C guide). The exact task title is UNVERIFIED (26D overview lists only Manage Transaction Source Types).
- Cycle count definitions, physical inventory, min-max: **no setup task in the 26D list**. They are done in the Inventory Management work area (UI) and via REST.
- Daily work: Inventory Management work area: Manage Pending Transactions (errors in the interface), Review Count Interface Records.

## Prerequisites & dependencies
Chain, in order:
1. Items enabled for the org (`items-item-classes.md`, `item-organizations.md`) with transactable, stockable flags (names UNVERIFIED).
2. Inventory org + parameters (`inventory-organizations.md`), subinventories + locators (`subinventories-locators.md`), UOMs (`uoms.md`).
3. Inventory Account Alias and Locator key flexfields defined.
4. Cost Accounting: cost org, cost book, relationship, cost profile (`cost-management.md`). Without it the transaction completes in Inventory but is not costed or accounted.
5. Transaction reasons, account aliases, interorg parameters + shipping network (`shipping-networks.md`) for interorg transfers; ASL/sourcing for min-max buy items.
6. Open inventory accounting period for the org (UNVERIFIED).
7. Then: transactions -> Manage Inventory Transactions process -> Transfer Transactions from Inventory to Costing -> Create Cost Accounting Distributions -> Create Accounting.
- Depends on this: transfer orders (`transfer-orders.md`), receipts, costing, planning.

## Key fields
Staged transaction (`inventoryStagedTransactions`):
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Source code | `SourceCode` (req, max 30) | origin tag | free text, e.g. `INV` |
| Source header / line | `SourceHeaderId`, `SourceLineId` (req, int64) | external refs | |
| Transaction date | `TransactionDate` (req) | | must be in open period (UNVERIFIED) |
| Transaction mode | `TransactionMode` (req, max 30) | | allowed values UNVERIFIED (doc example "3") |
| Quantity | `TransactionQuantity` (req) | sign by type | |
| Use current cost | `UseCurrentCostFlag` (req, boolean) | | no default, must send |
| Organization | `OrganizationName` / `OrganizationId` (max 255) | | resolved to Id in response |
| Item | `ItemNumber` / `InventoryItemId` | | |
| Subinventory / Locator | `SubinventoryCode` (max 10) / `LocatorName` or `LocatorId` | | send ids for locators (key flexfield) |
| Transfer to | `TransferSubinventory`, `TransferLocatorName`/`TransferLocator`, `TransferOrganizationName`/`TransferOrganization` | | transfers |
| Transaction type | `TransactionTypeName` / `TransactionTypeId`, `TransactionActionName`, `TransactionSourceTypeName`, `TransactionSourceName` / `TransactionSourceId` | | e.g. "Miscellaneous Receipt" |
| UOM | `TransactionUnitOfMeasure` (max 25) / `TransactionUOM` (max 3) | | |
| Reason | `ReasonName` / `ReasonId` | | |
| Account | `AccountCombination`, `AccountAliasCombination`, `DistributionAccountId` | | misc/account alias |
| Status | `ProcessStatus` (default "1"), `ErrorCode`, `ErrorExplanation`, `LockStatus` | | read after processing |
| Grouping | `TransactionHeaderId`, `TransactionBatchId`, `TransactionGroupId`, `TransactionInterfaceId` (PK) | | `processByHeader` uses header id |
- Children: `attachments`, `costs`, `dFFs`, `trackingAttributesDFF`, `transferTrackingAttributesDFF`, `projectCostingDFFs`, `lots`, `LotSummaries`, `serials`, `SerialSummaries` (Lot Serials, Lots, Tracking Attributes also listed as sub-pages).

## Common mistakes
- Posting `inventoryStagedTransactions` and expecting stock to change: it only stages. Run **processByHeader** (or the Manage Inventory Transactions process).
- Omitting `UseCurrentCostFlag`, `SourceCode`, `SourceHeaderId`, `SourceLineId`, `TransactionMode`: required by the schema (the use-case page example omits them, so maybe defaulted server side on the name-based flow: UNVERIFIED, always `rest_describe`).
- Sending `LocatorName` (key flexfield) instead of `LocatorId`.
- Misc issue for qty > on-hand where negative balances are not allowed.
- Lot/serial item without `lots`/`serials` children (or `lotItemLots`/`serialItemSerials` on `inventoryTransactions`).
- Interorg transfer without interorg parameters / shipping network.
- Running Manage Inventory Transactions concurrently (only one instance), or loading > 100K rows in one FBDI file.
- Forgetting costing: transaction shows in `inventoryCompletedTransactions` but has no accounting. Check cost org relationship.
- Leaving > 1,000 error rows in the interface: purge with Purge Inventory Transactions Interface.

## Channel & exact technique
- Preferred channel: **A (REST)** for single/small transactions and reads, **C (FBDI)** for bulk (> ~100 rows), **D (UI)** for cycle count review, physical inventory tag entry, account alias / reason / type setup (no REST write found).
- A (REST), base `/fscmRestApi/resources/11.13.18.05/`:
  - **`inventoryTransactions`** POST (synchronous, processes immediately). Body `{"transactionLines":[{...}]}`. Required: `TransactionDate`, `TransactionQuantity`. Line attrs: `InventoryItemId`, `Item`, `Revision`, `OrganizationId`, `OrganizationName`, `Subinventory`, `Locator`, `LocatorId`, `TransferSubinventory`, `TransferLocator`, `TransferLocatorName`, `TransferOrganizationId`, `TransferOrganizationName`, `TransactionTypeId`, `TransactionType`, `TransactionTypeName`, `TransactionAction`, `TransactionActionId`, `TransactionSourceId`, `TransactionSourceName`, `TransactionSourceTypeId`, `TransactionSourceTypeName`, `SourceHeaderId`/`SourceLineId` (default -999), `PrimaryQuantity`, `TransactionUnitOfMeasure`, `TransactionUOM`, `SecondaryTransactionQuantity`, `ReasonId`, `ReasonName`, `ShipmentNumber`, `VendorName`, `VendorNumber`, `OwningOrganizationId`, `OwningTpType`. Children: `lotItemLots` (LotNumber req + TransactionQuantity), `lotSerialItemLots` (+ nested `lotSerialItemSerials`), `serialItemSerials` (`FromSerialNumber` req), `transactionLinesDFF`, plus lot/serial DFF children. Response top-level: `ReturnStatus`, `ErrorCode`, `ErrorExplanation`, `ErrorUniqueTransactionId`. Doc examples: Miscellaneous receipt (`TransactionTypeName: "Miscellaneous receipt"`, `TransactionSourceTypeName: "Inventory"`, `ReasonName`) and Subinventory Transfer (`Subinventory` source, `TransferSubinventory` target, `TransactionTypeName: "Subinventory Transfer"`). Interorg: add `TransferOrganizationId|Name`. Method set beyond POST: UNVERIFIED.
  - **`inventoryStagedTransactions`** (staged then processed): POST create; GET collection; GET/PATCH/DELETE `/{TransactionInterfaceId}`; actions (header `Content-Type: application/vnd.oracle.adf.action+json`): `POST .../action/processByHeader` (body: `headerId`, `processType`, `transactionTypeId`, `transactionTypeName`, `transactionActionId`, `transactionSourceTypeId`, `transactionSourceName`, `transactionDate`, `reasonId`, `reasonName`, `lotGrade`, `distributionAccountId`, `dispositionId` (account alias id), `eresEnabled`, `transferOrganizationId|Name`, `transferSubinventory`, `transferLocatorId|Name`, `transferLpnId`, `toProjectId`, `toTaskId`, `carrierId`, `shipmentNumber`, `trackingNumber`, `expectedArrivalDate`, `noOfPackingUnits`; additionalProperties false; returns `{"result": "..."}`), `POST .../action/deleteByHeader`, `POST .../action/performBulkAction` (filters: `action`, `transactionHeaderId`, `transactionTypeId`, `organizationId`, `inventoryItemId`, `subinventoryCode`, `locatorId`, `transactionFromDate`, `transactionToDate`, `processFlag`, `status`, `transactionStatus`, `errorCode`, `loadRequestId`, `transactionIdList` = EXCLUDE list, ...; `action` allowed values UNVERIFIED; empty body matches ALL staged rows, so always filter), `POST .../action/generateTxnMultipleLots`. `Upsert-Mode: true` header supported. The documented REST flow (use case "Manage Inventory Transactions from External Applications") stages via POST (batch `parts` array with `operation: create` supported), then the **Manage Inventory Transactions** scheduled process picks them up.
  - **`inventoryCompletedTransactions`** GET (read-only). Finders `PrimaryKey;TransactionId=`, `findByPJCProjectTask`. Attrs: `TransactionId`, `TransactionType`, `TransactionAction`, `TransactionDate`, `Item`, `InventoryItemId`, `Organization`, `OrganizationId`, `SubinventoryCode`, `Locator`, `Quantity`, `TransactionQuantity`, `TransactionUOM`, `TransferOrganization`, `TransferSubinventory`, `PurchaseOrder`, `Lot`, `SerialNumber`, child `lots`, `serials`. Use `q=Organization='M1';TransactionDate>='2026-01-01'`.
  - **`inventoryTransactionTypes`** GET (read-only). Attrs `TransactionTypeId`, `TransactionTypeName`, `TransactionActionId`, `TransactionAction`, `TransactionSourceTypeId`, `TransactionSourceTypeName`, `TransactionTypeDefinedByCode` (N system, Y user). Finders `PrimaryKey;TransactionTypeId=`, `findByNameOrDescription;bindTransactionTypeName=,bindTransactionTypeDescription=`. Doc examples: id 1 Account Issue, 15 RMA Receipt, 18 Purchase Order Receipt, 61 Transfer Order Interorganization Receipt, 267 "Issue from Inventory" (user-defined, Account Alias source type 6). Look up real ids on the pod.
  - **`onhandQuantityDetails`** GET (read-only). Finder `PrimaryKey;InventoryItemId=,OrganizationId=,SubinventoryCode=,LocatorId=,LotNumber=,SerialNumber=`. Attrs `ItemNumber`, `OrganizationCode`, `SubinventoryCode`, `LocatorId`, `LotNumber`, `OnhandQuantity`, `ReceivingQuantity`, `ReservedQuantity`, `InboundQuantity`, `ConsignedQuantity`, `PrimaryUOMCode`; children `ConsignedQuantityDetails`, `InboundQuantityDetails` (use `expand`). Also `availableQuantityDetails` exists (not researched).
  - **`inventoryAccountAliases`** GET only (list, by uniq id). Creating aliases: UI (Manage Account Aliases).
  - **`cycleCountDefinitions`** POST: required `CycleCountName` (30), `OrganizationName`, `StartDateTime`, `StartingCountSequence`, `MaximumDaysBeforeLate`, `ApprovalRequiredCode`, `AutomaticallyScheduleCode`, `SerializedItemsAllowedCode` (lookup `INV_YES_NO_NUMERIC`), `SerialCountOption` (`INV_CC_SERIAL_COUNT_OPTIONS`), `SerialNumberAdjustment` (`INV_CC_SERIAL_ADJ_OPTIONS`), `WorkdaySchedule`, `WorkdayScheduleCode`. Other attrs seen: `CountByCategoryFlag`, `LocationBasedCountFlag`. Children: `countCategories`, `countCategoryItems`, `countClasses` (`AbcClassId`, `CountsPerYear`), `countItems` (`InventoryItemId`, `AbcClassId`, `AbcClass`, `IncludeInSchedule`), `countLocators`, `countSubinventories`, `DFF`. Related: `cycleCountSchedules`, `cycleCountSequenceDetails` (not researched).
  - **`cycleCountTransactions`** POST: submits counts. Body `{"countLines":[{CountName, CountSequence, CountQuantity, CountUnitOfMeasure, CountDate, CountedByEmployeeName, Item, OrganizationCode, Subinventory, LocatorName|LocatorId, Lot, SerialNumber, Revision, Reason, Comments}]}`. If no open `CountSequence` it is an unscheduled count. An adjustment transaction is created when needed. Required list not documented (UNVERIFIED). Response `ReturnStatus`, `ErrorCode`, `ErrorExplanation`, `ErrorUniqueTransactionId`.
  - **`physicalInventories`** POST/GET/DELETE (PATCH UNVERIFIED): required `PhysicalInventoryName` (30), `OrganizationId`, `AllowDynamicTagsCode` (1 permitted, 2 not), `ApprovalRequiredCode` (`INV_REQ_APPROVALS`), `TagTypeCode` (`INV_GENERATE_TAG_TYPE`). Optional: `AllowAllSubinventoriesCode` (default 1), `ExcludeZeroBalance`, `ExcludeNegativeBalance`, `FreezeDate`, `PhysicalInventoryDate`, tolerances (`ApprovalTolerancePositive/Negative`, `CostVariancePositive/Negative`), `NextTagNumber`, `NumberBlankTags`, seven `...TagGenerationSequence`. Children `physicalInventorySubinventories` (`Subinventory`), `physicalInventoryDFFs`. Action `copyPhysicalInventory` likely (UNVERIFIED). Taking the snapshot, tag counts, adjustments: UI (resource/action for it not found).
  - **`subinventoryItems`** POST (min-max at item-subinventory): required `OrganizationId`, `SecondaryInventory` (max 10); `InventoryItemId`; min-max: `MinimumMaximumPlanningCode` (lookup `INV_MATERIAL_PLANNING`, default 6; meaning of codes UNVERIFIED), `MinimumMinmaxQuantity`, `MaximumMinmaxQuantity`, `MinmaxQuantityUOM`, `MinimumOrderQuantity`, `MaximumOrderQuantity`. Children `GTINs`, `MPNs`, `onhandQuantity`, `subinventoryItemsDFF`. Org-level min-max is an item attribute (Inventory Planning Method) in Manage Items.
  - **ABC**: `abcClasses`, `abcClassifications`, `abcAssignmentGroups` (also in endpoint index). `abcClassifications` POST required `CompileName` (40), `CompileTypeCode` (`INV_ABC_COMPILE_TYPE`), `OrganizationId`, `ValuationScopeCode`; children `abcClassificationSetItems`, `DFF`. `abcAssignmentGroups` POST required `AssignmentGroupName` (40), `OrganizationId`; `ValuationScopeCode` 1 = org-wide, 2 = subinventory; children `abcAssignmentGroupClasses` (`AbcClassId`, `SequenceNumber`, `PercentOfItems`, `PercentOfValue`), `abcAssignmentGroupItems`, `abcAssignmentGroupAttachments`, `DFF`. `abcClasses` attributes not researched.
- B (FSM CSV): TaskCodes not looked up. Use `fsm_find_task` for Manage Account Aliases, Manage Transaction Reasons, Manage ABC Classes, Manage Transaction Source Types. CSV support: UNVERIFIED.
- C (FBDI/ESS):
  - **Inventory Transaction Import**: template `InventoryTransactionImportTemplate.xlsm`; control files `InvTransactionsInterface.ctl`, `InvTransactionLotsInterface.ctl`, `InvSerialNumbersInterface.ctl`, `CstTransCostInterface.ctl`; interface tables `INV_TRANSACTIONS_INTERFACE`, `INV_TRANSACTION_LOTS_INTERFACE`, `INV_SERIAL_NUMBERS_INTERFACE`, `CST_I_INCOMING_TXN_COSTS`; UCM account `scm/inventoryTransaction/import`; scheduled process on the FBDI page: **Create Inventory Transactions** (26D, Using Inventory docs say: after the import, submit **Manage Inventory Transactions**). Also usable for first-time on-hand balance with cost details.
  - **Create Inventory Transactions** (ESS): single required param `Transaction Header ID` (from Manage Pending Transactions). Reprocesses pending/stuck headers. Privilege `INV_CREATE_INVENTORY_TRANSACTION_PROCESS_PRIV`. One instance at a time.
  - **Manage Inventory Transactions** (ESS): no parameters. Reads `INV_TRANSACTIONS_INTERFACE`, `INV_TRANSACTION_LOTS_INTERFACE`, `INV_SERIAL_NUMBERS_INTERFACE`. Schedule every 30-60 min. One instance at a time. Do not exceed 100K rows per FBDI file. Tuning profile option: Inventory Transaction Manager Worker Size. Run **Transfer Transactions from Inventory to Costing** afterwards.
  - Zip CSV names inside the zip, ESS job path (e.g. `/oracle/apps/ess/scm/inventory/...`) and the `Load Interface File for Import` parameters: UNVERIFIED. Use the repo `fbdi_*` tools and `knowledge/channel-c-fbdi-ess.md`.
  - Other Inventory FBDI templates (26D FBDI-for-Inventory page): `InventoryBalanceImportTemplate.xlsm` (UCM `scm/inventoryBalanceMessage/import`, ctl `InvOnHandBalInterface.ctl`, `InvOnHandBalLotInterface.ctl`, `InvOnHandBalSerialInterface.ctl`, tables `INV_BALANCE_TXNS_INT`, `INV_BALANCE_TXNS_LOT_INT`, `INV_BALANCE_TXNS_SERIAL_INT`, process **Manage Inventory Balances Process**; this is the 3PL/WMS balance sync, NOT the opening balance load), `InventoryReservationImportTemplate.xlsm`, `ReceivingReceiptImportTemplate.xlsm`, `PerformShippingTransactionImportTemplate.xlsm`, `InterfacedPickTransactionsImportTemplate.xlsm`.
  - ESS for the other areas: **Perform ABC Assignments and Synchronize Cycle Counts** (params Organization req, Assignment Group Name req, Synchronize Cycle Counts Yes/No default No; privilege `INV_PERFORM_ABC_ASSIGNMENT`; resubmit the ABC classification set first to include new items). **Create ABC Classification Set** (26C). **Generate Count Schedules** then **Generate Count Sequences** (26C, names only; parameters UNVERIFIED). **Print Cycle Count Listing Report**. **Import Count Sequences** (cycle count error reprocessing). **Min-Max Planning** report (parameter 1 = planning level organization or subinventory; Restock param generates requests; 26C Using Inventory page). **Calculate Min-Max Planning Policy Parameters** (20B/21B pages only). **Process Supply Chain Orchestration Interface** (creates the requisitions/transfer orders/work orders from min-max requests). **Purge Inventory Transactions Interface** (run in review mode first; parameter codes conflicting across releases, check on pod).
  - Min-max results by source type (subinventory level): same org -> intraorg transfer order; other org -> interorg transfer order; subinventory -> movement request; supplier -> purchase requisition.
- D (UI): `playbooks/` none yet. Use for: Manage Account Aliases, transaction reasons, transaction types, cycle count adjustment approval, physical inventory snapshot/tag entry/adjustment, Manage Pending Transactions.

## How to verify
- `GET inventoryStagedTransactions/{TransactionInterfaceId}?fields=ProcessStatus,ErrorCode,ErrorExplanation` after processing (status value meanings: UNVERIFIED; interface table docs say flag 1 = ready, 3 = error).
- `GET inventoryCompletedTransactions?q=Organization='<code>';Item='<item>'&orderBy=TransactionDate:desc&fields=TransactionId,TransactionType,Item,Quantity,SubinventoryCode,TransactionDate&limit=5`.
- `GET onhandQuantityDetails?q=OrganizationCode='<code>';ItemNumber='<item>'&fields=SubinventoryCode,OnhandQuantity`.
- Errors: UI Manage Pending Transactions (edit and resubmit, max 500 rows at a time); Scheduled Processes log.
- Costing: `itemCosts?finder=findItemCosts;bindItem=<item>` and Cost Accounting > Review Cost Accounting Distributions.
- Test: misc receipt of 1 unit to a subinventory, process, confirm on-hand + completed transaction + cost distribution.

## Role needed
- Inventory transaction roles (Inventory Manager / Inventory Transactions...): codes UNVERIFIED (not researched).
- Privileges seen: `INV_CREATE_INVENTORY_TRANSACTION_PROCESS_PRIV` (Create Inventory Transactions), `INV_PERFORM_ABC_ASSIGNMENT` (ABC process).
- Cost side: `ORA_CST_COST_ACCOUNTANT_JOB` (see `cost-management.md`).

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/api-inventory-management-inventory-staged-transactions.html — endpoint list, actions, child resources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventorystagedtransactions-post.html — required attrs, attribute list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventorystagedtransactions-action-processbyheader-post.html — processByHeader body
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventorystagedtransactions-action-performbulkaction-post.html — performBulkAction body
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/use_case_integrate_inventory_transaction_processes_for_external_systems.html — staged flow, misc receipt payload
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventorytransactions-post.html — inventoryTransactions body, examples
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventorycompletedtransactions-get.html — completed transactions
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventorytransactiontypes-get.html — transaction types
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-onhandquantitydetails-get.html — on-hand
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-cyclecountdefinitions-post.html — cycle count definitions
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-cyclecounttransactions-post.html — cycle count transactions
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-physicalinventories-post.html — physical inventories
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-subinventoryitems-post.html — min-max attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-abcclassifications-post.html — ABC classifications
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-abcassignmentgroups-post.html — ABC assignment groups
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fasrp/api-inventory-management-list-values-inventory-management-inventory-account-aliases.html — account alias REST (26B, GET only)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — endpoint index (first 100k chars)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faips/inv-file-based-data-import-fbdi.html — FBDI objects for Inventory
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/inventorytransactionimport-3189.html — FBDI UCM, ctl, tables
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/inventorybalancemessageimport-3187.html — balance import
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faspc/manage-inventory-transactions.html — Manage Inventory Transactions process
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faspc/create-inventory-transactions.html — Create Inventory Transactions process
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faspc/perform-abc-assignments-and-synchronize-cycle-counts.html — ABC ESS process
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/overview-of-implementing-inventory-management.html — setup task names
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/famml/min-max-planning.html — min-max logic (26C)
- Search-result summaries only, pages not opened: 26B Using Inventory Management (Manage Pending Transactions rules), 26C Scheduled Processes for SCM (Generate Count Schedules/Sequences, Create ABC Classification Set).

## UNVERIFIED
- 26D FSM TaskCodes and CSV support for all Inventory setup tasks.
- Manage Inventory Transaction Sources and Types task title in 26D.
- Allowed values: `TransactionMode`, `performBulkAction.action`, `processByHeader.processType`, `ProcessStatus`.
- Whether the name-based staged payload (use case page) needs `SourceCode`, `UseCurrentCostFlag` etc. in practice.
- Methods beyond POST on `inventoryTransactions`; PATCH on `physicalInventories`; `copyPhysicalInventory` action.
- REST for: account alias create, transaction reason, physical inventory snapshot/count/adjust, min-max calculate, cycle count schedule generation.
- `MinimumMaximumPlanningCode` code meanings (lookup `INV_MATERIAL_PLANNING`).
- ESS job paths, `Load Interface File for Import` parameters, CSV zip names for FBDI; whether FBDI process name is Create Inventory Transactions or Manage Inventory Transactions in 26D.
- Process names/parameters: Generate Count Schedules, Generate Count Sequences, Create ABC Classification Set, Import Count Sequences, Purge Inventory Transactions Interface, Calculate Min-Max Planning Policy Parameters, Print/Min-Max Planning report title in 26D.
- Inventory role codes; open-period requirement; item flags required for transactions.
- Interorg transfer via REST in-transit flow (shipment, receipt) not researched; see `transfer-orders.md`.
