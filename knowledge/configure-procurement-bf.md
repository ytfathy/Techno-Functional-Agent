# Configure Procurement Business Function

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Per-procurement-BU defaults and controls for purchase orders, blanket and contract agreements, and sourcing. These include currency, payment, freight and FOB terms, inventory (item master) org, price break type, receipt close point and tolerance, match approval level, requisition grouping for automatic PO creation, buyer managed transportation, terms and conditions, and contract terms layouts. Affects buyers, the requisition-to-PO automation (Generate Orders), and any document created in the procurement BU.
Oracle has no single 26D page that lists every field. The field list below comes from the topics under "Define Procurement Configuration Options", the header-defaults table, and the BICC extract PVO.

## Where in Fusion (FSM)
- Offering: Procurement
- Functional area: Procurement Foundation
- Task name: **Configure Procurement Business Function**
- Scope prompt: **Specify Procurement BU** dialog. Select **Procurement BU**, then click **OK**.
- Page layout: **Main** tab, with a **General** section and a **Purchasing** section. The Purchasing section label is confirmed in the buyer-managed-transportation steps. A Sourcing section existed in older releases (UNVERIFIED for 26D).
- Related task: **Manage Procurement Document Numbering** (Procurement offering > Procurement Foundation). In 26D, document numbering is defined here, not by "Next ... Number" fields.

## Prerequisites & dependencies
- The BU exists and has the **Procurement** business function assigned (Manage Business Unit > Actions > **Assign Business Functions**, or the **Assign Business Unit Business Function** task).
- The item master / inventory organization exists. It is chosen once here and must never be changed afterwards.
- Currencies, payment terms, FOB, freight terms and shipping methods exist.
- Standard terms and conditions and the contract terms layout (BI Publisher RTF) exist if you use them.
- Feature opt-ins: **Buyer Managed Transportation** (Offerings > Procurement > Procurement functional area). "Generate Separate Purchase by Ship-To Location" exposes the Use ship-to location check box.
- Downstream: service provider relationships (client requisitioning BUs), supplier sites (owned by the procurement BU), procurement agents (per procurement BU), POs/BPAs/CPAs, and the Initiate Retroactive Price Update ESS process.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Inventory Organization (General) | BICC `InventoryOrganizationId` | Item master org for the procurement BU | Set once. Docs: "Do not change ... after you have assigned it." |
| Currency (General) | BICC `CurrencyCode` | Default currency on BPA/CPA when the supplier site has no invoice currency | PO currency comes from the supplier site, then the sold-to LE ledger, not from here |
| Payment Terms (General) | BICC `TermsId` | Default terms when the supplier agreement or site has none | Fallback #3 on PO, #2 on BPA/CPA |
| Buyer (General) | BICC `DefaultBuyerId` | Default buyer | UNVERIFIED label in 26D (13.1 quick start only) |
| Line Type (General) | BICC `LineTypeId` | Default PO line type | UNVERIFIED label in 26D (13.1 quick start only) |
| Conversion Rate Type | BICC `DefaultRateType` | Rate type default | UNVERIFIED label. PO header rate type comes from EMU Fixed, then Common Payables and Procurement Configuration of the sold-to BU, then Corporate |
| Buyer managed transportation (General, check box) | BICC `BuyerManagedTransportFlag` | BU intends to manage transportation | Doc-confirmed label and location. Needs the feature opt-in. Defaults after source agreement and supplier site |
| FOB | BICC `FobLookupCode` | Default FOB | After supplier site |
| Freight Terms | BICC `FreightTermsLookupCode` | Default freight terms | After supplier site |
| Shipping Method | BICC `CarrierId` / `ModeOfTransport` / `ServiceLevel` | Default shipping method | After source agreement and supplier site. BICC column mapping is inferred |
| Default promised date from requested date (Purchasing, check box) | BICC `DefaultPromiseDate` | Promised date = requested date | Doc-confirmed label |
| Price Break Type | BICC `PriceBreakLookupCode` | Cumulative Pricing / Non-Cumulative Pricing for BPAs | Cumulative can't be used with global agreements |
| Receipt Close Point | BICC `ReceiveCloseCode` | Accepted / Delivered / Received | Set together with the tolerance |
| Receipt Close Tolerance Percent | BICC `ReceiveCloseTolerance` | % short of ordered quantity allowed while still auto-closing for receipt | Override possible on items and orders |
| Match Approval Level | BICC `ReceivingFlag`/`MatchOption`? | Two-Way / Three-Way / Four-Way | Independent of invoice match option (Order vs Receipt). BICC mapping UNVERIFIED |
| Invoice match option | BICC `MatchOption` | Order / Receipt | UNVERIFIED that it is on this page |
| Invoice close tolerance | BICC `InvoiceCloseTolerance` | Close-for-invoicing tolerance | UNVERIFIED label |
| Group requisitions (check box) | BICC `GroupRequisitions` | Consolidate requisition lines from many requisitions into one PO | Grouping keys: req BU + sold-to LE, style, supplier/site, currency/rate, buyer, import source, BMT, shipping method, tax attributes |
| Group requisition lines (check box) | BICC `GroupRequisitionLines` | Combine req lines into one PO line | Keys: line type, item/rev/desc, category, UOM, source agreement line, negotiated, work order product |
| Use requested date (check box) | BICC `UseNeedByDate` | Requested date becomes a line-grouping key | |
| Use ship-to organization and location (check box) | BICC `UseShipTo` | Ship-to org/location becomes a line-grouping key | |
| Use ship-to location (check box) | BICC `UseShipToForGroupReqs` | Ship-to location becomes a header-grouping key | Visible only with the "Generate Separate Purchase by Ship-To Location" feature |
| Use customer sales order (check box) | BICC `UseSalesOrderNumberFlag` | Sales order becomes a grouping key; also defaults on agreements | |
| Automatically generate orders | BICC `GenerateOrdersAutomatic` | Default for BPA/CPA header flag | |
| Automatically submit for approval | BICC `SubmitApprovalAutomatic` | Default for BPA/CPA header flag | |
| Allow manual price update on fulfilled orders | BICC `AllowManulPriceUpdateOrder` (sic) | If deselected, retroactive repricing skips received/invoiced schedules | Doc-confirmed label (Initiate Retroactive Price Update) |
| Retroactive pricing option | BICC `AllowRetroPricing` | All orders vs open orders only | UI label UNVERIFIED. BPA header defaults are fixed: "Enable retroactive pricing" = Selected, "Reprice open orders only" = Selected |
| Aging Onset Point / Aging Period Days | BICC `AgingOnsetPoint` / `AgingPeriodDays` | Consignment aging defaults for BPA/CPA | After supplier site |
| Enable automatic sourcing / Punchout requests only | — | CPA header defaults | Doc table alignment unclear |
| Communication method (change orders) | BICC `CommunicateCoFlag`? | Default for change orders | Mapping UNVERIFIED |
| Maximum attachment size | BICC `MaxAttachmentSize` | Max file size MB | Label from 13.1 only (UNVERIFIED) |
| Standard terms and conditions (+ **Disable terms and conditions for all languages**) | — | T&C text sent with every PO/agreement | Doc-confirmed |
| Contract terms layout (per document type) | — | BI Publisher RTF layout for printed docs | Doc-confirmed concept; exact label UNVERIFIED |
| Default document style | BICC `StyleId` | — | UNVERIFIED. Docs say a new document's style defaults to the "Standard Style" display name per document type |

### Document numbering (Manage Procurement Document Numbering)
| Document Type | Determinant Type |
|---|---|
| Purchase Order | Sold-to Legal Entity |
| Purchase Agreement | Procurement BU |
| Requisition | Requisitioning BU |
| Negotiation | Procurement BU |
| Assessment | Procurement BU |
| Initiative | Procurement BU |
| Qualification | Procurement BU |

A sequence is unique per Document Type + Determinant Type + Determinant Value. If none is defined, Fusion creates one on the first transaction and starts at 1. PO numbering is per **sold-to LE**, not per procurement BU.

## Common mistakes
- Changing Inventory Organization after go-live. Docs forbid it.
- Expecting PO currency or rate type to come from this page. The PO takes them from the supplier site, the sold-to LE ledger, and Common Payables and Procurement Configuration.
- Leaving Receipt Close Point set without a tolerance, or the reverse. Both are needed.
- Choosing Cumulative pricing on a global BPA. Not allowed.
- Looking for "Next PO Number" here. In 26D use Manage Procurement Document Numbering. PO numbering is per sold-to LE.
- Enabling Buyer managed transportation without first opting into the feature.
- Group requisitions on, but documents differ in style, currency or buyer. Lines won't group.

## Channel & exact technique
- Preferred channel: **D (UI)**. No 26D business REST resource exists to read or write the Procurement Business Function configuration (none found in the 26D REST catalog). FSM CSV support is UNVERIFIED (B).
- A (REST): none for write. Read-only proxies: purchasing documents show the resulting defaults. BICC data store `FscmTopModelAM.PrcExtractAM.PoBiccExtractAM.PurchasingSystemParameterExtractPVO` (one row per `PrcBuId`) for read-back.
- B (FSM CSV): TaskCode UNVERIFIED. Check in Setup and Maintenance whether **Actions > Export to CSV File** is enabled on the task row (it is disabled when unsupported). If supported, use `POST /fscmRestApi/resources/11.13.18.05/setupTaskCSVExports` with `{"TaskCode":"<code>","SetupTaskCSVExportProcess":[{"TaskCode":"<code>"}]}`.
- C (FBDI/ESS): none. The ESS **Configure Basic Enterprise Structure for Procurement** (privilege `PO_MANAGE_BASIC_ENTER_STRUC_PRIV`; params Centralized Procurement Business Unit Name, Currency) creates a procurement BU, sets its BF currency, and makes it service provider to all BUs. Run once on greenfield only.
- D (UI): `playbooks/configure-procurement-bf.md`

## How to verify
- Reopen the task for the BU and screenshot the Main tab.
- Functional test: create a BPA without a supplier-site currency and check that Currency, Payment Terms and FOB default from here. Run requisition-to-PO (Generate Orders) and check grouping.
- BICC extract `PurchasingSystemParameterExtractPVO` filtered on `PrcBuId`.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-set-up-buyer-managed-transportation.html — task navigation, Specify Procurement BU dialog, Main tab / General / Purchasing sections, Buyer managed transportation, Default promised date from requested date
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/price-break-types.html — price break types, task location
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-choose-an-inventory-organization.html — inventory org, do not change
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/receipt-close-point.html — receipt close point values
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-s-a-receipt-close-tolerance-percent.html — tolerance
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/match-approval-level-options.html — 2/3/4-way
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/group-requisitions-options.html — grouping check boxes and keys
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/standard-purchasing-terms-and-conditions.html — T&C, Disable terms and conditions for all languages
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-s-a-contract-terms-layout.html — contract terms layout
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-define-procurement-document-numbering.html — numbering task, determinant table
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-purchasing-document-header-defaults-work.html — which header attributes default from Procurement BF config
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/initiate-retroactive-price-update.html — Allow manual price update on fulfilled orders
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/configure-basic-enterprise-structure-for-procurement.html — ESS alternative
- https://docs.oracle.com/en/cloud/saas/procurement/26b/oadpr/PurchasingSystemParameterExtractPVO.html — BICC column names (26B; 26D page not reachable)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Task_CSV_Export.html — setupTaskCSVExports REST
- https://docs.oracle.com/cloud/131/user_services/FASUP/F886527AN134A7.htm — 13.1 quick start (Buyer, Line Type, Maximum File Size, Next Agreement/Negotiation Number). Old release, used only as UNVERIFIED hint

## UNVERIFIED
- Exact 26D UI labels and sections for: Buyer, Line Type, Conversion Rate Type, invoice match option, invoice close tolerance, retroactive pricing option, communication method, maximum attachment size, contract terms layout, default document style.
- Whether a Sourcing section, Next Agreement Number or Next Negotiation Number still exist on the 26D page (13.1 only; 26D uses the numbering task).
- Mapping of BICC columns `ReceivingFlag`, `MatchOption`, `CarrierId`, `ModeOfTransport`, `ServiceLevel` and `CommunicateCoFlag` to UI fields.
- Whether "Enable automatic sourcing" and "Punchout requests only" default from Procurement BF for CPA only. The doc table alignment is unclear.
- FSM Setup Task CSV export/import support and TaskCode for Configure Procurement Business Function.
- Whether Manage Procurement Document Numbering supports CSV (TaskCode unknown).
