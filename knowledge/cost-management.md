# Cost Management (Cost Accounting setup for inventory transactions)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL

## Business purpose
Cost Accounting costs inventory transactions and creates the accounting distributions that go to GL through Subledger Accounting. An inventory org transaction is **not costed or accounted** until the org is tied to an active cost organization with a cost book, and every item has a cost profile. Affects: finance (inventory valuation, COGS), inventory (transactions stay "pending costing" otherwise), period close. Skipping this setup is the usual reason inventory transactions are not accounted.

## Where in Fusion (FSM)
- Offering: **Manufacturing and Supply Chain Materials Management**. Functional area: **Cost Accounting**.
- Task names (26D docs):
  - **Manage Cost Organizations** (create new, or mark an existing inventory org as a cost org)
  - **Manage Cost Books**
  - **Manage Cost Organization Relationships** (title of page: Manage Accounting Cost Organization Relationships)
  - **Manage Valuation Structures**
  - **Manage Valuation Units**
  - **Manage Cost Profiles**
  - **Manage Default Cost Profiles**
  - **Manage Item Cost Profiles** (named in the itemCosts REST text, not found in the 26D setup pages: UNVERIFIED as a 26D task title)
  - **Manage Cost Elements** (and Analysis Groups), plus cost component groups and mapping tasks. Quick Setup creates them, details UNVERIFIED.
  - **Manage Cost Accounting Profile Options** (e.g. Set Default Cost Organization Context)
- Manage Cost Scenarios / Manage Standard Costs are in the **Cost Accounting work area** (not Setup and Maintenance).
- Scope prompts: Cost Organization / Cost Book / Set (reference data set) per task. Valuation structures and cost profiles are defined at **set level**.
- Quick Setup for the Cost Accounting area exists (26C/26B Getting Started guides: it auto-creates cost org, cost book, relationship, cost element, cost component, mapping, valuation structure, cost profile tasks). 26D Quick Setup text: UNVERIFIED.

## Prerequisites & dependencies
Chain, in order:
1. Legal entity + primary ledger + accounting calendar (see `legal-entities-ledgers.md`).
2. Profit center BU, set on the inventory org (each inventory org must map to a profit center BU to join a cost org). All inventory orgs in one cost org: same profit center BU, same legal entity (`business-units.md`).
3. Inventory orgs (`inventory-organizations.md`) and the item master / item validation org (`item-organizations.md`).
4. Cost elements, cost components, cost component group, mapping (Quick Setup or manual). Overhead cost elements are needed before standard cost import.
5. Valuation structure (set level) then cost book then cost org.
6. Cost Organization Relationship: cost org + item validation org + inventory orgs + cost books (primary cost book gets primary ledger).
7. Valuation unit (per cost org + cost book + valuation structure) when the profile structure is below org level (manual mode).
8. Cost profile(s) then Default Cost Profile (cost org/book or item category), New Item Profile Creation = Automatic (recommended).
9. Subledger Accounting / accounting rules for Cost Management (UNVERIFIED in this pass).
10. Open cost accounting period for the cost book (First Opened Period derived from the relationship Effective Start Date).
- Depends on this: all inventory transactions costing (`inventory-transactions.md`), receipt accounting, COGS, period close.
- An inventory org cannot belong to more than one cost org. A cost book tied to a cost org via the relationship cannot be deleted or deactivated (FAQ page title says so; the 26D page body was not read: UNVERIFIED).
- Periodic Average Cost on a cost book cannot be disabled once associated with a cost org.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Cost Organization Code / Name | `CostOrgId`, `CostOrganizationName` (REST LOV) | cost org | Must be Active for the cost processor |
| Legal Entity Name | UI only (no REST write) | owner LE | Cost org and item validation org same LE |
| Effective Start Date (cost org) | UI | default 01/01/0001 | |
| Cost Book name / Periodic Average Cost checkbox | UI | accounting framework | One primary cost book per cost org, tied to LE primary ledger |
| Item Validation Organization | UI | where items/attributes (Costing Enabled, Asset flag) are read | Use item master org |
| Inventory Organizations tab: Effective Start Date | UI | transactions dated earlier are NOT costed | Effective End Date defaults to 12/31/12 display = 4712 |
| Cost Books tab: Ledger, Currency, Accounting Calendar, First Opened Period, Maximum Open Periods, Conversion Rate Type, Create Accounting | UI | cost book association | Primary ledger: Create Accounting forced on. Max Open Periods: match GL open periods |
| Period End Validations | UI | per book, Action Error/Ignore | default Error |
| Valuation Structure Set / Type (Asset, Expense, Consigned) / Code / Mode (Auto, Manual, Both) / Flexfield Structure | UI | cost granularity | Consigned = Auto only. Standard and periodic average must use Cost Org or Inventory Org level |
| Valuation Unit: Cost Organization, Cost Book, Name, Valuation Structure Code, segment rows | `ValuationUnitId`, `ValuationUnit` (REST LOV) | cost bucket instance | |
| Cost Profile Set, Cost Profile, Cost Method (Standard, Actual, Perpetual average, Periodic average), Quantity Depletion Method (FIFO), Process Negative Quantity (Always / To zero / Never), Valuation Structure Code, Cost By (primary/secondary UOM), Cost Component Mapping Group | UI | item costing policy | Periodic average needs Process Negative Quantity = Always and a periodic-average cost book |
| Default Cost Profile: New Item Profile Creation (Automatic / Review Required), Cost Organization, Category Name | UI | auto-assignment | Automatic recommended, required for FBDI standard cost import |

## Common mistakes
- Inventory org Effective Start Date later than first transaction date: transactions are silently not costed.
- Inventory org not mapped to profit center BU: cannot be added to cost org.
- Cost org left Inactive: cost processor skips it.
- No default cost profile or "Review Required": new item profiles sit in Awaiting Approval and transactions are held.
- Changing a cost profile / item profile assignment after transactions are processed: locked (profile cannot be deleted or modified once it costed transactions).
- Using a transactional inventory org as item validation org instead of the item master org.
- Running Create Cost Accounting Distributions before the transfer processes: nothing to cost.
- Item with Costing Enabled / Asset flags off in the item validation org: item not costed (item attribute names UNVERIFIED).
- Cost org access: the user running Transfer Transactions from Inventory to Costing needs data access to the cost org or the process ends with Warning.

## Channel & exact technique
- Preferred channel: **D (UI) for setup, A (REST) for reads/transactions**, C (FBDI) for standard costs. Reason: no business REST resource found that creates cost orgs, cost books, valuation structures or cost profiles. FSM CSV (B) for these tasks: UNVERIFIED (look up TaskCodes with `fsm_find_task`, then test export).
- A (REST), all under `/fscmRestApi/resources/11.13.18.05/`:
  - `periodicAverageCostOrganizationsLOV` GET: attrs `CostOrgId`, `CostOrganizationName`. Finders `PrimaryKey;CostOrgId=`, `findPeriodicAverageCostOrganizations;bindCostOrgId=,bindCostOrgName=`. Only cost orgs of periodic average books (name says so). A generic `costOrganizations` resource was NOT found in 26D docs.
  - `periodicAverageCostBooksLOV` GET (name seen in the 25C endpoint index only: UNVERIFIED for 26D).
  - `valuationUnitsLOV` GET: attrs `CostBook`, `CostOrganizationName`, `ValStructureTypeCode`, `ValuationUnit`, `ValuationUnitId`. Finders `PrimaryKey;ValuationUnitId=`, `findValuationUnits;bindCostBook=,bindCostBookId=,bindCostOrgId=,bindCostOrgName=,bindValuationUnit=,bindValuationUnitId=`.
  - `itemCosts` GET only (docs limited to perpetual average items). Finders `PrimaryKey;CostBookId,CostMethod,CostOrganizationId,ItemId,TransactionId,ValuationUnitId`; `findItemCosts;bindItem|bindItemId|bindCostOrg|bindCostOrgId|bindCostBook|bindCostBookId|bindCostMethod|bindCostDate|bindCostProfile|bindCategoryName|bindEffectiveStartDate|bindEffectiveEndDate|bindReceiptNumber|bindTotalUnitCost|bindValStructureCode|bindValuationUnit` (needs one of cost org, cost book, item; item recommended); `findItemCostAdjustmentDetails` (needs cost org, cost book, item). Read attrs: `CostOrganizationId/Name/Code`, `CostBookId`, `CostBook`, `CostProfile(Id)`, `ItemId`, `ItemNumber`, `CostMethod(Code)`, `ValuationStructureCode`, `ValuationUnit(Id)`, `TotalUnitCost`, `CostAsOfDate`, `CurrencyCode`, `QuantityOnhand`, `EffectiveStartDate/EndDate`; child `costDetails` (`CostElement`, `CostElementType`, `UnitCostAverage`, `CostPercent`).
  - `standardCosts`: GET collection + GET/PATCH/DELETE by `StandardCostId` (PATCH and GET-one confirmed in 26A search results, DELETE link seen: UNVERIFIED for 26D). Finders `PrimaryKey;StandardCostId`, `PublishedStandardCostsByInvOrgAsOfDate;bindAsOfDate,bindInvOrgId`, `findByCostOrgCostBookValUnitId;Bind_CostBookId,Bind_CostOrgId,Bind_InventoryItemId,Bind_ScenarioId,Bind_StatusCode,Bind_ValUnitId`, `findByInventoryItemId`, `findByScenarioId`, `findByStatusCode`. q attrs: `ItemNumber`, `CostBookId`, `CostOrgId`, `InventoryItemId`, `InventoryOrgId`, `StatusCode` (e.g. PUBLISHED), `CostType` (STANDARD or BUY), `AssignmentLevel`, `ScenarioId`, `ValUnitId`, `EffectiveStartDate`, `EffectiveEndDate`, `TotalCost`. Children: `StandardCostDetails` (`CostElementCode`, `CostLevelCode`, `UnitCost`, `ExpensePoolCode`, `EnteredUnitCost`), `Attachments`. POST on standardCosts: UNVERIFIED (not seen).
  - `costScenarios` (v1) and `costScenariosV2` (planning scenarios; action `runScenarioProcessor` at `costScenariosV2/{ScenarioId}/action/runScenarioProcessor`; children `AttachmentsVA`, `ScenarioTimeline`, `WorkDefinitionCriteria`). `costScenarios` finder `findByCostOrgCostBook` (26B result). Write support and required attrs: UNVERIFIED, run `rest_describe`.
  - `costAdjustments` (child `AdjustmentDetail`), `costRollupGroups` (child `costRollupGroupDetails`), `costAccountingOverheadRules` (child `OverheadRuleDetails`): exist in the 26D endpoint index; attributes not researched: UNVERIFIED.
  - Cost accounting distributions REST resource: NOT found in 26D docs. Review via UI page "Review Cost Accounting Distributions" (UI name from cost profile doc) or OTBI. UNVERIFIED.
- B (FSM CSV): TaskCodes not looked up. Use `fsm_find_task` with the task names above. CSV support: UNVERIFIED.
- C (FBDI / ESS):
  - **Standard Costs**: template `StandardCostImportTemplate.xlsm`, tabs Standard Cost Headers + Standard Cost Details. Control files `CstStdCostHeadersInterface.ctl`, `CstStdCostDetailsInterface.ctl`. Interface tables `CST_INTERFACE_STD_COST_HEADERS`, `CST_INTERFACE_STD_COST_DETAILS`. UCM account `scm/standardCost/import`. Scheduled process named **Define Standard Costs** (FBDI page) / **Interface Standard Costs** (procedure page). Same thing or two names: UNVERIFIED. Parameters, ESS job path, CSV zip names: UNVERIFIED.
  - Procedure (26D): set Default Cost Profile with New Item Profile Creation = Automatic; create Valuation Unit (CSV needs Valuation Unit Code); set overhead cost elements (Manage Cost Elements); create cost scenario in Cost Accounting work area > Manage Cost Scenarios (CSV needs scenario number); fill template; Generate CSV; run Interface Standard Costs; review "Manage Standard Cost Import Exceptions"; fix Error rows, Import Standard Costs; **Publish** the scenario so costs are used for transactions.
  - ESS processes (Scheduled Processes for Cost Accounting): **Transfer Transactions from Inventory to Costing** (param: Cost Organization optional), **Transfer Transactions from Production to Costing**, **Transfer Costs to Cost Management** (AP invoices), **Transfer Transactions from Receiving to Costing** (no params; role `ORA_CST_COST_ACCOUNTANT_JOB`; priv `RCV_TRANSFER_RECEIVING_TRANSACTIONS_FROM_RECEIVING_TO_COSTING_PRIV`), **Create Cost Accounting Distributions** (needs transfers done first; auto-triggers Purge Prior Cost Accounting Process Errors), **Create and Update Cost Accounting Events** (periodic average finalization only), **Validate and Update Cost Accounting Periods** (period-end validation/close), **Update Standard Costs**, **Undo Cost Update**, **Roll up Costs**, **Export Standard Costs** (output to UCM `scm/standardCost/export`), **Delete Standard Costs from Interface**, **Import Revenue Lines** (BU required, workers, as-of date, start date), **Create Receipt Accounting Distributions** (after receiving transfer).
  - Sequence for inventory: Manage Inventory Transactions (inventory side) -> Transfer Transactions from Inventory to Costing -> Create Cost Accounting Distributions -> **Create Accounting** (Subledger Accounting; application Cost Management; option Transfer to GL and Post) -> GL. Exact Create Accounting parameters and that it also transfers to GL: UNVERIFIED (no 26D cost page found; the older "Transfer Journal Entries to GL" is EBS only). Use `ess_*` with `ess_find_job` style lookup on the pod.
- D (UI): Setup and Maintenance as above. No playbook yet. Create `playbooks/cost-accounting-setup.md` after first successful run.

## How to verify
- `GET periodicAverageCostOrganizationsLOV?fields=CostOrgId,CostOrganizationName` (periodic average only) or UI Manage Cost Organization Relationships.
- `GET valuationUnitsLOV?finder=findValuationUnits;bindCostBook=<book>`.
- After a test misc receipt: `GET itemCosts?finder=findItemCosts;bindItem=<item>&fields=ItemNumber,CostBook,TotalUnitCost,CostMethod`.
- Cost Accounting work area: Review Cost Accounting Distributions; Scheduled Processes log for Transfer Transactions from Inventory to Costing (Warning = org not assigned or no access).
- Standard cost: `GET standardCosts?finder=findByStatusCode;Bind_StatusCode=PUBLISHED&fields=StandardCostId,ItemNumber,TotalCost,EffectiveStartDate`.

## Role needed
- **Cost Accountant**: `ORA_CST_COST_ACCOUNTANT_JOB` (confirmed on the 26B Transfer Receiving to Costing page; 24C Security Reference lists the role). Access limited to authorized cost orgs (data access set).
- Setup: user with access to Setup and Maintenance for the offering (e.g. Application Implementation Consultant). Exact role code: UNVERIFIED.
- Cost Accounting Manager role: not found (UNVERIFIED).

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/create-a-cost-organization.html — Manage Cost Organizations task, fields, prerequisites
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/create-a-cost-book.html — Manage Cost Books, primary book rule
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/cost-organization-relationship.html — rules, period end validations
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/create-cost-organization-relationships.html — relationship steps and parameters
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/create-a-valuation-structure.html — Manage Valuation Structures, modes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/create-a-valuation-unit.html — Manage Valuation Units
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/set-up-a-cost-profile.html — Manage Cost Profiles
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/set-up-a-default-cost-profile.html — Manage Default Cost Profiles
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/cost-profiles-default-cost-profiles-and-item-cost-profiles.html — assignment rules
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/toc.htm — Cost Accounting TOC (page names)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fapma/scheduled-processes-for-cost-accounting.html — processes list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fapma/import-standard-costs-using-file-based-data-import.html — standard cost import procedure
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/standardcosts-3175.html — FBDI Standard Costs: UCM, ctl, tables
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-standardcosts-get.html — standardCosts finders/children
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itemcosts-get.html — itemCosts
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-periodicaveragecostorganizationslov-get.html — cost org LOV
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-valuationunitslov-get.html — valuation unit LOV
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — endpoint index (first 100k chars only): costScenarios, costScenariosV2, costAdjustments, costRollupGroups
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faspc/transfer-transactions-from-receiving-to-costing.html — role code and privilege (26B page)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/24c/faosm/Cost-Accountant-JR-1.html — Cost Accountant role (24C)

## UNVERIFIED
- FSM TaskCodes and whether any cost setup task supports Setup Task CSV export/import.
- Whether `Manage Item Cost Profiles` is the 26D task title (seen only in REST text).
- Existence of REST resources for cost orgs (general), cost books, cost profiles, cost accounting distributions. Only `periodicAverageCostOrganizationsLOV`, `valuationUnitsLOV`, `itemCosts`, `standardCosts`, `costScenarios*` confirmed.
- standardCosts POST/PATCH/DELETE details on 26D; costScenarios write attributes.
- `periodicAverageCostBooksLOV` on 26D.
- Create Accounting parameters for Cost Management and the GL transfer step; Subledger Accounting setup for cost.
- Define Standard Costs vs Interface Standard Costs process name, its parameters, ESS job path, CSV zip name.
- Item attributes that gate costing (Costing Enabled etc.): named in docs but exact REST names not checked.
- Cost Accounting Manager role code; setup role code.
- Cost book delete/deactivate rules (FAQ body not read).
- Redwood UI differences for Cost Accounting pages.
- Cost elements, components, component groups, mapping task names and Quick Setup 26D content.

## VERIFIED-ON-POD 2026-11-25
- All setup tasks of this area report `CSVExportImportSupportedFlag=Y` on the 26D pod → channel B is available (TaskCodes in `fsm-task-codes.md`); the UI is only the fallback.
