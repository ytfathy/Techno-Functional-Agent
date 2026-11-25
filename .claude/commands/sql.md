---
description: Read-only SQL analysis on Fusion tables through BI Publisher (bi_sql)
argument-hint: <question in plain words, or a SELECT statement>
---
Request: $ARGUMENTS

1. If the user gave a question, write the SELECT yourself from `knowledge/tech-bi-publisher.md` (tables/columns) and the area knowledge file. Prefer views (`*_V`) and secured objects; always filter by BU / org / date when the user names them; join by IDs, not names.
2. Show the SQL in one block and run it with `bi_sql` (read-only; no confirmation needed). If the runner is missing, say so and offer the one-time setup in `playbooks/bi-sql-runner.md` (pod write + security exposure → needs the user's yes).
3. On an ORA- error: explain it, fix the SQL once, rerun. Never send DML/DDL/PL/SQL.
4. Answer with a compact table (≤ 30 rows) + the saved file path in reports/; summarize counts/totals. Bank numbers and secrets stay masked.
