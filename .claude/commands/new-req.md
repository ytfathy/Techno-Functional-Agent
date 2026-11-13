---
description: Create (and optionally submit) a purchase requisition
argument-hint: <requisitioning BU, item/description, qty, price, deliver-to, requester…>
---
Request: $ARGUMENTS

Follow the CLAUDE.md loop with `knowledge/requisitions.md`:
1. Resolve requisitioning BU, preparer/requester (email), item or description + category, UOM, deliver-to location, destination type/org, charge account if expense. One short question for anything missing.
2. `rest_describe purchaseRequisitions` (and lines/distributions), then `create_requisition` dry run → approval → execute.
3. Submit with `submit_requisition` if asked; then read status and approval. Report the requisition ID and number.
4. `log_request`.
