# Order Management (basics: parameters, orchestration, pricing, promising, sales order REST/import)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL

## Business purpose
- Order Management (DOO/FOM) captures sales orders (UI, REST, FBDI), prices them (Oracle Pricing), promises them (Global Order Promising), then runs an **orchestration process** per fulfilment line: Schedule -> Reserve -> Ship -> Invoice.
- Affected: order entry specialists, order managers, pricing admins, warehouse (shipping), billing.
- **No "transaction type" setup object like EBS.** Order type is an attribute whose values come from lookup `ORA_DOO_ORDER_TYPES` (no predefined values; add on **Manage Order Lookups**). Order types are used for grouping, routing and processing constraints. Receivables transaction types link is separate (topic "Specify Transaction Types When You Integrate Order Management with Oracle Receivables", not read).

## Where in Fusion (FSM)
- **Manage Orchestration Process Definitions**: Offering **Order Management**, functional area **Orders** (from 23D page; 26D page gives only "Setup and Maintenance" - confirm on pod). Actions > Create; process name gets prefix `CustomDOO_` (<=80 chars incl. prefix), Process Class (e.g. Ship Order Class), Set (Common Set or a set containing the BU), then add steps, then **Deploy**.
- **Manage Order Management Parameters**: task in Setup and Maintenance (offering/functional area not stated on the page: UNVERIFIED; search `fsm_find_task`). Has a **Pricing** button that opens Oracle Pricing parameters.
- **Manage Order Lookups**: Offering Order Management, functional area Orders (per 26B doc snippet): holds `ORA_DOO_ORDER_TYPES`.
- Pricing (work area **Pricing Administration**, Order Management > Pricing Administration; not FSM-driven): tasks **Manage Pricing Profiles, Manage Pricing Segments, Manage Pricing Strategies, Manage Price Lists, Manage Cost Lists, Manage Discount Lists, Manage Shipping Charge Lists, Manage Currency Conversion Lists, Assign Pricing Strategies**; foundation: Manage Pricing Charge Definitions, Manage Price Elements, Manage Pricing Bases, Manage Pricing Parameters, Manage Rounding Rules, Manage Pricing Lookups.
- Global Order Promising (work area **Global Order Promising**, Tasks): **Manage Sourcing Rules**, **Manage Assignment Sets**, **Manage ATP Rules**; plus Setup and Maintenance **Manage Administrator Profile Values** (application Global Order Promising: `MSP_DEFAULT_ASSIGNMENT_SET`, `MSC_SRC_ASSIGNMENT_CATALOG`).
- Setup Task CSV for any of these: UNVERIFIED.

## Prerequisites & dependencies
Chain, in order (see `dependencies.md`):
1. Enterprise structure: ledger, legal entity, **business unit** with Sales/ordering function; reference data sets (Common Set) -> `business-units.md`, `reference-data-sets.md`.
2. Customers (TCA accounts, sites, ship-to/bill-to) and Receivables setup (transaction types, payment terms).
3. Items + inventory org (item validation org), UOM, subinventories -> `items-item-classes.md`, `inventory-organizations.md`.
4. Collect planning data (Global Order Promising needs Collect Planning Data / runtime data) -> then sourcing rule -> assignment set (+ assignment catalog) -> ATP rule -> profile values `MSP_DEFAULT_ASSIGNMENT_SET`, `MSC_SRC_ASSIGNMENT_CATALOG` -> refresh server.
5. Pricing: Pricing foundation (charge definitions, price elements, bases, parameters, rounding) -> profile -> segment -> strategy (create without lists) -> price list / cost / discount / shipping charge / currency conversion lists -> strategy (add lists) -> **Assign Pricing Strategies** -> test on a sales order. All steps optional per roadmap.
6. Order Management Parameters, Manage Order Lookups (order types), order numbering sequences, orchestration prerequisites (task types, status codes, status catalogs), then orchestration process definition -> Deploy -> assign (via business rules / default process by item or order type).
7. Shipping setup (`shipping-execution.md`) for the Ship step.
8. Roles/data access for users (below).

## Key fields
Manage Order Management Parameters (UI labels, from guide):
| Field | Meaning | Notes |
|---|---|---|
| Activate Credit Check on Order Submit / Credit Check Failure at Order Submit | credit check at submit; Draft or hold on failed lines | |
| Start Approval Process for Sales Orders | if No, approval rules not applied | high impact |
| Use Configurator for Order Import Validation, Allow Changes Through Configurator Validation, Halt Configurator Validation on First Error | configurator | |
| Item Validation Organization | org validating items | |
| Number of Processes for Order Import | concurrent Load Interface File for Import; default 4, max 60 | |
| Preparer for Procurement | needed for drop ship purchase requests | per selling BU override |
| Use Pricing Algorithms to Calculate Totals for Sales Order | default No | |
| Use Price on Imported Orders That Oracle Fusion Already Priced | see "Freeze Price on Sales Orders" | |
| Cancel Supply When Canceling Backorders | | |
| Check for Trade Compliance When User Submits Sales Order | | |
| Days to Retry Recovery for Business Events | default 5, max 30 | |
| Enable Orchestration Process Planning and Calculate Jeopardy | | |

Sales order header (`salesOrdersForOrderHub`):
| Field | REST attribute | Notes |
|---|---|---|
| BU | `BusinessUnitId` (req, int64) | |
| Source system | `SourceTransactionSystem` (req, <=50) | e.g. `LEG`, `OPS` |
| Source order id / number | `SourceTransactionId` (req), `SourceTransactionNumber` (req) | |
| Revision | `SourceTransactionRevisionNumber` (req, int64) | PATCH non-nullable; use for revise |
| Order type | `TransactionTypeCode` | lookup `ORA_DOO_ORDER_TYPES` (also seen in doc example) |
| Ordered date | `TransactionOn` (nullable:false on PATCH) | |
| Customer | `BuyingPartyId`, `BuyingPartyNumber`, `BuyingPartyName` | |
| Currency | `TransactionalCurrencyCode` | seen on Requests resource |
| Submit | `SubmittedFlag` | schema default `true`, description says `false`: **set explicitly**; false = Draft |
| Cancel | `CanceledFlag` (default false), `CancelReasonCode`, `CancelReason` | |
| Other | `CustomerPONumber`, `PaymentTermsCode`, `RequestedShipDate`, `PartialShipAllowedFlag`, `FreezePriceFlag`/`FreezeTaxFlag`/`FreezeShippingChargeFlag` (default true), `RevisionSourceSystem`, `OrigSystemDocumentReference`, `PricingDate`, `BatchName` | |
| Children | `lines`, `billToCustomer` (card. 1), `shipToCustomer` (card. 1), `copyOrderReference`, `holds`, `notes`, `payments`, `promotionCodes`, `salesCredits`, `totals`, `attachments`, `additionalInformation` (discriminator `Category`=`DOO_HEADERS_ADD_INFO`) | |

Line (`lines`, POST child):
| Field | REST attribute | Notes |
|---|---|---|
| Item | `ProductId` (req, int64), `ProductNumber` | |
| Qty / UOM | `OrderedQuantity` (req), `OrderedUOMCode` (req, <=3) | |
| Source keys | `SourceTransactionLineId` (req), `SourceTransactionLineNumber` (req), `SourceTransactionScheduleId` (req), `SourceScheduleNumber` (req) | page spells it `SourceScheduleNumber` |
| Ship-from | `RequestedFulfillmentOrganizationCode`/`Id`/`Name` | |
| Date | `RequestedShipDate` | |
| Other | `CancelBackordersFlag`, `CanceledFlag`, `InventoryTransactionFlag`, `DemandClassCode`; children `holds`, `billToCustomer`, `lineDetails`, `charges`, `attachments`, `lotSerials` | |

## Common mistakes
- Assuming `SubmittedFlag` default: always send it. Draft orders are not fulfilled.
- Mixing up `salesOrdersForOrderHub` (path key `OrderKey`, opaque hash: query with `q=`, never build it) and `salesOrdersForOrderHubRequests` (create via request, `OrderRequestId`, `InterfaceStatusCode`, `BatchName`, children incl. `orderPreferences`, `supplier`).
- Orchestration process not deployed / BU not in the process' Set -> order stuck at "Awaiting Scheduling/Shipping".
- Order type values do not exist until added to `ORA_DOO_ORDER_TYPES`.
- Global Order Promising without collected planning data or without `MSP_DEFAULT_ASSIGNMENT_SET`: promising fails / no sourcing.
- Pricing: segment match is attribute based and stops at first match; strategy must have lists added in pass two and be assigned; segment/strategy are looked up when the customer is set.
- Imported orders with price: freeze price rules (parameter above).
- Cancelling backordered line by PATCH of line may error (community report, UNVERIFIED); use action requests.

## Channel & exact technique
- Preferred channel: **A (REST)** for single orders; **C (FBDI)** for bulk import (large volumes); setup (parameters, orchestration, pricing, GOP): **D (UI)** unless pod shows FSM CSV support (B) - no REST found for these.
- A (REST), base `/fscmRestApi/resources/11.13.18.05/`; `rest_describe` first:
  - `salesOrdersForOrderHub`: GET all, GET `/{OrderKey}`, **POST** create (media `application/json`; optional `Upsert-Mode`), **PATCH** `/{OrderKey}` update/revise (send higher `SourceTransactionRevisionNumber` plus `RevisionSourceSystem`), DELETE `/{OrderKey}` (no deletes unless asked; prefer cancel).
  - Actions (POST, collection level): `/action/applyHold`, `/action/releaseHold`, `/action/splitFulfillmentLine`, `/action/updateActualDeliveryDate`, `/action/updateSchedulingAttribute`.
  - Children: `lines` (`/{OrderKey}/child/lines`, PATCH `/lines/{lineid}`), `holds`, `notes`, `payments`, `promotionCodes`, `salesCredits`, `billToCustomer`, `shipToCustomer`, `copyOrderReference`, `additionalInformation`, `totals`, `attachments`.
  - `salesOrdersForOrderHubRequests` POST (26D page confirms path; 26B text): another create path.
  - **Submit a Draft / bulk submit**: POST `salesOrderActionRequests` body `{"ActionCode":"ORA_FOM_SUBMIT_ORDER","requests":[{"HeaderId":<id>}]}`; async: returns `ActionRequestId`, `StatusCode` `PRE_PROCESSING`; poll `salesOrderActionRequests/{id}/child/requests` until `StatusCode`=`COMPLETE`, check `OutcomeCode` SUCCESS/ERROR and `SummaryMessageText`. Cancel lines in bulk: `ActionCode` `ORA_FOM_CANCEL_LINE` with fulfill line ids (from 26A page snippet).
  - **Minimal create** (illustrative; doc shows no official example): `{"SourceTransactionSystem":"OPS","SourceTransactionId":"T1","SourceTransactionNumber":"T1","SourceTransactionRevisionNumber":1,"BusinessUnitId":<bu>,"BuyingPartyId":<party>,"TransactionTypeCode":"<ORA_DOO_ORDER_TYPES value>","TransactionOn":"<ts>","SubmittedFlag":false,"billToCustomer":[{...}],"shipToCustomer":[{...}],"lines":[{"ProductId":..,"OrderedQuantity":1,"OrderedUOMCode":"EA","SourceTransactionLineId":"1","SourceTransactionLineNumber":"1","SourceTransactionScheduleId":"1","SourceScheduleNumber":"1"}]}`. Start with `SubmittedFlag:false`, read back, then submit. Required child attributes of bill-to/ship-to: UNVERIFIED.
  - **Cancel** (header): PATCH `CanceledFlag=true` + `CancelReasonCode` (UNVERIFIED end-to-end). Line: PATCH line `CanceledFlag=true`, `OrderedQuantity=0` (per 25A doc), or action request `ORA_FOM_CANCEL_LINE`.
  - Read-only lookups for setup state: no REST for orchestration definitions found.
- B (FSM CSV): task names above; TaskCodes UNVERIFIED -> `fsm_find_task`.
- C (FBDI/ESS) **Import Sales Orders** (source order import):
  - Template `SourceSalesOrderImportTemplate.xlsm`, object owner Source Sales Order, UCM account `scm/sourceSalesOrder/import`.
  - Tabs/tables: `DOO_ORDER_HEADERS_ALL_INT`, `DOO_ORDER_LINES_ALL_INT`, `DOO_ORDER_ADDRESSES_INT`, `DOO_ORDER_TXN_ATTRIBUTES_INT`, `DOO_ORDER_SALES_CREDITS_INT`, `DOO_ORDER_PAYMENTS_INT`, `DOO_ORDER_LOT_SERIALS_INT`, `DOO_ORDER_DOC_REFERENCES_INT`, `DOO_ORDER_CHARGES_INT`, `DOO_ORDER_CHARGE_COMPS_INT`, `DOO_ORDER_CHARGE_TIERS_INT`, `DOO_ORDER_BILLING_PLANS_INT`, `DOO_ORDER_MANUAL_PRICE_ADJ_INT`, `DOO_ORDER_HDRS_ALL_EFF_B_INT`, `DOO_ORDER_LINES_ALL_EFF_B_INT`, `DOO_ORDER_TERMS_INT`, `DOO_PROJECTS_INT`; control files named `DooOrderHeadersAllInt.ctl` etc. CSV names inside the zip: UNVERIFIED (convention: control file base name).
  - ESS order: (a) **Load Interface File for Import**, Import Process = `Import Sales Orders`, Data File = zip; (b) **Import Sales Orders** (params: Batch Name (recommended), Delete Processed Orders Y/N, optional single filter: Source System / Source Order Number / Customer / Ordered Date within N days / Order Interface Status); (c) optional **Delete Orders from Interface Tables** (Batch Name, Source System, days prior, Order Interface Status; at least one param). Fill `BatchName` in the data.
  - Check errors: Order Management > Manage Order Orchestration Messages.
  - **Price List** FBDI: template `PriceListImportTemplate.xlsm`, UCM `scm/priceLists/import`, process **Import Price List**, control files `QpPriceListsInt.ctl`, `QpPriceListSetsInt.ctl`, `QpPriceListItemsInt.ctl`, `QpPriceListChargesInt.ctl`, `QpPlCompItemsInt.ctl`, `QpPlCoveredItemsInt.ctl`, `QpTierHeadersInt.ctl`, `QpTierLinesInt.ctl`, `QpMatrixDimensionsInt.ctl`, `QpMatrixRulesInt.ctl`. Related templates: Cost Lists, Discount Lists, Price Lists Batch (UCM/process UNVERIFIED).
  - Large volumes: REST create via `salesOrdersForOrderHubRequests` / FBDI (guide chapter "Import > Large Volumes").
- D (UI): Order Management work area (Create Order, Manage Orders), Setup and Maintenance for parameters/orchestration, Pricing Administration, Global Order Promising. No playbook yet.

## Roles
| Role | Code | Notes |
|---|---|---|
| Order Entry Specialist | `ORA_FOM_ORDER_ENTRY_SPECIALIST_JOB` | verified on 26D implementation page |
| Order Administrator | `ORA_DOO_ORDER_ADMINISTRATOR_JOB` | verified on 26D page |
| Pricing Administrator | `ORA_QP_PRICING_ADMINISTRATOR_JOB` | verified on 26D page; guide mentions data role for all BUs (name `QP_PRICING_ADMINISTRATOR_ALL_BUSINESS_UNITS_DATA` from search snippet, UNVERIFIED) |
| Order Manager | `ORA_DOO_ORDER_MANAGER_JOB` | code from search snippet only; 26D role page shows hierarchy (includes Order Entry Specialist, Orchestration Order Management/Monitoring/Scheduling, Order Management Integration Specialist) but no code |
| Shipping Agent | code not on page | UNVERIFIED |
- Order Entry Specialist inherits "Upload data for Source Sales Order Import" (FBDI upload).
- Privilege prefixes: `DOO_`, `FOM_`, `QP_`, `MSP_`, `DOS_`, `CZ_`. Oracle advises copying predefined roles.

## How to verify
- `GET salesOrdersForOrderHub?q=SourceTransactionNumber='T1'&fields=OrderKey,HeaderId,OrderNumber,StatusCode,SubmittedFlag` (attribute names for read: `rest_describe`).
- Order status in Order Management work area; Manage Order Orchestration Messages for errors.
- Action request: `OutcomeCode`=SUCCESS.
- Pricing: create test order for a customer; segment/strategy appear in order dialog.
- GOP: scheduled date/ship-from org on line after submit.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/toc.htm — guide structure
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/manage-order-management-parameters.html — parameters
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/set-up-orchestration-processes.html — orchestration (23D page gives offering/area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/23d/faiom/set-up-orchestration-processes.html)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/overview-of-order-management-cloud.html — setup areas
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/set-up-promising-rules-and-sourcing-rules-for-order-management.html — GOP setup
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/import-orders-into-order-management.html — import procedure
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/job-roles-and-duty-roles-that-you-use-to-implement-order.html — role codes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fammm/Order_Manager_job_roles.html, .../Shipping_Agent_job_roles.html — role hierarchies
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faupr/roadmap-to-manage-oracle-fusion-pricing.html and how-profiles-segments-and-strategies-work-together.html — pricing
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/api-order-management-sales-orders-order-hub.html — paths/actions
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-salesordersfororderhub-post.html, op-salesordersfororderhub-orderkey-patch.html, op-salesordersfororderhub-orderkey-child-lines-post.html, op-salesordersfororderhubrequests-post.html — attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/use-case_SubmitLargeVolSalesOrders_ListOfHeaderIDs.html — action requests (26A-linked 26D slug)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/importsalesorders-3177.html — FBDI import sales orders
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oefsc/pricelist-3258.html — FBDI price list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faiom/manage-lookups-in-order-management.html (26B) — order type lookup
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25a/faiom/cancel-backordered-quantity-during-order-import.html (25A) — cancel via CanceledFlag/qty 0
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26a/fasrp/use-case_CancelLargeVolSalesOrderLinesAcrossOrders.html (26A) — ORA_FOM_CANCEL_LINE

## UNVERIFIED
- FSM offering/functional area for Manage Order Management Parameters, Manage Order Lookups (26D), and the pricing tasks; all TaskCodes; Setup Task CSV support.
- Exact `lines` required attributes beyond those listed (page truncated); required attributes of `billToCustomer`/`shipToCustomer`; real `OrderKey` response fields (HeaderId, OrderNumber, StatusCode names for the GET).
- Header cancel via `CanceledFlag` end-to-end; revise semantics (replace vs merge of children).
- `SubmittedFlag` true/false default (doc conflict).
- Order Manager role code; Shipping Agent code; pricing data role name.
- CSV file names inside the Import Sales Orders zip; ESS job package paths; FBDI for cost/discount lists.
- Order type setup details beyond lookup `ORA_DOO_ORDER_TYPES`; ATP rule creation steps; assignment set creation steps (referenced in `fascp`/`faurp` guides, not read); Manage Pricing Segments page content (26A path seen: Order Management > Pricing Administration > Manage Pricing Segments > Create Pricing Segment Matrix).
- `salesOrderActionRequests` full attribute list (read only through the use-case page).
