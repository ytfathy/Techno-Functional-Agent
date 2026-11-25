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

## Added 2026-11-25 (verified on the new TEST pod fa-eteo via `fsm_find_task`)
| Task name | TaskCode | CSV (channel B) |
|---|---|---|
| Manage Supply Chain Financial Orchestration System Options | ORA_FOS_MANAGE_SYSTEM_OPTIONS | Y |
| Manage Supply Chain Financial Orchestration Documentation and Accounting Rules | ORA_FOS_DEFINE_TRADE_AND_ACCOUNTING_RULES | Y |
| Manage Supply Chain Financial Orchestration Transfer Pricing Rules | ORA_FOS_DEFINE_TRANSFER_PRICING_RULES | Y |
| Manage Profit Center Business Unit Party Relationship | ORA_FOS_DEFINE_PROFIT_CENTER_BUSINESS_UNIT_PARTY_RELATIONSHIP | Y |
| Manage Supply Chain Financial Orchestration Qualifiers | ORA_FOS_MANAGE_TRADE_QUALIFIER | Y |
| Manage Supply Chain Financial Orchestration Flows | ORA_FOS_MANAGE_SUPPLY_CHAIN_FINANCIAL_TRADE_AGREEMENTS | Y |
| Manage Drop Ship Financial Flows | ORA_FOS_MANAGE_DROP_SHIP_AGREEMENTS | Y |
| Manage Facility Schedules | RCS_MANAGE_FACILITY_SCHEDULES | Y |
| Manage Plant Parameters | ORA_RCS_MANAGE_PLANT_PARAMETERS | Y |
| Manage Descriptive Flexfields | FND_MANAGE_DESCRIPTIVE_FLEXFIELDS | Y |
| Manage Extensible Flexfields | FND_MANAGE_EXTENSIBLE_FLEXFIELDS | Y |
| Manage Key Flexfields | FND_MANAGE_KEY_FLEXFIELDS | Y |
| Manage Value Sets | FND_MANAGE_VALUE_SETS | Y |
| Manage Inventory Descriptive Flexfields | INV_MANAGE_INVENTORY_DESCRIPTIVE_FLEXFIELDS | Y |
| Manage Inventory Locator Key Flexfield | INV_MANAGE_INVENTORY_LOCATOR_KEY_FLEXFIELD | Y |
| Deploy Item Extensible Flexfields | EGO_DEPLOY_EFFS | Y |

Note: Supply Chain Financial Orchestration setup is CSV-enabled (channel B), although the docs only describe the UI. Flexfield *deploy* stays a UI action even when the segment setup is exported/imported by CSV.

### Cost, inventory transactions, shipping, order management (added 2026-11-25, same pod)
| Task name | TaskCode | CSV (channel B) |
|---|---|---|
| Manage Cost Organizations | CST_MANAGE_COST_ORGANIZATIONS | Y |
| Manage Cost Books | CST_MANAGE_COST_BOOKS | Y |
| Manage Cost Organization Relationships | CST_MANAGE_COST_ORGANIZATION_RELATIONSHIPS | Y |
| Manage Valuation Structures | CST_MANAGE_VALUATION_STRUCTURES | Y |
| Manage Valuation Units | CST_MANAGE_VALUATION_UNITS | Y |
| Manage Cost Profiles | CST_MANAGE_COST_PROFILES | Y |
| Manage Default Cost Profiles | CST_MANAGE_DEFAULT_COST_PROFILES | Y |
| Manage Item Cost Profiles | CST_MANAGE_ITEM_COST_PROFILE | Y |
| Manage Cost Elements | CST_MANAGE_COST_ELEMENTS | Y |
| Manage Account Aliases | INV_MANAGE_ACCOUNT_ALIASES | Y |
| Manage Item Transaction Defaults | INV_MANAGE_ITEM_TRANSACTION_DEFAULTS | Y |
| Manage Material Statuses | INV_MANAGE_MATERIAL_STATUSES | Y |
| Manage ABC Classes | INV_MANAGE_ABC_CLASSES | Y |
| Manage ABC Classification Sets | INV_MANAGE_ABC_CLASSIFICATION_SETS | Y |
| Manage ABC Assignment Groups | INV_MANAGE_ABC_ASSIGNMENT_GROUPS | Y |
| Manage Release Sequence Rules | WSH_MANAGE_RELEASE_SEQUENCE_RULES | Y |
| Manage Ship Confirm Rules | WSH_MANAGE_SHIP_CONFIRM_RULES | Y |
| Manage Pick Slip Grouping Rules | INV_MANAGE_PICK_SLIP_GROUPING_RULES | Y |
| Manage Pick Wave Release Rules | WSH_MANAGE_PICK_WAVE_RELEASE_RULES | Y |
| Manage Shipping Parameters | WSH_MANAGE_SHIPPING_PARAMETERS | Y |
| Manage Shipping Zones | WSH_MANAGE_SHIPPING_ZONES | Y |
| Manage Shipping Document Job Set Rules | ORA_MANAGE_SHIPPING_DOCUMENT_JOB_SET_RULES | N |
| Manage Orchestration Process Definitions | DOO_MANAGE_ORCHESTRATION_PROCESS_DEFINITIONS | Y |
| Manage Order Management Parameters | ORA_FOM_MANAGE_ORDER_MANAGEMENT_SYSTEM_PARAMETERS | Y |
| Manage Order Lookups | DOO_MANAGE_ORCHESTRATION_LOOKUPS | Y |

Notes: Cost Accounting setup (cost orgs, books, valuation, profiles) is CSV-enabled → channel B, although the docs show only the UI. "Manage Transaction Source Types" / "Manage Transaction Reasons" not found under those names (search shorter names). Manage Shipping Document Job Set Rules = CSV N → channel D.
