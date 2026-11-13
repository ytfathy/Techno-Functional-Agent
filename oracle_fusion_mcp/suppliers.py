"""Supplier shortcuts. Flow = separate calls in order (knowledge/suppliers.md):
create_supplier -> add_supplier_address -> create_supplier_site -> assign_site_to_bu -> add_supplier_contact."""
from __future__ import annotations

from .generic import create_checked, q_str


def create_supplier(name: str, business_relationship_code: str = "", tax_organization_type_code: str = "",
                    supplier_type_code: str = "", taxpayer_id: str = "", tax_registration_number: str = "",
                    extra: dict | None = None, dry_run: bool = True, confirm_prod: str = "",
                    allow_duplicate: bool = False) -> dict:
    """Step 1/5: create the supplier header only. Blocks if the name (or taxpayer id) already exists.
    Valid codes come from the LOV children of rest_describe('suppliers') (e.g. BusinessRelationshipLookup)."""
    payload = {"Supplier": name, "BusinessRelationshipCode": business_relationship_code,
               "TaxOrganizationTypeCode": tax_organization_type_code, "SupplierTypeCode": supplier_type_code,
               "TaxpayerId": taxpayer_id, "TaxRegistrationNumber": tax_registration_number}
    dup = f"Supplier={q_str(name)}" + (f" or TaxpayerId={q_str(taxpayer_id)}" if taxpayer_id else "")
    return create_checked("suppliers", payload, dup_q=dup, extra=extra, dry_run=dry_run,
                          confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


def add_supplier_address(supplier_id: int, address_name: str, country_code: str, address_line1: str, city: str,
                         state: str = "", postal_code: str = "", email: str = "", ordering: bool = True,
                         remit_to: bool = True, rfq_or_bidding: bool = False, extra: dict | None = None,
                         dry_run: bool = True, confirm_prod: str = "", allow_duplicate: bool = False) -> dict:
    """Step 2/5: add an address to a supplier (needed before a site). country_code: ISO (EG, SA)."""
    payload = {"AddressName": address_name, "CountryCode": country_code, "AddressLine1": address_line1,
               "City": city, "State": state, "PostalCode": postal_code, "Email": email,
               "AddressPurposeOrderingFlag": ordering, "AddressPurposeRemitToFlag": remit_to,
               "AddressPurposeRFQOrBiddingFlag": rfq_or_bidding}
    return create_checked(f"suppliers/{supplier_id}/child/addresses", payload, dup_q=f"AddressName={q_str(address_name)}",
                          extra=extra, dry_run=dry_run, confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


def create_supplier_site(supplier_id: int, site_name: str, procurement_bu: str, supplier_address_name: str,
                         purchasing: bool = True, pay: bool = True, extra: dict | None = None,
                         dry_run: bool = True, confirm_prod: str = "", allow_duplicate: bool = False) -> dict:
    """Step 3/5: create a supplier site in a procurement BU, on an existing supplier address."""
    payload = {"SupplierSite": site_name, "ProcurementBU": procurement_bu, "SupplierAddressName": supplier_address_name,
               "SitePurposePurchasingFlag": purchasing, "SitePurposePayFlag": pay}
    return create_checked(f"suppliers/{supplier_id}/child/sites", payload,
                          dup_q=f"SupplierSite={q_str(site_name)} and ProcurementBU={q_str(procurement_bu)}",
                          extra=extra, dry_run=dry_run, confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


def assign_site_to_bu(supplier_id: int, supplier_site_id: int, client_bu: str, bill_to_bu: str = "",
                      ship_to_location_code: str = "", bill_to_location_code: str = "", extra: dict | None = None,
                      dry_run: bool = True, confirm_prod: str = "", allow_duplicate: bool = False) -> dict:
    """Step 4/5: assign a supplier site to a client (requisitioning) BU. bill_to_bu defaults to client_bu.
    The client BU must be served by the site's procurement BU (service provider relationship)."""
    payload = {"ClientBU": client_bu, "BillToBU": bill_to_bu or client_bu,
               "ShipToLocationCode": ship_to_location_code, "BillToLocationCode": bill_to_location_code}
    return create_checked(f"suppliers/{supplier_id}/child/sites/{supplier_site_id}/child/assignments", payload,
                          dup_q=f"ClientBU={q_str(client_bu)}", extra=extra, dry_run=dry_run,
                          confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


def add_supplier_contact(supplier_id: int, first_name: str, last_name: str, email: str, phone_number: str = "",
                         administrative: bool = False, extra: dict | None = None, dry_run: bool = True,
                         confirm_prod: str = "", allow_duplicate: bool = False) -> dict:
    """Step 5/5: add a supplier contact. Blocks if a contact with the same email exists."""
    payload = {"FirstName": first_name, "LastName": last_name, "Email": email, "PhoneNumber": phone_number,
               "AdministrativeContactFlag": administrative}
    return create_checked(f"suppliers/{supplier_id}/child/contacts", payload, dup_q=f"Email={q_str(email)}",
                          extra=extra, dry_run=dry_run, confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


TOOLS = [create_supplier, add_supplier_address, create_supplier_site, assign_site_to_bu, add_supplier_contact]
