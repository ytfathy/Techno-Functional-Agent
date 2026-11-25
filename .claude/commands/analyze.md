---
description: Techno-functional analysis — data checks, setup gaps, root-cause of an error or a stuck transaction
argument-hint: <what to analyze, e.g. "why PO 1234 is stuck in approval", "suppliers missing sites on US1", "on-hand vs receipts for item X">
---
Request: $ARGUMENTS

Work like a techno-functional consultant; read-only unless the user asks for a fix.
1. **Frame** the question: objects involved, BU/org/date scope, expected vs actual.
2. **Collect evidence** with the cheapest channel:
   - Setup: REST reads (`rest_get`), `fsm_export` for setup tasks, `knowledge/dependencies.md` for what should exist.
   - Data: `bi_sql` for joins/aggregates across tables (counts, totals, missing links, duplicates).
   - Approvals: `wf_tasks` / `wf_task` (state, assignees, history), `purchaseRequisitions .../getApprovalWorkflowStatus`, PO history (`purchasingDocumentHistoryDetails`), faulted tasks `wf_tasks(assignment='ADMIN', status='ERRORED')`.
   - Jobs / imports: `ess_status`, `ess_output`, `fbdi_import_job`.
   - Access: `user_roles`, `ensure_access`.
3. **Conclude**: root cause in one or two sentences, the evidence (IDs, rows, codes), and the fix with its channel. Offer to apply the fix (normal plan → yes rules).
4. Save the evidence to reports/analysis-<topic>-<date>.md (or .xlsx via `bulk_write_report`) and give the path.
