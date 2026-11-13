---
description: Create a location (ship-to / receiving / bill-to / office)
argument-hint: <location name/code, address, set, site usages…>
---
Request: $ARGUMENTS

Follow the CLAUDE.md loop with `knowledge/locations.md`:
1. Duplicate check by LocationCode and LocationName (`rest_get /hcmRestApi/resources/11.13.18.05/locationsV2`).
2. Resolve the reference data set (default COMMON unless the user says otherwise) and site usage flags (ship-to, receiving, bill-to, office).
3. `rest_describe` locationsV2, then `create_location` dry run → approval → execute.
4. Verify read-back; config-docs/enterprise-structure.md; `log_request`. Report LocationId / LocationCode.
