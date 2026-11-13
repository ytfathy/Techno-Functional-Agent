# Items, Item Classes, Item Import (FBDI) and Item Batches

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- Items (parts, products, services) are created in an item master or definition org within an **item class**, then assigned to inventory or item orgs.
- An item class gives templates, attribute groups, lifecycle phases, numbering and description rules, and data security.
- You must create **at least one item class** before creating items. Setting Item Creation Allowed = No blocks creation in a class.
- Bulk loads go through FBDI (ItemImportTemplate) or the REST item batch + uploadFile.

## Where in Fusion (FSM)
- Offering: Product Management. Functional area: **Items**. Tasks:
  - **Manage Item Classes**
  - Manage Item Statuses
  - Manage Item Types
  - Manage Lifecycle Phases
  - Manage Operational Attributes Groups
  - Manage Item Attribute Groups and Attributes
  - Deploy Item Extensible Flexfields
  - Download Import Template, Upload Item Data, Load Interface File through Scheduled Process, Import Items, Monitor Item Imports
- Other task lists: "Define Item Import Batch Configuration", "Define Product Spoke Systems" (Manage Spoke System), Manage Item Batches.
- Units of Measure must exist first: "Define Units of Measure".

## Prerequisites & dependencies
- Item organization / item master (`item-organizations.md`).
- UOMs (`uoms.md`).
- Lifecycle phases assigned to the item class or a parent class.
- Item statuses and types (seeded).
- Deployed item flexfields after item class changes.
- For batches: a spoke system.
- Depends on this: subinventories (item subinventories), transfer orders, POs, receiving.

## Key fields
| Field (UI label) | REST attribute (`itemsV2`) | Meaning | Notes |
|---|---|---|---|
| Organization | `OrganizationCode` / `OrganizationId` (marked req) | org where the item is created / assigned | |
| Item | `ItemNumber` | max 300 | |
| Description | `ItemDescription` | max 240 | |
| Item Class | `ItemClass` | item class name | |
| Template | `Template` | item template | default comes from the item class |
| Primary UOM | `PrimaryUOMValue` | e.g. "Each" | |
| Item Status | `ItemStatusValue` | e.g. Active | |
| Lifecycle Phase | `LifecyclePhaseValue` | e.g. Design / Production | |
| User Item Type | `UserItemTypeValue` | lookup `EGP_ITEM_TYPE` | e.g. "Finished Good" |
| Inventory Item / Stocked / Transactable | `InventoryItemFlag`, `StockEnabledFlag`, `MaterialTransactionEnabledFlag` | | |
| Purchased / Purchasable | `PurchasingFlag`, `PurchasableFlag` | | |
| Customer orderable / OM transactable | `CustomerOrderFlag`, `CustomerOrderEnabledFlag`, `TransactionEnabledFlag` | | |
| Transfer orders enabled | `TransferOrdersEnabledFlag` | needed for transfer orders | |
| Lot / Serial control | `LotControlValue`, `SerialGenerationValue` | | |
| Receipt routing | `ReceiptRoutingValue` | | |
| Copy from item | `CopyFromItemValue`, `CopyOrganizationAssignmentsFlag`, `CopyCategoriesFlag` | | |

## Common mistakes
- Creating an item in a child org before it exists in the master org. Assignment needs the master item.
- Item class without a lifecycle phase, or flexfields not deployed after class changes.
- An inconsistent combination of operational attributes. The docs refer to "Interdependent Item Attributes". Prefer `Template`.

## Channel & exact technique
- Preferred channel:
  - **A (REST `itemsV2`)** for single items and org assignment.
  - **C (FBDI)** for volume.
  - Item classes are **read-only in REST**: create them with **D (UI)** Manage Item Classes.
- A (items):
  - `GET|POST /fscmRestApi/resources/11.13.18.05/itemsV2`; `GET|PATCH .../itemsV2/{itemsV2UniqID}`.
  - Actions: `itemsV2/action/addItemsToDeleteGroup`, `addSupplierAssociationsToDeleteGroup`.
  - Children: `ItemCategory`, `ItemRevision` (with `ItemRevisionDFF`, `RevisionAttachment` and more), `ItemTranslation`, `ItemSupplierAssociation`, `ItemAttachment`, `ItemDFF`, `ItemGlobalDFF`, `ItemEffCategory`, `ProductCosts`.
  - Finders: `PrimaryKey` (ItemId, OrganizationId), `ItemRF` (ItemNumber, OrganizationCode), `ItemNumberAltKey`, `ItemVersionAltKey`.
  - Doc example (batch `parts` request, `operation: create`): `{"OrganizationCode":"V1","ItemClass":"KM_IC","ItemNumber":"..","ItemDescription":".."}`.
  - **Assign to org**: POST `itemsV2` again with the same `ItemNumber` and the child `OrganizationCode`. This is UNVERIFIED as a documented pattern; the FBDI equivalent is "Item Org Assignments". `rest_describe` first.
  - Legacy read-only resource: `items` (GET only).
- A (item classes): `GET /itemClasses`, `GET /itemClasses/{ItemClassId}` (GET only).
  - Children: `ItemClassPhases`, `ItemClassAttachmentCategories`, `ItemClassDQAttributes`.
  - Finders include `CreateItem` (OrgId), `CreateDocument`, `AdvancedTPICreate`.
  - Response attrs: `ItemClass`, `ItemClassCode`, `ItemClassId`, `ParentItemClass`, `ItemCreationAllowedFlag`, `ItemNumberGenMethodCode`, `EnabledFlag` and more.
- A (item batches):
  - `GET|POST /itemBatches`; `GET|PATCH /itemBatches/{itemBatchesUniqID}`. Child `itemBatchTranslations`.
  - Required: `BatchName`, spoke system (`SpokeSystemId` or `SpokeSystemCode`/`SpokeSystemName`). Optional: `DefaultOrganizationCode`, `ImportSchedule` ("Manual"), `ProcessItems`, change-order and new-item-request options.
  - Action `POST /itemBatches/action/uploadFile`. Content-Type `application/vnd.oracle.adf.action+json`. Params: `batchId` | `batchNumber`, `dataFilePath`, `importMapName`, `errorResponseType` (file|text).
- C (FBDI):
  - Template `ItemImportTemplate.xlsm`. UCM account **`scm/item/import`**. Scheduled process **Item Import** ("Item Import Job"); run it after **Load Interface File for Import**.
  - Control files: `EgpSystemItemsInterface.ctl`, `EgpItemRevisionsInterface.ctl`, `EgpItemCategoriesInterface.ctl`, `EgoItemAssociationsIntf.ctl`, `EgpItemRelationshipsIntf.ctl`, `EgoItemIntfEffb.ctl`, `EgoItemIntfEfftl.ctl`, `EgoItemRevisionIntfEffb.ctl`, `EgoItemRevisionIntfEfftl.ctl`, `EgoItemSupplierIntfEffb.ctl`, `EgoItemSupplierIntfEfftl.ctl`, `EgoStyleVariantAttrvsIntf.ctl`, `EgpTradingPartnerItemsIntf.ctl`, **`EgpOrgAssociationsIntf.ctl`** (Item Org Assignments).
  - Interface tables: `EGP_SYSTEM_ITEMS_INTERFACE`, `EGP_ITEM_REVISIONS_INTERFACE`, `EGP_ITEM_CATEGORIES_INTERFACE`, `EGP_ITEM_RELATIONSHIPS_INTF`, `EGO_ITEM_INTF_EFF_B/TL`, `EGP_TRADING_PARTNER_ITEMS_INTF`, `ACA_PD_ITEM_COST_INT` and more.
  - Separate FBDI object: "Reference Org Item Import" (`referenceorgitemimport-3184.html`), not researched.
- D (UI): Product Information Management > Create Item. Item classes: Manage Item Classes.

## How to verify
- `GET itemsV2?finder=ItemRF;ItemNumber=<n>,OrganizationCode=<org>`. Repeat for each org it must be assigned to.
- After FBDI: check Monitor Item Imports, or the ESS log of Item Import.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itemsv2-post.html — itemsV2 attributes, example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itemsv2-get.html — finders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itemclasses-get.html — itemClasses (GET only), finders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itembatches-post.html — item batch attributes, example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itembatches-action-uploadfile-post.html — uploadFile action
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — method inventory (itemClasses and items GET only)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/item-3182.html — FBDI Item: template, UCM account, control files, tables, scheduled process
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faipr/implementing-product-management.pdf — setup tasks to define items, Manage Item Classes path (Product Management / Items)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/implementing-common-features-for-scm.pdf — ch. 35 Items setup tasks

## UNVERIFIED
- REST pattern for assigning an existing item to another org (second `itemsV2` POST with a new `OrganizationCode`).
- Exact ESS job path/name and parameters of "Item Import" (Batch ID, Process All, Process Sequentially...), and of Load Interface File for Import (import process value).
- CSV file names inside the FBDI zip (the template generates them; not listed on the page).
- Whether `OrganizationId` is truly required when `OrganizationCode` is sent (the example sends only the code).
- Item class creation channel other than UI (no POST in REST 26D).
