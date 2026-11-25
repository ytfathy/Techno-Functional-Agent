---
description: Run, build or schedule a BI Publisher report (techno-functional)
argument-hint: <report path or what the report should show, parameters, format>
---
Request: $ARGUMENTS

- **Run an existing report**: find it (`bi_catalog_list` on /Custom or the seeded folder), then `bi_run_report(path, params, fmt)`. Show the preview + saved file.
- **Build a new report**: design the SQL first and prove it with `bi_sql`. Then build the data model + report in the BI catalog under `/Custom/<folder>` (channel D via fusion-ui-operator, or `bi_deploy_object` with an exported .xdmz/.xdoz). Never edit seeded reports in place; copy to /Custom. Pod write → plan + yes.
- **Schedule / run as a scheduled process**: register it as an ESS job (Job Type `BIPJobType`, application `FscmEss`, Report ID `Custom/.../<File>.xdo`; task "Manage Enterprise Scheduler Job Definitions and Job Sets", channel D), grant the generated `RUN_<NAME>` privilege, then run with `ess_submit` and read output with `ess_output`.
- Document new reports in config-docs/reports.md (path, purpose, SQL summary, parameters, who can run it).
