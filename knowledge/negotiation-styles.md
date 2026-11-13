# Sourcing Basics: Negotiation Styles and Negotiation Templates

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- **Negotiation style**: controls which features and pages are available when a category manager creates a negotiation (auction, RFQ, RFI), the terminology (for example "Quote" → "Offer"), and default text content. A simple style gives a short creation flow. Seeded styles cannot be edited: copy one and enable only what you need. Inactivating a seeded style hides it from category managers.
- **Negotiation template**: a skeleton with default data (lines, suppliers, terms, response controls, addresses). It standardizes practice, for example per item category. Users need access to the template's Procurement BU. You can set a default template and require category managers to use a specific template.
Affects: category managers, sourcing administrators.

## Where in Fusion (FSM)
- Negotiation styles: Offering **Procurement** > Functional Area **Sourcing** > Task **Manage Negotiation Styles** (page "Manage Negotiation Styles", add icon → "Create Negotiation Style"). Classic UI only in 26D; Redwood style page is planned for a future update.
- Negotiation templates: **not** an FSM task. Negotiations work area > Task Panel > **Manage Negotiation Templates** (classic page "Manage Templates"). 26D Redwood: Sourcing page > **View More Actions** > **Manage Negotiation Templates** → "Negotiation Templates" page. Also View Negotiation > Actions > **Copy to Template**.
- Sourcing BU settings: **Configure Procurement Business Function** (Sourcing BU level defaults, negotiation terms and conditions, abstract listing configuration, sourcing document types). There is no separate "Configure Sourcing Business Function" task in the docs found.
- 26D Redwood sourcing setup tasks: Manage Cost Factors, Manage Cost Factor Lists, Manage Sourcing Notifications, Manage Procurement Category Hierarchy. Not yet Redwood: Negotiation Styles, Line Attribute Lists, Supplier Negotiation Approval Rules, Supplier Negotiation Award Approval Rules.

## Prerequisites & dependencies
- Procurement BU with sourcing function configured (Configure Procurement Business Function).
- Templates depend on style, negotiation type, outcome and currency.
- Optional: attribute lists, cost factors and cost factor lists, terms and conditions, abstracts.

## Key fields
### Negotiation style
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Negotiation Style | none | Style name | |
| Description | none | Usage text | optional |
| Code | none | Unique alphanumeric code | |
| Status | none | Availability | Active/Inactive |
| Enable (per Document Type) | none | Style usable for that type (Auction, RFQ, RFI) | Deselect types not needed |
| Document Type | none | Negotiation type | |
| Negotiation Display Name | none | Buyer-side label | for example "Solicitation" |
| Response Document Type / Response Display Name | none | Supplier-side label | Defaults: Auction=Bid, RFI=Response, RFQ=Quote |
| Edit Content | none | Icon to change display names | |
| Controls (check boxes) | none | Two-stage RFQ, Integration with Oracle Fusion Project Management project plans, Abstracts, Team Scoring, Composite Scoring, Negotiation Document Format (Single document / Lines in a separate spreadsheet), alternate response lines, partial quantities, response revision, spreadsheet response (Requirements and Lines: rich or light weight format; Lines only), collaboration team, requirements | |

### Negotiation template (classic Create pop-up)
| Field (UI label) | Required | Notes |
|---|---|---|
| Procurement Business Unit | Yes | |
| Negotiation Type | | |
| Negotiation Style | if appropriate | |
| Negotiation Outcome | Yes | |
| Negotiation Currency | Yes | |
| Template Name | Yes | entered in train stops |
| Close Date | not available | entered by category manager |
| Status | | Template stays inactive until activated |
- Redwood (26D): Private templates (owner and collaborators) or Global (by BU access). Copied/duplicated templates keep attachments if needed. Not supported in Redwood templates: internal cost factors, contracts, line attachments, DFFs, retainage, large negotiations.

### Profile options (26D Redwood)
| Code | Display name |
|---|---|
| `ORA_PON_SOURCING_REDWOOD_ENABLED` | Redwood Pages for Sourcing Enabled |
| `ORA_PON_NEGOTIATION_TEMPLATES_ENABLED` | Redwood Page to Manage Negotiation Templates Enabled |
Both must be enabled for the Redwood template page.

### Privileges
- `PON_MANAGE_SUPPLIER_NEGOTIATION_TEMPLATE_PRIV` (Manage Supplier Negotiation Template)
- `PON_MANAGE_SUPPLIER_NEGOTIATION_COST_FACTOR_PRIV`, `PON_MANAGE_SUPPLIER_NEGOTIATION_COST_FACTOR_LIST_PRIV`, `PON_MANAGE_NOTIFICATIONS_PRIV`, `POR_MANAGE_PROCUREMENT_CATEGORY_HIERARCHY_PRIV`
- Privilege for Manage Negotiation Styles: UNVERIFIED.

## Common mistakes
- Editing a seeded style. Not allowed. Copy it.
- Creating a style with all features on. It defeats the purpose (shorter creation flow).
- Expecting a template to set Close Date. Not available in templates.
- Forgetting to activate a template. New and updated templates stay inactive.
- Global template not visible: user lacks access to the template's Procurement BU.

## Channel & exact technique
- Preferred channel: **D (UI)** for styles and templates. No REST resource for negotiation styles or templates was found (26D new-resource list has none). `supplierNegotiations` REST has a create-from-template use case (template must already exist).
- A (REST): `procurementBusinessFunctions` (26D new) for sourcing BU function settings:
  - `GET|POST /fscmRestApi/resources/11.13.18.05/procurementBusinessFunctions`
  - `GET|PATCH|DELETE /fscmRestApi/resources/11.13.18.05/procurementBusinessFunctions/{ProcurementBUId}`
  - `POST .../procurementBusinessFunctions/action/createAndUpdateSourcingTermsAndConditions`
  - `POST .../procurementBusinessFunctions/action/defaultProcurementBusinessUnit`
  - Subcategories: Abstract Listing Configurations, Document Types, Terms and Conditions.
  - Always `rest_describe` first.
- B (FSM CSV): UNVERIFIED for Manage Negotiation Styles.
- C: none.
- D (UI): Setup and Maintenance > Procurement > Sourcing > Manage Negotiation Styles > add icon > fill header, document types, controls > Save. Playbook not yet written.

## How to verify
- Create a negotiation in the Negotiations work area, pick the new style, check that only enabled pages and the new labels show.
- Templates: Manage Negotiation Templates search shows the template as active; create a negotiation from it.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/negotiation-styles.html — what a style controls, default labels
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/negotiation-style-contents.html — style fields, controls, seeded styles
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/example-of-negotiation-styles.html — FSM task path, create steps
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/create-a-negotiation-template.html — classic template steps and fields
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-s-the-difference-between-a-negotiation-style-and-a.html — style vs template
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f42877.htm — Redwood templates, profile options, privilege
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f50341.htm — Redwood sourcing setup, not-yet-Redwood items
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-procurement-business-functions.html — procurementBusinessFunctions endpoints

## UNVERIFIED
- Privilege needed for Manage Negotiation Styles.
- Setup Task CSV support for Manage Negotiation Styles.
- Field names inside procurementBusinessFunctions for sourcing defaults (not fetched).
- Whether a "Configure Sourcing Business Function" task exists separately (not found; Configure Procurement Business Function covers sourcing).
