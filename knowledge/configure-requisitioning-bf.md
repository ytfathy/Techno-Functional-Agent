# Configure Requisitioning Business Function

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Per-requisitioning-BU defaults and behavior for requisitions and for POs created from them. It covers the deliver-to org, default line type, one-time address handling, import grouping, reapproval and approval override, the default procurement BU, price change tolerance, the PO ship-to fallback, cancel-unfulfilled-demand, multiple-LE control, and UOM conversion during agreement sourcing. It affects requesters, approvers, buyers and the sold-to LE derivation.

## Where in Fusion (FSM)
- Offering: Procurement
- Functional area: Procurement Foundation (listed under "Configure Requisitioning Business Function" in the Purchasing Configuration chapter)
- Task name: **Configure Requisitioning Business Function**
- Scope prompt: select the Requisitioning BU (dialog title UNVERIFIED; by analogy with "Specify Procurement BU" it is probably "Specify Requisitioning BU")
- Sections: **Requisitioning** and **Purchasing**

## Prerequisites & dependencies
- The BU has the **Requisitioning** business function. Manage Business Unit > Actions > **Assign Business Functions**. Requisitioning creates financial transactions, so the BU needs a **primary ledger** and a **default legal entity**.
- A procurement BU exists with a service provider relationship to this requisitioning BU (needed for Default Procurement BU). See `service-provider-relationships.md`.
- Global locations enabled for the requisitioning BU (One-Time Location, Ship-to Location). An inventory org exists for Default Deliver-to Organization. Line types exist. Requisition DFF contexts exist if used.
- Users need data access: **Manage Business Unit Data Access for Users** (Procurement > Users and Security), with Security Context = Business unit and Security Context Value = the requisitioning BU. Without it they get POR-2010674.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| **Requisitioning section** | | | |
| Default Deliver-to Organization | — | Deliver-to org for a req line (global location). Drives which item master items requesters see | Also the last fallback for sold-to LE when Multiple Legal Entities on Order = Error |
| Line Type | `requisitioningOptions.LineTypeId` (read-only) | Default req line type; can be changed on the line | e.g. Goods |
| One-Time Location | — | Location code defaulted as deliver-to for an unstructured one-time address | Must be a global location enabled for the req BU. Ignored when structured one-time addresses are enabled |
| Group Requisition Import By | — | Default Group-by for the Import Requisition process: None, Buyer, Category, Item, Location, Supplier | Grouping order: header number, then Group Code, then this value |
| Allow one-time addresses | `requisitioningOptions.AllowOnetimeAddrFlag` (read-only) | Requesters may enter an ad hoc delivery address | Structured format needs feature "Capture One-Time Address in Structured Format" (Edit Features: Self Service Procurement), enabled for the BU |
| Reapproval required for changes made during an active approval process | — | Approver edits send the req back for reapproval | |
| Create orders immediately after requisition import | — | Runs Generate Orders right after import | |
| Approval required for buyer modified lines | — | Buyer edits on a req line trigger approval | |
| Enable approval override | `requisitioningOptions.EnableApproverOverrideFlag` (read-only) | Allows approver override | |
| Enable Supply Availability Details for Internal Transfers | — | Shows supply-source availability in the Select Supply Source dialog | Internal transfer lines |
| Context Values for Requisition Descriptive Flex-fields (header / line / distribution) | `HeaderDffContextCode`, `LineDffContextCode`, `DistributionDffContextCode` (read-only) | DFF context pulled in on requisitions | |
| **Purchasing section** | | | |
| Default Procurement BU | `requisitioningOptions.DefaultProcurementBUId` (read-only) | Procurement BU used when none can be determined from the req line | Must be a service provider of this req BU |
| Price Change Tolerance (percentage and/or amount) | — | Max PO price change versus the req line. Null means no check. The more restrictive of % and amount wins | PO can't be submitted if outside tolerance |
| Ship-to Location | — | PO ship-to fallback when the PO can't derive one | Also fallback #2 for PO "Default Ship-to Location", after the supplier site assignment |
| Cancel Unfulfilled Demand | — | Always / Never / Optional: whether PO cancel also cancels backing req demand | |
| Multiple Legal Entities on Order | — | Allow / Warning / Error: whether one PO may span ship-to orgs of different LEs | Drives sold-to LE: Allow/Warning = LE of req BU (centralized). Error = LE of the deliver-to inventory org (decentralized) |
| Allow Requisition-To-Agreement UOM Conversion | — | Agreements with a different line UOM can still be sourced | |
| Conversion rate type | `requisitioningOptions.ConversionRateType` (read-only) | Default rate type of the req BU | UI label/location UNVERIFIED |

### Sold-to legal entity derivation (PO)
1. If Supply Chain Financial Orchestration is implemented, the LE comes from the matched financial orchestration flow.
2. Otherwise, with Multiple Legal Entities on Order = Allow or Warning, the LE of the requisitioning BU is used.
3. With Error, the LE of the inventory org is used. Fusion looks for it in this order: the req line deliver-to location's inventory org, then the requester preference deliver-to location's inventory org, then Default Deliver-to Organization.
The sold-to LE is also the **PO numbering determinant**.

## Common mistakes
- Default Procurement BU is not a service provider of this req BU, so requisitions can't be processed.
- One-Time Location is not a global location enabled for the req BU.
- Expecting One-Time Location to apply with structured one-time addresses. It is ignored then.
- Multiple Legal Entities on Order = Error in a centralized model, which gives an unexpected sold-to LE and PO numbering sequence.
- The Requisitioning function was assigned but the BU has no primary ledger or default LE.
- Users not given BU data access, which raises POR-2010674.

## Channel & exact technique
- Preferred channel: **D (UI)**. No 26D REST write resource exists. B (FSM CSV) is UNVERIFIED.
- A (REST), read-back only: `GET /fscmRestApi/resources/11.13.18.05/requisitionPreferences/{requisitionPreferencesUniqID}/child/requisitioningOptions[/{RequisitioningBUOptionsId}]`. Exposes `RequisitioningBUId`, `RequisitioningBUOptionsId`, `DefaultProcurementBUId`, `LineTypeId`, `AllowOnetimeAddrFlag`, `EnableApproverOverrideFlag`, `ConversionRateType`, `HeaderDffContextCode`, `LineDffContextCode`, `DistributionDffContextCode`, `FunctionalCurrencyCode`, `ChartOfAccountId`, `PurchasingCategorySetId`. It is scoped to the calling user's requisition preferences. Deliver-to org is not exposed.
- B (FSM CSV): TaskCode UNVERIFIED. Check Actions > Export to CSV File on the task row.
- C: the ESS **Configure Basic Enterprise Structure for Procurement** assigns the Requisitioning function to every BU (greenfield only).
- D (UI): `playbooks/configure-requisitioning-bf.md`

## How to verify
- Reopen the task and screenshot both sections.
- REST read-back of `requisitioningOptions` as a requester of that BU.
- Functional test: create a req and check deliver-to org, line type and one-time address. Convert it to a PO and check procurement BU, ship-to and sold-to LE.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-configure-business-units-with-requisitioning-business.html — all field labels and meanings
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-the-sold-to-legal-entity-is-determined.html — sold-to LE logic
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-purchasing-document-header-defaults-work.html — Default Ship-to Location fallback
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html — Assign Business Functions check, BU data access, POR-2010674
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/business-functions.html — Requisitioning needs primary ledger and default LE
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-define-procurement-document-numbering.html — requisition numbering per Requisitioning BU
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-requisition-preferences-requisitioning-options.html — read-only REST operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-requisitionpreferences-requisitionpreferencesuniqid-child-requisitioningoptions-get.html — attribute names

## UNVERIFIED
- Scope dialog title when opening the task.
- UI label and location of the conversion rate type on this page (REST exposes `ConversionRateType`).
- Emergency requisition / emergency PO number reservation settings: not on the 26D page. Probably not configured here.
- Whether "Next Requisition Number" / "Next Purchase Order Number" fields still exist (13.1 only; 26D uses Manage Procurement Document Numbering).
- FSM Setup Task CSV support and TaskCode.
