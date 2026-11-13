# Playbook: Configure Procurement Business Function

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS
> Knowledge file: `knowledge/configure-procurement-bf.md`

## When to use
No 26D REST resource writes the Procurement Business Function configuration. FSM CSV support is unverified. Use the UI to set or change procurement BU defaults.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Procurement BU | Yes | US1 Business Unit | BU with the Procurement function |
| Inventory Organization | Yes (first time) | Master Item Org | Item master. Never change after it is assigned |
| Currency | Recommended | USD | Ledger currency |
| Payment Terms | Optional | Net 30 | Payables terms |
| FOB / Freight Terms / Shipping Method | Optional | — | Lookups / carriers |
| Buyer managed transportation | Optional | unchecked | Needs the feature opt-in |
| Default promised date from requested date | Optional | unchecked | |
| Price Break Type | Optional | Non-Cumulative Pricing | Cumulative is not allowed with global BPAs |
| Receipt Close Point + Receipt Close Tolerance Percent | Optional | Received / 0 | Set both |
| Match Approval Level | Optional | Three-Way | |
| Group requisitions / Group requisition lines (+ Use requested date, Use ship-to organization and location, Use ship-to location, Use customer sales order) | Optional | checked | |
| Allow manual price update on fulfilled orders | Optional | unchecked | |
| Standard terms and conditions | Optional | text | |

## Pre-checks (read before write)
- The BU has the Procurement function: Manage Business Unit > select BU > Actions > Assign Business Functions, then Cancel.
- If the Inventory Organization is already populated, do NOT change it. Stop and ask.
- For Buyer managed transportation, check that the feature is enabled (Offerings > Procurement > Procurement functional area).
- Backup: screenshot every section to `backups/<date>/configure-procurement-bf-<BU>-before.png`.

## Navigation path
1. Navigator > My Enterprise > Setup and Maintenance
2. Setup: Procurement > Functional Area: Procurement Foundation > Task: Configure Procurement Business Function (or Search Tasks: "Configure Procurement Business Function")
3. **Specify Procurement BU** dialog: select **Procurement BU** > **OK**
4. The page opens on the **Main** tab.

## Steps
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|
| 1 | Select | General > Inventory Organization (label UNVERIFIED) | input (only if empty) |
| 2 | Select | General > Currency (label UNVERIFIED) | input |
| 3 | Select | General > Payment Terms / FOB / Freight Terms / Shipping Method (labels UNVERIFIED) | input |
| 4 | Check/uncheck | General > **Buyer managed transportation** | input |
| 5 | Check/uncheck | Purchasing > **Default promised date from requested date** | input |
| 6 | Select | Purchasing > Price Break Type (label UNVERIFIED) | Cumulative Pricing / Non-Cumulative Pricing |
| 7 | Select / enter | Receipt Close Point; Receipt Close Tolerance Percent (labels UNVERIFIED) | Accepted / Delivered / Received; % |
| 8 | Select | Match Approval Level (label UNVERIFIED) | Two-Way / Three-Way / Four-Way |
| 9 | Check | **Group requisitions**, **Group requisition lines**, **Use requested date**, **Use ship-to organization and location**, **Use ship-to location**, **Use customer sales order** | input |
| 10 | Check/uncheck | **Allow manual price update on fulfilled orders** | input |
| 11 | Enter | Standard terms and conditions text. Optionally **Disable terms and conditions for all languages** | input |

## Save / submit
Click **Save**, then **Save and Close**. Expect a return to the task list with no error. (The confirmation message text is UNVERIFIED.)

## Verification
- Reopen the task for the same BU. Screenshot to `playbooks/screenshots/configure-procurement-bf-after.png`.
- Functional check: create a BPA for a supplier site without an invoice currency. Currency, Payment Terms and FOB should default from this BU.

## Known UI differences / gotchas
- Labels marked UNVERIFIED come from doc prose, not screen captures. Record the real labels on first run.
- "Next Agreement Number" / "Next Negotiation Number" may not exist in 26D. Numbering is in **Manage Procurement Document Numbering**.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-set-up-buyer-managed-transportation.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/price-break-types.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-choose-an-inventory-organization.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/receipt-close-point.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/match-approval-level-options.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/group-requisitions-options.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/standard-purchasing-terms-and-conditions.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/initiate-retroactive-price-update.html
