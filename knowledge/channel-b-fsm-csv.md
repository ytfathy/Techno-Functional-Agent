# Channel B — FSM Setup Task / Setup Offering CSV Export & Import (REST)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL (payloads, paths, status values VERIFIED on 26D pages; a few behaviours UNVERIFIED)

## Business purpose
Export or import the setup data of one FSM task (or a whole offering / functional area) as a zip of CSV files, without the UI. Used for: backup before change, migration DEV→TEST→PROD, bulk edit of setup rows, and reading setup data that has no business REST resource. Same engine as "Actions > Export to CSV File / Import from CSV File" in Setup and Maintenance.

## Where in Fusion (FSM)
- Any task whose `CSVExportImportSupportedFlag = Y` (see "Find a TaskCode" below).
- UI equivalent: Setup and Maintenance > task > Actions > Export to CSV File / Import from CSV File.
- Find codes in UI: Setup and Maintenance > Tasks panel > **Manage Setup Content** > **Manage Task Lists and Tasks** (search Tasks, open task, read **Code**) or **Manage Offerings and Functional Areas** (read **Code**). Business object codes: Manage Setup Content > **Manage Business Objects**.

## Prerequisites & dependencies
- Role **Export Import Functional Setups User** (`ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT`) — required to submit export/import by API and to read codes.
- Plus a role with task-specific privileges to modify that setup data, plus the application administrator role for offering-level work.
- Import requires the zip produced by an export of the **same** task / offering / functional area (CSV file names and columns must match). Edited CSV zip max 10 MB.

## Key fields
| Field | REST attribute | Meaning | Notes |
|---|---|---|---|
| Task code | `TaskCode` | Unique code of setup task | string ≤255; also the item key in the URL |
| Export supported | `ExportSupportedFlag` | BooleanYN | read on GET `setupTaskCSVExports/{TaskCode}` |
| Import supported | `ImportSupportedFlag` | BooleanYN | read on GET `setupTaskCSVImports/{TaskCode}` |
| Process id | `ProcessId` | int, generated on POST | key of the process child AND of the result child (same value) |
| Completed | `ProcessCompletedFlag` | BooleanYN ("Y"/"N"; sample shows `true`) | poll until true/Y |
| Status | `StatusCode` (on *ProcessResult*) | `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `COMPLETED_WARNINGS`, `COMPLETED_ERRORS` | final = last three |
| Zip | `FileContent` | base64 zip (export result / import process input) | |
| Zip name | `FileName` | export result only | |
| Log | `ProcessLog` | base64 | per business object |
| Reports | `ProcessResultsReport`, `ProcessResultsSummaryReport`, `CSVTemplateReport` | base64 | CSVTemplateReport export only |
| Revision override | `SourceTargetDiffOkFlag` | Y/N, default N | import only: Y = import even if setup data revision differs |
| Scope filter | `SetupTaskCSVExportCriteria[]`: `BusinessObjectCode`, `AttributeSet`, `AttributeName`, `AttributeValue` (+`TaskCode`, `ProcessId`) | optional export filter | only for scope-enabled business objects; AttributeName = CSV column name of the business object's CSV; AttributeSet groups pairs into one condition (e.g. "Set1") |

**There is no `OperationCode` attribute** on any of these resources (checked task + offering export/import POST schemas, 26D). Export vs import is chosen by the resource name.

## Common mistakes
- Using `GET /setupTaskCSVExports` (collection) — "not supported". Only GET by `{TaskCode}`.
- Reading `StatusCode` on the process: it lives on the **ProcessResult** child, the process only has `ProcessCompletedFlag`.
- Importing a hand-made zip: must keep exported file names/columns; size ≤10 MB; Excel must treat all columns as Text.
- Sending read-only base64 fields (ProcessLog etc.) in POST.
- Expecting import to overwrite across revisions: default `SourceTargetDiffOkFlag=N` stops the import.

## Channel & exact technique
- Preferred channel: **B** when no business REST resource (A) exists for the setup; also the generic backup tool before any change (A or B).
- Base: `/fscmRestApi/resources/11.13.18.05`. Media type for POST: `application/vnd.oracle.adf.resourceitem+json` (or `application/json`).

### Find a TaskCode / check CSV support (VERIFIED)
```
GET /fscmRestApi/resources/11.13.18.05/setupTasks?q=TaskName='Manage Procurement Agents'&fields=TaskCode,TaskName,AvailableFlag,ExportImportSupportedFlag,CSVExportImportSupportedFlag
GET /fscmRestApi/resources/11.13.18.05/setupTasks/{TaskCode}
GET /fscmRestApi/resources/11.13.18.05/setupTasks?finder=PrimaryKey;TaskCode=<code>
```
Attributes (all read-only): `TaskCode` (≤240), `TaskName` (≤256), `AvailableFlag` (Y/N), `ExportImportSupportedFlag` (Y/N), `CSVExportImportSupportedFlag` (Y/N). Only `CSVExportImportSupportedFlag='Y'` tasks can use this channel.

Offering / functional area codes (resource `features`, VERIFIED example):
```
GET /fscmRestApi/resources/11.13.18.05/features?fields=FeatureName,FeatureCode,FeatureType&q=FeatureType='OFFERING';FeatureName LIKE 'Order Management'
GET /fscmRestApi/resources/11.13.18.05/features?fields=FeatureName,FeatureCode,FeatureType&q=FeatureType='FUNCTIONAL_AREA';FeatureName LIKE 'Legal Structures'
```
`FeatureType` values seen: `OFFERING`, `FUNCTIONAL_AREA`. Use `FeatureCode` (doc sample's link href is wrong). There is no `setupOfferings` / `functionalAreas` resource in the 26D endpoint list; use `features`.

### Task export (VERIFIED)
1. Start:
```
POST /fscmRestApi/resources/11.13.18.05/setupTaskCSVExports
{
  "TaskCode": "HZ_MANAGE_RESOURCE_ROLES",
  "SetupTaskCSVExportCriteria": [      // optional
    {"TaskCode":"HZ_MANAGE_RESOURCE_ROLES","BusinessObjectCode":"JTF_RS_ROLES_B",
     "AttributeSet":"Set1","AttributeName":"RoleTypeCode","AttributeValue":"CHANNEL_SALES"}
  ],
  "SetupTaskCSVExportProcess": [ {"TaskCode":"HZ_MANAGE_RESOURCE_ROLES"} ]
}
```
→ response `SetupTaskCSVExportProcess[0].ProcessId`.
2. Poll: `GET .../setupTaskCSVExports/{TaskCode}/child/SetupTaskCSVExportProcess/{ProcessId}` → `ProcessCompletedFlag`.
3. Result: `GET .../setupTaskCSVExports/{TaskCode}/child/SetupTaskCSVExportProcess/{ProcessId}/child/SetupTaskCSVExportProcessResult/{ProcessId}` → `StatusCode`, `FileName`, base64 fields.
4. Download (enclosures, GET): `.../SetupTaskCSVExportProcessResult/{ProcessId}/enclosure/FileContent` (zip), `/enclosure/ProcessLog`, `/enclosure/ProcessResultsReport`, `/enclosure/ProcessResultsSummaryReport`, `/enclosure/CSVTemplateReport`. Doc: "The response is a base64-encoded string that you can download as a .zip file" (decode handling: UNVERIFIED whether raw bytes or base64 text on the enclosure — handle both: if body starts with `PK` it is raw zip, else base64-decode).
- Alt start on existing parent: `POST .../setupTaskCSVExports/{TaskCode}/child/SetupTaskCSVExportProcess`, criteria via `POST .../{TaskCode}/child/SetupTaskCSVExportCriteria`.

### Task import (VERIFIED)
```
POST /fscmRestApi/resources/11.13.18.05/setupTaskCSVImports
{
  "TaskCode": "HZ_MANAGE_RESOURCE_ROLES",
  "SetupTaskCSVImportProcess": [{
     "TaskCode": "HZ_MANAGE_RESOURCE_ROLES",
     "SourceTargetDiffOkFlag": "N",
     "FileContent": "<base64 zip>"
  }]
}
```
→ `SetupTaskCSVImportProcess[0].ProcessId`.
- Poll: `GET .../setupTaskCSVImports/{TaskCode}/child/SetupTaskCSVImportProcess/{ProcessId}` → `ProcessCompletedFlag`.
- Result: `GET .../SetupTaskCSVImportProcess/{ProcessId}/child/SetupTaskCSVImportProcessResult/{ProcessId}` → `StatusCode`, `ProcessName`.
- Log/reports: `.../SetupTaskCSVImportProcessResult/{ProcessId}/enclosure/ProcessLog|ProcessResultsReport|ProcessResultsSummaryReport`.
- `GET .../SetupTaskCSVImportProcess/{ProcessId}/enclosure/FileContent` is "not supported".

### Template export (empty CSV templates)
`setupTaskCSVTemplateExports` — POST root, child `SetupTaskCSVTemplateExportProcess`, result `SetupTaskCSVTemplateExportProcessResult` with enclosures `FileContent`, `ProcessLog`, `CSVTemplateReport`, `ProcessResultsReport`, `ProcessResultsSummaryReport`. Payload by analogy with export (`TaskCode` + process array) — UNVERIFIED (POST page not read).

### Offering / functional area export & import (VERIFIED)
```
POST /fscmRestApi/resources/11.13.18.05/setupOfferingCSVExports
{ "OfferingCode":"XLE_FINANCIALS_JUR",
  "FunctionalAreaCode":"ORA_ASK_ORGANIZATION_STRUCTURE",       // omit for whole offering
  "SetupOfferingCSVExportCriteria":[{"OfferingCode":"XLE_FINANCIALS_JUR","BusinessObjectCode":"FUN_BUSINESS_UNIT",
      "AttributeSet":"Set1","AttributeName":"OrganizationCode","AttributeValue":"..."}],
  "SetupOfferingCSVExportProcess":[{"OfferingCode":"XLE_FINANCIALS_JUR"}] }
```
- Process: `GET .../setupOfferingCSVExports/{OfferingCode}/child/SetupOfferingCSVExportProcess/{ProcessId}`
- Result: `.../SetupOfferingCSVExportProcess/{ProcessId}/child/SetupOfferingCSVExportProcessResult/{ProcessId}` + enclosures `FileContent`, `ProcessLog`, `CSVTemplateReport`, `ProcessResultsReport`, `ProcessResultsSummaryReport`.
```
POST /fscmRestApi/resources/11.13.18.05/setupOfferingCSVImports
{ "OfferingCode":"XLE_FINANCIALS_JUR", "FunctionalAreaCode":"ORA_ASK_ORGANIZATION_STRUCTURE",
  "SetupOfferingCSVImportProcess":[{"OfferingCode":"XLE_FINANCIALS_JUR","SourceTargetDiffOkFlag":"N","FileContent":"<base64 zip>"}] }
```
- Process: `.../setupOfferingCSVImports/{OfferingCode}/child/SetupOfferingCSVImportProcess/{ProcessId}`; result child `SetupOfferingCSVImportProcessResult/{ProcessId}` (enclosures `ProcessLog`, `ProcessResultsReport`, `ProcessResultsSummaryReport`).
- `setupOfferingCSVTemplateExports` exists (child `SetupOfferingCSVTemplateExportProcess`, result `SetupOfferingCSVTemplateExportProcessResult`).
- Configuration Set Migration (whole-pod, not per task): `/fscmUI/applcoreApi/v2/csm/export`, `/export/status/{csId}`, `/import/{csId}`, `/apply/{csId}` — out of scope, listed for completeness.

### Polling algorithm (code-ready)
```
pid = POST(...).Setup*Process[0].ProcessId
loop: p = GET(process/pid); if p.ProcessCompletedFlag in (True,"Y","true"): break; sleep backoff (5s→60s), timeout 30 min
r = GET(process/pid/child/<Result>/pid); status = r.StatusCode
ok = status in ("COMPLETED","COMPLETED_WARNINGS"); always fetch ProcessLog when status != COMPLETED
```

## How to verify
- Export: `StatusCode=COMPLETED`, zip opens, contains one CSV per business object (+ metadata).
- Import: `StatusCode=COMPLETED`; read back with export again or business REST GET; read `ProcessResultsSummaryReport`.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Task_CSV_Export.html — 3-step task export flow, status/result URLs, enclosure FileContent
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-setuptaskcsvexports-post.html — export schema, criteria fields, StatusCode values
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-setuptaskcsvimports-post.html — import schema, SourceTargetDiffOkFlag, example response links
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-setupofferingcsvexports-post.html — offering export schema/example
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-setupofferingcsvimports-post.html — offering import schema/example
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/rest-endpoints.html — full endpoint list incl. enclosures, "not supported" GETs, setupTasks, template exports, CSM
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-setuptasks-get.html — setupTasks attributes and finder
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Find_Offering_Code.html — features resource for offering/functional area codes
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/oafsm/automate-export-and-import-of-csv-file-packages.html — required role, UI code lookup, scope filter rules, 10 MB limit

## UNVERIFIED
- Enclosure `/enclosure/FileContent` returns raw zip bytes vs base64 text (doc wording ambiguous) — handle both.
- Literal values of BooleanYN flags in responses (doc sample shows JSON `true`; schema says Y/N value map).
- `setupTaskCSVTemplateExports` POST payload shape (by analogy only).
- Whether `ProcessCompletedFlag` becomes true before `StatusCode` reaches a final value (assume poll result until final status too).
- Exact TaskCodes for SCM/Procurement tasks: not listed in docs; always resolve at runtime via `setupTasks?q=TaskName=...`.
