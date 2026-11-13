# Fusion REST (ADF) conventions

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL (describe JSON shape and Upsert-Mode semantics partly UNVERIFIED)

## Business purpose
Shared rules for every Channel A call made by the MCP server: URLs, query syntax, paging, actions, batch, errors, framework version, date-effective headers.

## Where in Fusion (FSM)
N/A (technical). REST guides: "REST API for Common Features" (farca), Financials (farfa), HCM (farws), Procurement, SCM.

## Prerequisites & dependencies
- Auth: Basic or OAuth bearer (see `access-and-roles.md`). Every resource also needs the role privileges "Use REST Service - …" or the functional privileges.

## Key fields
| Item | Value |
|---|---|
| FSCM base | `https://<host>/fscmRestApi/resources/11.13.18.05/<resource>` (also `/fscmRestApi/resources/latest/` seen in docs) |
| HCM base | `https://<host>/hcmRestApi/resources/11.13.18.05/<resource>`; SCIM `https://<host>/hcmRestApi/scim/<Users|Roles|Bulk|Schemas|ResourceTypes>` |
| CRM base | `/crmRestApi/resources/11.13.18.05/` |
| Spectra (v1) | `https://<host>/api/boss/data/objects/<module>/v1/<resource>` |
| ESS scheduler | `https://<host>/ess/rest/scheduler/v1/requests` |
| Item URL | `<collection>/{key}`; child: `<collection>/{key}/child/<ChildName>/{childKey}`; enclosure: `.../enclosure/<Attr>`; action: `.../action/<name>` |
| Key | Treat `{key}` as opaque (may be a hash); get it from `links[rel=self].href` or query collection with `q` |

### Headers
- `REST-Framework-Version: <n>` — default **1** when omitted. Recommended: send explicitly. Check `defaultFrameworkVersion`/`allowedFrameworkVersions` by `GET <context root>` (e.g. `/fscmRestApi/resources/`). Not applicable to SCIM/BPM.
  - 1 base; q = query-by-example + RowMatch
  - 2 advanced `q` (and/or, in, between, child-field filter, UPPER); QBE `;` syntax errors
  - 3 expanded children returned as collection objects (`items,count,hasMore,limit,offset,links`) instead of arrays
  - 4 rich error payload `o:errorDetails`
  - 5 custom actions return typed values; some dependent LOVs move to root level
  - 6 item context in `@context` {key, headers(ETag), links, warnings}
  - 7 row-level `/lov/` sub-resources hidden
  - 8 ClobDomain as plain text; multi-select FCL as JSON arrays; key encoding in links fixed
  - 9 >15-digit numbers as strings (BigInt); `fields`/`expand` on disabled accessors → 400; `\` escapes `%`/`_` in LIKE
  - **MCP choice: send `REST-Framework-Version: 4`** (v2 q syntax + error details, arrays for children). Higher versions change shapes; only adopt deliberately.
- `Content-Type`: item create/update `application/vnd.oracle.adf.resourceitem+json`; action `application/vnd.oracle.adf.action+json`; batch `application/vnd.oracle.adf.batch+json`; SCIM `application/json`.
- `Accept`: `application/json`; `application/vnd.oracle.adf.resourceitem+json;q=0` = status only, no body. OpenAPI describe: `Accept: application/vnd.oracle.openapi3+json`. Localized labels: `Accept-Language`.
- `Upsert-Mode: true` on POST → updates the matching row if found, else creates; request must still contain all mandatory create attributes.
- `Metadata-Context: sandbox="<name>"` → target a sandbox shape.
- `Effective-Of: RangeMode=<mode>;RangeStartDate=<yyyy-mm-dd>;RangeEndDate=<yyyy-mm-dd>` (date-effective HCM-style resources). Range attrs: `RangeMode`, `RangeStartDate`, `RangeEndDate`, `RangeSpan`, `RangeStartSequence`, `RangeEndSequence`. PATCH modes: `CORRECTION`, `UPDATE`, `END_DATE`; DELETE modes: `DELETE_CHANGES`, `ZAP`; POST implicit. Never send EffectiveStartDate/EffectiveEndDate/EffectiveSequence/EffectiveLatestChange in payload. GET as-of: query param `effectiveDate=<date>` (default sysdate).

### Methods
GET (item/collection), POST (create on collection; custom actions), PATCH (partial update item; only sent fields change), DELETE (item). Success codes: POST create 201, PATCH/DELETE 200/204 (v1 examples show 204).

### Query parameters (GET collection)
| Param | Syntax |
|---|---|
| `q` | v1: `q=Attr=val;Attr2>5` (QBE, `;`=AND). v2+: `q=DeptName = 'SALES' and Salary between 1 and 2`; operators `=,<>,<,<=,>,>=,LIKE,NOT LIKE,IN,NOT IN,BETWEEN,NOT BETWEEN,IS NULL,IS NOT NULL`, `UPPER(x) LIKE UPPER('%e%')`, child filter `q=names.FirstName like '%Ki%'`. Strings single-quoted, `''` escapes quote. Dates `'1999-01-01'`, datetime `'1999-01-01T08:30:40Z'`. Only attributes with `queryable=true` (else 400). |
| `finder` | `finder=<Name>;var1=val1,var2=val2` (e.g. `PrimaryKey;TaskCode=X`) |
| `fields` | `fields=A,B` (child: `fields=A;Child:X,Y` — child form UNVERIFIED); fields wins over expand if both |
| `expand` | `expand=all` or `expand=Child1,Child1.GrandChild` |
| `onlyData` | `onlyData=true` → no `links` |
| `limit`/`offset` | page size / 0-based start; default page 25 in examples, default max "500 rows or similar" |
| `totalResults` | `true` → adds `totalResults` |
| `orderBy` | `orderBy=A:asc,B:desc` (asc default; case-sensitive) |
| `links` | `links=self,canonical` |
| others | `dependency`, `include`, `includeChildren`, `showAnnotations`, `metadataMode`, `resources`, `partialDescription`, `polymorphicType` |

Collection response: `{"items":[...],"count":n,"hasMore":bool,"limit":n,"offset":n,"links":[...],"totalResults":n?}`. Page while `hasMore`; use `orderBy` on a unique key for stable paging.
Item `links[]`: `{rel: self|lov|parent|canonical|child|enclosure|action|custom, href, name, kind: collection|item|describe|other, properties.changeIndicator}`.

SCIM: `filter=userName eq "X"` (ops eq, nq, co, sw, ew, gt, ge, lt, le, pr, and, or, not), `attributes=id,userName`, `startIndex` (1-based), `count` (recommended 100), `sortBy`, `sortOrder=ascending|descending`. Response `{itemsPerPage,startIndex,Resources:[...]}`.

### describe
- `GET /fscmRestApi/resources/11.13.18.05/<resource>/describe` (resource-level; do not add metadataMode)
- `GET /fscmRestApi/resources/11.13.18.05/describe?metadataMode=list` (URLs only) / `?metadataMode=minimal` (all resources)
- Content per docs: resource URIs, attributes with `name`, `type`, `mandatory`, `updatable`, `queryable`, supported actions, child resources, LOV resources.
- JSON shape (UNVERIFIED — not shown on 26D page; parse defensively): `{"Resources": {"<resource>": {"discrColumnType":..,"title":..,"titlePlural":..,"attributes":[{"name","type","updatable","mandatory","queryable","allowChanges","precision","maxLength","annotations":{"description"},"title","properties":{...},"lov":{...}}],"collection":{"rangeSize","finders":[{"name","attributes":[{"name","type"}]}],"actions":[{"name","method","requestType","responseType"}]},"item":{"links":[...],"actions":[{"name","method","parameters":[{"name","type","mandatory"}],"requestType":["application/vnd.oracle.adf.action+json"],"responseType":[...]}]},"children":{"<ChildName>":{ same shape }}}}}`. Code must locate `Resources[<name>]` then `attributes`, `collection.finders`, `item.actions`, `children`.

### Custom action invocation (VERIFIED)
```
POST /fscmRestApi/resources/11.13.18.05/<resource>/{id}/action/<actionName>
Content-Type: application/vnd.oracle.adf.action+json
{ "param1": "v1", "param2": "v2" }            # action name in URL → flat params, no "name"
```
or (URL without action name)
```
POST /fscmRestApi/resources/11.13.18.05/<resource>/{id}
Content-Type: application/vnd.oracle.adf.action+json
{ "name": "<actionName>", "parameters": [ {"param1":"v1"}, {"param2":"v2"} ] }
```
Response media `application/vnd.oracle.adf.actionresult+json` — body `{"result": ...}` (UNVERIFIED key name). Collection-level actions: `POST <collection>/action/<name>`. Prefer URL form; never put `name` in body when it is in URL.

### Batch (VERIFIED)
```
POST https://<host>/fscmRestApi/resources/11.13.18.05          # version root, not a resource
Content-Type: application/vnd.oracle.adf.batch+json
{"parts":[
  {"id":"part1","path":"/purchaseOrders/123","operation":"get"},
  {"id":"part2","path":"/suppliers","operation":"create","payload":{...}},
  {"id":"part3","path":"/territories/300","operation":"update","payload":{"Name":"X"}}
]}
```
- `operation`: `get`, `create`, `update`, `replace`, `delete`; optional `ifMatch` / `ifNoneMatch` (response adds `preconditionSucceeded`).
- Response: `{"parts":[{"id","path","operation","payload"}]}`.
- **All-or-none**: one failed part → nothing processed; response lists only failed parts. Some custom actions refuse batch: "The action {ACTION_NAME} isn't enabled for batch execution."

### Error JSON
- v1–3: body is a plain text/string message.
- v4+:
```json
{"title":"Bad Request","status":"400",
 "o:errorDetails":[{"detail":"This invoice number already exists. ... (AP-810776)",
                    "o:errorCode":"AP:::AP_RS_INV_NUM_DUPLICATE_VALUE","o:errorPath":"/InvoiceNumber"}]}
```
- ESS scheduler errors: `{type, title, status, detail, errorCode}` (e.g. `ESS-00500`).

## Common mistakes
- Using v2 `q` syntax without `REST-Framework-Version: 2+` (or QBE `;` with v2+ → error).
- `expand` + `fields` together (fields wins).
- Constructing item keys by hand for composite/hashed keys.
- Not paginating: default page is small; loop on `hasMore`.
- Sending batch to a resource URL instead of the version root.

## Channel & exact technique
- Preferred channel: A. Always `describe` the resource (and child) before first write; cache per session.
- Write flow: describe → GET existing (q on natural key) → POST/PATCH → GET read-back.

## How to verify
- `GET /fscmRestApi/resources/` → returns framework versions (UNVERIFIED shape).
- Read-back GET after every write; compare fields.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Setting_the_REST_Framework_Version.html — versions 1–9, header, v4 error example
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Manage_Collections.html — q syntax v1/v2, finder, paging, orderBy, SCIM filter/paging
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Access_Metadata.html — describe URL forms, metadataMode, OpenAPI accept, Accept-Language
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Resource_Methods.html — methods, custom action media types + schema, Upsert-Mode
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/Media_Types.html — media type list, Accept q=0
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/custom-actions.html — action URL forms and payloads
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Batch_Actions.html — batch body, operations, all-or-none
- https://docs.oracle.com/en/cloud/saas/human-resources/farws/Manage_Date_Effective_Objects.html — Effective-Of header, RangeMode per method, effectiveDate (unversioned = current HCM guide)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-setuptasks-get.html — query params list, collection properties, link object
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-ess-rest-scheduler-v1-requests-post.html — ESS error body

## UNVERIFIED
- Exact JSON shape of `/describe` (no sample on 26D page).
- Action result body key (`result`).
- Child-level `fields` syntax (`fields=A;Child:X`).
- Default/maximum `limit` per resource (doc: "500 rows or a similar value").
- Shape of `GET /fscmRestApi/resources/` version info.
- Effective-Of doc is from the unversioned (current) HCM guide, not a /26d/ URL.
