---
description: Export (back up) a setup task via FSM CSV
argument-hint: <setup task name, scope e.g. BU>
---
Request: $ARGUMENTS

1. `fsm_find_task` with the task name → TaskCode and CSV support. If CSV is not supported, say so and offer a UI snapshot backup via fusion-ui-operator instead.
2. `fsm_export` (with scope criteria if given) → poll `fsm_status` → `fsm_download` saves the zip in backups/<YYYY-MM-DD>/.
3. Summarize what the export contains (files, row counts). Read-only: no import.
