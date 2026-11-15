"""Enterprise structure + common lookups (read-mostly). See knowledge/business-units.md, common-setup.md."""
from __future__ import annotations

from .generic import q_str, rest_get


def find_business_unit(name: str = "", limit: int = 50) -> dict:
    """List business units (finBusinessUnitsLOV). name: part of the BU name (case-sensitive LIKE); empty = all.
    Use it to offer the user the existing BUs when a request names one that does not match."""
    q = f"BusinessUnitName LIKE {q_str('%' + name + '%')}" if name else ""
    # list-all keeps 3 fields: all 181 BUs with every field was ~58 KB of context
    return rest_get("finBusinessUnitsLOV", q=q, limit=limit, all_pages=not name,
                    fields="" if name else "BusinessUnitId,BusinessUnitName,ActiveFlag")


def lookup_values(lookup_type: str, kind: str = "standard") -> dict:
    """List the codes/meanings of a lookup type. kind: 'standard' (standardLookupsLOV) or 'common' (commonLookupsLOV).
    Example: lookup_values('WSH_MODE_OF_TRANSPORT')."""
    resource = {"standard": "standardLookupsLOV", "common": "commonLookupsLOV"}.get(kind)
    if not resource:
        return {"error": True, "message": "kind must be 'standard' or 'common'"}
    return rest_get(resource, q=f"LookupType={q_str(lookup_type)}", fields="LookupCode,Meaning,Description",
                    all_pages=True)


TOOLS = [find_business_unit, lookup_values]
