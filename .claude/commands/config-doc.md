---
description: Produce a consultant-style configuration document for an area
argument-hint: <area, e.g. procurement setup for BU Egypt Operations>
---
Request: $ARGUMENTS

Build a configuration document (setup-document style) in config-docs/<area>-<date>.md:
1. Read the current configuration live from Fusion (REST reads, `fsm_export` where possible), not just the change log.
2. Merge with the change history in config-docs/<area>.md and logs/audit-*.jsonl.
3. Sections: scope, enterprise structure context, setup values per task (table: task / field / value / reason), dependencies, open points, change history.
4. Never include passwords, tokens or bank account numbers.
