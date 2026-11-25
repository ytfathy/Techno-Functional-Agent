---
description: Bulk mode — load suppliers, sites, items, agents… from an Excel/CSV
argument-hint: <file path> <object type>
---
Request: $ARGUMENTS

1. Read the file (`bulk_read_file`). Map columns to the REST attributes (`rest_describe`) or, for FBDI, to the control-file columns (`fbdi_ctl_columns` on the object's .ctl — ask before downloading it — or on the SQL*Loader log of an earlier load; `fbdi_template_columns` only explains the labels).
2. Validate every row: mandatory fields, reference values exist (BUs, locations, categories, UOMs…), duplicates in Fusion and inside the file.
3. Show a summary: rows OK, rows with errors (row number + reason), channel (REST batch for up to ~100 rows, FBDI for larger loads), target env.
4. After approval: run (`rest_batch` in chunks, or `fbdi_build_zip(data, name, columns)` + `fbdi_import` + `fbdi_import_job` + `ess_output` of the import request), then `bulk_write_report` → reports/<object>-<date>.xlsx with the per-row result and IDs.
5. Supplier objects still follow the order suppliers → addresses → sites → assignments → contacts (separate passes).
