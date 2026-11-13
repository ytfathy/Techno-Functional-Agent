---
description: Create a supplier end-to-end (supplier → address → site → BU assignment → contacts)
argument-hint: <supplier name, tax id, address/city, procurement BU, client BU, contact…>
---
Request: $ARGUMENTS

Follow the request loop in CLAUDE.md. Specifics:
1. Read `knowledge/suppliers.md`. Check duplicates: `rest_get suppliers` by name and by taxpayer / tax registration number.
2. Resolve the procurement BU and client BU(s) (`find_business_unit`); confirm the client BU is served by that procurement BU (`knowledge/service-provider-relationships.md`). Missing mandatory data → one short question with the options found.
3. Plan the separate calls in order: `create_supplier` → `add_supplier_address` → `create_supplier_site` (procurement BU) → `assign_site_to_bu` (client BU, bill-to BU) → `add_supplier_contact`. Never one combined payload.
4. Dry-run each, then execute after approval (or directly in auto mode on DEV/TEST).
5. Bank accounts: high-impact; never put numbers in chat or logs (safety rules).
6. Verify with `rest_get suppliers/{id}` expand=addresses,sites,contacts; then config-docs/suppliers.md + `log_request`. Report SupplierId, SupplierNumber, SupplierSiteId, assignment ID.
