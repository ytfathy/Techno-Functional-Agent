# Subinventories and Locators

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- A **subinventory** is a physical or logical stock area in an inventory org, for example Stores, Receiving or a PAR location.
- A **locator** is a row/rack/bin/shelf inside a subinventory.
- Subinventories carry these settings:
  - asset / depreciable / quantity-tracked flags
  - locator control
  - material status
  - sourcing / replenishment and lead times
  - picking order
  - transfer-order backorder cancel option
- Item subinventories hold item-level min-max per subinventory.

## Where in Fusion (FSM)
- Offering: Manufacturing and Supply Chain Materials Management. Task: **Manage Subinventories and Locators**. It asks for the organization: "Select Organization" dialog.
- Functional area: the docs show both **Inventory Management** and **Facilities**, in different topics.
- Buttons inside the task: Manage Item Subinventories.
- **Supports Setup CSV export/import**:
  - Export: Actions icon on the task > Export to CSV File > Create New > Submit.
  - Import: edit the CSV, then Import from CSV File.
  - Covers subinventories, locators and item-subinventory records.
- Related task: **Manage Intersubinventory Parameters** (Inventory Management). Used for intra-org transfer orders.

## Prerequisites & dependencies
- An inventory org with a locator control parameter.
- If only some subinventories should use locators, the org must be set to *Locator control determined at subinventory level*.
- Location (optional `LocationId`). It is needed for transfer orders and transit times.
- Locator flexfield structure (`LocatorStructure` / `StructureInstanceNumber`). See resource `locatorStructureInstances`.
- Material statuses.
- Depends on this: transfer orders (source/destination subinventory), receiving put-away, shipping staging, intersubinventory parameters.

## Key fields
| Field (UI label) | REST attribute (`subinventories`) | Meaning | Notes |
|---|---|---|---|
| Subinventory (name) | `SubinventoryName` (req) / `SecondaryInventoryName` | max 30 / 10 | the doc example uses `SecondaryInventoryName` |
| Organization | `OrganizationId` / `OrganizationCode` | owning org | the example uses `OrganizationCode` |
| Description | `Description` | max 50 | |
| Subinventory Type | `SubinventoryType` | lookup `INV_SUB_TYPE` | default "1" (Storage) |
| Locator Control | `LocatorControl` | lookup `INV_SUB_LOCATOR_CONTROL` | default "1". The example uses "2". Options: None / Prespecified / Dynamic entry / Item level |
| Locator structure | `LocatorStructure` | locator KFF structure instance | example 101 |
| Quantity tracked | `QuantityTracked` | 1/2 | default 1 |
| Asset subinventory | `AssetSubinventory` | 1 asset / 2 not | default 1 |
| Depreciable | `Depreciable` | 1/2 | default 2 |
| Material Status | `MaterialStatusId` / `MaterialStatusCode` | | "Active" |
| Default locator status | `DefaultLocStatusId` / `DefaultLocStatusCode` | | |
| Location | `LocationId` / `LocationCode` | | |
| Picking Order | `PickingOrder` | | |
| Sourcing | `SourcingType`, `SourceOrganizationId`/`Code`, `SourceSubinventory` | replenishment | |
| Lead times | `PreprocessingLeadTime`, `ProcessingLeadTime`, `PostprocessingLeadTime` | | |
| PAR location | `ParLocation` | 1/2 | default 2 |
| Cancel backorders (TO) | `FillKillToLookup` | cancel / don't / use next level | lookup name UNVERIFIED |
| End Date | `DisableDate` | | |
| **Locator** (`locators` child) | `locatorsKeyFlex[]` segments + `StructureInstanceNumber`, `SubinventoryCode`, `Description`, `InventoryLocationType`, `MaterialStatusId`/`Code`, `PickingOrder`, `DisableDate` | | sample segments `_Row`, `_Rack`, `_Bin` (`_Aisle` is also in the sample structure). Real segment names depend on the KFF |

## Common mistakes
- Setting locator control on a subinventory while the org is not "determined at subinventory level". The field is not assignable then.
- Changing locator control with pending transactions or on-hand. The docs say this is not allowed.
- Locator segment attribute names are structure-specific. Always `rest_describe` the `locatorsKeyFlex` for the structure.

## Channel & exact technique
- Preferred channel: **A (REST)**. B (FSM CSV) is a verified alternative for bulk loads.
- A:
  - `GET|POST /fscmRestApi/resources/11.13.18.05/subinventories`; `GET|PATCH .../subinventories/{subinventoriesUniqID}` (no DELETE; use `DisableDate`).
  - Children:
    - `locators`: GET/POST, plus GET/PATCH `{InventoryLocationId}`. Grandchildren `locatorsKeyFlex` (POST, discriminator `_STRUCTURE_INSTANCE_NUMBER`), `locatorsDFF`, and `itemLocators` (GET/POST/PATCH/DELETE).
    - `itemSubinventories` (GET/POST/PATCH/DELETE).
    - `subinventoriesDFF`.
    - `translations` (GET/PATCH).
  - Finders on subinventories:
    - `PrimaryKey` (OrganizationId, SecondaryInventoryName)
    - `filterByOrganizationIdOnly` (BindOrganizationId)
    - `findByOrganizationId` (BindItem, BindOrganizationId)
    - `findDefaultZoneSubinventories`, `findUserDefinedZoneSubinventories`
  - Read-only helpers: `activeSubinventories`, `activeLocators`, `locatorStructureInstances`, `subinventoryGroups`, `locatorCombinationsLOV`.
  - Item-level resources: `subinventoryItems`, `locatorItems` (CRUD).
  - Intersubinventory parameters: `POST /interSubinventoryParameters`. Required: `OrganizationId`, `DestinationTypeCode`, `StartDate`. Also PATCH and DELETE `{IntersubParametersId}`.
  - Locator POST example (doc): `{"StructureInstanceNumber":101,"MaterialStatusCode":"Active","locatorsKeyFlex":[{"EnabledFlag":"Y","_Row":"R1","_Rack":"1","_Bin":"1"}]}`
- B (FSM CSV): Manage Subinventories and Locators task > Actions > Export/Import CSV. The TaskCode is UNVERIFIED.

## How to verify
- `GET subinventories?finder=PrimaryKey;OrganizationId=<id>,SecondaryInventoryName=<name>&expand=locators`
- UI: Manage Subinventories and Locators.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-subinventories-post.html — attributes, lookups, example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-subinventories-get.html — finders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-subinventories-subinventoriesuniqid-child-locators-post.html — locator attributes, keyflex example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — children / methods, interSubinventoryParameters
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implementing-manufacturing-and-supply-chain-materials-management.pdf — ch. 3 (Intersubinventory parameters, subinventory cancel backorders), ch. 8 (locator control, CSV bulk export/import, FAQs)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/implementing-common-features-for-scm.pdf — ch. 23 org-level locator control rules

## UNVERIFIED
- Which of `SubinventoryName` vs `SecondaryInventoryName` the server really requires on POST. The schema marks `SubinventoryName` but the example sends `SecondaryInventoryName`. Use `rest_describe`.
- Whether `OrganizationId`/`OrganizationCode` is mandatory on POST. It must be logically, but the schema does not say "required".
- FSM CSV TaskCode / business object codes for Manage Subinventories and Locators.
- Lookup code meanings for `LocatorControl` (1..n) and the `FillKillToLookup` lookup name.
