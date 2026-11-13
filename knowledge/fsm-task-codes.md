# FSM setup task codes & CSV support (verified on the TEST pod)

> Release: 26D · Verified on pod: 2026-11-14 (TEST) via `GET setupTasks` (tool `fsm_find_task`) · Status: VERIFIED-ON-POD

`CSVExportImportSupportedFlag = Y` → channel B (`fsm_export` → edit CSV → `fsm_import`) is possible, and the export is the backup.
`N` → channel D (UI playbook). Re-check with `fsm_find_task` on other pods/releases.

| Task name | TaskCode | CSV (channel B) |
|---|---|---|
| Manage Business Unit | FUN_MANAGE_BUSINESS_UNIT | Y |
| Assign Business Unit Business Function | FUN_ASSIGN_BUSINESS_UNIT_BUSINESS_FUNCTION | Y |
| Manage Business Unit Set Assignment | FUN_MANAGE_BUSINESS_UNIT_SET_ASSIGNMENT | Y |
| Manage Reference Data Sets | FND_MANAGE_REFERENCE_DATA_SETS | Y |
| Manage Locations | PER_MANAGE_LOCATIONS | Y |
| Configure Procurement Business Function | PO_CONFIGURE_PROCUREMENT_BUSINESS_FUNCTION | Y |
| Configure Requisitioning Business Function | POR_CONFIGURE_REQUISITIONING_BUSINESS_FUNCTION | Y |
| Manage Service Provider Relationships | FUN_MANAGE_SERVICE_PROVIDER_RELATIONSHIPS | Y |
| Manage Procurement Document Numbering | ORA_PO_MANAGE_PROCUREMENT_DOCUMENT_NUMBERING | Y |
| Manage Document Styles | PO_MANAGE_DOCUMENT_STYLES | Y |
| Manage Line Types | not found |  |
| Manage Procurement Agents | PO_MANAGE_PROCUREMENT_AGENTS | Y |
| Manage Requisition Approvals | POR_MANAGE_REQUISITION_APPROVALS | N |
| Manage Purchasing Document Approvals | PO_MANAGE_PURCHASING_DOCUMENT_APPROVALS | N |
| Manage Supplier Registration Approvals | ORA_POZ_MANAGE_SUPPLIER_REGISTRATION_APPROVALS | N |
| Specify Supplier Numbering | POZ_SPECIFY_SUPPLIER_NUMBERING | Y |
| Manage Negotiation Styles | PON_MANAGE_NEGOTIATION_STYLES | Y |
| Manage Inventory Organizations | INV_MANAGE_INVENTORY_ORGANIZATIONS | Y |
| Manage Subinventories and Locators | INV_MANAGE_SUBINVENTORIES_AND_LOCATORS | Y |
| Manage Units of Measure | INV_MANAGE_UNITS_OF_MEASURE | Y |
| Manage Interorganization Parameters | INV_MANAGE_INTERORGANIZATION_PARAMETERS | Y |
| Manage Receiving Parameters | RCV_MANAGE_RECEIVING_PARAMETERS | Y |
| Manage Carriers | WSH_MANAGE_CARRIERS | Y |
| Manage Shipping Methods | not found |  |
| Manage Item Classes | EGO_MANAGE_ITEM_CLASSES | Y |
| Manage Business Unit Data Access for Users | ORA_FUN_MANAGE_BUSINESS_UNIT_DATA_ACCESS_FOR_USERS | N |
| Manage Data Access for Users | ORA_FUN_MANAGE_DATA_ACCESS_FOR_USERS | Y |
| Manage Procurement Category Hierarchy | POR_MANAGE_AGENT_ASSIGNMENTS_CATEGORY_HIERARCHY | Y |
| Manage Purchasing Profile Options | PO_MANAGE_PURCHASING_PROFILE_OPTIONS | Y |
## Consequences for channel choice
- Business Unit, business functions, BU set assignment, Configure Procurement / Requisitioning Business Function, service provider relationships, document numbering, document styles, procurement agents, supplier numbering, negotiation styles, inventory orgs, subinventories/locators, UOMs, interorg parameters, receiving parameters, carriers, item classes, purchasing profile options → **channel B available** (prefer A where a REST resource exists, e.g. document styles, procurement agents, carriers).
- Approvals (Manage Requisition / Purchasing Document / Supplier Registration Approvals) and Manage Business Unit Data Access for Users → **channel D** (or `dataSecurities` REST for data access).
- "Manage Line Types" and "Manage Shipping Methods" were not found under those exact names: use `fsm_find_task` with a shorter name (e.g. "Line Types") or the REST resources `purchasingLineTypes` / `carriers/{id}/child/shippingMethods`.

## Sources
- Live pod: `GET /fscmRestApi/resources/11.13.18.05/setupTasks?q=TaskName LIKE '%…%'` (see knowledge/channel-b-fsm-csv.md for the API docs).
