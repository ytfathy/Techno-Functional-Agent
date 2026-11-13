# Procurement Profile Options and Lookups

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- **Profile options** change application behavior at Site / Product / User level (for example enable a Redwood page, validate ASL on BPA submit). Lower level overrides higher level.
- **Lookups** are code/meaning lists behind choice lists (supplier type, business relationship, etc.). Three kinds: standard, set-enabled (codes tied to a reference data set), common (legacy or with attributes). Customization level decides what you can change: User (all), Extensible (add codes, not delete predefined), System (nothing).

## Where in Fusion (FSM)
- Profile options:
  - **Manage Profile Options** (search any predefined profile; case-sensitive; filter by Application/Module)
  - **Manage Administrator Profile Values** (set values; used for Redwood enablement `ORA_*_REDWOOD_ENABLED`)
  - **Manage Purchasing Profile Options** (Offering Procurement > Functional Area **Procurement Foundation**)
  - Self Service Procurement buyer options: Manage Administrator Profile Values in the Self Service Procurement functional area
  - Other product-specific "Manage ... Profile Options" tasks: UNVERIFIED
- Lookups:
  - **Manage Standard Lookups**, **Manage Common Lookups**, **Manage Set-enabled Lookups**
  - **Manage Purchasing Lookups** (lookups of module Purchasing; you can delete user-level lookups here)
  - **Manage Supplier Type Lookup** (`POZ_VENDOR_TYPE`), **Manage Tax Organization Type Lookup** (`POZ_ORGANIZATION_TYPE`)
  - "Manage Procurement Lookups" as a single task: not found in docs (UNVERIFIED)
- Import: Import Profile Values and Import Lookups (file-based, from the Manage pages).

## Prerequisites & dependencies
- Privilege to manage profile values / lookups (standard setup roles).
- Redwood profile options often need a parent Redwood option first (for example supplier profile needs supplier management).

## Key fields
### Profile options (verified codes)
| Code | Display name | Default / values | Set in |
|---|---|---|---|
| `PO_ASL_VALIDATION_FOR_BPA` | Approved Supplier Validation for Blanket Purchase Agreements | Yes (default) / No | Manage Purchasing Profile Options |
| `ORA_PO_ASL_REDWOOD_ENABLED` | Redwood Page for Approved Supplier List Entries Enabled | disabled; set Site = Y | Manage Administrator Profile Values |
| `ORA_PON_SOURCING_REDWOOD_ENABLED` | Redwood Pages for Sourcing Enabled | | Set Profile Option Values |
| `ORA_PON_NEGOTIATION_TEMPLATES_ENABLED` | Redwood Page to Manage Negotiation Templates Enabled | | Set Profile Option Values |
| `ORA_PON_COPY_NEG_HDR_DFF_TO_PO_HDR` | Copy negotiation header DFF to PO header | No / Copy internal Supplier Negotiation Headers DFF / Copy external Supplier Negotiation Headers for Suppliers DFF | Manage Administrator Profile Values |
| `ORA_PON_COPY_NEG_LINE_DFF_TO_PO_LINE` | Copy negotiation line DFF to PO line | Yes / No | same |
| `ORA_PON_COPY_NEG_HDR_DFF_TO_BPA_HDR` | Copy negotiation header DFF to BPA header | as header above | same |
| `ORA_PON_COPY_NEG_LINE_DFF_TO_BPA_LINE` | Copy negotiation line DFF to BPA line | Yes / No | same |
| `ORA_PON_COPY_NEG_HDR_DFF_TO_CPA_HDR` | Copy negotiation header DFF to CPA header | as header above | same |
| `POR_REQUESTED_DATE_OFFSET` | POR: Requested Delivery Date Offset | 7 | |
| `POR_ASSIGN_REQ_SAME_BUYER` | Use Same Buyer for All Lines in a Requisition | No | |
| `ORA_POR_BPA_PRICE_OVERRIDE` | Agreement Price Override on Requisition Lines Allowed | Yes | |
| `ORA_POR_BPA_DESCRIPTION_OVERRIDE` | Override of Agreement Line Description on Requisition Lines Allowed | No | |
| `ORA_POR_PIM_ES_DATA_SYNC` | Data Sync Between Master Items and Elasticsearch Index Enabled | | |
| `ORA_POR_SHOW_DFF_BY_DEFAULT_IN_PWA` | Descriptive Flexfields Displayed by Default in the Redwood Self Service Procurement Application | Yes | |
| `ORA_POR_ALLOW_CANCEL_ON_BCEA_FAILURE` | Cancellation of Budgetary-Controlled Encumbrance Accounting Requisitions Allowed on Failure to Release Funds | No | |
| `ORA_POR_WITHDRAW_CANCEL_WAIT_TIME` | Cancellation or Withdrawal of a Requisition after a Specified Wait Time | 300000 ms | |
| `ORA_POR_ENABLE_ROUNDING_FACTOR_FOR_IMT` | Rounding Factor Enforced for Internal Material Transfers | No | |
| `ORA_POR_RESP_SHOW_ADDN_ITEM_ATTRS` | Additional Attributes Displayed During Shopping in the Redwood Self Service Procurement Application | No | |
| `ORA_POR_RESP_DISABLE_CONTACT_AUTOSOURCING` | Disallow Contact Redefaulting in the Redwood Self Service Procurement Application | No | |
| `ORA_POR_USE_SUPP_SITE_INVOICE_CURR` | Supplier Site Invoice Currency Defaulting Allowed on Requisition Lines | No | |
| `ORA_POR_VIEW_PO_REDWOOD_ENABLED` | Redwood Page for Purchase Orders Enabled for Redwood Self Service Procurement Application | Yes | |
| `ORA_POR_RCO_REDWOOD_ENABLED` | Redwood Page for Create or Edit Requester Change Orders Enabled | Yes, Site only | |
| `ORA_RCS_PACKAGING_STRING_ORDER` | SCM Common: Display Order of Packaging String Units | | |
| `ORA_FND_RECENT_SEARCH_RETENTION_INTERVAL` | Recent Search Items Retention Interval | 90 | |
| `ORA_POZ_SUPPLIER_MANAGEMENT_REDWOOD_ENABLED` | Redwood Page for Supplier Management Enabled | | Manage Administrator Profile Values (UNVERIFIED, snippet only) |
| `ORA_POZ_SUPPLIER_PROFILE_REDWOOD_ENABLED` | Redwood Pages for Supplier Profile Enabled | disabled | same (UNVERIFIED, snippet only) |
| `ORA_PO_PURCHASE_ORDERS_REDWOOD_ENABLED` | Redwood Purchase Orders page (Purchasing) | disabled (25A) | UNVERIFIED for 26D |
| `ORA_PO_CONTRACT_FULFILLMENTS_REDWOOD_ENABLED` | Redwood Contract Fulfillments page | disabled (26C) | UNVERIFIED (snippet only) |

### Lookup types (verified codes)
| Lookup type | Used by | Managed by |
|---|---|---|
| `ORA_POZ_BUSINESS_RELATIONSHIP` | Supplier business relationship (`BusinessRelationshipCode`) | Manage Standard Lookups |
| `POZ_VENDOR_TYPE` | Supplier type (`SupplierTypeCode`) | Manage Supplier Type Lookup |
| `POZ_ORGANIZATION_TYPE` | Tax organization type (`TaxOrganizationTypeCode`) | Manage Tax Organization Type Lookup |
| `MONTH` | Fiscal year end month (`FiscalYearEndMonthCode`) | Manage Standard Lookups |
| `YES_NO` | Supplier Y/N flags | system |
| `RCV_RECEIVING_OPTION` | Receipt quantity exception code (`QtyRcvExceptionCode`) | UNVERIFIED task |

## Common mistakes
- Searching profile codes with wrong case. Search is case-sensitive.
- Setting a Redwood profile at User level when docs say Site only.
- Expecting profile changes to apply immediately. Redwood page profiles take effect at next sign-in.
- Deleting or changing predefined codes of an Extensible or System lookup.
- Creating a new lookup type for an existing choice list. The choice list reads only its own lookup type.

## Channel & exact technique
- Preferred channel: lookups **A (REST)**; profile values **D (UI)** unless a profile REST is confirmed.
- A (REST): Applications Common REST lookups resources `standardLookups`, `commonLookups`, `setEnabledLookups`, `genericLookups` (read utility for any view). Base path `/fscmRestApi/resources/11.13.18.05/<resource>`: UNVERIFIED (not stated on the page). Need lookup view + lookup type to query. Always `rest_describe` first.
- A (REST) for profile values: UNVERIFIED (no resource confirmed).
- B (FSM CSV): UNVERIFIED.
- C (file import): Import Profile Values and Import Lookups (file format topics exist: "File Format for Importing Profile Values", "File Format for Importing Lookups"); column details not captured here.
- D (UI): Setup and Maintenance > search "Manage Administrator Profile Values" > search Profile Option Code > Profile Values: level Site, value > **Save and Close**. Lookups: "Manage Standard Lookups" > search Lookup Type > add code row > Save.

## How to verify
- Re-open the profile and check the value at each level; sign in again for Redwood switches.
- `GET .../standardLookups?q=LookupType='POZ_VENDOR_TYPE'` (path UNVERIFIED) or reopen the lookup page.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/list-of-profile-options.html — POR / ORA_POR / ORA_RCS / ORA_FND codes and defaults
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-enable-profile-options.html — ORA_PON_COPY_* codes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-approved-supplier-status-validation-for-blanket.html — PO_ASL_VALIDATION_FOR_BPA, Manage Purchasing Profile Options
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-can-i-access-predefined-profile-options.html — Manage Profile Options
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-can-i-access-predefined-lookups.html — lookup tasks
- https://docs.oracle.com/en/cloud/saas/procurement/24c/oapro/overview-of-lookups.html — Manage Purchasing Lookups, lookup kinds (24C)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42846.htm — ORA_PO_ASL_REDWOOD_ENABLED
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f42877.htm — ORA_PON_* Redwood template profiles
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-post.html — POZ lookup types and tasks
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Work_with_Lookups.html — lookups REST resources

## UNVERIFIED
- REST resource for profile option values.
- Exact base path for lookups REST resources.
- Product-specific "Manage ... Profile Options" tasks other than Manage Purchasing Profile Options.
- A single "Manage Procurement Lookups" task (not found).
- Setup Task CSV support for these tasks.
- `ORA_POZ_*`, `ORA_PO_PURCHASE_ORDERS_REDWOOD_ENABLED`, `ORA_PO_CONTRACT_FULFILLMENTS_REDWOOD_ENABLED`: from search snippets / older releases.
- Task that manages `RCV_RECEIVING_OPTION`.
- Manage Purchasing Lookups confirmed only in 24C docs.
