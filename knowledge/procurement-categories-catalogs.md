# Procurement Categories & Catalogs (Purchasing Catalog, Category Hierarchies)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Three separate category structures exist, and they can mirror each other:
- **Purchasing (item) catalog**: the item catalog assigned to the **Purchasing** functional area. Its categories are the purchasing categories that every requisition and PO line carries. Every item must belong to one item category.
- **Procurement category hierarchy**: groups purchasing categories under browsing (non-item) categories to show how spend is categorized. Used in approval rules, account generation (Transaction Account Builder) and BI on the Requisitions, Purchasing and Sourcing subject areas.
- **Catalog category hierarchy**: the shopping-catalog browse tree for requesters. Browsing categories hold child categories, not items.
- A supplier **Products and Services** hierarchy also exists (supplier profile, registration, negotiation invites). It is out of scope here.

## Where in Fusion (FSM)
- Item catalogs:
  - **Manage Catalogs** (Product Information Management work area, or Setup).
  - **Manage Functional Area Catalogs** (Setup: Product Management > Catalogs. Also in Procurement > **Purchasing Categories** functional area, and in the Catalogs functional area).
- Procurement category hierarchy: **Manage Procurement Category Hierarchy** (Procurement > Procurement Foundation).
- Catalog category hierarchy (shopping browse): Manage Catalog Category Hierarchy topics (Procurement Catalog chapter). The exact task name is UNVERIFIED.

## Prerequisites & dependencies
- An item master org exists (Configure Procurement BF > Inventory Organization).
- The purchasing catalog needs at least one category set as **default category** before you assign it to Purchasing.
- Dependents: items (auto-assigned to the purchasing default category when Purchased = Yes), line type default category, approval rules and account rules (procurement hierarchy), shopping (catalog hierarchy), content zones.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Catalog Code | `CatalogCode` (required) | | itemCatalogs |
| Catalog Name | `CatalogName` (required) | | |
| Description | `Description` | | |
| Default Category | `DefaultCategoryCode` | Used for automatic item assignment | **Required** for Purchasing |
| Start / End Date | `StartDate` / `EndDate` | | |
| Controlled At | `MasterControlledFlag` (default true) | Master vs org-controlled | Purchasing allows org-controlled catalogs only if the Purchased / Internal Ordered control is org level |
| Allow multiple item category assignments | `AllowItemToMultipleCategoriesFlag` (default false) | | Unchecked and disabled for Purchasing |
| Catalog Content (items at all levels vs leaf only) | `AssignItemsToLeafOnlyFlag` (default true) | | Purchasing: "Assign items to leaf level categories only" unchecked and disabled |
| Public | `PublicCatalogFlag` | | |
| Functional area assignment | child `functionalAreaAssignments` | Assign to **Purchasing** | One catalog per functional area. No change once items have PURCHASING_ITEM_FLAG=Y or INTERNAL_ORDER_FLAG=Y |
| Category Code / Name | `CategoryCode`, `CategoryName` (required) + `CatalogId` (required) | itemCategories | |
| Parent Category | `ParentCategoryCode` | Hierarchy placement | Purchasing catalog: "Enable hierarchy for catalog" = No |
| Items only | `ItemsOnlyFlag` (default false) | | |
| Browsing category (procurement hierarchy) | — | Name + Description in the **Create Browsing Category** dialog | UI only |
| Insert Item Category (procurement hierarchy) | — | **Select and Add: Item Categories** dialog | UI only |

## Common mistakes
- Assigning a catalog to Purchasing without a default category. This is blocked.
- Trying to swap the purchasing catalog after items exist. This is blocked.
- Expecting the procurement category hierarchy to drive shopping browse. It doesn't; that is the catalog category hierarchy.
- Putting items in browsing categories. Browsing categories can't hold items.
- Building a multi-level hierarchy inside the purchasing catalog. Hierarchy is not enabled for Purchasing; use the procurement hierarchy instead.

## Channel & exact technique
- Preferred channel: **A (REST)** for item catalogs and categories (SCM REST). **D (UI)** for the procurement category hierarchy (no REST or upload documented). **A** for content zones.
- A (REST, SCM):
  - `POST/GET /fscmRestApi/resources/11.13.18.05/itemCatalogs`. Children: `categoryHierarchies`, `functionalAreaAssignments`, `translatableAttributes`, `attachments`, `DFF`. Path: `/itemCatalogs/{CatalogId}/child/categoryHierarchies`.
  - `POST/GET /fscmRestApi/resources/11.13.18.05/itemCategories` (required `CatalogId`, `CategoryCode`, `CategoryName`). `Upsert-Mode` is supported.
  - Related: `/categorySets`.
- A (REST, Procurement), read-only:
  - `GET /fscmRestApi/resources/11.13.18.05/browsingCategories[/{CategoryId}]`
  - `GET /fscmRestApi/resources/11.13.18.05/catalogCategoryHierarchyNodes[/{CategoryId}]`
- A (REST, Procurement content zones): `/contentZones` (POST/GET/PATCH/DELETE, action `duplicate`, `deleteAssignments`). Children: `catalogAssignments`, `publicShoppingListAssignments`, `securityAssignments`, `smartFormAssignments`.
- B (FSM CSV): UNVERIFIED for Manage Procurement Category Hierarchy and Manage Functional Area Catalogs.
- C: item category assignment through Item FBDI/import (not researched here).
- D (UI): procurement hierarchy. Highlight a node, then Create (browsing category) or Insert Item Category. No playbook yet.

## How to verify
- `GET itemCatalogs?q=CatalogCode='<code>'&expand=functionalAreaAssignments`
- `GET itemCategories?q=CatalogCode='<code>'`
- `GET browsingCategories` and `catalogCategoryHierarchyNodes`
- UI: Manage Procurement Category Hierarchy tree.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/create-a-procurement-category-hierarchy.html — task, dialogs, uses
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-s-the-difference-between-the-catalog-procurement-and.html — three hierarchies
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-s-the-difference-between-an-item-category-and-a-browsing.html — item vs browsing category
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/overview-of-catalog-category-hierarchy.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-catalogs-work-together.html — catalog components, Catalog Content field
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/catalog-details.html — Edit Catalog header, Details and Category Hierarchy tabs
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faipr/functional-area-catalog-rules.html — Purchasing rules, task, assignment steps
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itemcatalogs-post.html — itemCatalogs attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-itemcategories-post.html — itemCategories attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html — contentZones, browsingCategories, catalogCategoryHierarchyNodes

## UNVERIFIED
- The exact FSM task name for the shopping catalog category hierarchy in 26D.
- Whether itemCatalogs / itemCategories support PATCH or DELETE in 26D (only the POST pages were read).
- FSM Setup Task CSV support for Manage Procurement Category Hierarchy and Manage Functional Area Catalogs.
