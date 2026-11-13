---
description: Find / list anything in Fusion (read-only)
argument-hint: <what to find, filters>
---
Request: $ARGUMENTS

Read-only. Map the request to REST resources (knowledge/ or `rest_describe`), use `rest_get` with `q=` filters, `fields=` and `all_pages=True` when the user wants "all". For cross-object questions (e.g. suppliers without a site assignment on BU X) read both sides and compute the difference. Show a compact table; if more than 50 rows, save to reports/<name>-<date>.csv and show a summary. No writes.
