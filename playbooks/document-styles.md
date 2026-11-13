# Playbook: Manage Document Styles

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS
> Knowledge file: `knowledge/document-styles.md`

## When to use
**Fallback only.** REST `purchasingDocumentStyles` (POST/PATCH) is the preferred channel. Use the UI when REST fails, when a setting is not exposed in REST, or when the user asks for UI evidence.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Name | Yes | Services Style | User |
| Description | Optional | Services POs | User |
| Status | Yes | Active | |
| Purchase Bases | Yes | Goods / Services / Both | |
| Line Types | Yes | All / Specified (+ list) | `purchasingLineTypesLOV` |
| Outside Processing / Consignment Terms / Configuration Ordering | Optional | at most one = Yes | Mutually exclusive |
| Progress Payments Enabled / Retainage Enabled / work confirmation | Optional | Yes | Complex work |
| Credit Line Types Enabled | Optional | No | Irreversible |
| Purchase Order: Display Name | Yes | Services Order | |
| Blanket Purchase Agreement: enable + Display Name + price breaks | Optional | Services Agreement | |
| Contract Purchase Agreement: enable + Display Name | Optional | Services Contract | |

## Pre-checks (read before write)
- `GET /fscmRestApi/resources/11.13.18.05/purchasingDocumentStyles?q=StyleName='<name>'`. If found, edit it; do not duplicate.
- Delivered styles (Outside Processing Style, and Standard Style) can't be changed in the restricted ways described. Create a new style instead.
- Backup screenshot: `backups/<date>/document-styles-<name>-before.png`

## Navigation path
1. Navigator > My Enterprise > Setup and Maintenance
2. Setup: Procurement > Functional Area: Procurement Foundation > Task: Manage Document Styles (or Search Tasks: "Manage Document Styles")
3. Click Create (+). For an edit, select the style and click Edit. (Button names UNVERIFIED.)

## Steps
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|
| 1 | Enter | Name, Description | input |
| 2 | Select | Status | Active |
| 3 | Select | **Purchase Bases** | Goods / Services / Both |
| 4 | Select | **Outside Processing Enabled** / **Consignment Terms Enabled** / **Configuration Ordering Enabled** | at most one Yes |
| 5 | Select | **Progress Payments Enabled**, **Retainage Enabled** | Yes / No |
| 6 | Select | Work confirmation option (label UNVERIFIED) | Yes / No |
| 7 | Select | **Credit Line Types Enabled** | Confirm with the user first: this is irreversible |
| 8 | Select | **Line Types** | All / Specified (then add line types) |
| 9 | Enter | **Purchase Order** section > **Display Name** | input |
| 10 | Enable + enter | **Blanket Purchase Agreement** section > **Display Name**; price breaks allowed | input |
| 11 | Enable + enter | **Contract Purchase Agreement** section > **Display Name** | input |

## Save / submit
Click **Save and Close**. (The confirmation message text is UNVERIFIED.)

## Verification
- `GET purchasingDocumentStyles?q=StyleName='<name>'&expand=lineTypes`: compare the flags and display names.
- Screenshot `playbooks/screenshots/document-styles-after.png`.

## Known UI differences / gotchas
- The OSP option can't be disabled once any document uses the style.
- Credit line types can't be disabled after enabling, and they are incompatible with complex work, OSP, consignment and configuration ordering.
- The 26D work confirmation topic says to set "Progress Payments Enabled". Confirm the separate work confirmation control on screen.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/define-a-document-style-for-outside-processing.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-review-the-delivered-document-style-for-outside.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/enable-progress-payment-schedules.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-retainage.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/enable-work-confirmation.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-you-create-purchase-order-lines-with-negative-amounts.html
