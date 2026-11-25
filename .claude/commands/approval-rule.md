---
description: Create or change an approval rule (requisition / purchasing document / supplier registration)
argument-hint: <document type, condition (amount, category, BU…), approvers in order>
---
Request: $ARGUMENTS

High-impact. Follow the CLAUDE.md loop with `knowledge/approvals.md` and `playbooks/approval-rules.md`.
1. Identify the task (Manage Requisition Approvals / Manage Purchasing Document Approvals / Manage Supplier Registration Approvals), stage, participant, rule conditions and actions (supervisory levels, approval group, user).
2. Read existing rules (UI snapshot): look for overlapping or conflicting rules; resolve approval groups/users (e.g. "Finance" → an existing approval group?). Ask one question if ambiguous.
3. Show before/after of the rule set; ask twice.
4. Back up (screenshot + rule text), execute via fusion-ui-operator, verify by reopening.
5. Functional test: create a test requisition/PO that meets the condition (`/new-req`), submit it, and check the approval routing; report who it went to.
6. config-docs/approvals.md; `log_request`; update the playbook if the UI differed.

Technical side (`knowledge/tech-approvals-workflow.md`): rules and groups have no API (channel D). Test and troubleshoot with the API:
- `wf_tasks(keyword=<doc number>)` / `wf_task(<n>)` show who the test document was routed to, with history.
- `wf_tasks(assignment='ADMIN', status='ERRORED')` finds faulted approvals.
- `purchaseRequisitions/{id}/action/getApprovalWorkflowStatus` and `retrieveCurrentApprovers` return the approval status and current approvers of a requisition.
- PO history comes from `purchasingDocumentHistoryDetails` → `documentVersionActions`.
- Moving rules pod-to-pod uses SOA Composer export/import (UI).
