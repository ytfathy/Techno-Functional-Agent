# Playbook: BI Publisher SQL runner (one-time setup for `bi_sql`)

> Channel D (BI Publisher catalog UI in the Claude browser pane) · Release: 26D · Status: DRAFT (needs a first run)
> Knowledge file: `knowledge/tech-bi-publisher.md` · Tool that uses it: `bi_sql`

## When to use
Once per pod, so that the agent can run read-only analysis SQL (`bi_sql`). Fusion SaaS has no direct DB access; BI Publisher data models are the only SQL path.

**Security — ask the user before creating it.** The runner executes any SELECT the BI data source can read (all modules). Keep it in a private folder that only the agent's role can open, and delete it when no longer needed. On PROD, do not create it unless the user types `CONFIRM PROD` and the security owner agrees.

## Inputs
| Input | Required | Example | Where it comes from |
|---|---|---|---|
| Catalog folder | yes | `/Shared Folders/Custom/AI_SCM_AGENT` | fixed (profile `ORACLE_BI_SQL_REPORT` can override the report path) |
| Data source | yes | `ApplicationDB_FSCM` | default Fusion FSCM data source |
| Role allowed on the folder | yes | the agent user's BI role | `user_roles` |

## Pre-checks
- The agent user has BI Author (to create) — `find_role("BI Author")` / `user_roles(<agent>, "BI")`; add with `assign_roles` if missing (high-impact; ask).
- `bi_catalog_list("/Custom/AI_SCM_AGENT")` — does the runner already exist?

## Steps
1. Open `<pod>/analytics/saw.dll?catalog` (or Navigator > Tools > Reports and Analytics > Browse Catalog). Go to **Shared Folders > Custom**, create folder **AI_SCM_AGENT**.
2. **New > Data Model.** Data source `ApplicationDB_FSCM`. Add a **SQL Query** data set named `RUNNER`:
   ```sql
   SELECT DBMS_XMLGEN.GETXML(
            UTL_RAW.CAST_TO_VARCHAR2(UTL_ENCODE.BASE64_DECODE(UTL_RAW.CAST_TO_RAW(:P_SQL_B64)))
          ) AS RESULT_XML
   FROM DUAL
   ```
   Set the `RESULT_XML` column type to CLOB/String if asked. Accept the generated parameter `P_SQL_B64` (Text, no default).
3. Save the data model as `/Custom/AI_SCM_AGENT/SQL_RUNNER_DM.xdm`.
4. **New > Report** from that data model, no layout needed (default output XML). Save as `/Custom/AI_SCM_AGENT/SQL_RUNNER.xdo`.
5. **Permissions** on folder `AI_SCM_AGENT`: remove BI Consumer / Authenticated User access; grant only the agent user's role (Read + Run Publisher Report).

## Verification
- `bi_sql("select sysdate as run_date from dual")` returns 1 row.
- `bi_sql("select segment1, type_lookup_code from po_headers_all where rownum <= 5")` returns PO numbers.

## Known UI differences / gotchas
- UNVERIFIED: whether the Fusion BI data source allows `DBMS_XMLGEN` / `UTL_ENCODE` in data model SQL on this pod. If not, the run fails at step "Verification": fall back to one data model per analysis (written by the agent, deployed with `bi_deploy_object`).
- Bind parameter values are limited to about 4000 characters → keep analysis SQL under ~2900 characters (base64 overhead).
- Record here what the real screens looked like on the first run.

## Sources
- `knowledge/tech-bi-publisher.md` (runReport, catalog, data model concepts; docs.oracle.com URLs there).
