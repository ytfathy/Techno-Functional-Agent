# Inventory Organizations (and Inventory Organization Parameters)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
An inventory organization is the warehouse / plant / distribution center that stores and transacts items. Each one belongs to **one management business unit** (with the Materials Management business function), **one legal entity** and **one primary ledger**. The legal entity owns the inventory. Transactions are accounted in that legal entity's primary ledger. Manufacturing plants, maintenance orgs and contract manufacturers are also inventory orgs (Additional Usages flags). Several inventory orgs can share one location, for example one per BU in a shared DC. **You can rename an org later, but you cannot change its code.**

## Where in Fusion (FSM)
- Offering: Manufacturing and Supply Chain Materials Management. Functional area: **Facilities**. Task: **Manage Inventory Organizations**. Create gives a basic-info page, then Next gives the **Manage Inventory Organization Parameters** page.
- The same task appears under Offering: Product Management, Functional area: **Inventory Organizations**. Use it for Actions > *Process Item Grouping Change*.
- Task: **Copy Inventory Organizations** submits a scheduled process. Check the result in Scheduled Processes.
- Related tasks: Manage Facility Schedules (Facilities). Manage Inventory Locations: Quick Setup's prerequisite says to create the org location with this task.
- Quick Setup for the Facilities functional area needs at least 1 BU with Materials Management and 1 HCM organization location.
- Redwood "Manage Facilities" page: UNVERIFIED. The 26D docs only mention Redwood organization pages in HCM/enterprise-structure FAQs.

## Prerequisites & dependencies
- Must exist first:
  - Location (HCM `locationsV2` / Manage Locations).
  - Management BU with the Materials Management function.
  - Legal entity (same primary ledger as the BU).
  - Profit center BU, so trade transactions do not error in costing.
  - Facility schedule / workday calendar. `ScheduleId` is required in invOrgParameters.
  - Item master organization: normally an *item* org, not an inventory org.
- Depends on this: subinventories, locators, interorg parameters, receiving and shipping parameters, carrier ship-method org assignments, item org assignment, cost org relationships.

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Name | `OrganizationName` (req) | org name | max 240 |
| Organization (code) | `OrganizationCode` (req) | short code | max 18, immutable |
| Usage | `InventoryFlag` (req) | true = inventory org, false = item org | no default, must send |
| Management Business Unit | `ManagementBusinessUnitId` / `ManagementBusinessUnitName` | owning BU | required for inventory orgs. The doc example uses the Name |
| Legal Entity | `LegalEntityId` / `LegalEntityName` | owner LE | required for inventory orgs |
| Profit Center Business Unit | `ProfitCenterBusinessUnitId` / `ProfitCenterBusinessUnitName` | intercompany trade | strongly recommended |
| Location | `LocationId` | org address | |
| Status | `Status` | Active / inactive | example: "Active" |
| Item Master Organization | `MasterOrganizationId` / `MasterOrganizationCode` | item master | doc says required |
| Item Grouping Behavior | `ItemGroupingCode` | `ORA_RCS_IGB_DFTN` (definition) / `ORA_RCS_IGB_RFRC` (reference) | |
| Item Definition Organization | `ItemDefinitionOrganizationId` / `...Code` / `...Name` | used when the org is a reference org | |
| Organization is a manufacturing plant | `ManufacturingPlantFlag` | | needs plantParameters |
| Performs maintenance | `MaintenanceEnabledFlag` | | |
| Contract manufacturer | `ContractManufacturingFlag` | | needs `SupplierId` + `SupplierSiteId` in params |
| Integrated System Type | `IntegratedSystemType` | `ORA_RCS_IS_WMS`, `ORA_RCS_IS_3PL`, `ORA_RCS_IS_INVMGMT` | |
| Schedule | invOrgParameters.`ScheduleId` (req) / `ScheduleName` | workday calendar | |
| Time Zone | invOrgParameters.`Timezone` | | |
| Locator Control | invOrgParameters.`StockLocatorControl` | none / prespecified / dynamic / determined at subinventory level | code values UNVERIFIED |
| Enable inventory tracking by project | `TrackByProjectFlag` | | |
| Allow negative balances | `NegativeInvReceiptFlag` | | |
| Allow negative on-hand transactions | `AllowNegativeOnhandTransactionsFlag` | cycle count | |
| Automatically cancel transfer order backorders | `FillKillTransferOrdersFlag` | | |
| Starting Revision | `StartingRevision` | | |
| Lot / serial generation | `LotNumberGeneration`, `LotNumberUniqueness`, `SerialNumberGeneration`, `SerialNumberType`, `AutoLotAlphaPrefix`, `StartAutoSerialNumber` | | |
| Pick Slip Batch Size | `PickSlipBatchSize` | | |
| Item sourcing | `SourceType`, `SourceOrganizationId`/`Code`, `SourceSubinventory` | | |

## Common mistakes
- No profit center BU: trade transaction errors in Cost Management.
- Using the item master as a transacting inventory org. The docs say to keep them separate.
- Locator control: you can go from "No locator control" to "determined at subinventory level" later. You can only go back if no subinventory has locators.
- Copy org: the source cannot be a contract-manufacturing or item-sourcing-enabled org.
- Choosing the wrong org code. It is permanent, so the fix is a new org plus disabling the old one.

## Channel & exact technique
- Preferred channel: **A (REST)**. Full create/update is supported.
- A: `GET|POST /fscmRestApi/resources/11.13.18.05/inventoryOrganizations`; `GET|PATCH .../inventoryOrganizations/{OrganizationId}` (no DELETE)
  - Children:
    - `invOrgParameters`: GET/POST/PATCH `{OrganizationId2}`. Grandchild `organizationParameterDFF`.
    - `plantParameters`: GET/POST/PATCH `{OrganizationId4}`.
  - Deep create works: nest `invOrgParameters:[{ScheduleId:..}]` and `plantParameters:[..]` in the POST. The doc example shows this.
  - Action `POST .../inventoryOrganizations/action/copyInventoryOrganizations`. Content-Type `application/vnd.oracle.adf.action+json`. Body:
    - `sourceOrganizationId` | `sourceOrganizationCode` | `sourceOrganizationName`.
    - `organizationCopies` (array of objects, each with Name, Code, Location; key names UNVERIFIED).
    - `copyParamsList`: `INV_ORG_PARAM`, `DATA_SECURITY`, `PLANT_PARAMETERS`, `SUBINVENTORIES`, `LOCATORS`.
  - Finders: `OrganizationIdFinder`, `PrimaryKey` (OrganizationId), `activeOrgs`, `inventoryOrgs` (Status), `itemOrgs` (Status), `lotConversionEnabledOrgs`, `maintenanceOrgs`, `manufacturingOrgs`.
  - Read-only LOVs: `inventoryOrganizationsLOV`, `inventoryOrganizationsOpenLOV`.
  - Related read-only resource: `shippingParameters` (GET only, finder `PrimaryKey` OrganizationId). Holds `EnforceShipMethodFlag`, `CarrierManifestFlag` and more.
  - Example POST (from the doc): `{"OrganizationCode":"..","OrganizationName":"..","ManagementBusinessUnitName":"..","LegalEntityName":"..","ProfitCenterBusinessUnitName":"..","Status":"Active","LocationId":1001,"InventoryFlag":true,"MasterOrganizationId":204,"ItemGroupingCode":"ORA_RCS_IGB_RFRC","ItemDefinitionOrganizationName":"..","invOrgParameters":[{"ScheduleId":100000016383001}]}`
- B (FSM CSV): UNVERIFIED for Manage Inventory Organizations.
- D (UI): Manage Inventory Organizations, then Manage Inventory Organization Parameters.

## How to verify
- `GET inventoryOrganizations?q=OrganizationCode='XXX'&expand=invOrgParameters`. Check `InventoryFlag`, `ManagementBusinessUnitName`, `LegalEntityName`, `ScheduleName`.
- UI: search the org in Manage Inventory Organizations.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — resource and child list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventoryorganizations-post.html — attributes, required flags, example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventoryorganizations-get.html — finders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventoryorganizations-action-copyinventoryorganizations-post.html — copy action
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventoryorganizations-organizationid-child-invorgparameters-post.html — parameters child
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-shippingparameters-get.html — shippingParameters (read-only)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/implementing-common-features-for-scm.pdf — ch. 22 Facilities (Quick Setup prerequisites), ch. 23 Inventory Organizations (FSM path, parameters page, copy, considerations)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faipr/implementing-product-management.pdf — Product Management offering / Inventory Organizations functional area, Process Item Grouping Change

## UNVERIFIED
- Allowed code values for `StockLocatorControl`, `LotNumberGeneration`, `SerialNumberGeneration`. Run `rest_describe` / the lookup.
- Exact key names inside `organizationCopies` objects for the copy action.
- Whether Manage Inventory Organizations supports FSM Setup Task CSV export/import.
- Any 26D Redwood "Manage Facilities" page for inventory orgs.
- Whether the POST requires an explicit `invOrgParameters` row (`ScheduleId`). Probably yes, because `ScheduleId` is "required" in the child.
