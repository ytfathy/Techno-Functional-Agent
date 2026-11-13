# Supplier Setup (Numbering, Registration, Spend Authorization)

> Release: 26D · Last researched: 2026-11-13 · Status: PARTIAL

## Business purpose
Global supplier setup that controls how new suppliers get created and approved:
- **Supplier numbering**: automatic number for suppliers created by the Create Supplier flow, by supplier registration, or by supplier import. Default start = 1. You can change the next number at any time (for example to skip a range). The app checks that the number is not already used.
- **Supplier registration**: which profile sections a registering supplier sees or must fill (prospective vs spend authorized), default business relationship per registration source, required identifiers, required attachments, post-approval site-assignment creation, registration URLs.
- **Supplier profile change request**: which profile entities need approval when changed by a supplier, by Supplier Qualification, or by Supplier Negotiation.
- **Spend authorization**: a prospective supplier (sourcing and qualification only) must be promoted to **spend authorized** before POs, agreements and invoices. Promotion creates a spend authorization request that is routed for approval.
Affects: supplier administrators, supplier managers, buyers, sourcing, Supplier Portal users.

## Where in Fusion (FSM)
- Offering: Procurement
- Functional area: Suppliers
  - **Specify Supplier Numbering** (Redwood "Supplier Numbering" page in 26D)
  - **Configure Supplier Registration** (Redwood "Supplier Registration Configuration" page). Old name: "Configure Supplier Registration and Profile Change Request". When the Redwood feature is disabled, only the classic Configure Supplier Registration task exists, and it covers both registration and profile change request.
  - **Configure Supplier Profile Change Request** (Redwood "Supplier Profile Change Request Configuration" page)
  - Other 26D Redwood supplier setup tasks: Manage Supplier Products and Services Category Hierarchy, Configure New Supplier Notification, Manage Certifying Agencies, Manage Supplier User Roles / Manage Supplier User Role Usages, Specify Supplier News Content, Configure Supplier Notifications.
- Functional area: Approval Management (task list "Define Approval Management for Procurement")
  - **Manage Supplier Registration Approvals** (registrations from external users)
  - **Manage Internal Supplier Registration Approvals** (registrations by internal users for a supplier)
  - **Manage Supplier Spend Authorization Approvals**
  - Manage Supplier Profile Change Approvals / Manage Internal Supplier Profile Change Approvals
  - Details: `knowledge/approvals.md`
- Redwood status: "Redwood: Set up Supplier Registration and Profile Change Request" (26A) is **No Longer Optional from 26D**, enabled by default. "Set up supplier management" (26D) is enabled by default.
- Supplier registration URLs (prospective and spend authorized) are set on **Configure Procurement Business Function**.

## Prerequisites & dependencies
- Procurement BU with the procurement business function configured. Registration URLs live there.
- Procurement agents with the **Manage Suppliers** action (task: Manage Procurement Agents). They are the "supplier managers" that seeded registration and spend authorization approval rules route to.
- Supplier Products and Services Category Hierarchy (if the Products and Services section is used in registration).
- Downstream: supplier creation (REST `suppliers`, FBDI Import Suppliers), Supplier Portal user provisioning, ASL, sourcing invitations.

## Key fields
### Supplier numbering
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Next Supplier Number | `NextSupplierNumber` (int64) | Next unique supplier number | Default start 1. Changeable any time. Must not be already used. |
| (key) | `SupplierNumberingId` | Record key | Get it with GET collection. Do not build it yourself. |

### Supplier registration / profile change (REST `supplierOptions`)
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Autocreate site assignments for spend authorized suppliers | `AutoCreateSiteAssignmentFlag` | Create site assignments automatically when a registration is approved or promoted to spend authorized | Default true |
| (New Supplier Notification enabled) | `EnableNewSupplierNotificationFlag` | Email all supplier contacts when supplier registered or promoted to spend authorized | Default false |
| Require supplier identifier, External Supplier Request | `ExternalRegSupplierIdRequiredFlag` | Need at least one of D-U-N-S Number, Taxpayer ID, Tax Registration Number | Default true |
| Require supplier identifier, Internal Supplier Request | `InternalRegSupplierIdRequiredFlag` | Same, internal requests | Default true |
| Require supplier identifier, Sourcing Invitation | `SourcingSupplierIdRequiredFlag` | Same, sourcing invitation | Default true |
| Require supplier identifier, Self Service Procurement | `SSPSupplierIdRequiredFlag` | Same, self-service request | Default false |
| Default business relationship, Internal Supplier Request | `InternalRegSupplierBusRelationDefaultCode` | Default business relationship | Code values: UNVERIFIED (likely lookup `ORA_POZ_BUSINESS_RELATIONSHIP`) |
| Default business relationship, Sourcing Invitation | `SourcingSupplierBusRelationDefaultCode` | Same, sourcing source | as above |
| Default business relationship, Self Service Procurement | `SSPSupplierBusRelationDefaultCode` | Same, SSP source | as above |
| Company details attachments, External Supplier Request | `ExternalRegCompanyDetailsAttachmentsRequiredCode` | Which relationship types must attach company documents (for example W9) | Code values UNVERIFIED |
| Bank account attachments (external registration) | `ExternalRegBankAccAttachmentsRequiredFlag` | Force bank proof on external registration | Default false |
| Bank account attachments (internal change) | `InternalChangeBankAccAttachmentsRequiredFlag` | Force bank proof on internal profile change | Default false |
| Bank account attachments (supplier change) | `SupplierPortalChangeBankAccAttachmentsRequiredFlag` | Force bank proof on supplier-initiated change | Default false |
| Welcome message / Success message | `ExternalRegWelcomeMessage` / `ExternalRegSuccessMessage` | External registration page text | max 4000 chars |
| Expiring business classification notice | `NotifyPriorToExpirationDays`, `ReminderFrequencyDays` | Supplier notification timing | |
| Regenerate encryption key | action `regenerateUrlEncryptionKey` | New key for registration URLs | Breaks saved-for-later and returned registration URLs. Spend authorization URLs on Configure Procurement Business Function change. |

### Registration flows (UI only, no REST attribute found)
- Business relationship flows: **Spend Authorized Supplier requests** and **Prospective Supplier requests**.
- Profile sections per flow: Organization Details, Contacts, Contact User Account, Addresses, Business Classifications, Bank Accounts, Products and Services, Qualifications Questionnaire. Each attribute: **Enabled** (shown, optional) or **Required**.
- Registration sources: Internal Sourcing Invitation, Internal Supplier Request, External request (self-registration).
- Profile change approval per entity, separately for prospective and spend authorized: **No Approval Required** / **Approval Required**. Entities: Organization Details, Contacts, Contact User Account, Addresses, Business Classifications, Bank Accounts, Payment Methods, Products and Services, Tax Identifiers, Site Details (spend authorized only).
- Bank account change attachments trigger when a new bank account is created or country, account number, bank, branch, IBAN or currency changes.

### Spend authorization
- Created by: **promote to spend authorized** button on Edit Supplier; creating a supplier with business relationship spend authorized (after registration approval); negotiation award to a prospective supplier.
- Approver actions: approve, reject, reassign. Rejected requests can be resubmitted.
- **Resubmit Request** (View Spend Authorization Request page) only for **pending approval** requests. Needs privilege **Resubmit Supplier Spend Authorization Request**. Rejects the current request and starts a new one.
- There is no separate "spend authorization review" setup switch in the docs. The review is driven by the approval task **Manage Supplier Spend Authorization Approvals**.

### Supplier-related lookups and profile options (verified)
| Item | Code | Managed by |
|---|---|---|
| Business relationship lookup | `ORA_POZ_BUSINESS_RELATIONSHIP` | Manage Standard Lookups |
| Supplier type lookup | `POZ_VENDOR_TYPE` | Manage Supplier Type Lookup |
| Tax organization type lookup | `POZ_ORGANIZATION_TYPE` | Manage Tax Organization Type Lookup |
| Redwood supplier management pages | `ORA_POZ_SUPPLIER_MANAGEMENT_REDWOOD_ENABLED` | Manage Administrator Profile Values |
| Redwood supplier profile pages | `ORA_POZ_SUPPLIER_PROFILE_REDWOOD_ENABLED` (needs the one above first; default disabled) | Manage Administrator Profile Values |
More in `knowledge/procurement-profile-options-lookups.md`.

### Privileges (26D readiness)
- `POZ_MAINTAIN_SUPPLIER_NUMBERING_SETUP_PRIV` (Maintain Supplier Numbering Setup)
- `POZ_CONFIGURE_SUPPLIER_REGISTRATION_PRIV` (Configure Supplier Registration)
- `POZ_CONFIGURE_NEW_SUPPLIER_NOTIFICATION_PRIV`, `POZ_MANAGE_CERTIFYING_AGENCIES_PRIV`, `POZ_MANAGE_SUPPLIER_USER_ROLES_PRIV`, `POZ_MANAGE_SUPPLIER_USER_ROLE_USAGES_PRIV`, `POZ_MAINTAIN_SUPPLIER_NEWS_CONTENT_PRIV`, `POZ_CONFIGURE_SUPPLIER_NOTIFICATIONS_FOR_PROFILE_MGMT_PRIV`, `POR_MANAGE_PROCUREMENT_CATEGORY_HIERARCHY_PRIV`

## Common mistakes
- Setting Next Supplier Number to a value already used. The app rejects it.
- Expecting suppliers imported with non-numeric legacy numbers to be blocked. Import supports non-numeric numbers to keep legacy IDs (source: older 23D import topic, re-check in 26D).
- Regenerating the URL encryption key in production. It kills saved and returned registration links.
- Deselecting **Autocreate site assignments** and then wondering why spend-authorized suppliers cannot be used on POs. Site assignments must then be created by hand.
- Forgetting supplier managers. Seeded approval rules route to procurement agents with **Manage Suppliers**. No such agent in the BU = no approver.
- Not disabling unused seeded approval participants. In spend authorization approvals, unused seeded participants **must** be disabled.
- Sites and site assignments cannot be imported for prospective suppliers. Business relationship cannot be updated through import.

## Channel & exact technique
- Preferred channel: **A (REST)** for numbering and registration options (new 26D resources). **D (UI)** for registration section matrix and profile change approval matrix (no REST attribute found for those).
- A (REST):
  - `GET /fscmRestApi/resources/11.13.18.05/supplierNumbering`
  - `GET|PATCH /fscmRestApi/resources/11.13.18.05/supplierNumbering/{SupplierNumberingId}` body `{"NextSupplierNumber": 5000}`
  - `POST /fscmRestApi/resources/11.13.18.05/supplierNumbering/action/initializeSetup` (no body; returns `{"result": "ROW EXISTS"}` when setup already exists). Media type `application/vnd.oracle.adf.action+json`.
  - `GET /fscmRestApi/resources/11.13.18.05/supplierOptions`
  - `GET|PATCH /fscmRestApi/resources/11.13.18.05/supplierOptions/{SupplierOptionsConfigId}`
  - `POST /fscmRestApi/resources/11.13.18.05/supplierOptions/action/regenerateUrlEncryptionKey` (destructive, ask user first)
  - Related new 26D resources: Certifying Agencies, New Supplier Notification, Supplier News Content, Supplier User Roles, Procurement Business Functions (`procurementBusinessFunctions`). Paths for the first four: UNVERIFIED (not fetched).
  - Always `rest_describe` first.
- B (FSM CSV): UNVERIFIED for all tasks here.
- C (FBDI/ESS): not applicable to setup. Supplier data import: Import Suppliers, Import Supplier Addresses, Import Supplier Sites, Import Supplier Site Assignments, Import Supplier Contacts, Import Supplier Business Classifications, Import Supplier Products and Services Categories, Import Supplier Attachments, Purge Supplier Interface Records.
- D (UI): Setup and Maintenance > search task "Configure Supplier Registration" / "Configure Supplier Profile Change Request" > change > **Save** or **Save and Close**. Approval rules: `playbooks/approval-rules.md` (same Manage Approvals page pattern).

## How to verify
- `GET supplierNumbering` and check `NextSupplierNumber`. Create a test supplier and confirm its number.
- `GET supplierOptions` and compare flags.
- Submit a test registration via the prospective URL and check the approval routes to the expected supplier manager.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/supplier-numbering.html — numbering behavior, default 1, next number update
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/Chunk24954695.html — Options to Configure Supplier Registration (flows, sections, sources, identifier, attachments, post approval, URL encryption, profile change)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/spend-authorization-requests.html — spend authorization request creation, resubmit
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/set-up-supplier-registration-approvals.html — registration approval tasks, seeded rules
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/supplier-spend-authorization-approvals.html — spend authorization approval task, stages, seeded rule
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/create-suppliers-with-the-import-suppliers-process.html — import process names and constraints
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/ssproc26a/26A-ssproc-wn-f41604.htm — Redwood registration setup, task rename, 26D mandatory
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f46282.htm — Redwood supplier management setup tasks, privileges
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f50411.htm — new 26D REST resources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-supplier-numbering.html — supplierNumbering endpoints
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernumbering-suppliernumberingid-patch.html — NextSupplierNumber
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernumbering-action-initializesetup-post.html — initializeSetup
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-supplier-configuration-options.html — supplierOptions endpoints
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-supplieroptions-supplieroptionsconfigid-patch.html — supplierOptions attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-post.html — lookup types on supplier attributes
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/proc26a/26A-procurement-wn-f41533.htm — ORA_POZ_SUPPLIER_PROFILE_REDWOOD_ENABLED (seen via search snippet only)

## UNVERIFIED
- Allowed code values for `*BusRelationDefaultCode` and `ExternalRegCompanyDetailsAttachmentsRequiredCode` (probably `ORA_POZ_BUSINESS_RELATIONSHIP` codes).
- Exact REST paths of Certifying Agencies, New Supplier Notification, Supplier News Content, Supplier User Roles resources.
- Whether any of these FSM tasks supports Setup Task CSV export/import.
- Non-numeric supplier numbers on import in 26D (seen only in 23D topic).
- `ORA_POZ_SUPPLIER_PROFILE_REDWOOD_ENABLED` / `ORA_POZ_SUPPLIER_MANAGEMENT_REDWOOD_ENABLED`: taken from search snippet of the 26A readiness page, page not fetched.
- Full list of spend authorization request statuses (docs name only "pending approval").
