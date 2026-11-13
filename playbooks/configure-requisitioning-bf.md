# Playbook: Configure Requisitioning Business Function

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS
> Knowledge file: `knowledge/configure-requisitioning-bf.md`

## When to use
No 26D REST write resource exists. REST `requisitionPreferences/.../requisitioningOptions` is read-only. FSM CSV support is unverified.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Requisitioning BU | Yes | US1 Business Unit | BU with the Requisitioning function |
| Default Deliver-to Organization | Recommended | Seattle Org | Inventory org |
| Line Type | Recommended | Goods | `purchasingLineTypesLOV` |
| One-Time Location | Optional | ONE-TIME-US | Global location enabled for the req BU |
| Group Requisition Import By | Optional | None | None / Buyer / Category / Item / Location / Supplier |
| Allow one-time addresses | Optional | checked | |
| Reapproval required for changes made during an active approval process | Optional | unchecked | |
| Create orders immediately after requisition import | Optional | unchecked | |
| Approval required for buyer modified lines | Optional | unchecked | |
| Enable approval override | Optional | unchecked | |
| Enable Supply Availability Details for Internal Transfers | Optional | unchecked | |
| Context Values for Requisition Descriptive Flex-fields | Optional | — | DFF contexts |
| Default Procurement BU | Yes | US1 Procurement BU | Must be a service provider of this req BU |
| Price Change Tolerance (% / amount) | Optional | 10 | |
| Ship-to Location | Recommended | Seattle | Location |
| Cancel Unfulfilled Demand | Optional | Optional | Always / Never / Optional |
| Multiple Legal Entities on Order | Recommended | Allow | Allow / Warning / Error |
| Allow Requisition-To-Agreement UOM Conversion | Optional | unchecked | |

## Pre-checks (read before write)
- The BU has the Requisitioning function (Manage Business Unit > Actions > Assign Business Functions). The BU has a primary ledger and a default LE.
- The Default Procurement BU is a service provider of this BU (Manage Service Provider Relationships).
- Read the current values with `GET /fscmRestApi/resources/11.13.18.05/requisitionPreferences/{id}/child/requisitioningOptions`. Use a user who has access to the BU.
- Backup screenshot: `backups/<date>/configure-requisitioning-bf-<BU>-before.png`

## Navigation path
1. Navigator > My Enterprise > Setup and Maintenance
2. Setup: Procurement > Functional Area: Procurement Foundation > Task: Configure Requisitioning Business Function (or Search Tasks: "Configure Requisitioning Business Function")
3. Select the Requisitioning BU in the scope dialog (dialog title UNVERIFIED) > **OK**

## Steps
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|
| 1 | Select | Requisitioning > **Default Deliver-to Organization** | input |
| 2 | Select | Requisitioning > **Line Type** | input |
| 3 | Select | Requisitioning > **One-Time Location** | input |
| 4 | Select | Requisitioning > **Group Requisition Import By** | input |
| 5 | Check | **Allow one-time addresses** | input |
| 6 | Check | **Reapproval required for changes made during an active approval process** | input |
| 7 | Check | **Create orders immediately after requisition import** | input |
| 8 | Check | **Approval required for buyer modified lines** | input |
| 9 | Check | **Enable approval override** | input |
| 10 | Check | **Enable Supply Availability Details for Internal Transfers** | input |
| 11 | Select | **Context Values for Requisition Descriptive Flex-fields** (header / line / distribution) | input |
| 12 | Select | Purchasing > **Default Procurement BU** | input |
| 13 | Enter | Purchasing > **Price Change Tolerance** (percentage and/or amount) | input |
| 14 | Select | Purchasing > **Ship-to Location** | input |
| 15 | Select | Purchasing > **Cancel Unfulfilled Demand** | Always / Never / Optional |
| 16 | Select | Purchasing > **Multiple Legal Entities on Order** | Allow / Warning / Error |
| 17 | Check | Purchasing > **Allow Requisition-To-Agreement UOM Conversion** | input |

## Save / submit
Click **Save and Close**. (The confirmation message text is UNVERIFIED.)

## Verification
- REST read-back of `requisitioningOptions`: `DefaultProcurementBUId`, `LineTypeId`, `AllowOnetimeAddrFlag`, `EnableApproverOverrideFlag`, DFF context codes.
- Screenshot `playbooks/screenshots/configure-requisitioning-bf-after.png`.
- Functional check: create a requisition and check deliver-to and line type defaults.

## Known UI differences / gotchas
- Field labels come from the 26D concept topic. The check box wording may differ slightly on screen.
- One-Time Location is ignored if structured one-time addresses are enabled.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-configure-business-units-with-requisitioning-business.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/assign-a-user-to-a-business-unit-that-supports-requisitioning.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-requisition-preferences-requisitioning-options.html
