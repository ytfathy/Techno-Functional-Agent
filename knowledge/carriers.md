# Carriers and Shipping Methods (incl. "enable carrier on an inventory org")

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- A carrier is the transport company. A **shipping method** = carrier + **service level** + **mode of transport**. You must define and activate a shipping method after creating the carrier.
- **A carrier is "enabled" for an inventory org by assigning its shipping method(s) to that org** (organization associations). The org can then use that carrier + method to ship from and to its warehouses. There is **no carrier-level org assignment**; org associations exist only under shipping methods and inbound tracking rules.
- Inbound tracking rules: carrier website URL, request method and parameters. Used for shipment tracking links.
- Shipping methods feed transit times, transfer orders, sales order shipping and shipping costs.

## Where in Fusion (FSM)
- Task **Manage Carriers**. The UI pages are "Edit Carriers"; the docs say "Create shipping method and assign to organizations on the Edit Carriers page". Offering Manufacturing and Supply Chain Materials Management. Functional area likely **Carriers and Transit Times** (UNVERIFIED for this task).
- **Manage Transit Times**: Offering MSCMM, Functional area **Carriers and Transit Times** (verified).
- **Manage Carriers Lookups**: holds the lookups `WSH_MODE_OF_TRANSPORT`, `WSH_SERVICE_LEVELS`, `WSH_TRACKING_METHODS`.
- Docs: Implementing Common Features for SCM, ch. 33 Carriers.

## Prerequisites & dependencies
- An inventory org must exist for the org association.
- Service level and mode of transport codes must exist in the lookups `WSH_SERVICE_LEVELS` / `WSH_MODE_OF_TRANSPORT`. Add them with Manage Carriers Lookups if missing.
- Depends on this:
  - Transit times (Default Shipping Method)
  - Transfer orders (Enforce Shipping Method in `shippingParameters.EnforceShipMethodFlag`)
  - Supply request `CarrierId`
  - Shipping costs

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Carrier | `carriers.CarrierName` | unique, max 360 | |
| Active | `ActiveFlag` | default true | |
| Manifesting enabled | `ManifestingEnabledFlag` | default false | |
| (key) | `CarrierId` | generated | path key |
| Service Level | `shippingMethods.ServiceLevelCode` (req) | lookup `WSH_SERVICE_LEVELS` | doc example "EXP"; meaning in `ServiceLevel` (read-only) |
| Mode of Transport | `shippingMethods.ModeOfTransportCode` (req) | lookup `WSH_MODE_OF_TRANSPORT` | doc example "PARCEL"; meaning in `ModeOfTransport` (read-only) |
| Shipping method active | `shippingMethods.ActiveFlag` | default true | |
| Ship method code | `shippingMethods.ShipMethodCode` | **read-only**, generated: carrier name + service level + mode concatenation (max 30) | path key for children |
| (id) | `OrganizationCarrierServiceId` | generated | |
| Organization (assignment) | `organizationAssociations.OrganizationCode` (max 18) **or** `OrganizationId` | inventory org that may use the shipping method | one of the two is required; `OrganizationName` optional |
| Contacts | `contacts`: `LastName` (req), `FirstName`, `EmailAddress`, `PhoneNumber`, `JobTitle` | | |
| Tracking rule | `inboundTrackingRules`: `TrackingRuleName` (req), `BaseURL` (req), `RequestMethodCode` (req, `WSH_TRACKING_METHODS` G/P), `ActiveFlag`, children `parameters` (`ParameterName`, `Sequence` req, `ConstantValue`, `LookupParameterCode`) and `organizationAssociations` | | |

## Common mistakes
- Creating the carrier only. Without an active shipping method assigned to the org, the org cannot use the carrier.
- Wrong service level / mode code (meaning sent instead of code, or a code not in the lookup).
- Hard-coding `ShipMethodCode`. It is generated, so read it back from the shipping method response. The path key may be a hash: the docs recommend querying the collection.
- Transfer orders fail when Enforce Shipping Method is on and no transit time has this method as default.

## Channel & exact technique
- Preferred channel: **A (REST)**. Full CRUD except carrier DELETE (deactivate with `ActiveFlag=false`).
- Resource tree (`/fscmRestApi/resources/11.13.18.05/...`):
  - `carriers`: GET, POST. `carriers/{CarrierId}`: GET, PATCH. Finders `CarrierFinder` (ActiveFlag, CarrierId, CarrierName, ManifestingEnabledFlag), `PrimaryKey` (CarrierId).
  - `carriers/{CarrierId}/child/shippingMethods`: GET, POST. `.../shippingMethods/{ShipMethodCode}`: GET, PATCH (no DELETE; set `ActiveFlag=false`).
  - `carriers/{CarrierId}/child/shippingMethods/{ShipMethodCode}/child/organizationAssociations`: GET, POST. `.../organizationAssociations/{OrganizationId}`: GET, **DELETE** (unassign).
  - `carriers/{CarrierId}/child/shippingMethods/{ShipMethodCode}/child/DFF` (`{OrgCarrierServiceId}`).
  - `carriers/{CarrierId}/child/contacts` (CRUD, key `RelationshipRecordId`). `carriers/{CarrierId}/child/DFF`.
  - `carriers/{CarrierId}/child/inboundTrackingRules` (GET/POST, `{TrackingRuleName}` GET/PATCH/DELETE). Children `parameters` (CRUD) and `organizationAssociations` (GET/POST/DELETE).
  - Read-only LOV: `shippingShipMethodsLOV`. Org shipping parameters: `shippingParameters` (GET, `EnforceShipMethodFlag`, `CarrierManifestFlag`).
- **Recipe: "create carrier FastShip and enable it on the Cairo inventory org"**
  1. Resolve the org: `GET inventoryOrganizations?q=OrganizationName LIKE '%Cairo%'` (or the code). Note `OrganizationCode`/`OrganizationId`. Confirm with the user if more than one matches.
  2. Idempotency: `GET carriers?finder=CarrierFinder;CarrierName=FastShip`.
  3. Pick a service level and mode from the lookups `WSH_SERVICE_LEVELS` / `WSH_MODE_OF_TRANSPORT` (`GET /fscmRestApi/resources/11.13.18.05/standardLookups?q=LookupType='WSH_SERVICE_LEVELS'`; resource name UNVERIFIED in SCM). Ask the user if not given.
  4. Option A, one deep POST (schema supports nested children): `POST carriers` `{"CarrierName":"FastShip","ActiveFlag":true,"shippingMethods":[{"ServiceLevelCode":"<code>","ModeOfTransportCode":"<code>","ActiveFlag":true,"organizationAssociations":[{"OrganizationCode":"<CAIRO_CODE>"}]}]}`
  5. Option B, step by step (safer for error isolation):
     1. `POST carriers {"CarrierName":"FastShip"}` returns `CarrierId`.
     2. `POST carriers/{CarrierId}/child/shippingMethods {"ServiceLevelCode":"..","ModeOfTransportCode":".."}` returns `ShipMethodCode` (use the self link).
     3. `POST carriers/{CarrierId}/child/shippingMethods/{ShipMethodCode}/child/organizationAssociations {"OrganizationCode":"<CAIRO_CODE>"}`.
  6. Optional: add a transit time with this method as default (UI Manage Transit Times) if Cairo uses transfer orders with Enforce Shipping Method.
- B (FSM CSV): UNVERIFIED for Manage Carriers.
- D (UI): Manage Carriers, then Create/Edit Carrier, then the Shipping Methods tab, then assign organizations.

## How to verify
- `GET carriers?finder=CarrierFinder;CarrierName=FastShip&expand=shippingMethods.organizationAssociations`. Expect `ActiveFlag=true` and the Cairo `OrganizationCode` under the method.
- `GET shippingShipMethodsLOV` filtered by org (finder UNVERIFIED) shows that the method is available to the org.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-carriers-post.html — carrier attributes, nested schema (shippingMethods, organizationAssociations, contacts, inboundTrackingRules), example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-carriers-get.html — finders, queryable attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-carriers-carrierid-child-shippingmethods-post.html — shipping method attributes, lookups, example {"ServiceLevelCode":"EXP","ModeOfTransportCode":"PARCEL"}
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-carriers-carrierid-child-shippingmethods-shipmethodcode-child-organizationassociations-post.html — org association attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-carriers-carrierid-child-shippingmethods-shipmethodcode-patch.html — path params (hash-key note)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — full method list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/implementing-common-features-for-scm.pdf — ch. 33 Carriers (shipping methods assigned to organizations, tracking rules), ch. 34 Transit Times
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implementing-manufacturing-and-supply-chain-materials-management.pdf — ch. 3: "Create shipping method and assign to organizations on the Edit Carriers page", Manage Transit Times in Carriers and Transit Times, Enforce Shipping Method

## UNVERIFIED
- The exact functional area of the FSM task "Manage Carriers" (probably Carriers and Transit Times).
- Whether the deep POST (carrier, then shippingMethods, then organizationAssociations in one call) is accepted at runtime. The schema allows it.
- Lookup code values present on the pod for `WSH_SERVICE_LEVELS` / `WSH_MODE_OF_TRANSPORT`; "EXP" / "PARCEL" are only doc examples. Also the REST resource used to read those lookups.
- FSM CSV support for Manage Carriers. REST for Manage Transit Times.
