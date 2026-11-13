---
description: End-to-end test cycle Requisition → PO → Receipt to prove the setup works
argument-hint: <BU, supplier, item/description…>
---
Request: $ARGUMENTS

Follow `knowledge/p2p-test-cycle.md`. Run on DEV/TEST; on PROD only if the user types CONFIRM PROD.
1. Pick test data (BU, requester, supplier site assigned to the BU, item or description, ship-to/deliver-to, buyer). Show it as a plan.
2. Create + submit requisition → poll approval status → convert to PO (per the knowledge file) → submit PO → poll until open → create receipt → read the receipt back.
3. Stop at the first failure: show the parsed Oracle error, explain which setup is missing (dependencies.md), propose the fix.
4. Report a table: step, document number/ID, status, time. Save to reports/p2p-test-<date>.md; `log_request`.
