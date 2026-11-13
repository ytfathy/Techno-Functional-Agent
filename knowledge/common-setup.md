# Common setup: lookups, value sets, flexfields, profile options, scheduled processes

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Cross-application reference data every SCM/Procurement setup touches: lookups (codes in LOVs), value sets (flexfield/segment values), descriptive flexfields (extra attributes), profile options (behaviour switches), scheduled processes (ESS jobs).

## Where in Fusion (FSM)
- Offering: any (e.g. Procurement) · Functional area: Application Extensions / Enterprise Profile / Maintain Common Reference Objects.
- Tasks: Manage Standard Lookups, Manage Common Lookups, Manage Set-Enabled Lookups, Manage Value Sets, Manage Descriptive Flexfields, Manage Profile Options / Manage Administrator Profile Values, Manage Profile Categories, Manage Enterprise Scheduler Job Definitions and Job Sets for Financial, Supply Chain Management, and Related Applications. (Task names from general FSM knowledge of the docs read; exact 26D task names UNVERIFIED except the ESS one.)

## Prerequisites & dependencies
- Set-enabled lookups need reference data sets (`setIdSets`).
- Value sets used by DFF/KFF segments; DFF deploy needed after change (UI).

## Key fields
| Area | REST resource (fscmRestApi/resources/11.13.18.05) | Ops | Key/finders | Item attributes |
|---|---|---|---|---|
| Standard lookups | `standardLookups` | GET/POST, GET/PATCH/DELETE `/{LookupType}` | children `lookupCodes` (CRUD `/{LookupCode}`), `lookupCodes/{LookupCode}/child/lookupsDFF`, `translations` | describe at runtime |
| Standard lookups LOV | `standardLookupsLOV` | GET | finder `LookupTypeCascadingAllRowsFinder` (BindLookupCode, BindLookupType) seen; others UNVERIFIED | |
| Common lookups | `commonLookups` | GET/POST, GET/PATCH/DELETE `/{LookupType}` | children `lookupCodes`, `translations` | |
| Common lookups LOV | `commonLookupsLOV` | GET | `LookupTypeFinder` (ActiveDate, LookupCode, LookupType), `LookupTypeAllRowsFinder` (LookupCode, LookupType), `LegislationCodeFinder` (ActiveDate, LegislationCode, LookupCode, LookupType), `PrimaryKey` (LookupCode, LookupType) | `LookupType`, `LookupCode`, `Meaning`, `Description`, `Tag`, `LegislationCode` |
| Set-enabled lookups | `setEnabledLookups` (+ `setEnabledLookupsLOV`) | CRUD `/{LookupType}` | children `lookupCodes`, `translations` | |
| Generic lookups | `genericLookups` (+LOV) | CRUD | finder param `ApplicationCode` selects view | |
| fndStaticLookups | NOT in 26D farca endpoint list | — | — | — |
| Reference data sets | `setIdSets`, `setIdAssignmentsBusinessUnit`, `setIdReferenceGroups` (+ `…LOV`) | CRUD / GET | | |
| Value sets | `valueSets` | GET only; child `values` POST/GET/PATCH/DELETE; child `validationTable` GET | `PrimaryKey` (ValueSetId), `ValueSetCodeFinder` (ValueSetCode) | `ValueSetId, ValueSetCode, ValidationType, ValueDataType, MaximumLength, SecurityEnabledFlag, IndependentValueSetCode…`; values: `ValueId, Value, Description, EnabledFlag, StartDateActive, EndDateActive, SortOrder, IndependentValue, TranslatedValue…` |
| DFF contexts | `FlexFndDffDescriptiveFlexfieldContexts` | GET | — | (seen in Financials/SCM guides 24B–25B; 26D page not read) |
| Profile values | `profileValues` | GET only | `PrimaryKey` (ApplicationId, ProfileOptionId), `ProfileOptionNameFinder` (ProfileOptionName) | `ApplicationId, ProfileOptionId, ProfileOptionName, ProfileOptionValue, UserProfileOptionName` |
| Scheduled processes | `/ess/rest/scheduler/v1/requests` (not under fscmRestApi) | POST submit, GET list/item, `/{id}/cancel`, `/forceCancel`, `/hold`, `/release`, `/executionStatus`, PATCH, DELETE | | see below |
| Setup tasks | `setupTasks` | GET | `PrimaryKey` (TaskCode) | see channel-b |

profileValues only returns profiles in categories `ORA_FND_AUTH_REST_ACCESS` (authenticated users) or `ORA_FND_ANON_REST_ACCESS` (anonymous). Others are invisible — add the profile to the category via Manage Profile Categories, or read via BI/UI.

Spectra alternatives: `/api/boss/data/objects/ora/commonAppsInfra/objects/v1/` `commonLookupCodes`, `commonLookupTypes`, `setEnabledLookupCodes`, `setEnabledLookupTypes`, `standardLookupCodes` (`$views/lookupLOV`), `standardLookupTypes`.

### ESS submit (scheduler REST)
```
POST https://<host>/ess/rest/scheduler/v1/requests
Content-Type: application/json
{"jobDefinitionId":"JobDefinition://oracle/apps/ess/<path>/<JobDef>",
 "application":"<ESS application, e.g. FscmEss — UNVERIFIED>",
 "description":"agent run",
 "requestParameters":[{"name":"submit.argument1","paramType":"STRING","value":"..."}]}
```
- `RequestParameter.paramType`: `BOOLEAN|LONG|INTEGER|DATETIME|STRING`. Parameter names for Fusion jobs (`submit.argumentN`) UNVERIFIED for this API (documented for erpintegrations SOAP paramList).
- Response 201: `{"id": <requestId>, "links":[...]}`, `Location` header.
- Status: `GET /ess/rest/scheduler/v1/requests/{id}` → `state`, `processPhase`, `requestType`, `processStartTime`, `processEndTime`… ; `?fields=requestId,state`.
- Simpler and verified alternative: erpintegrations `submitESSJobRequest` + `ESSJobStatusRF` (see `channel-c-fbdi-ess.md`).
- Status names (UI, 26D): Blocked, Canceled, Canceling, Completed, Error, Error Auto-Retry, Error Manual Recovery, Expired, Finished, Hold, Paused, Pending Validation, Ready, Retrying, Running, Schedule Ended, Succeeded, Validation Failed, Wait, Warning. Final: Canceled, Error, Expired, Finished, Succeeded, Validation Failed, Warning.

## Common mistakes
- Trying to POST `valueSets` (GET only; only `values` child is writable).
- Expecting `profileValues` to list every profile.
- Treating "Completed" as final (postprocessing still running).
- Editing predefined (system) lookup codes — UI blocks; REST will error (customization level).

## Channel & exact technique
- Preferred channel: **A** for lookups (standard/common/set-enabled CRUD) and value set values. **B** (FSM CSV) for profile option values and DFF definitions (no write REST). **D** (UI) for DFF deploy.
- Read lookup codes: `GET /commonLookupsLOV?finder=LookupTypeFinder;LookupType=<TYPE>` or `GET /standardLookups/{LookupType}/child/lookupCodes`.
- Add value: `POST /valueSets/{valueSets_Id}/child/values` (get id via `?finder=ValueSetCodeFinder;ValueSetCode=X`).

## How to verify
Read back via the same resource; for profiles, `profileValues?finder=ProfileOptionNameFinder;ProfileOptionName=X`.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/rest-endpoints.html — endpoint list: lookups, LOVs, setId, profileValues, ESS scheduler, SCIM, valueSets, setupTasks
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-servername-fscmrestapi-resources-11.13.18.05-commonlookupslov-get.html — commonLookupsLOV finders/attributes
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-servername-fscmrestapi-resources-11.13.18.05-valuesets-get.html — valueSets finders/attributes/children
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-servername-fscmrestapi-resources-11.13.18.05-profilevalues-get.html — profileValues finders/attributes
- https://docs.oracle.com/en/cloud/saas/applications-common/25d/farca/api-profile-values.html — securing categories rule (25D; same resource)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-ess-rest-scheduler-v1-requests-post.html — ESS submit schema
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-ess-rest-scheduler-v1-requests-requestid-get.html — ESS request GET attributes/enums
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/statuses-of-scheduled-processes.html — status list
- https://docs.oracle.com/en/cloud/saas/financials/24d/farfa/api-list-values-descriptive-flexfield-contexts.html — FlexFndDffDescriptiveFlexfieldContexts (24D)

## UNVERIFIED
- `standardLookupsLOV` full finder list; `standardLookups/lookupCodes` attribute names (use describe).
- `FlexFndDffDescriptiveFlexfieldContexts` on 26D and its attributes; no DFF definition write REST found.
- ESS scheduler: `application` value for FSCM jobs, parameter naming (`submit.argumentN`), upper-case `state` values.
- Exact FSM task names for lookups/value sets/DFF/profile tasks in 26D.
- Whether lookup REST writes are allowed on Oracle-owned (system/extensible) lookup types.
