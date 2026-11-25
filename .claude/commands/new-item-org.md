---
description: Create an item organization (item master or child item org) with its prerequisite checks
argument-hint: <org code, name, location, master org (if child)…>
---
Request: $ARGUMENTS

Follow the CLAUDE.md loop with `knowledge/item-organizations.md`, `knowledge/inventory-organizations.md` and the "Items" chain in `knowledge/dependencies.md`. Backend channels only (A → B).

1. **Prerequisite checklist — read each one and show a table:**
   1. Location (`locationsV2`).
   2. Management BU + legal entity (same values the related inventory orgs use).
   3. Is this the item master or a child? Item master already present → `inventoryOrganizations?finder=itemOrgs` (most pods have one master; a second master is rare — confirm with the user).
   4. Reference data set for items / item classes (`reference-data-sets.md`).
   5. Duplicate check: `OrganizationCode` / `OrganizationName`.
2. **Plan:** `POST inventoryOrganizations` with `InventoryFlag=false` (item org) + `MasterOrganizationId` for a child; then (if needed) organization tree / item class setup (`EGO_MANAGE_ITEM_CLASSES`, UI or channel B).
3. Back up, dry run, execute after "yes", verify read-back, config-docs/inventory.md + `log_request`.
4. After the first run: add `create_item` / item-org shortcuts with tests, and clear the confirmed UNVERIFIED items in item-organizations.md / items-item-classes.md.
