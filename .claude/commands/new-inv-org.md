---
description: Create an inventory organization end-to-end (prerequisite checklist → reads → create → parameters → verify)
argument-hint: <org code, name, location/city, management BU, legal entity, item master org…>
---
Request: $ARGUMENTS

Follow the CLAUDE.md loop with `knowledge/inventory-organizations.md`, `knowledge/cost-management.md`, `knowledge/calendars-flexfields.md` and the "Inventory org" chain in `knowledge/dependencies.md`. Backend channels only (A → B); the pane only if the user asks to watch.

1. **Prerequisite checklist — read each one in Fusion and show a table (item / exists? / value found):**
   1. Location for the org (`locationsV2`, receiving / ship-to flags) — missing → `/new-location` step first.
   2. Management BU with the Materials Management business function (`find_business_unit`, then the BU usage in an `FUN_MANAGE_BUSINESS_UNIT` export if unclear).
   3. Legal entity on the same primary ledger as the BU (`legalEntitiesLOV`).
   4. Profit center BU (default = management BU).
   5. Schedule / workday calendar (`ScheduleId` is required in `invOrgParameters`; see calendars-flexfields.md).
   6. Item master organization (`inventoryOrganizations?finder=itemOrgs`).
   7. Reference data set / set assignments used by the BU (`reference-data-sets.md`).
   8. Cost organization and cost book that the new org will join (`cost-management.md`); cost org relationship is a follow-up step.
   9. Duplicate check: `OrganizationCode` and `OrganizationName` (`find_inventory_org`).
   Missing mandatory values → one short question listing what exists.
2. **Plan** (channel per step): `POST inventoryOrganizations` (`OrganizationCode`, `OrganizationName`, `InventoryFlag=true`, `ManagementBusinessUnit…`, `LegalEntity…`, `ProfitCenterBusinessUnit…`, `LocationId`, `MasterOrganizationId`, `invOrgParameters` with `ScheduleId`) — or `copyInventoryOrganizations` action from a similar org when the user prefers a copy (copies parameters / subinventories / locators per `copyParamsList`) — then cost org relationship, receiving parameters (channel B `RCV_MANAGE_RECEIVING_PARAMETERS`), interorg parameters if transfers are needed, data access for the agent user on the new org.
3. Back up (`fsm_export INV_MANAGE_INVENTORY_ORGANIZATIONS` or JSON of a similar org), dry run, execute after "yes", verify with `rest_get inventoryOrganizations/{id}?expand=invOrgParameters`.
4. Document in config-docs/inventory.md + `log_request`. Report OrganizationId / code.
5. After the first successful run: add a `create_inventory_org` shortcut (duplicate check + mocked test) and clear the UNVERIFIED items in inventory-organizations.md that the run confirmed.
