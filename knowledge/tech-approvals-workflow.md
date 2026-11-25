# Approvals: Technical Workflow (BPM REST, Transaction Console, Task Config, Notifications, Migration, Troubleshooting)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL
> Extends `knowledge/approvals.md` (rule model, stages, participants, attributes) and `playbooks/approval-rules.md` (UI rule creation). Do not repeat them; read them first.

## Business purpose
Technical-consultant view of procurement approvals: what can be configured, read, acted on, migrated and recovered by API, and what stays in the UI. Covers BPM Worklist REST (`/bpm/api/4.0/tasks`), business REST approval reads and actions, Transaction Console, task configuration (expiration/escalation/notifications), BI Publisher notification templates, rule migration between pods (SOA Composer), diagnostics.
Affects: requesters, approvers, buyers, procurement admins, support.

## Where in Fusion (FSM)
- Offering: Procurement. Functional area: **Approval Management** (task list **Define Approval Management for Procurement**). Exact task names in `approvals.md`.
- **Manage Task Configurations** (Application Extensions): opens BPM Worklist > Task Configuration tab. Needed for assignment, expiration, escalation, notification, aggregation.
- **Transaction Console**: Navigator > Tools > Transaction Console (page "Transaction Manager: Transactions"). Not an FSM task.
- **Run Diagnostic Tests**: user name menu (needs role **Business Flow Troubleshooting**). Not an FSM task.
- **SOA Composer**: `https://host:port/soa/composer` (Export/Import). Needs **BPMProcessAdmin** (HCM doc; see UNVERIFIED for procurement).
- BI Publisher catalog: notification reports (Requisition Approval Email Report etc.).

## Prerequisites & dependencies
- Rules, groups, HCM hierarchies: see `approvals.md`.
- Calling `/bpm/api/4.0/tasks`: a user who owns/participates in the task. Admin-wide reads use `assignment=ADMIN|ALL` (whether this needs a special privilege is not stated in the docs, UNVERIFIED).
- Transaction Console: job role with duty **Review Procurement Approval Transactions as Administrator** (`ORA_PO_REVIEW_PRC_APPROVAL_TRANSACTIONS`). Failed-transaction actions "usually" need administrator access.
- Scheduled process **Refresh Transaction Administrator Console Transaction Status** (Financials 26D page: runs automatically hourly; 24A Procurement readiness note: admin must schedule it, recommended hourly. Check on the pod with `ess_*`).
- Notification templates: BI Administrator privileges; Template Builder for Word; email domain set up in Oracle Analytics Publisher.

## Key fields

### 1. Is there any API to create / export approval rules or groups?
| Question | What the 26D docs show |
|---|---|
| REST resource to create/update/read approval rules, stages, participants | None found in the 26D Procurement REST guide. Only attribute helpers: `approvalAttributesLOV`, `approvalAttributeValuesLOV`, `approvalCurrencyAttributes`, `approvalSummationAttributes` (see `approvals.md`). |
| REST resource for approval groups | None found in official docs. Customer Connect posts ask for it with no confirmed answer (not an official source). UNVERIFIED that none exists. |
| FSM Setup Task CSV for approval tasks | Not documented. A community post reports Export CSV / Import CSV greyed out under Manage Purchasing Document Approvals (not official). UNVERIFIED. |
| FBDI for approval rules | None. |
| Config package (implementation project export/import) | Order Management guide documents approval rules migration through config packages (not Procurement). For Procurement: UNVERIFIED. |
| SOA Composer Export/Import | Documented (HCM guide): Export SOA Changes > Download > edit `CS_SOA_ExportList.txt` > Import SOA Changes on target. Source and target must be same patch level and release. Export carries saved/uncommitted rule changes too. Verify on target in **Transaction Manager: Rules**. Procurement-specific doc: only My Oracle Support note 2600760.1 (title seen only, not readable here, UNVERIFIED). |
| BPM Worklist approval group REST | Not found. `/bpm/api/4.0/*` Manage Tasks covers tasks only (list below). |

Conclusion: rules and groups = **channel D** (UI) or SOA Composer for pod-to-pod migration (also UI, no API documented). Do not invent a REST path for them.

### 2. BPM Worklist REST (REST API for Common Features, "Manage Tasks")
Base: `https://<pod>/bpm/api/4.0/...` (NOT under `/fscmRestApi`). JSON. Basic auth or the pod's configured auth (docs do not specify, UNVERIFIED for OAuth/JWT).

| Operation | Method + path |
|---|---|
| Retrieve a Task List | `GET /bpm/api/4.0/tasks` |
| Retrieve a Task | `GET /bpm/api/4.0/tasks/{id}` |
| Perform Action on Task | `PUT /bpm/api/4.0/tasks/{id}` |
| Perform Bulk Action on Tasks | `PUT /bpm/api/4.0/tasks` |
| Retrieve Task History | `GET /bpm/api/4.0/tasks/{id}/history?displayStyle=flatList` |
| Retrieve Task Payload | `GET /bpm/api/4.0/tasks/{id}/payload` (XML) |
| Update a Task Payload | `PUT /bpm/api/4.0/tasks/{id}/payload` |
| Comments | `GET|POST /bpm/api/4.0/tasks/{id}/comments` |
| Attachments | `GET|POST /bpm/api/4.0/tasks/{id}/attachments`; `GET|DELETE .../attachments/{attachmentName}`; `GET .../attachments/{attachmentName}/stream` |
| Task form URI | `GET /bpm/api/4.0/tasks/{id}/form` |
| Custom task lists | `GET /bpm/api/4.0/tasks/views`, `GET /bpm/api/4.0/tasks/views/{viewname}` |

**GET /tasks query parameters (exact):** `assignment` (default `MY_AND_GROUP`; `MY`, `GROUP`, `MY_AND_GROUP`, `MY_AND_GROUP_ALL`, `REPORTEES`, `OWNER`, `REVIEWER`, `PREVIOUS`, `ALL`, `ADMIN`), `status` (default `ASSIGNED`; `ASSIGNED`, `COMPLETED`, `SUSPENDED`, `WITHDRAWN`, `EXPIRED`, `ERRORED`, `ALERTED`; `COMPLETED` only with `ADMIN`, `ALL`, `PREVIOUS`), `keyword` (title), `createdBy`, `fromuser`, `identificationKey`, `outcome`, `priority` (1-5 or Any), `pattern` (`ToDo`), `since`/`until` (`YYYY-MM-DD HH:MM:SS`, UTC), `dueDateFrom`/`dueDateTo`, `fields` (createdDate, creator, updatedDate, fromUser, tasknumber, priority, ownerUser, state, approvalDuration, taskDefinitionName, taskNameSpace, taskId, category, assignedDate, dueDate, outcome, ecid, identificationKey), `orderBy` (`field:asc|desc`), `limit` (default 25), `offset`, `totalResults`, `metadataFlag`, `showActionFlag`, `showPermissionFlag`.
Task item fields include `taskId`, `number`, `title`, `state`, `outcome`, `identificationKey`, `taskDefinitionName`, `assignees`, `actionList`, `payload`, `history`, `comments`.
`ALL`/`ADMIN` = no filtering by assignment or creator.

**Perform action (single):**
```
GET /bpm/api/4.0/tasks/{taskId}        -> read actionList[].actionId (e.g. APPROVE, REJECT custom; REASSIGN, DELEGATE, SUSPEND, ESCALATE system)
PUT /bpm/api/4.0/tasks/{taskId}
Content-Type: application/json
{"action": {"id": "APPROVE"}, "comments": "text"}
```
Success: response has `outcome`="APPROVE", `titlePrefix`="Completed", `actionList` only VIEW_* actions.
Action names on the page: APPROVE, REJECT, REASSIGN, DELEGATE, WITHDRAW, SUSPEND, RESUME, DELETE, PURGE, ACQUIRE, RELEASE, PUSHBACK, ERROR, ADHOC_ROUTE, INFO_REQUEST, INFO_SUBMIT, SKIP_CURRENT_ASSIGNMENT, SAVE, ESCALATE. Custom actions depend on the task definition.
Body fields: `action{id,type,assignees[Identity]}`, `comment{commentStr}`, `comments` (string), `priority`, `routingType` (`Simple|Sequential|Parallel`, ADHOC_ROUTE), `routingAction`, `votersPercentage` (single) / `voterPercentage` (bulk) , `defaultActionForGroupVote`.
Reassign payload (Oracle bulk example): `{"tasks":["100003"],"action":{"id":"REASSIGN","assignees":[{"id":"jdoe","type":"USER"}]},"comments":"..."}`; single version: same without `tasks`.
Bulk: `PUT /bpm/api/4.0/tasks` with `{"tasks":["100001","100002"],"action":{"id":"APPROVE"},"comments":"..."}`. Returns `Collection` (count, items, ...).
Errors: 400 invalid task number (no action done), 401, 404, 409 (state does not allow action), 500.
Known doc ambiguity: pages say it is unclear whether the action name goes in `action.id` or `action.type`. Oracle's HCM sample uses `action.id`. Use `id`; if the response is just the task GET (no state change) retry once with `type` after reading the error. A Customer Connect thread reports PUT returning only the GET result (not official).
Roles: not documented on any of these pages. Actor must be assignee/owner/admin of the task (UNVERIFIED exact privilege).

**Task identity link to business doc:** `identificationKey` is the key the app sets for the document (UNVERIFIED which value for requisitions/POs). `taskDefinitionName` identifies the task type. Read one real task to learn it; use `fields=` to keep output small.

**HCM/Common "workflow"/"approval" REST:** no other generic workflow or approval resource was found in the Common Features REST endpoint list; the Manage Tasks group above (17 operations) is the only BPM one. HCM approvals are in the HCM guide (not researched here).

### 3. Business REST approval reads and actions (Procurement 26D)
| Need | Resource and path | Notes |
|---|---|---|
| Submit requisition | `POST /fscmRestApi/resources/11.13.18.05/purchaseRequisitions/{purchaseRequisitionsUniqID}/action/submitRequisition` | exact name `submitRequisition` (not `submit`) |
| Withdraw requisition | `POST .../purchaseRequisitions/{uniqID}/action/withdraw` | |
| Approval workflow status | `POST .../purchaseRequisitions/{uniqID}/action/getApprovalWorkflowStatus` | new 26D; payload not shown on index page: `rest_describe` / op page |
| Current approvers | `POST .../purchaseRequisitions/{uniqID}/action/retrieveCurrentApprovers` | 26C |
| Approver checkout | `POST .../purchaseRequisitions/action/initiateApproverCheckout` (collection) | purpose UNVERIFIED |
| Reassign requisitions | `POST .../purchaseRequisitions/action/reassignRequisitions` (collection) | reassigns requisition ownership/preparer, not the approval task (UNVERIFIED semantics) |
| Resubmit PO for approval | `POST /fscmRestApi/resources/11.13.18.05/purchaseOrders/{purchaseOrdersUniqID}/action/submit` | Content-Type `application/vnd.oracle.adf.action+json`; body `{"bypassApprovalsFlag": false}` (boolean, only allowed field, default false; `true` bypasses approval). Response `{"result":"Success"}`. PO in Pending Approval is withdrawn automatically before resubmit. Oracle's own example is inconsistent (name/parameters wrapper, string value, URL missing `/action/submit`): use the schema form. |
| Withdraw PO / change order | `POST .../draftPurchaseOrders/{draftPurchaseOrdersUniqID}/action/withdraw` | exists on `draftPurchaseOrders`, NOT on `purchaseOrders` (26D `purchaseOrders` action list has no withdraw, no approve/reject) |
| PO approval action history | `GET .../purchasingDocumentHistoryDetails/{purchasingDocumentHistoryDetailsUniqID}/child/documentVersionActions` | `q=DocumentId=<id>`, `orderBy=SequenceNumber:asc`, `totalResults=true`. Get the parent UniqID by querying the parent collection first (`q=DocumentId=...`). Item attributes: `DocumentId`, `VersionId`, `DocumentTypeCode`, `DocumentSubTypeCode`, `SequenceNumber`, `ActionCode` (SUBMIT, APPROVE, REJECT ...), `Action`, `ActionDate`, `PerformedById`, `PerformedBy`, `AdditionalInformation`, `OriginatorRole`, `EsignEnvelopeId`, `EsignEnvOwnerEmailId`. Finder `PrimaryKey;ActionCode,DocumentId,DocumentSubTypeCode,DocumentTypeCode,SequenceNumber`. |
| PO approvers / pending approvers | no REST found | use BPM `/tasks` (`identificationKey`) or Transaction Console (UNVERIFIED mapping) |
| Approve / reject a document | no business REST action | use BPM `PUT /bpm/api/4.0/tasks/{id}` with `APPROVE` / `REJECT` |

### 4. Task configuration (BPM Worklist > Task Configuration, via Manage Task Configurations)
Settings (all UI, no API found): assignment/routing flags (allow route to others, edit future participants, initiator adds participants, auto claim), early completion (requisition default completes on Reject), approval preconditions (require comments), administrators to notify on routing error, task aggregation (Once per task = requisition default; Once per stage; None = purchasing document default), **Expiration** (auto-reject, whole task not per approver), **Escalation** (LDAP management chain, max levels; at cap with no action = auto-reject), **Renewal**, notification settings (email/voice/IM/SMS per participant type and action; reminders before expiration or after assignment), **Make notification actionable**, **Send task attachments with email notifications**.
Save path: Tasks to be configured > select task > **Edit task** > Assignees / task settings > **Validate** (Business Rule Validation - Log) > **Commit task**.
If Application Composer fields were created: click **Start Synchronization** when prompted.
Rule set must be Active and effective (leave effective date Always). Never delete **Modification Rules** or **Substitution Rules**.

### 5. Transaction Console (Tools > Transaction Console)
- Page: Transaction Manager: Transactions. Filters: Status (default e.g. Failed), Name, Process Name, Priority, Submitted By, Assignee Name, Assignee Role. Saved searches. Refresh icon (page or row). Opening details refreshes that transaction.
- Details: Issues list, Instructions, Details, Issue Priority, Assigned To, comments (comments visible only in Transaction Console, not in Worklist). **Download** in details = diagnostic log (shows related workflow task, approval rule and the condition that caused the error).
- Actions menu (table or details): **Withdraw** (even if you did not submit), **Reassign**, **Recover** (for faulted approvals; availability depends on status and access), terminate failed approval process (Procurement page wording), **Download** spreadsheet (Actions > Download).
- Recover flow (24A Procurement note): select failed transaction > read issue description, diagnostic log, resolution > fix cause (often a faulty approval rule) > **Recover** > approver completes approval.
- Alternative: withdraw, fix the rule, resubmit (requisition `submitRequisition`, PO `action/submit`).
- No REST for Transaction Console found. Channel D (or read via BPM `status=ERRORED`).

### 6. Notifications (BI Publisher based)
- Each procurement workflow task has a predefined report in the BI catalog. Example: **Requisition Approval Email Report** > layout **Requisition Approval Email Layout** > data model **Requisition Approval Email Data Model** (folder: Self Service Procurement per readiness notes; exact catalog path not on the 26D page, UNVERIFIED).
- Customize: use **Customize** (More menu) or copy the report to the **Custom** folder; edit the copied `.rtf` layout in **Template Builder for Word** only. Report, layout, data model, subtemplate: copy and edit. Style template: cannot be modified.
- Prereqs: enable configurable notifications in Offerings (Procurement), Sourcing setting **Negotiation Invitation Notification with Oracle Analytics Publisher**, email domain in Oracle Analytics Publisher, BI Administrator privileges.
- Mobile: avoid adding table columns. Approver-attached files are not attached to the requisition/PO.
- Email vs online notification can be edited separately: administrator generates the notification, **Edit**, Page Composer to hide/show fields or add static text.
- Redwood-style notifications (requisition approval, FYI, PO/agreement, supplier items) are in 25A-26A readiness notes: unmodified templates switch automatically; for modified templates, reapply changes on the new Redwood template after update.
- Email reply approve/reject works; other actions need Worklist. More than 25 requisition lines: approver must log in. Position-hierarchy routing: no email notifications.
- Channel: D (BI catalog) or BI/Catalog SOAP (UNVERIFIED, not researched).

### 7. Diagnostics
| Test | Use |
|---|---|
| **Requisition Approval - Validate** (search `Requisition Approval%`) | Failed Participants, Participants without Any Rules, AutoReject Rules, Passed Rules, Invalid Rules. Needs requisition number as input. Role: Business Flow Troubleshooting. |
| Requisition Details Validate | header/line/distribution DB data |
| Manage Purchasing Documents Lifecycle Validate | DB data for a PO |
| Define Purchasing Configuration Validate | purchasing config |
| Configure Requisitioning Business Function Validate | BU suitability for requisitions |
No purchase-order-specific approval diagnostic test is listed on the 26D diagnostic page (the 26D list has no approval test other than the Requisition one in the approval page). Community note: requisition approval diagnostic may not work for workflows built directly in BPM instead of the procurement rules page (unofficial).

## Common mistakes
- Looking for an approval rule REST/FBDI/CSV: none documented. Do not call `rest_create` on guessed resources.
- Using `/fscmRestApi/...` path for tasks: BPM REST is `/bpm/api/4.0/tasks`.
- Using `action: submit` on requisitions (correct: `submitRequisition`), or withdraw on `purchaseOrders` (correct: `draftPurchaseOrders`).
- `bypassApprovalsFlag=true` on PO submit skips approvals entirely: high-impact, needs explicit user confirmation.
- Acting on a task in a state that does not allow it: 409. Re-read `actionList` first.
- Hardcoding action ids: read `actionList` per task.
- Importing SOA Composer archive from a different patch level: import fails. Export also carries uncommitted rule changes: trim `CS_SOA_ExportList.txt`.
- Forgetting to schedule **Refresh Transaction Administrator Console Transaction Status**: stale console.
- Expiration/escalation apply to the whole task, not per approver.
- Editing style templates for notifications (not allowed); editing the predefined report instead of a copy.
- Rule changes in BPM not committed (**Commit task**) or rule set not Active.

## Channel & exact technique
- Preferred channel: **A** for runtime (read approval status/history, submit/withdraw, act on tasks via BPM REST). **D** for design-time (rules, groups, task configuration, notification templates, Transaction Console recovery). No B or C path documented.
- A (REST): paths in sections 2 and 3. Always `rest_describe` first for `fscmRestApi` resources. `/bpm/api/4.0` is a different root: check the MCP `rest_get`/`rest_action` can target it (UNVERIFIED in code; flag to caller).
- B (FSM CSV): UNVERIFIED for approval tasks.
- C (FBDI/ESS): none for rules. ESS only for **Refresh Transaction Administrator Console Transaction Status** (check name with `ess_*`).
- D (UI): `playbooks/approval-rules.md`; extend later with Transaction Console recovery and Task Configuration playbooks.

### Typical technical-consultant tasks
| Task | Channel | How |
|---|---|---|
| Create/change approval rule or group | D | `playbooks/approval-rules.md` (Manage Requisition/Purchasing Document Approvals, BPM Worklist Approval Groups) |
| List attributes usable in rules | A | `GET approvalAttributesLOV` |
| Add currency/summation attribute | A | `POST approvalCurrencyAttributes` / `approvalSummationAttributes` |
| Back up rules before change | D (screenshot) or SOA Composer Export | no API export found |
| Migrate rules DEV to TEST/PROD | D (SOA Composer) | same patch level; trim export list; verify in Transaction Manager: Rules |
| Test a rule | A+D | create requisition, `getApprovalWorkflowStatus`, `retrieveCurrentApprovers`, Run Diagnostic **Requisition Approval - Validate** |
| Find who is approving now | A | requisition: `retrieveCurrentApprovers`; any: `GET /bpm/api/4.0/tasks?assignment=ADMIN&status=ASSIGNED&keyword=<doc no>&fields=...` |
| Approval history | A | PO: `purchasingDocumentHistoryDetails/.../child/documentVersionActions`; any task: `GET /bpm/api/4.0/tasks/{id}/history` |
| Approve/reject/reassign/withdraw a stuck task | A | `PUT /bpm/api/4.0/tasks/{id}` after reading `actionList` |
| Resubmit PO | A | `purchaseOrders/{id}/action/submit` |
| Withdraw requisition / PO | A | `purchaseRequisitions/{id}/action/withdraw`; `draftPurchaseOrders/{id}/action/withdraw` |
| Recover faulted approval | D | Transaction Console > Recover; or fix rule, withdraw, resubmit (A) |
| Find faulted approvals | A or D | `GET /bpm/api/4.0/tasks?assignment=ADMIN&status=ERRORED`; Transaction Console filter Status = Failed |
| Set expiration/escalation/renewal | D | Manage Task Configurations > Edit task > Commit task |
| Customize approval email | D | BI catalog copy report, edit RTF in Template Builder for Word |
| Mass reassign approver (vacation) | A | bulk `PUT /bpm/api/4.0/tasks` with REASSIGN; vacation/delegation rules in Worklist preferences are UI (not researched, UNVERIFIED) |
| Route missing approver | A+D | HCM supervisor check (REST `workers`), fix rule; see `approvals.md` common mistakes |

## How to verify
- After rule change: run **Requisition Approval - Validate** for a test requisition; rules appear under Passed Rules; no Invalid Rules / Failed Participants.
- `POST .../purchaseRequisitions/{id}/action/getApprovalWorkflowStatus` and `retrieveCurrentApprovers`.
- BPM: `GET /bpm/api/4.0/tasks/{id}` shows `state`, `outcome`; `/history` shows actions.
- After task action: response `outcome` set and `titlePrefix`=`Completed`.
- PO: `documentVersionActions` list shows SUBMIT then APPROVE/REJECT.
- After SOA import: Transaction Manager: Rules lists migrated rules.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/rest-endpoints.html — list of 17 Manage Tasks BPM operations and paths
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-bpm-api-4.0-tasks-get.html — GET /tasks parameters, fields
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-bpm-api-4.0-tasks-put.html — bulk action schema, examples
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-bpm-api-4.0-tasks-id-put.html — single action, action names, errors
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-bpm-api-4.0-tasks-id-history-get.html — task history schema
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-bpm-api-4.0-tasks-id-payload-get.html — payload (XML)
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/Performing_Task_Action.html — actionList then PUT `{"action":{"id":"APPROVE"}}`
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchase-requisitions.html — requisition actions list
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchase-orders.html — PO actions list (submit; no withdraw/approve)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-purchaseordersuniqid-action-submit-post.html — bypassApprovalsFlag payload
- https://docs.oracle.com/en/cloud/saas/procurement/25c/fapra/op-draftpurchaseorders-draftpurchaseordersuniqid-action-withdraw-post.html — withdraw on draftPurchaseOrders (25C page; 26D not fetched)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-purchasing-document-versions-document-history-details.html — documentVersionActions
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchasingdocumenthistorydetails-purchasingdocumenthistorydetailsuniqid-child-documentversionactions-get.html — attributes, q, finder
- https://docs.oracle.com/en/cloud/saas/financials/26d/fafcf/manage-workflow-transactions.html — Transaction Console navigation, actions, scheduled process
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/how-you-recover-approval-exceptions-using-transaction-console.html — capabilities (negotiation-focused wording)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/24a/proc24a/24A-procurement-wn-f30600.htm — recover steps, duty ORA_PO_REVIEW_PRC_APPROVAL_TRANSACTIONS
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/approval-rules-management-for-procurement.html — task configuration settings, notifications settings
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-approval-rule-sets-and-rules.html — Manage Task Configurations, Validate, Commit task
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/document-approvals-in-procurement.html — worklist actions, email approvals, diagnostic steps
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/what-diagnostic-tests-are-available-for-procurement.html — diagnostic test list
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/configure-procurement-workflow-notifications.html — BI notification customization
- https://docs.oracle.com/en/cloud/saas/human-resources/faucf/export-and-import-rules-using-soa-composer.html — SOA Composer export/import (HCM guide)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faiom/migrate-approval-rules-between-instances-of-order-management.html — config-package migration (Order Management only; search result, not fetched)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/25b/ssproc25b/25B-ssproc-wn-f35309.htm — Redwood requisition FYI notifications (search result)

## UNVERIFIED
- Any REST/SOAP/FSM CSV/FBDI to create, export or import procurement approval rules or approval groups (none found; negative not provable).
- Approval group REST (`/identities/group/...` BPM reference mentioned only in a community post).
- Whether `action.id` vs `action.type` carries the action name (Oracle pages contradict each other; `id` used in Oracle's HCM sample).
- Privileges/roles needed for `/bpm/api/4.0/tasks` with `assignment=ADMIN|ALL` and to act on other users' tasks.
- Auth schemes accepted by `/bpm/api/4.0` (basic assumed; OAuth/JWT not confirmed).
- Request/response schema of `getApprovalWorkflowStatus`, `retrieveCurrentApprovers`, `initiateApproverCheckout`, `reassignRequisitions` (only names and paths seen).
- Mapping of `identificationKey`/payload to requisition or PO numbers.
- 26D page for `draftPurchaseOrders` withdraw (25C page seen).
- Whether the Refresh Transaction Administrator Console Transaction Status job is auto-scheduled in 26D (26D Financials page says hourly automatic; 24A note says admin schedules).
- Exact BI catalog folder paths of procurement notification reports; SOAP/catalog API for deploying them.
- SOA Composer export/import for Procurement rules (only HCM doc and MOS 2600760.1 title); role needed on Procurement pods.
- Vacation rules / delegation setup (Worklist preferences) and any API for them.
- Transaction Console recover action: exact label and any REST/SOAP.
- Procurement config-package (implementation project) coverage of approval rules.
