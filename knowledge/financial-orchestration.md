# Supply Chain Financial Orchestration (intercompany financial flows)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL

## Business purpose
Supply Chain Financial Orchestration (SFO, code prefix `FOS`) separates the physical movement of goods from the financial/legal ownership change. When a supply chain event happens (shipment, receipt, PO receipt, transfer order shipment/receipt), SFO finds a matching flow and creates the intercompany trade: transfer price, intercompany receivables invoice (seller) and intercompany payables invoice (buyer), trade distributions, profit-in-inventory tracking. Used for global procurement, intercompany sales, internal (interorg) transfers across Profit Center BUs, drop ship. Affects: cost accountants, intercompany/AR/AP, procurement and inventory teams.

SFO runs automatically on events. There is no user "run flow" step; you configure, then transact and monitor.

## Where in Fusion (FSM)
- Offering: **Manufacturing and Supply Chain Materials Management**
- Functional area: **Supply Chain Financial Flows**
- Task names, in the order Oracle recommends (later tasks depend on earlier ones):
  1. Manage Supply Chain Financial Orchestration System Options
  2. Manage Supply Chain Financial Orchestration Documentation and Accounting Rules
  3. Manage Supply Chain Financial Orchestration Transfer Pricing Rules
  4. Manage Profit Center Business Unit Party Relationship (the shipment/global procurement example pages write it as "...Relationships"; use FSM search "Profit Center Business Unit Party")
  5. Manage Supply Chain Financial Orchestration Qualifiers
  6. Manage Supply Chain Financial Orchestration Flows
  7. Manage Drop Ship Financial Flows
- Monitoring (work area, not FSM): Financial Orchestration work area > **Monitor Financial Orchestration Execution** (search by orchestration order number, "View Tasks").
- Scope/parameters: none asked; all are global pages. Flows pick BUs inside the page.
- Redwood: Transfer Pricing Rules page controlled by profile option `ORA_FOS_TRANSFER_PRICING_RULES_REDWOOD_ENABLED` (from 24C readiness); flows page has a Redwood version "Financial Orchestration Flows" (25D readiness). Status of both in 26D: UNVERIFIED.

## Prerequisites & dependencies
Chain in order:
1. Legal entities, ledgers, Business Units with correct business functions; **Profit Center BU** (BU with Profit Center business function) for each node. See `dependencies.md` enterprise structure nodes.
2. Inventory orgs (trade orgs) assigned to the BUs (`knowledge/` inventory org file).
3. Customer and Supplier records representing each legal entity/BU for the intercompany invoice. Oracle: import BUs, customers, suppliers via Export and Import Application Setup, **Financials business objects before MSCM business objects**.
4. Receivables transaction types (invoice type "Intercompany", credit memo type "Credit Memo"), payment terms (e.g. Immediate); bill-to/ship-to customer locations and customer address sets; supplier site "Internal" assigned to the client BU.
5. A service item and an item validation organization (system options).
6. Then SFO tasks 1-7 above.
Depends on this: global procurement POs (sold-to LE != receiving BU), shipment/sales orders across BUs, transfer orders across Profit Center BUs, drop ship, cost accounting (trade events interface to Cost Management).
- When creating/updating a global procurement PO, Procurement checks that a validating flow exists.
- A buyer or seller profile cannot be deleted while the Profit Center BU is a buying BU in any financial route of a flow.

## Key fields
### System Options (page "Manage Supply Chain Financial Orchestration System Options")
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Item Validation Organization | none known | Org used to validate each item against qualifiers | e.g. master/trade org V1 |
| Consider service item for descriptive global purchase order processing | none known | Global procurement flow for description (amount) lines with or without service item | check box |
| Service Item | none known | Service item used by FO tasks | required when above is used |
| Maximum Number of Records per Batch | none known | Records processed per event batch | example 100; performance tuning |
| Calculate tax for trade receipt accrual | none known | Taxes on intercompany accrual | check box |
| Ignore bill only flows | none known | Skip FO for bill-only flows (credit-only returns vs intercompany drop ship SO, bill-only shippable) | check box |
| Process referenced RMA without forward flow as unreferenced | none known | seen in global procurement example | check box |

### Documentation and Accounting Rule
| Field | Meaning | Notes |
|---|---|---|
| Currency Option | Trade currency source | seen values: Buying Node, Source Document |
| Conversion Type | Rate type | e.g. Corporate |
| Trade Distributions / Track Profits In Inventory / Intercompany Invoices | What accounting documents FO creates | global procurement example needs all three |

### Transfer Pricing Rule ("Accounting Transfer Price" dialog)
| Option | Behaviour |
|---|---|
| Transaction Cost Basis | Seller's production cost (standard / layer actual / average of valuation unit). Not supported for nonshippable sales |
| Source Document Price Basis | Procurement: PO line price. Shipment: sales order line price (shipping charges excluded; recurring charge treated one-time; SO lines with recurring charges unsupported). **Internal transfer: not supported.** Drop ship: PO line price by default, check box switches to SO price |
| Item Cost Basis | Item's current cost (Review Item Cost page, cost org, primary cost book) at ownership change; need not be cost processed |
| Pricing Strategy | Oracle Pricing derives price at run time (price list, cost list, discounts) - from 25C/25D pages; 26D UNVERIFIED |
| Markup / markdown % | Applied on the basis; negative = markdown (e.g. +15% on 1.00 = 1.15; -10% example) |
- Multi-node flows: do not mix Item Cost Basis on one node and Transaction Cost Basis on others.
- Transfer-pricing source document basis for back-to-back internal transfers: 26B readiness item (Back-to-Back qualifier); 26D behaviour UNVERIFIED.

### Intercompany buyer / seller profiles (Profit Center BU Party Relationship)
| Profile | Fields seen in official example |
|---|---|
| Buyer profile (PCBU as buyer) | Default Trade Org, Customer, Supplier (number), Procurement BU, Bill-to BU, Customer location for seller's invoice (+ trade org) |
| Seller profile (PCBU as seller) | Default Trade Org, Customer, Supplier, Receivables BU (where seller's AR invoice goes), Customer Address Set, buyer's Procurement BU + Bill-to BU, Supplier Site (e.g. internal site) |
Each PCBU participating as buyer or seller needs the matching profile before it can be used in a flow route.

### Qualifiers (rule deciding when a flow runs)
No qualifier = flow runs for all transactions it receives. Available qualifier attributes by business process type:
- Procurement: Asset Item, Item, Item Class, Purchasing Category, Ship to Organization, Supplier, Supplier Country, Supplier Site Code, User Item Type, User-Defined Category.
- Shipment: Asset Item, Bill to Country, Bill to Party, Financial Orchestration Category, Item, Item Class, Order Type, Purchasing Category, Ship from Organization, Ship to Address, Ship to Country, Ship to Party, Sold to Country, Sold to Party, User Item Type, User-Defined Category.
- Internal Transfer: Asset Item, Destination Type, Financial Orchestration Category, Item, Item Class, Ship from Organization, Ship to Organization, User Item Type, User-Defined Category.
- Drop Shipment: Asset Item, Bill to Country/Party, FO Category, Item, Item Class, Order Management Business Unit, Order Type, Purchasing Category, Ship to Address/Country/Party, Sold to Country/Party, Supplier, Supplier Country, Supplier Site Code, User Item Type, User-Defined Category.
- Nonshippable Sales: Asset Item, Bill to Country/Party, FO Category, Item, Item Class, Order Type, Sold to Country/Party, User Item Type, User-Defined Category.

### Flows
| Field | Meaning | Notes |
|---|---|---|
| Name, Business Process Type | Flow type | **Procurement** (start = Sold-to BU, end = Receiving BU), **Shipment** (Shipping BU -> Selling BU), **Internal Transfer** (Shipping BU -> Receiving BU). Qualifier tables also name Drop Shipment and Nonshippable Sales (drop ship has its own task "Manage Drop Ship Financial Flows") |
| Qualifier | Link to qualifier | optional |
| Priority | Ranks flows against each other | shipment example uses 1; ordering semantics not documented (UNVERIFIED) |
| Effective start date | When flow applies | source docs created before the date can still be processed by the modified flow |
| Primary route | Start BU (internal seller) -> end BU (internal buyer) | >= 1 per flow |
| Financial route | Terms between selling and buying BU: transfer pricing rule, documentation and accounting rule, buying trade org, sell-side/buy-side tax determinants (optional), **Receivables Invoice Type, Credit Memo Type, Payment Terms (required when intercompany invoices created)** | each primary route needs >= 1; add more for intermediary BUs. UI: "Simplified view" default; check box "Separate Primary and Financial route" |

## Effect on POs and transfer orders
- **Global procurement PO**: receiving BU and sold-to LE on the PO are different. Sold-to LE (PO line) owns supplier liability and pays the supplier; receiving BU gets goods. Bill-to BU is not supplied by FO; Procurement derives it from the supplier site assignment of the client BU. Receipt triggers: seller books intercompany COGS + intercompany AR invoice (cost/PO price +/- markup); buyer books intercompany accrual + intercompany AP invoice. Example: PO $1000, 10% markup -> $1100 intercompany invoice.
- **Transfer orders** (interorg, intraorg, intercompany): TO shipment/receipt events come from Inventory/Receiving. If sender and receiver are in different Profit Center BUs and an Internal Transfer flow exists, FO adds Trade in Transit Issue, Trade Receipt Accrual, Trade in Transit Receipt events (26A accounting example). Transfer price via transaction cost, Oracle Pricing, or third-party service (registered web service).
- **Shipment flow**: shipping BU sells through intermediary BUs to selling BU; each leg its own price/currency/invoice.

## Common mistakes
- Creating a flow before the transfer pricing rule / documentation rule / party relationships exist (flow task cannot reference them).
- Missing intercompany buyer or seller profile on a PCBU: flow route cannot be saved.
- Not importing Financials objects (customers/suppliers/BUs) first.
- Missing receivables invoice type / credit memo type / payment terms on a financial route while "Intercompany Invoices" is on.
- Using Source Document Price Basis for Internal Transfer (unsupported); Transaction Cost Basis for nonshippable sales (unsupported); mixing cost bases across nodes.
- No qualifier + several flows of the same type: every transaction matches; set qualifiers/priority deliberately.
- Editing a flow and expecting history re-processing; effective start date governs.
- Deleting a buyer/seller profile still used as a buying BU in a route.

## Channel & exact technique
- Preferred channel: **D (UI)** for all setup (rules, relationships, qualifiers, flows). No business REST for setup objects found in 26D docs; FSM CSV support for these tasks not confirmed. Read-only/ops tracking is possible by REST (below).
- A (REST, `/fscmRestApi/resources/11.13.18.05/`) - operational only, from 26D SCM REST endpoint list:
  - `financialOrchestrationTransferPriceforShipments` (GET, POST); action `POST .../financialOrchestrationTransferPriceforShipments/action/calculateTransferPrice`; GET one `/{financialOrchestrationTransferPriceforShipmentsUniqID}`
  - `financialOrchestrationSourceTransactionEvents` (GET, POST; GET/PATCH/DELETE one); child `TransactionEventLog` (GET, POST; one GET/PATCH/DELETE). Privilege `FOS_IMPORT_EXTERNAL_TRADE_EVENTS_WEB_SERVICE_PRIV` (for external source apps, not for ordinary use).
  - `financialOrchestrationDropshipEvents` (GET; one; child `financialTradeRelationships` GET)
  - `financialOrchestrationUnidentifiedEvents` (GET; one) - events with no matching flow; first thing to check when invoices are missing.
  - Transfer prices GET resource `financialOrchestrationTransferPrices` and LOVs `financialOrchestrationShipToLocationsLOV`, `financialOrchestrationCountryOfOriginsLOV`, `financialOrchestrationOrchestrationStatusLOV` appear in 26B list; 26D presence UNVERIFIED. Always `rest_describe`.
- B (FSM CSV): UNVERIFIED. Run `fsm_find_task` for the 7 task names; if a TaskCode comes back, test `fsm_export`.
- C (FBDI/ESS): none found for flows/rules. No SFO-specific ESS job name confirmed (UNVERIFIED); events are processed by the system, errors surface in Monitor Financial Orchestration Execution.
- D (UI): no playbook yet; save one after first successful run (`playbooks/financial-orchestration-flow.md`).

## How to verify
- Open each created object in its manage page; flow shows primary + financial routes with rules.
- Functional test: global PO receipt / shipped sales order / interorg transfer order. Then Monitor Financial Orchestration Execution (status, View Tasks) and GET `financialOrchestrationUnidentifiedEvents` (should be empty for the test).
- Check intercompany AR/AP invoices and cost accounting trade events.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fauso/overview-of-supply-chain-financial-orchestration.html - rules/objects overview (26D book "Using Supply Chain Financial Orchestration" opens; text identical in 26B copy)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implement-supply-chain-financial-orchestration.html - offering, functional area, task order, import prerequisite
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/financial-orchestration-flow.html - event processing steps, integrated applications
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/financial-orchestration-system-options.html - system option fields
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/financial-orchestration-qualifiers.html - qualifier attributes per process type
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/financial-orchestration-flows.html - process types, routes, financial route fields, effective date, rules
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/accounting-transfer-price.html - transfer price options and restrictions
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/global-procurement-flow.html - procurement flow example, PO effect, party profile fields
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/shipment-flow.html - shipment flow example, monitor page
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/when-can-i-delete-an-intercompany-buyer-or-seller-profile.html - delete rule
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html - financialOrchestration* REST resources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fasrp/Roles_and_Privileges.html - `FOS_IMPORT_EXTERNAL_TRADE_EVENTS_WEB_SERVICE_PRIV` (26B)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/fapma/example-of-accounting-of-interorganization-transfers.html - transfer order trade events (26A, seen only in search snippet)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/24c/inv24c/24C-inventory-wn-f33533.htm - Redwood transfer pricing profile option (snippet)

## UNVERIFIED
- Exact TaskCodes for the 7 tasks; Setup Task CSV support for any of them.
- Job role / duty roles for SFO setup and monitoring (no role code found; likely Supply Chain Application Administrator / Cost Accountant, not confirmed). Only privilege confirmed: `FOS_IMPORT_EXTERNAL_TRADE_EVENTS_WEB_SERVICE_PRIV` (26B REST doc).
- Any SFO-specific ESS scheduled process name.
- Business REST for flows, rules, qualifiers, party relationships (none found).
- "Manage Intercompany Organizations" and supplier-customer associations: that is the Financials Advanced Global Intercompany feature; not researched; SFO uses Profit Center BU Party Relationship instead.
- Priority semantics between flows; Pricing Strategy and Redwood details in 26D; 26D presence of `financialOrchestrationTransferPrices` and the three LOV resources.
- Page content of the 26D `fauso` book was read only at overview level (other chapters returned landing page); detail comes from the `faims` book 26D pages.

## VERIFIED-ON-POD 2026-11-25
- All setup tasks of this area report `CSVExportImportSupportedFlag=Y` on the 26D pod → channel B is available (TaskCodes in `fsm-task-codes.md`); the UI is only the fallback.
