"""Technical consultant — approval workflow tasks via the BPM REST API (/bpm/api/4.0). knowledge/tech-approvals-workflow.md.
Approval RULES / groups have no API (channel D, playbooks/approval-rules.md); these tools handle the TASKS they create."""
from __future__ import annotations

from .client import FusionError, get_client
from .generic import write

BPM = "/bpm/api/4.0/tasks"
ASSIGNMENTS = {"MY", "GROUP", "MY_AND_GROUP", "MY_AND_GROUP_ALL", "REPORTEES", "OWNER", "REVIEWER", "PREVIOUS", "ALL", "ADMIN"}
STATUSES = {"ASSIGNED", "COMPLETED", "SUSPENDED", "WITHDRAWN", "EXPIRED", "ERRORED", "ALERTED"}


def wf_tasks(assignment: str = "MY_AND_GROUP", status: str = "ASSIGNED", keyword: str = "", identification_key: str = "",
             limit: int = 25, offset: int = 0) -> dict:
    """List approval/workflow tasks. assignment: MY | GROUP | MY_AND_GROUP | ALL | ADMIN …; status: ASSIGNED | COMPLETED |
    ERRORED | WITHDRAWN | SUSPENDED | EXPIRED | ALERTED (COMPLETED needs ADMIN, ALL or PREVIOUS).
    Faulted approvals: assignment='ADMIN', status='ERRORED'. keyword: e.g. a requisition or PO number."""
    if assignment.upper() not in ASSIGNMENTS or status.upper() not in STATUSES:
        return {"error": True, "message": f"assignment must be one of {sorted(ASSIGNMENTS)}; status one of {sorted(STATUSES)}"}
    params = {"assignment": assignment.upper(), "status": status.upper(), "limit": limit, "offset": offset,
              "keyword": keyword, "identificationKey": identification_key}
    try:
        data = get_client().request("GET", BPM, params={k: v for k, v in params.items() if v not in ("", None)})
    except FusionError as e:
        return e.to_dict()
    keep = ("number", "title", "state", "outcome", "priority", "createdDate", "assignees", "creator", "identificationKey", "fromUserDisplayName")
    items = [{k: t.get(k) for k in keep if k in t} for t in data.get("items", [])]
    return {"count": len(items), "hasMore": data.get("hasMore"), "tasks": items}


def wf_task(task_number: str, history: bool = True) -> dict:
    """Read one task: state, assignees, allowed actions (actionList) and, with history=True, who did what and when."""
    c = get_client()
    try:
        t = c.request("GET", f"{BPM}/{task_number}")
        out = {"number": t.get("number"), "title": t.get("title"), "state": t.get("state"), "outcome": t.get("outcome"),
               "assignees": t.get("assignees"), "actions": [a.get("actionId") or a.get("id") for a in t.get("actionList") or []]}
        if history:
            h = c.request("GET", f"{BPM}/{task_number}/history", params={"displayStyle": "flatList"})
            out["history"] = [{k: i.get(k) for k in ("actionName", "displayName", "userId", "reason", "updatedDate")}
                              for i in h.get("items", [])]
        return out
    except FusionError as e:
        return e.to_dict()


def wf_task_action(task_number: str, action: str, comments: str = "", reassign_to_user: str = "",
                   dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Act on a workflow task: APPROVE | REJECT | REASSIGN | DELEGATE | WITHDRAW | SUSPEND | RESUME | ESCALATE …
    (check wf_task(...)['actions'] first). REASSIGN/DELEGATE need reassign_to_user. Acting on someone else's approval is a
    business decision: show the task and get the user's explicit yes first."""
    action = action.upper().strip()
    body: dict = {"action": {"id": action}, "comments": comments}
    if action in ("REASSIGN", "DELEGATE"):
        if not reassign_to_user:
            return {"blocked": True, "reason": f"{action} needs reassign_to_user"}
        body["action"]["assignees"] = [{"id": reassign_to_user, "type": "USER"}]
    return write(f"wf_task:{action}", "PUT", f"{BPM}/{task_number}", body, dry_run=dry_run, confirm_prod=confirm_prod,
                 validate=False)


TOOLS = [wf_tasks, wf_task, wf_task_action]
