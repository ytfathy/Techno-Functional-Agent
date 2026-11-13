"""Procurement shortcuts: agents, requisitions, purchase orders. knowledge/procurement-agents.md, requisitions.md,
purchase-orders.md."""
from __future__ import annotations

from .generic import _describe_raw, _node_for, create_checked, q_str, rest_action, rest_create


def create_procurement_agent(agent_email: str, procurement_bu: str, all_access: bool = True,
                             overrides: dict | None = None, dry_run: bool = True, confirm_prod: str = "",
                             allow_duplicate: bool = False) -> dict:
    """Give a person procurement agent access on a procurement BU (buyer, catalog admin, supplier manager…).
    all_access=True: every *AllowedFlag = true and every AccessLevelToOtherAgents*Code = FULL (read from describe,
    so new flags in later releases are covered). overrides: exact attribute -> value to change any of them."""
    payload: dict = {"AgentEmail": agent_email, "ProcurementBU": procurement_bu, "StatusCode": "Y"}
    if all_access:
        attrs = [a.get("name", "") for a in _node_for(_describe_raw("procurementAgents"), "procurementAgents").get("attributes", [])]
        payload |= {a: True for a in attrs if a.endswith("AllowedFlag")}
        payload |= {a: "FULL" for a in attrs if a.startswith("AccessLevelToOtherAgents") and a.endswith("Code")}
    payload |= overrides or {}
    return create_checked("procurementAgents", payload,
                          dup_q=f"AgentEmail={q_str(agent_email)} and ProcurementBU={q_str(procurement_bu)}",
                          dry_run=dry_run, confirm_prod=confirm_prod, allow_duplicate=allow_duplicate)


def create_requisition(requisitioning_bu: str, lines: list[dict], description: str = "", preparer_email: str = "",
                       extra: dict | None = None, dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Create a requisition (header + lines in one POST to purchaseRequisitions).
    lines: dicts with exact line attributes, e.g. {"LineNumber":1,"LineTypeCode":"Goods","ItemDescription":"Laptop",
    "CategoryName":"...","Quantity":2,"UOM":"Each","Price":1000,"CurrencyCode":"EGP","DestinationTypeCode":"EXPENSE",
    "DeliverToLocationCode":"...","RequesterEmail":"...","RequestedDeliveryDate":"2026-12-01"}.
    Note: the preparer must be the REST user's own person record (Oracle rule)."""
    payload = {"RequisitioningBU": requisitioning_bu, "Description": description, "PreparerEmail": preparer_email,
               "lines": lines, **(extra or {})}
    return rest_create("purchaseRequisitions", {k: v for k, v in payload.items() if v not in (None, "")},
                       dry_run=dry_run, confirm_prod=confirm_prod)


def submit_requisition(requisition_header_id: int, dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Submit a requisition for approval (action submitRequisition)."""
    return rest_action(f"purchaseRequisitions/{requisition_header_id}", "submitRequisition", {},
                       dry_run=dry_run, confirm_prod=confirm_prod)


def create_purchase_order(procurement_bu: str, supplier: str, supplier_site: str, buyer_email: str, lines: list[dict],
                          requisitioning_bu: str = "", document_style: str = "", currency_code: str = "",
                          description: str = "", extra: dict | None = None, dry_run: bool = True,
                          confirm_prod: str = "") -> dict:
    """Create a draft PO (draftPurchaseOrders: header + lines + schedules in one POST). The buyer must be a
    procurement agent on the BU; the supplier site must be assigned to the requisitioning BU.
    lines: e.g. [{"LineNumber":1,"LineType":"Goods","Description":"...","Category":"...","Quantity":5,"UOM":"Each",
    "Price":100,"schedules":[{"ScheduleNumber":1,"Quantity":5,"ShipToOrganizationCode":"...","ShipToLocationCode":"...",
    "RequestedDeliveryDate":"2026-12-01","DestinationTypeCode":"EXPENSE"}]}]."""
    payload = {"ProcurementBU": procurement_bu, "RequisitioningBU": requisitioning_bu, "Supplier": supplier,
               "SupplierSite": supplier_site, "BuyerEmail": buyer_email, "DocumentStyle": document_style,
               "CurrencyCode": currency_code, "Description": description, "lines": lines, **(extra or {})}
    return rest_create("draftPurchaseOrders", {k: v for k, v in payload.items() if v not in (None, "")},
                       dry_run=dry_run, confirm_prod=confirm_prod)


def submit_purchase_order(po_header_id: int, bypass_approvals: bool = False, dry_run: bool = True,
                          confirm_prod: str = "") -> dict:
    """Submit a draft PO / change order (action submit on draftPurchaseOrders)."""
    params = {"bypassApprovalsFlag": True} if bypass_approvals else {}
    return rest_action(f"draftPurchaseOrders/{po_header_id}", "submit", params, dry_run=dry_run, confirm_prod=confirm_prod)


TOOLS = [create_procurement_agent, create_requisition, submit_requisition, create_purchase_order, submit_purchase_order]
