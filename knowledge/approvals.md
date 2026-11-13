# Procurement Approvals (Requisitions, Purchasing Documents, Supplier Registration, Spend Authorization)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Approval routing for procurement documents and supplier objects. It runs on the Approval Management Extensions (AMX) rules engine with the BPM workflow. Each approval task has **stages**. A stage has **participants**. A participant has **rules**. A rule has conditions (IF) and actions (THEN). Approvers act in the BPM Worklist (Worklist task) or by email reply.
Affects: requesters, buyers, approvers, supplier managers, finance.

## Where in Fusion (FSM)
- Offering: Procurement. Functional area: **Approval Management**. Task list: **Define Approval Management for Procurement**.
- Tasks (exact labels from the docs):
  - Manage Task Configurations (Application Extensions functional area; opens BPM Worklist)
  - Manage Approval Groups (Application Extensions; opens BPM Worklist, Approval Groups tab)
  - **Manage Requisition Approvals** (also in Self Service Procurement functional area)
  - **Manage Purchasing Document Approvals** (POs, agreements, change orders)
  - Manage Supplier Negotiation Approvals
  - Manage Supplier Negotiation Award Approvals (spelled "Mange..." on the doc page)
  - **Manage Supplier Registration Approvals** (external registrations)
  - **Manage Internal Supplier Registration Approvals**
  - **Manage Supplier Spend Authorization Approvals**
  - Manage Internal Supplier Profile Change Approvals / Manage Supplier Profile Change Approvals
  - Manage External Purchase Price Approvals
  - Manage Task Configuration for Procurement (BPM Worklist)
- UI: the Manage ... Approvals tasks open the procurement "Manage Approvals Task" page (Oracle Procurement Approval Rules Management page, integrated with AMX). Task-level settings (expiration, escalation, notifications, aggregation) are in **BPM Worklist** > Task Configuration. Approval groups are in BPM Worklist > Approval Groups tab.
- 26D Redwood: no Redwood approval-rule editor for requisitions or purchasing documents was found in 26A–26D What's New. 26D Sourcing setup says Supplier Negotiation Approval Rules and Award Approval Rules are **not yet** in Redwood. Notifications have Redwood-style templates (separate features).

## Prerequisites & dependencies
- HCM: workers with supervisor (manager) assignments for Supervisory Hierarchy routing; jobs with job levels for Job Level routing; positions and position hierarchy for Position Hierarchy routing.
- Approval groups (Manage Approval Groups) before rules that route to them.
- Procurement agents with **Manage Suppliers** action (supplier managers) for supplier registration and spend authorization seeded rules.
- Optional: user-defined attributes (currency-based, summation, mapping set based).

## Key fields
### Seeded stages and participants
**Requisition approval** (Manage Requisition Approvals), in order:
1. **Header Preapproval Stage**: Requester FYI (seeded rule), Preapproval Header Consensus (parallel, all approve), Preapproval Header First Responder Wins (parallel), Preapproval Header Hierarchy (serial).
2. **Header Stage** (fiscal/amount approvals): Header Hierarchy (serial), Header Hierarchy 2 (serial, runs in parallel with 1), Header Hierarchy 3 (serial), Header Stage Consensus (parallel), Header Stage First Responder Wins (parallel).
3. **Header Postapproval Stage**: Header Consensus, Header First Responder Wins, Postapproval Header Hierarchy (serial), plus delivered Funds Override Approval participant (parallel, consensus; enable/disable only).
4. **Postapproval FYI Stage**: FYI to preparer. Not configurable.

**Purchasing documents** (POs, agreements, change orders; Manage Purchasing Document Approvals), in order:
1. **Preapproval**: Preapproval FYI Participant, Preapproval Parallel Consensus Participant, Preapproval Parallel First Responder Wins Participant, Preapproval Serial Participant.
2. **Terms**: Terms Approval FYI Participant, Terms Approval Serial Participant, Terms Approval 2 Serial Participant, Terms Approval 3 Serial Participant, Terms Approval Parallel First Responder Wins Participant, Terms Approval Parallel Consensus Participant.
3. **Post Approval**: Postapproval Parallel Consensus Participant, Postapproval Parallel First Responder Wins Participant, Postapproval Serial Participant, plus delivered Funds Override Approval (Postapproval Stage, parallel, consensus).
4. **Post Approval FYI**: Post Approval FYI Participant.

**Supplier registration** (both tasks): First stage approvals, then Second stage approvals. Each stage: Parallel Approval First Responder Wins, Parallel Approval, Serial Approval. Seeded rule (first stage, First Responder Wins): Prospective → supplier administrator; Spend Authorized → supplier managers.

**Supplier spend authorization**: Spend Authorization Approval First Stage, then Second Stage. One participant each: Parallel Approval First Responder Wins. Seeded rule routes all requests to supplier managers of the Procurement BU. Unused seeded participants **must be disabled**. Routing group: **Route Using** = Single Approver, **User Type** = Supplier Managers.

### Participant properties
| Property | Values | Meaning |
|---|---|---|
| Routing type | Serial, Parallel, FYI | FYI cannot change the outcome |
| Voting regime | Serial, Consensus, First Responder Wins | Consensus = all must approve. First Responder Wins = first approve/reject decides for all. |

### Rule components
| Field (UI label) | Values / meaning |
|---|---|
| Rule Name | Identifier (Query by Example filter on Rule Name) |
| Condition | Attribute + operator + value, joined by and/or. All must be true. Rules in a header-dimension stage can use line or distribution attributes. Attributes marked (*) in docs need an extra "is not blank" test. |
| Action Type | **Approval Required**, **Automatic** (Set Outcome To Approved/Rejected), **Information Only** (FYI) |
| Route Using | **Approval Group**, **Job Level**, **Position Hierarchy**, **Single Approver**, **Supervisory Hierarchy**, **User-Defined Routing** (supplier registration docs list: Supervisory, Position, Job Level, Single User, User-Defined Approval Groups) |
| Supervisory Hierarchy fields | **Approval Chain Of** (Preparer, Requester, Buyer, or a named worker), **Start With** (Manager default), **Number of Approval Levels**, **Top Worker in Hierarchy** |
| Job Level fields | Approval Chain Of, Start With, **Minimum Job Level**, Top Worker in Hierarchy, **Include** (everyone / first and last / last only) |
| Position Hierarchy fields | **Position Chain Of**, Start With (Next Position default), Minimum Job Level, Top Worker in Hierarchy, Include |
| Single Approver | Specific worker, or **User Type** = person on the document (requester, preparer, project manager, assigned buyer, principal investigator, funds override approver, supplier managers) |
| Approval Group | Group name. Option to auto-approve if the group returns no approvers. |

### Key rule attributes (exact names from docs)
- Requisition header: **Requisition Approval Amount** (incl. nonrecoverable tax), Requisition Amount, **Functional Currency**, **Requisitioning BU**, Requisition BU Name, Ledger, **Preparer**, Preparer Username, Preparer Job Level, Emergency Requisition, Overriding Approver, Funds Override Approver.
- Requisition line: Line Approval Amount, **Category Name**, Procurement Category Hierarchy (Level 1–10), UNSPSC, **Requester**, Requester Username, Requester Job Level, Requester Level 1–10 Supervisor, Item, Supplier, Deliver-to Location, Urgent.
- Requisition distribution: Distribution Approval Amount, Cost Center, Cost Center Manager, Natural Account, Project, Project Manager.
- PO/agreement header: **Document Total Amount**, Document Ordered Amount, **Functional Total Amount**, Agreement Amount, **Document Currency**, Functional Currency, **Procurement BU**, Requisitioning BU, Sold-to Legal Entity, Buyer, Buyer Job Level, Submitter, Document Style, Document Type, **Is Change Order**, Change Order Type, Change in Document Total Amount, Supplier, Payment Terms, PO Overriding Approver.
- PO line/schedule/distribution: Category Name, Procurement Category Hierarchy Level, Price Change Percent, Line Total Amount Change Percent, Cost Center, Requester user name, Project.
- Note: the docs requisition example uses labels "Approval Amount" and "Functional Currency Code"; the attribute list says "Requisition Approval Amount" and "Functional Currency". Use what the condition browser shows.
- User-defined attributes: currency-based (`approvalCurrencyAttributes`), summation (`approvalSummationAttributes`), mapping-set based (Mapped Approval Attribute 1–5 using mapping sets `REQ_APPROVAL_MAPPING_SET_X` / `REQ_APPROVAL_DATA_SET_X` under the Purchasing subledger application).

### Task configuration (BPM Worklist > Task Configuration)
- Defaults: Allow all participants to route task to other participants (on), Allow participants to edit future participants (on), Allow initiator to add participants (on), Enable auto claim (on).
- Early completion: complete on Approve or Reject (requisition default completes on Reject).
- Task aggregation: Once per task (requisition default), Once per stage, None (purchasing document default).
- Expiration (auto-reject), Escalation (LDAP manager chain, max levels), Renewal.
- Notifications: **Make notification actionable**, **Send task attachments with email notifications**.

### Approval groups (BPM Worklist)
- Steps: Manage Approval Groups > Approval Groups tab > **Create Approval Group** icon > name > Members > **Add Member** > User or Approval Group > OK > **Save**.
- Parallel participant: one member claims; serial participant: every member in member order.
- Do not delete a group used in a rule. Edit is allowed.

## Common mistakes
- A participant in use with no rule that applies: the document is not auto-approved. Add a catch-all Automatic/Approved rule per participant.
- Amount rules without Functional Currency and Requisitioning BU when policies differ by BU.
- Optional attribute in a condition without an "is not blank" test.
- Editing seeded stages or participants in BPM Administration pages. Oracle advises against it (known issues).
- Deleting predefined rule sets, or **Modification Rules** / **Substitution Rules** in BPM Worklist.
- Missing supervisor in HCM, or no supplier manager in the BU: approval errors or no approver.
- Position-hierarchy routing: Oracle BPM does not support email notifications; without auto claim, emails have no action buttons.
- Mapping-set rules: wrong attribute name or trailing spaces return null; always add a null-handling rule.
- Not disabling unused spend authorization participants (mandatory).

## Channel & exact technique
- Preferred channel: **D (UI)**. No REST resource creates or edits approval rules, stages, participants or approval groups (none found in 26D REST guide or 26D new resources list).
- A (REST, supporting only):
  - `GET /fscmRestApi/resources/11.13.18.05/approvalAttributesLOV` (+ `/{AttributeId}`): attributes available for rules
  - `GET /fscmRestApi/resources/11.13.18.05/approvalAttributeValuesLOV`
  - `GET|POST /fscmRestApi/resources/11.13.18.05/approvalCurrencyAttributes`, `GET|PATCH|DELETE .../{CurrencyAttributeId}` (new 26D)
  - `GET|POST /fscmRestApi/resources/11.13.18.05/approvalSummationAttributes`, `GET|PATCH|DELETE .../{SummationAttributeId}` (new 26D)
  - Diagnostics: `POST /fscmRestApi/resources/11.13.18.05/purchaseRequisitions/{purchaseRequisitionsUniqID}/action/getApprovalWorkflowStatus` (new 26D), `.../action/retrieveCurrentApprovers` (26C)
  - Always `rest_describe` first.
- B (FSM CSV): UNVERIFIED (assume not supported for AMX rules).
- C (FBDI): none.
- D (UI): `playbooks/approval-rules.md`.
- Generic BPM Worklist rule editing (Manage Task Configurations): Task Configuration tab > select task > **Edit task** > **Assignees** > participant > **Go to rule** > Rules tab > IF (Left Value / operator / Right Value via Condition Browser) and THEN (**Insert Action** > Add Approver > list builder; Response Type Required/FYI, Number of Levels, Starting Participant, Top Participant, Auto Action Enabled, Auto Action) > **Validate** (Business Rule Validation – Log) > **Commit task**.

## How to verify
- Run diagnostic **Requisition Approval - Validate**: user with **Business Flow Troubleshooting** role > user menu > **Run Diagnostic Tests** > Test Name `Requisition Approval%` > **Add to Run** > enter requisition number > **Run** > Report. Shows Failed Participants, Participants without Any Rules, AutoReject Rules, Passed Rules, Invalid Rules.
- Functional test: create a requisition above and below the threshold, open **Manage Approvals** (approval preview) before submit, check the approver list and rule names (rule names visible by default since 25B).
- REST: `getApprovalWorkflowStatus` action on the submitted requisition.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/overview-of-managing-approvals-and-notifications.html — task list under Define Approval Management for Procurement
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/approval-task.html — task names, stage/participant/rule model
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/approval-rules.html — action types, Route Using values and fields
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/various-aspects-of-approval-rules.html — navigation, participants, voting regimes, routing fields
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/purchasing-approval-stages.html — PO/agreement stages and participants
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/considerations-for-setting-up-requisition-approval-task.html — requisition stages and participants
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/example-of-requisition-approval-policy.html — example rules
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/requisition-attributes.html — requisition attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/purchase-order-and-purchase-agreement-attributes.html — PO/agreement attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/approval-rules-management-for-procurement.html — AMX page, BPM task configuration settings
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-approval-rule-sets-and-rules.html — BPM Worklist rule editing, Validate, Commit
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/create-approval-groups.html — approval groups
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/types-of-participants.html — participant types
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/document-approvals-in-procurement.html — worklist actions, email, diagnostic test
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-manage-funds-override-approval-rules-for-requisitions.html — funds override participants
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/set-up-supplier-registration-approvals.html — registration approvals
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/supplier-spend-authorization-approvals.html — spend authorization approvals
- https://docs.oracle.com/en/cloud/saas/readiness/scm/24c/ssproc24c/24C-ssproc-wn-f32332.htm — mapping set approval attributes, privilege POR_MANAGE_APPROVAL_TASK_PRIV
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f50411.htm — new approval REST resources, getApprovalWorkflowStatus
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f50341.htm — negotiation approval rules not yet Redwood
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-approval-attributes-list-values.html, https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-currency-based-approval-attributes.html, https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-summation-approval-attributes.html — REST paths
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchase-requisitions.html — getApprovalWorkflowStatus (via search snippet)

## UNVERIFIED
- Exact button/icon labels on the procurement Manage Approvals Task page (for example "Edit Rules", "Add Rule", "Deploy").
- Whether a Redwood approval-rule editor exists for requisitions or purchasing documents in 26D (none found).
- Setup Task CSV support for any approval task.
- Request/response schema of `getApprovalWorkflowStatus` and `approvalAttributeValuesLOV` path details (not fetched).
- Manage Approval Groups FSM functional area under Procurement offering (docs say Application Extensions).
