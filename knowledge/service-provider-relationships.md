# Service Provider Relationships (Requisitioning BU to Procurement BU)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
In the service provider model, a BU with the **Procurement** business function is the service provider. Client BUs have the **Requisitioning** (and usually **Payables Invoicing**) function. The provider negotiates with suppliers, maintains supplier sites, and processes requisitions and POs for its clients. The relationship frames service level agreements, drives security, and sets which procurement BUs can serve a requisition. Clients subscribe to the provider's supplier sites through **supplier site assignments**.

## Where in Fusion (FSM)
- Offering: Procurement. Functional area: Organization Structures (task list Define Business Units).
- Task names:
  - **Manage Business Unit** (Actions > **Assign Business Functions**). Also the standalone task **Assign Business Unit Business Function**.
  - **Manage Service Provider Relationships**: defines which procurement BU serves which client BU.
- Docs show you can view the clients of a service provider BU and the service providers of a client BU.
- Exact page and section names inside Manage Service Provider Relationships are UNVERIFIED in 26D. The docs only have conceptual topics under this task.

## Prerequisites & dependencies
- Both BUs exist and are active.
- The client BU has Requisitioning, which needs a primary ledger and a default LE. The provider BU has Procurement.
- Dependents:
  - Configure Requisitioning Business Function > **Default Procurement BU** must be one of the req BU's providers.
  - Supplier site assignments: Client BU must be a client of the site's procurement BU.
  - PO header Requisitioning BU defaulting: Fusion uses the client of the procurement BU if there is only one active client, otherwise the buyer's Procurement BU assignment.
  - Auto-created site assignments on supplier registration approval.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Business function: Procurement / Requisitioning / Payables Invoicing | — | Assigned on the BU | Requisitioning requires Primary Ledger + Default Legal Entity |
| Service provider (procurement BU) for client BU | — | Relationship row | UI labels UNVERIFIED |
| Supplier site assignment: Client BU | `ClientBU` / `ClientBUId` | BU allowed to transact on the site | Required |
| Supplier site assignment: Bill-to BU | `BillToBU` / `BillToBUId` | BU liable for the purchases (usually = Client BU) | Required. Allowed values come from the Intercompany Transaction Flow setup |
| Bill-to Location | `BillToLocationCode` / `BillToLocationId` | Default billing location on purchasing docs | |
| Ship-to Location | `ShipToLocationCode` / `ShipToLocationId` | Default ship-to on PO (fallback #1 for Default Ship-to Location) | |
| Inactive Date | `InactiveDate` | Assignment end | |
| Use Withholding Tax / Withholding Tax Group | `UseWithholdingTaxFlag` / `WithholdingTaxGroup(Id)` | | `UseWithholdingTaxFlag` is boolean (example shows "Y"; use true/false) |
| Liability / Prepayment / Bill Payable Distribution, Distribution Set | `LiabilityDistribution(Id)`, `PrepaymentDistribution(Id)`, `BillPayableDistribution(Id)`, `DistributionSet(Id)` | Invoice accounting defaults | |

## Implications for supplier site assignments
- The site belongs to the **procurement BU** (the provider). Client BUs never own sites.
- Every site needs an **active assignment** for a client BU before any PO or invoice can be created for that client.
- Only Client BU and Bill-to BU are required.
- If a separate bill-to BU acts as agent for the client, it also needs its own assignment so it can process invoices.
- Autocreate on supplier registration approval: Fusion creates an assignment for every client BU that has both Requisitioning and Payables Invoicing and is served by the procurement BU. Sites with purpose Sourcing Only are excluded. To stop this, deselect **Autocreate site assignments for spend authorized suppliers** (Configure Supplier Registration and Profile Change Request).
- The PO Supplier Site defaults only when there is exactly one active purchasing site for the procurement BU with an active assignment for the req BU.

## Common mistakes
- A client BU is added later but has no site assignments, so its POs fail on the supplier site.
- The Default Procurement BU on the req BU is not one of its providers.
- The Bill-to BU is not allowed by the intercompany transaction flow.
- The Requisitioning function was assigned without a primary ledger or default LE.
- The Configure Basic Enterprise Structure ESS was run on a non-greenfield pod. It makes the new procurement BU the provider for all BUs.

## Channel & exact technique
- Preferred channel: **D (UI)** for business functions and service provider relationships. No 26D business REST resource was found for either. **A (REST)** for site assignments.
- A (REST) site assignments: `GET/POST /fscmRestApi/resources/11.13.18.05/suppliers/{SupplierId}/child/sites/{SupplierSiteId}/child/assignments`. Always `rest_describe` first.
- B (FSM CSV): TaskCodes for Manage Service Provider Relationships and Assign Business Unit Business Function are UNVERIFIED.
- C: Supplier site assignments can also be loaded by FBDI. Run the Suppliers import, then Supplier Sites, then site assignments. Template details are not researched here.
- C (ESS): **Configure Basic Enterprise Structure for Procurement** creates the procurement BU as service provider for all other BUs (greenfield only).
- D (UI): no playbook yet (UI field labels unconfirmed).

## How to verify
- Manage Business Units: select the BU > Actions > Assign Business Functions, then Cancel.
- Manage Service Provider Relationships: view the clients of the procurement BU.
- `GET .../suppliers/{SupplierId}/child/sites/{SupplierSiteId}/child/assignments` shows the ClientBU rows.
- Functional test: create a PO with Requisitioning BU = client and pick the supplier site.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/service-provider-models.html — provider/client model, procurement example
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/shared-service-centers.html — Procurement serves Requisitioning BUs
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/guidelines-for-shared-service-centers.html — view clients and providers, BU security
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/toc.htm — task list placement: Define Business Units > Assign Business Unit Business Function / Manage Service Provider Relationships
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/business-functions.html — Requisitioning needs ledger + LE
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/items-and-supplier-site-reference-data-sharing.html — clients subscribe to sites via site assignments
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/supplier-sites-and-supplier-site-assignments.html — assignment rules and fields
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-supplierid-child-sites-suppliersiteid-child-assignments-post.html — REST attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-purchasing-document-header-defaults-work.html — Requisitioning BU and Supplier Site defaulting
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html — Assign Business Functions action
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/configure-basic-enterprise-structure-for-procurement.html — ESS
- https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/supplier-sites-and-supplier-site-assignments.html — autocreate rule and Intercompany Transaction Flow (via search, 25C)

## UNVERIFIED
- UI page, section and field labels of Manage Service Provider Relationships in 26D. The caller's assumed path "Assign Business Unit Business Function > service provider section" is not confirmed by 26D docs. The TOC lists it as a separate task.
- Whether any REST or FSM CSV exists for business function assignment or service provider relationships.
- The autocreate check box label and the Intercompany Transaction Flow rule (seen in 25C via search, not fetched for 26D).
- The FBDI template name for supplier site assignments.
