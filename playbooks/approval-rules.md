# Playbook: Create Requisition and Purchasing Document Approval Rules

> Channel D (Claude browser pane) · Release: 26D · Status: DRAFT-FROM-DOCS
> Knowledge file: `knowledge/approvals.md`

## When to use
Approval rules, stages, participants and approval groups have no REST resource and no confirmed FSM CSV in 26D. REST only reads approval attributes (`approvalAttributesLOV`) and manages user-defined currency/summation attributes. So rules are created in the UI:
- Rule A (requisitions): Requisition Approval Amount > 50,000 → supervisor (1 level), then a Finance approval group.
- Rule B (purchasing documents): example amount rule on POs.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Requisitioning BU | Yes | US1 Business Unit | User / `knowledge` BU list |
| Functional currency | Yes | USD | Ledger of BU |
| Threshold | Yes | 50000 | User |
| Top Worker in Hierarchy | Yes for supervisory | CEO name | User / HCM |
| Finance approval group name | Yes | Finance Approvers | User; created in step group |
| Group members | Yes if group new | user names | User |
| PO threshold, Procurement BU | Yes for Rule B | 100000, US1 Business Unit | User |
| Rule names | Yes | REQ_GT_50K_SUPERVISOR, REQ_GT_50K_FINANCE, PO_GT_100K_SUPERVISOR | Agent (naming convention) |

## Pre-checks (read before write)
- `GET /fscmRestApi/resources/11.13.18.05/approvalAttributesLOV` to confirm attribute names available (Requisition Approval Amount, Functional Currency, Requisitioning BU).
- HCM: requisition preparers have a supervisor (manager) assignment. Otherwise supervisory routing fails.
- Open Manage Requisition Approvals and check existing rules in Header Hierarchy and Header Stage Consensus / First Responder Wins participants: no rule with the same name, no overlapping condition that would double-route.
- Check each participant you use keeps a catch-all rule (Automatic → Approved) for amounts below the threshold. Without it, documents are not auto-approved.
- BPM Worklist > Approval Groups: check whether "Finance Approvers" already exists.
- Backup: screenshot of each participant's rule list to `backups/<date>/approval-rules-before.png`.

## Navigation path
1. Navigator > My Enterprise > Setup and Maintenance
2. Approval group: Search Tasks: "Manage Approval Groups" (functional area Application Extensions; also in Define Approval Management for Procurement) → opens BPM Worklist, **Approval Groups** tab.
3. Requisition rule: Setup: Procurement > Functional Area: **Approval Management** > Task: **Manage Requisition Approvals** (or Search Tasks: "Manage Requisition Approvals") → "Manage Approvals Task" page.
4. PO rule: Setup: Procurement > Functional Area: **Approval Management** > Task: **Manage Purchasing Document Approvals**.

## Steps
### 1. Finance approval group (BPM Worklist)
| # | Action | Element (label as shown on screen) | Value |
|---|---|---|---|
| 1 | Click | **Create Approval Group** icon (Groups toolbar) | |
| 2 | Type | Group name (Details page) | Finance Approvers |
| 3 | Click | **Add Member** icon (Members section) | |
| 4 | Select | **Add to Group** dialog: User | |
| 5 | Search/select | user | finance user 1, then **OK** |
| 6 | Repeat 3–5 | | more members, in routing order if used in a serial participant |
| 7 | Click | **Save** | |

### 2. Requisition rule, supervisor part (Header Stage > Header Hierarchy participant, serial)
| # | Action | Element | Value |
|---|---|---|---|
| 1 | Select | Stage **Header Stage**, participant **Header Hierarchy** | |
| 2 | Click | add rule control (label UNVERIFIED, for example "Add Rule" / "+" in the rules table) | |
| 3 | Type | **Rule Name** | REQ_GT_50K_SUPERVISOR |
| 4 | Condition 1 | attribute **Requisition Approval Amount** (docs example label: "Approval Amount"), operator **is greater than** | 50000 |
| 5 | Condition 2 (and) | **Functional Currency** (docs example: "Functional Currency Code"), **equals** | USD |
| 6 | Condition 3 (and) | **Requisitioning BU**, **equals** | US1 Business Unit |
| 7 | Action | **Action Type** | Approval Required |
| 8 | Action | **Route Using** | Supervisory Hierarchy |
| 9 | Action | **Approval Chain Of** | Preparer |
| 10 | Action | **Start With** | Manager |
| 11 | Action | **Number of Approval Levels** | 1 |
| 12 | Action | **Top Worker in Hierarchy** | CEO name |

### 3. Requisition rule, Finance group part (runs after supervisor)
Header Hierarchy is serial within its stage but parallel with Header Hierarchy 2/3 and the Consensus / First Responder Wins participants of the same stage. To get "supervisor **then** Finance", put the Finance rule in the next stage: **Header Postapproval Stage**.
| # | Action | Element | Value |
|---|---|---|---|
| 1 | Select | Stage **Header Postapproval Stage**, participant **Header First Responder Wins** (any one member approves) or **Header Consensus** (all members approve) | per policy |
| 2 | Click | add rule control (UNVERIFIED label) | |
| 3 | Type | **Rule Name** | REQ_GT_50K_FINANCE |
| 4 | Conditions | same 3 conditions as step 2 | |
| 5 | Action | **Action Type** | Approval Required |
| 6 | Action | **Route Using** | Approval Group |
| 7 | Action | Approval group field (label UNVERIFIED) | Finance Approvers |
| 8 | Optional | auto-approve when the group returns no approvers (label UNVERIFIED) | leave off |

### 4. Catch-all rules (only if missing in each participant used)
| # | Action | Element | Value |
|---|---|---|---|
| 1 | Rule Name | | REQ_LE_50K_AUTO_HDR / _POST |
| 2 | Condition | Requisition Approval Amount **is less than or equal to** 50000 (+ currency, BU) | |
| 3 | Action | **Action Type** = Automatic, **Set Outcome To** = Approved | |

### 5. Purchasing document rule (Manage Purchasing Document Approvals)
| # | Action | Element | Value |
|---|---|---|---|
| 1 | Select | Stage **Preapproval**, participant **Preapproval Serial Participant** (UNVERIFIED which stage your org uses for fiscal approval; Terms stage is for contract terms) | |
| 2 | Click | add rule control (UNVERIFIED label) | |
| 3 | Type | **Rule Name** | PO_GT_100K_SUPERVISOR |
| 4 | Condition 1 | **Functional Total Amount** **is greater than** | 100000 |
| 5 | Condition 2 (and) | **Procurement BU** **equals** | US1 Business Unit |
| 6 | Action | **Action Type** | Approval Required |
| 7 | Action | **Route Using** | Supervisory Hierarchy |
| 8 | Action | **Approval Chain Of** | Buyer |
| 9 | Action | **Start With** | Manager |
| 10 | Action | **Number of Approval Levels** | 1 |
| 11 | Action | **Top Worker in Hierarchy** | CEO name |
| 12 | Catch-all | Functional Total Amount <= 100000 → Automatic / Approved | if missing |

## Save / submit
- Approval group: **Save** in BPM Worklist.
- Manage Approvals Task page: save button label UNVERIFIED (expect **Save** / **Save and Close**; some releases also need a deploy step). Expected: confirmation message, rules listed under the participant with status enabled.
- If editing through BPM Worklist instead: **Validate** (check Business Rule Validation – Log) then **Commit task**.

## Verification
- Diagnostic: user with Business Flow Troubleshooting role > user menu > **Run Diagnostic Tests** > Test Name `Requisition Approval%` > **Add to Run** > requisition number > **Run** > Report. Expect the new rules under **Passed Rules** for a 60,000 USD requisition and no **Invalid Rules**.
- Functional: create a 60,000 USD requisition in the BU; check approval preview shows manager then Finance Approvers; create a 10,000 USD one and expect auto-approval.
- REST read-back: `POST /fscmRestApi/resources/11.13.18.05/purchaseRequisitions/{purchaseRequisitionsUniqID}/action/getApprovalWorkflowStatus`.
- Screenshot `playbooks/screenshots/approval-rules-after.png`.

## Known UI differences / gotchas
- Labels for add/save/deploy controls on the Manage Approvals Task page were not found in 26D docs. Record the real labels here on first run (date, env).
- Do not edit seeded stages/participants in BPM Administration pages (known issues). Do not delete Modification Rules or Substitution Rules.
- Funds Override Approval rule: enable/disable only.
- Attributes marked (*) in docs (for example Overriding Approver, Supplier) need an extra "is not blank" condition.
- Postapproval FYI Stage is not configurable.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/approval-task.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/approval-rules.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/various-aspects-of-approval-rules.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/considerations-for-setting-up-requisition-approval-task.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/purchasing-approval-stages.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/example-of-requisition-approval-policy.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/requisition-attributes.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/purchase-order-and-purchase-agreement-attributes.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/create-approval-groups.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-approval-rule-sets-and-rules.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/document-approvals-in-procurement.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-manage-funds-override-approval-rules-for-requisitions.html
