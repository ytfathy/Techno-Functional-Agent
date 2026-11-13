# Setup dependency graph (what must exist before what)

> Release: 26D · Built from the knowledge files in this folder (each node links to its file) + TaskCodes verified on the TEST pod (`fsm-task-codes.md`).
> Rule: before creating/changing a node, check that every node it points FROM exists (read it in Fusion). Missing → add it to the plan first, in this order.

## New Business Unit end-to-end (P2P-ready)
```mermaid
flowchart TD
  LOC[Location<br/>locations.md · REST locationsV2 / B PER_MANAGE_LOCATIONS] --> BU
  SET[Reference data set<br/>reference-data-sets.md · REST setIdSets / B FND_MANAGE_REFERENCE_DATA_SETS] --> BU
  LED[Ledger + Legal entity exist<br/>legal-entities-ledgers.md · read-only] --> BF
  BU[Business Unit<br/>business-units.md · B FUN_MANAGE_BUSINESS_UNIT / D] --> BF
  BF[Assign BU business functions<br/>Requisitioning, Procurement, Payables, Receiving, Materials Mgmt…<br/>B FUN_ASSIGN_BUSINESS_UNIT_BUSINESS_FUNCTION / D] --> SETA
  SETA[BU set assignment<br/>REST setIdAssignmentsBusinessUnit / B FUN_MANAGE_BUSINESS_UNIT_SET_ASSIGNMENT] --> PBF
  BF --> PBF[Configure Procurement BF<br/>configure-procurement-bf.md · B PO_CONFIGURE_PROCUREMENT_BUSINESS_FUNCTION]
  BF --> RBF[Configure Requisitioning BF<br/>configure-requisitioning-bf.md · B POR_CONFIGURE_REQUISITIONING_BUSINESS_FUNCTION]
  PBF --> SPR[Service provider relationship req BU ↔ proc BU<br/>service-provider-relationships.md · B FUN_MANAGE_SERVICE_PROVIDER_RELATIONSHIPS]
  RBF --> SPR
  SPR --> AG[Procurement agents<br/>procurement-agents.md · REST procurementAgents]
  SPR --> DA[Data access for users<br/>bu-data-access.md · REST dataSecurities / D]
  PBF --> NUM[Document numbering + styles<br/>B ORA_PO_MANAGE_PROCUREMENT_DOCUMENT_NUMBERING · REST purchasingDocumentStyles]
  AG --> APR[Approval rules<br/>approvals.md · D playbooks/approval-rules.md]
  NUM --> APR
  SUP[Supplier + site in proc BU + assignment to client BU<br/>suppliers.md · REST suppliers] --> TEST
  SPR --> SUP
  APR --> TEST[Test: requisition → PO → receipt<br/>p2p-test-cycle.md]
  DA --> TEST
  INV[Inventory org / ship-to location / receiving params<br/>for goods receipts] --> TEST
```

### Same chain as an ordered checklist
1. **Location** (ship-to / receiving / bill-to flags) — `locations.md`
2. **Reference data set** (or use COMMON / existing) — `reference-data-sets.md`
3. **Ledger + legal entity exist** (read-only; needed for Requisitioning, Payables Invoicing, Receiving, Materials Management, Billing, Customer Payments, Expense, Collections, Project Accounting) — `legal-entities-ledgers.md`
4. **Business Unit** (name, location, manager, default set) — `business-units.md` — HIGH-IMPACT
5. **Assign business functions** (+ primary ledger + default legal entity where required) — HIGH-IMPACT
6. **BU set assignment** (must be saved even with no change) — `reference-data-sets.md`
7. **Configure Procurement Business Function** (procurement BU) — `configure-procurement-bf.md`
8. **Configure Requisitioning Business Function** (requisitioning BU: default procurement BU, deliver-to, destination org, one-time location, conversion rate type) — `configure-requisitioning-bf.md`
9. **Service provider relationship** (requisitioning BU → procurement BU; also client BUs for supplier site assignments) — `service-provider-relationships.md`
10. **Procurement agents** (buyers on the procurement BU) — `procurement-agents.md`
11. **Data access for users** (BU / inventory org) — `bu-data-access.md`
12. **Document numbering** (per sold-to legal entity in 26D) + **document styles** + line types — `configure-procurement-bf.md`, `document-styles.md`, `line-types.md` — numbering HIGH-IMPACT
13. **Approval rules** (requisition / purchasing document) — `approvals.md` — HIGH-IMPACT
14. **Suppliers** with a site in the procurement BU assigned to the requisitioning BU — `suppliers.md`
15. **Test**: requisition → approval → PO → receipt — `p2p-test-cycle.md`

## Supplier
Procurement BU (with Procurement BF) → client BU served by it (service provider) → **supplier** → **address** → **site** (proc BU, on the address) → **site assignment** (client BU + bill-to BU, needs Payables Invoicing on bill-to BU for invoicing) → **contacts** → (bank account: Financials, high-impact, `suppliers.md`). Supplier numbering must be set up (`supplier-setup.md`).

## Requisition
Requisitioning BU with Requisitioning BF → preparer is a user with a person record + requester role + data access → deliver-to location (in the BU's set) → destination org (for inventory destination) → category / item → charge account defaults (expense) → approval rules (or auto-approve).

## Purchase order
Procurement BU with Procurement BF → buyer = procurement agent with Manage Orders on that BU → document style (active) → line type → supplier site (purchasing flag) assigned to the requisitioning (sold-to) BU → ship-to org/location → numbering → approval rules.

## Receipt
Approved, open PO with receipt-required schedule → inventory/receiving org with **receiving parameters** (`receiving-parameters.md`) → for inventory destination: subinventory (+ locator if controlled) (`subinventories-locators.md`) → user with receiving role + inventory org data access.

## Inventory org
Location → management BU + legal entity (+ profit center BU) → item master org (`item-organizations.md`) → inventory org (`inventory-organizations.md`) → org parameters (schedule required) → subinventories / locators → receiving parameters → interorg parameters / shipping networks (`shipping-networks.md`) → transfer orders (`transfer-orders.md`).

## Items
Item master org → item class (UI / B `EGO_MANAGE_ITEM_CLASSES`) → UOMs (`uoms.md`) → catalogs / categories (`procurement-categories-catalogs.md`) → item (`items-item-classes.md`) → org assignment.

## Carrier
Lookups WSH_SERVICE_LEVELS / WSH_MODE_OF_TRANSPORT → **carrier** → **shipping method** (service level + mode) → **organization association** (inventory org) — `carriers.md`.
