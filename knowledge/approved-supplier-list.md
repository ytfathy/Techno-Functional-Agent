# Approved Supplier List (ASL)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
An ASL entry says which supplier or supplier site is approved (or blocked) to supply an item or a procurement category. Scope is a whole procurement BU or one ship-to organization. The ASL status decides two things: whether the supplier can be sourced for the item or category, and whether related POs can be approved. Source documents (blanket or contract agreements) on an entry default the buyer, supplier contact and supplier item number when requisition lines are created automatically.
Affects: buyers, requisition sourcing, PO approval, BPA submission (profile option `PO_ASL_VALIDATION_FOR_BPA`).

## Where in Fusion (FSM)
- Offering: Procurement
- **Manage Approved Supplier List Statuses**: setup task. Redwood page "Approved Supplier List Statuses" since 26C. Mandatory ("No Longer Optional") from 27A, enabled by default. You can create, update, view and delete statuses, set a default status, and set end dates that make a status inactive. Functional area: UNVERIFIED (likely Procurement Foundation).
- **Manage Approved Supplier List Entries**: transactional task in the Purchase Agreements and Purchase Orders work areas (not FSM). Redwood page "Approved Supplier List Entries" with a **Procurement BU** selector. It needs profile option `ORA_PO_ASL_REDWOOD_ENABLED` = Y at Site level (default disabled).
- Auto-create: ASL entries can be created automatically from blanket agreements (Manage Agreements task).

## Prerequisites & dependencies
- Procurement BU, ship-to inventory organizations, items or procurement categories.
- Supplier and supplier site with a site assignment for the BU.
- ASL statuses (seeded "Approved" used in docs examples).
- For source documents: approved blanket purchase agreement or contract purchase agreement. Category-level ASLs can only be sourced from contract purchase agreements (Redwood page).
- Before switching to the Redwood ASL page, run the scheduled process **Migrate Supplier Item Attributes from Global Approved Supplier List Entries**.

## Key fields
### ASL entry (`procurementApprovedSupplierListEntries`)
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Procurement BU | `ProcurementBU` / `ProcurementBUId` | Owning BU | Required in practice |
| Ship-to Organization | `ShipToOrganization` / `ShipToOrganizationId` | Ship-to org scope | Omit for Global scope (server sets `ShipToOrganizationId` = -1, `AslScopeCode` = `GLOBAL`). Provide it for `SHIP_TO_ORG` scope. |
| Scope | `Scope`, `AslScopeCode` | Global or Ship-to Organization | Read-only. Derived from ShipToOrganization. |
| Item | `Item` / `ItemId` | Item | REST supports Item type only (see restrictions) |
| Category | `CategoryName` / `CategoryId` | Procurement category | Category-type entries cannot be created, updated or read through REST |
| Supplier | `Supplier` / `SupplierId` | Supplier | Required in practice |
| Supplier Site | `SupplierSite` / `SupplierSiteId` | Supplier site | Required in practice |
| Status | `Status` / `AslStatusId` | ASL status | for example `Approved` |
| Supplier Item | `PrimaryVendorItem` | Supplier part number | |
| Review Due Date | `ReviewDueDate` | Recertification reminder date | yyyy-MM-dd |
| Disabled | `DisableFlag` | Entry no longer used | boolean |
| Comments | `Comments` | Free text | max 240 |
| Purchasing UOM | `PurchasingUOM` / `PurchasingUOMCode` | Supplier item attribute | |
| Country of Origin | `CountryOfOrigin` / `CountryOfOriginCode` | Supplier item attribute | |
| Minimum Order Quantity | `MinimumOrderQuantity` | Supplier item attribute | |
| Fixed Lot Multiple | `FixedLotMultiple` | Supplier item attribute | |
| (key) | `AslId` | Entry ID | System-assigned |
| DFF | child `DFF` (`__FLEX_Context`) | Descriptive flexfield | Not supported on the Redwood page |

### ASL source document (`approvedSupplierListSourceDocuments`)
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Procurement BU | `ProcurementBU` / `ProcurementBUId` | Key of ASL entry | required |
| Ship-to Organization | `ShipToOrganization` / `ShipToOrganizationId` | Key of ASL entry | null for global |
| Supplier / Supplier Site | `Supplier`, `SupplierSite` (+Id) | Key of ASL entry | |
| Item | `Item` / `ItemId` | Key of ASL entry | |
| Agreement Type | `AgreementType` / `AgreementTypeCode` | `Blanket Purchase Agreement` or contract purchase agreement | required |
| Agreement | `Agreement` / `AgreementId` | Agreement number | required |
| Agreement Line | `AgreementLine` (number) / `AgreementLineId` | Agreement line | required for BPA |
| (keys) | `AslSourceDocumentsId`, `AslId` | IDs | returned |
| Read-only | `AgreementStartDate`, `AgreementEndDate`, `AgreementStatus`, `Scope`, `ScopeCode` | | do not send |

### ASL status (UI only)
- Status name, default status, end date. Processing controls (sourcing allowed, PO approval allowed) are set on the status. Exact control labels: UNVERIFIED.

### Related profile options
| Code | Display name | Values | Task |
|---|---|---|---|
| `PO_ASL_VALIDATION_FOR_BPA` | Approved Supplier Validation for Blanket Purchase Agreements | Yes (default) / No. Yes blocks BPA submit unless the supplier has approved ASL status for lines marked to use only approved suppliers. | Manage Purchasing Profile Options (Procurement Foundation) |
| `ORA_PO_ASL_REDWOOD_ENABLED` | Redwood Page for Approved Supplier List Entries Enabled | Y/N at Site, default disabled | Manage Administrator Profile Values |

### Privileges
- `PO_MANAGE_APPROVED_SUPPLIER_LIST_STATUS_PRIV` (Manage Approved Supplier List Status)
- `PO_SEARCH_APPROVED_SUPPLIER_LIST_ENTRY_PRIV`, `PO_CHANGE_APPROVED_SUPPLIER_LIST_ENTRY_PRIV`
- `PO_MIGRATE_SUPPLIER_ITEM_ATTRS_FROM_GLOBAL_ASL_ENTRY_PRIV` (new 26B), `FND_MANAGE_SCHEDULED_JOB_DEFINITION_PRIV`

## Common mistakes
- Trying to create category-type, manufacturer or distributor ASL entries through REST. Not supported. Use UI.
- Adding ship-to-org-specific supplier item attributes to a Global entry. Not allowed through REST. Create a ship-to org entry instead.
- Creating source documents before the ASL entry exists. Create entries first.
- Copying the docs batch example as is. The source document batch example has a trailing comma (invalid JSON).
- Redwood page: only **Direct** ASL business type. Manufacturer ASLs do not show. Distributor ASLs behave as direct. One supplier item attribute record per entry. No DFF on supplier item attributes or source documents.
- Deleting an ASL status in use. End-date it instead (UNVERIFIED whether delete is blocked).

## Channel & exact technique
- Preferred channel: **A (REST)** for item-type ASL entries and source documents. **D (UI)** for ASL statuses (no REST found) and category-type entries.
- A (REST):
  - `GET|POST /fscmRestApi/resources/11.13.18.05/procurementApprovedSupplierListEntries`
  - `GET|PATCH /fscmRestApi/resources/11.13.18.05/procurementApprovedSupplierListEntries/{procurementApprovedSupplierListEntriesUniqID}` (no DELETE; disable with `DisableFlag`)
  - child `.../{id}/child/DFF`
  - `GET|POST /fscmRestApi/resources/11.13.18.05/approvedSupplierListSourceDocuments` (+ GET/PATCH/DELETE by key, per 26B endpoint list)
  - Batch: POST to `/fscmRestApi/resources/11.13.18.05` style batch with `Content-Type: application/vnd.oracle.adf.action+json`, `parts[]` with `"operation": "create"` (docs use-case example)
  - Minimal create body: `{"ProcurementBU":"Vision Operations","ShipToOrganization":"Vision Operations","Supplier":"Big Computers","SupplierSite":"Austin","Item":"CM13139","Status":"Approved"}`
  - Header `Upsert-Mode: true` supported.
  - Always `rest_describe` first.
- B (FSM CSV): UNVERIFIED for Manage Approved Supplier List Statuses.
- C (FBDI): UNVERIFIED (no ASL FBDI template found in this research).
- D (UI): Setup and Maintenance > search "Manage Approved Supplier List Statuses" > create or edit > **Save** or **Save and Close**. Playbook not yet written.

## How to verify
- `GET procurementApprovedSupplierListEntries?q=Item='CM13139';Supplier='Big Computers'` and check `Status`, `Scope`.
- `GET approvedSupplierListSourceDocuments?q=AslId=<id>`.
- Functional: create a requisition for the item and check the supplier and agreement default; submit a BPA for an item marked "use approved supplier" with a non-approved supplier and expect a block when `PO_ASL_VALIDATION_FOR_BPA` = Yes.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/approved-supplier-list.html — scope, entry types, capabilities, auto-create from BPA
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/considerations-for-creating-approved-supplier-list-entry.html — scope, type, status controls, supplier item attributes, source documents
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-procurement-approved-supplier-list-entries.html — endpoints and restrictions
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-procurementapprovedsupplierlistentries-post.html — attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-approvedsupplierlistsourcedocuments-post.html — source document attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/use-case_create_approved_supplier_list_entries.html — batch create examples, required attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26b/fapra/rest-endpoints.html — source document CRUD operations (26B list)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/proc26c/26C-procurement-wn-f46550.htm — Redwood ASL statuses task, privilege, 27A mandatory
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42846.htm — Redwood ASL entries page, profile option, migration process
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-approved-supplier-status-validation-for-blanket.html — PO_ASL_VALIDATION_FOR_BPA

## UNVERIFIED
- FSM functional area of Manage Approved Supplier List Statuses.
- Exact field and processing-control labels on the ASL status page (for example "PO approval allowed", "Sourcing allowed").
- Whether an ASL status in use can be deleted.
- Setup Task CSV support for ASL statuses; any ASL FBDI template.
- Source document DELETE/PATCH by key in 26D (confirmed only in 26B endpoint list).
