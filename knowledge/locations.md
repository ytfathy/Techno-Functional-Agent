# Locations (HR locations used as ship-to / bill-to / receiving / deliver-to)

> Release: 26D · Last researched: 2026-11-13 · Status: PARTIAL

## Business purpose
A location is the physical address record (HR location, `PER_LOCATIONS`-style) reused by workforce structures (departments, jobs, BUs) and by SCM/Procurement as ship-to, bill-to, receiving and deliver-to addresses on requisitions, POs and inventory orgs. One record, entered once, picked from LOVs everywhere else.
Docs: "You enter information about a location only once. Subsequently, when you set up other workforce structures you select the location from a list."
Affected: Procurement (requisition deliver-to, PO ship-to/bill-to), Inventory/Receiving (inventory org location, receiving), HCM (assignments), BU definition (BU Location field).

## Where in Fusion (FSM)
- Offering: Manufacturing and Supply Chain Materials Management → Functional area: **Enterprise Profile** → Task: **Manage Locations** (SCM "Create Locations" doc; the task only shows when "Show: All Tasks" is selected in the Enterprise Profile region).
- Offering: Financials → Functional area: Enterprise Profile → Task: Manage Locations (search snippet only, see UNVERIFIED).
- Procurement offering: functional area for Manage Locations not confirmed on a 26D page (UNVERIFIED; expect Enterprise Profile).
- Redwood HCM UI alternative: My Client Groups > Show More > Locations (Location Details quick action in Workforce Structures).
- Scope: none asked when opening the task.

## Prerequisites & dependencies
- Needs: reference data set (Location Set) → `reference-data-sets`; geography setup for the country (address validation); optional inventory org (must be effective today and exist in the selected location set).
- Used by: `business-units` (BU Location field, optional), inventory organizations (Manage Inventory Organizations, Facilities functional area), Configure Requisitioning Business Function (default deliver-to / one-time location: "must be a global location that's enabled for the requisitioning BU"), PO ship-to/bill-to.

## Reference-data-set behaviour
- Location is **set-enabled**: "When you create a location, you must associate it with a set. Only those users who have access to the set's business unit can access the location set..."
- Associate to the **common set** to make it visible enterprise-wide: "users ... can see the locations that they have access to along with the locations in the common set."
- In BU set assignment the Locations reference group follows the BU default set unless overridden (example in docs: BU default set used for grades, departments and locations).
- Inventory organization field on the location: if selected, "The location is available for selection in purchase documents of that inventory organization ... If you don't select an inventory organization, then the location is available in purchase documents across all inventory organizations."

## Ship-to / bill-to / receiving / office flags — what they really do
- 26D Implementing Procurement, Locations: "the Ship-to Site, Receiving Site, Bill-to Site, Office Site, and Designated Receiver fields in the Shipping Details section of a location setup are for information purpose only and can be used to report upon. They aren't currently used by any feature or process within HCM."
- That statement is scoped to **HCM**. Whether Procurement/Receiving LOVs filter on these flags is not stated on any 26D page found → UNVERIFIED. Safe practice: keep Ship-to Site / Receiving Site / Bill-to Site = Yes (REST default true) on locations used in purchasing.
- Newer attributes (Redwood): **Deliver-to Site** (distinguish dock vs point-of-use, e.g. PAR rooms) and **Receivable Materials** (multiselect from lookup `ORA_PER_LOC_RCVBL_MATERIALS` / `ORA_PER_LOCATION_RECEIVABLE_MATERIALS` — doc uses both names). Hidden by default on Redwood pages (enable in VB Studio). Supported in HDL/HSDL and "included in FSM Export and Import".

## Key fields
| Field (UI label) | REST attribute (locationsV2) | Meaning | Notes / typical value |
|---|---|---|---|
| Effective Start Date | `EffectiveStartDate` (date, required) | Date-effective start | Back-date before first transaction |
| (end date) | `EffectiveEndDate` (date, required in schema) | Effective end | `4712-12-31` UNVERIFIED as accepted open end |
| Location Set | `SetCode` (string 30, required) / `SetId` (int64, required) | Reference data set the location belongs to | Common set for shared locations |
| Name | `LocationName` (string 60, required) | Location name | |
| Code | `LocationCode` (string 120, required) | "Code that uniquely references the location within the set" | Unique per set, not globally |
| Status | `ActiveStatus` (string 30, default `A`) | Active / inactive | |
| Description | `Description` (240) | | |
| Ship-to Site | `ShipToSiteFlag` (bool, default true) | Location is a ship-to site | Informational in HCM |
| Ship-to Location | `ShipToLocationId` / `ShipToLocationCode` | Other location used as ship-to for this one | |
| Receiving Site | `ReceivingSiteFlag` (bool, default true) | Receiving site | |
| Bill-to Site | `BillToSiteFlag` (bool, default true) | Bill-to site | |
| Office Site | `OfficeSiteFlag` (bool, default true) | Office site | |
| Deliver-to Site | `DeliverToSiteFlag` (bool, REST default true) | Point-of-use deliver-to | Redwood doc says default N — conflict, see UNVERIFIED |
| Receivable Materials | `ReceivableMaterials` (string 2000) | Hazardous/special materials handled | lookup-driven |
| Designated Receiver | `DesignatedReceiverId` / `DesignatedReceiverNumber` | Person who receives | |
| Inventory Organization | `InventoryOrganizationId` / `InventoryOrganizationName` | Restricts location to that org's purchase docs | |
| Employee Location | `EmployeeLocationFlag` (bool, default true) | Usable on employee assignments | |
| Geographic hierarchy node | `GeoHierarchyNodeCode` | | |
| Main phone / fax / email | `MainPhone*`, `Fax*`, `EmailAddress` | | |
| Address (child `addresses`) | `AddressUsageType`, `Country` (60), `AddressLine1..4` (240), `TownOrCity` (60), `Region1..3` (120), `PostalCode` (30), `LongPostalCode`, `Building`, `FloorNumber`, `TimezoneCode`, `EffectiveStartDate`, `EffectiveEndDate`, `ValidateAddressFlag` (default false), `AddlAddressAttribute1..5` | Main and other addresses | UI labels City / State / ZIP Code / County map to TownOrCity / Region* / PostalCode per country address style (mapping per country UNVERIFIED) |

## Common mistakes
- Location created in the wrong set → invisible in a BU's LOVs. Use common set unless partitioning is intended.
- Location created in Trading Community Model (customer/supplier address) is not an HR location: "you can't access that location from Oracle Fusion Global Human Resources."
- Only **approved** locations show in search (location changes can go through HCM approvals).
- Inventory org not shown on Create Location: org must be effective today and exist in the selected location set.
- Inactivating a location: from that date it can no longer be associated with other workforce structures, assignments or applications.
- Create/update via REST runs postprocessing and "may take several minutes to complete" — don't read back immediately and assume failure.
- Bulk loads: Oracle recommends HCM Data Loader (Location object) over REST.

## Channel & exact technique
- Preferred channel: **A (REST)** — locationsV2 supports full create/update/delete; documented and stable.
- A (REST): `GET/POST /hcmRestApi/resources/11.13.18.05/locationsV2`; item `GET/PATCH/DELETE /locationsV2/{locationsV2UniqID}`.
  - Finders: `PrimaryKey` (LocationId, EffectiveStartDate, EffectiveEndDate), `findByLocationId` (LocationId, SysEffectiveDate), `findByLocationIdAfterReload`. No set finder on locationsV2 → use `q=SetCode='<code>';LocationCode='<code>'`.
  - Query param `effectiveDate=yyyy-MM-dd`; headers `Effective-Of`, `Upsert-Mode`.
  - Child resources: `addresses`, `attachments`, `bannerOverrideMessages`, `locationsDFF`, `locationsEFFContainer`, `locationLegislativeEFF` (CategoryCode `HCM_LOC_LEG`), `translations`.
  - Actions: `/{id}/action/changeEffectiveStartDate`, `/action/splitLocationForChildUpdate`, `/{id}/action/deleteLocationOtherAddresses`, `/{id}/action/modifyLocationRowForChildCorrect`, `/action/getReloadedEFFData`, `/action/verifyForeignKeysOnDateChange`.
  - Read-only LOV also exists: `/hcmRestApi/resources/11.13.18.05/locationsLov` (seen in search index only; UNVERIFIED attributes). Older `locations` resource exists too; use V2.
  - Always `rest_describe` first; send both `SetCode` and `SetId` (both marked required) — resolve SetId via `setIdSets?finder=SetCodeFinder;SetCode=<code>`.
- B (FSM CSV): Manage Locations is stated to be "included in FSM Export and Import" (Redwood attributes note). TaskCode not found → UNVERIFIED.
- C: HCM Data Loader `Location` business object (recommended for bulk). File/attribute names not researched here.
- D (UI): Manage Locations task (fields above) — no playbook needed while A works.

## How to verify
- `GET /hcmRestApi/resources/11.13.18.05/locationsV2?q=LocationCode='<code>';SetCode='<set>'&expand=addresses&onlyData=true`
- Check ActiveStatus = A, flags, address; then open a requisition in a BU whose set is the location's set (or common) and confirm the location shows in Deliver-to LOV.

## Sources
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-locationsv2-post.html — path, request attributes, types, defaults, required list, addresses child attributes (latest unversioned REST guide; no /26d/ REST page exists for HCM)
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-locationsv2-get.html — finders, query params
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/api-locations-v2.html — operations, actions, child resource list, postprocessing note, HDL recommendation
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/locations.html — set association, common set, Shipping Details flags informational in HCM, Redwood update steps
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/what-happens-if-i-select-an-inventory-organization-when-i-am.html — inventory org effect
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-can-i-associate-a-location-with-an-inventory-organization.html — inventory org must be effective and in location set
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/why-can-t-i-see-my-location-in-the-search-results.html — approved only; TCA locations not visible
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-configure-business-units-with-requisitioning-business.html — one-time location must be global location enabled for requisitioning BU
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-business-units-work-with-reference-data-sets.html — locations follow BU set assignment
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fammi/create-locations.html — MSCMM > Enterprise Profile > Manage Locations, UI field list
- https://docs.oracle.com/en/cloud/saas/human-resources/faigh/deliver-to-site-and-receivable-materials-attributes-on-redwood-locations-pages.html — Deliver-to Site, Receivable Materials, FSM export/import + HDL support

## UNVERIFIED
- UNVERIFIED: Whether Procurement / Receiving LOVs filter ship-to, bill-to or receiving locations on `ShipToSiteFlag` / `BillToSiteFlag` / `ReceivingSiteFlag` (26D doc only says flags are not used by HCM).
- UNVERIFIED: Functional area of Manage Locations in the **Procurement** offering (Enterprise Profile confirmed for MSCMM; Financials only from search snippet).
- UNVERIFIED: Set code of the common set (commonly `COMMON`) — read it via `setIdSets` at runtime.
- UNVERIFIED: Accepted value for open-ended `EffectiveEndDate` (e.g. `4712-12-31`).
- UNVERIFIED: Valid `AddressUsageType` codes for the main address and per-country mapping of UI labels (City/State/County) to `TownOrCity`/`Region1..3`.
- UNVERIFIED: FSM Setup Task CSV TaskCode for Manage Locations (doc says locations are included in FSM Export and Import, no TaskCode given).
- UNVERIFIED: Deliver-to Site default — REST `DeliverToSiteFlag` default true vs Redwood doc "Deliver-to Site: N"; also the two lookup names for Receivable Materials.
- UNVERIFIED: `locationsLov` attributes/finders (not read).
