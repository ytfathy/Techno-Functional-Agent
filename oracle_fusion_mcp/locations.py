"""Location shortcuts (HCM locationsV2). See knowledge/locations.md."""
from __future__ import annotations

from .client import HCM
from .generic import create_checked, q_str, rest_get

LOCATIONS = f"{HCM}/locationsV2"


def create_location(location_code: str, location_name: str, set_code: str, country: str, address_line1: str,
                    town_or_city: str, effective_start_date: str, postal_code: str = "", region1: str = "",
                    ship_to: bool = True, receiving: bool = True, bill_to: bool = True, office: bool = True,
                    effective_end_date: str = "4712-12-31", extra: dict | None = None, address_extra: dict | None = None,
                    dry_run: bool = True, confirm_prod: str = "", allow_duplicate: bool = False) -> dict:
    """Create a location (ship-to / receiving / bill-to / office) in a reference data set.
    Resolves SetId from set_code; blocks if LocationCode already exists. Dates: YYYY-MM-DD. country: ISO code (EG, SA)."""
    sets = rest_get("setIdSets", q=f"SetCode={q_str(set_code)}", limit=2)
    if sets.get("error") or not sets.get("items"):
        return {"blocked": True, "reason": f"Reference data set {set_code!r} not found", "detail": sets}
    address = {"AddressLine1": address_line1, "TownOrCity": town_or_city, "Country": country,
               "PostalCode": postal_code, "Region1": region1, **(address_extra or {})}
    payload = {
        "SetCode": set_code, "SetId": sets["items"][0].get("SetId"),
        "LocationCode": location_code, "LocationName": location_name,
        "EffectiveStartDate": effective_start_date, "EffectiveEndDate": effective_end_date,
        "ShipToSiteFlag": ship_to, "ReceivingSiteFlag": receiving, "BillToSiteFlag": bill_to, "OfficeSiteFlag": office,
        "addresses": [{k: v for k, v in address.items() if v not in (None, "")}],
    }
    return create_checked(LOCATIONS, payload, dup_q=f"LocationCode={q_str(location_code)}", extra=extra,
                          dry_run=dry_run, confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


TOOLS = [create_location]
