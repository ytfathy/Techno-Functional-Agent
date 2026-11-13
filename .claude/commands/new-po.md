---
description: Create (and optionally submit) a purchase order
argument-hint: <procurement BU, supplier/site, buyer, lines…>
---
Request: $ARGUMENTS

Follow the CLAUDE.md loop with `knowledge/purchase-orders.md`:
1. Resolve procurement BU, requisitioning BU, supplier + site (site must be assigned to the client BU), buyer (must be a procurement agent on the BU), document style, currency, lines (item/description, category, qty, UOM, price, ship-to, destination).
2. `rest_describe draftPurchaseOrders` (+ children), then `create_purchase_order` dry run → approval → execute.
3. `submit_purchase_order` if asked; read back the status. Report the PO header ID and order number.
4. Change order / cancel / close: use the actions in knowledge/purchase-orders.md via `rest_action` (describe first).
5. `log_request`.
