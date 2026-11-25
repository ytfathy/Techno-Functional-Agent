"""MCP server 'oracle-fusion': registers every tool. Run: python -m oracle_fusion_mcp.server"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import bi, bulk, client, enterprise, fbdi, fsm, generic, inventory, locations, procurement, security, smoke, suppliers, workflow

mcp = FastMCP(
    "oracle-fusion",
    instructions=(
        "Hands of the Oracle Fusion SCM/Procurement consultant agent. Every write tool defaults to dry_run=True "
        "(returns the exact endpoint + payload). Call rest_describe before building any payload. On PROD every "
        "write needs confirm_prod='CONFIRM PROD' typed by the user. Errors come back parsed with Oracle codes."
    ),
)


def env_info() -> dict:
    """Show the active environment profile (env name, pod URL, release, auth mode, agent user) and the autonomy mode."""
    return {**client.get_client().info(), "mode": client.get_mode()}


def switch_environment(name: str) -> dict:
    """Switch to the .env.<name> profile (dev | test | prod). Switching to PROD forces confirm mode."""
    c = client.switch_environment(name)
    return {**c.info(), "mode": client.get_mode()}


def disconnect() -> dict:
    """Turn the agent off: close the Oracle connection and refuse every Fusion call until switch_environment
    (/agent on). Mode resets to confirm."""
    client.disconnect()
    return {"connected": False, "mode": client.get_mode()}


def set_mode(mode: str) -> dict:
    """Set autonomy mode: 'confirm' (plan + one yes) or 'auto' (DEV/TEST only)."""
    try:
        return {"mode": client.set_mode(mode), "env": client.get_client().env_name}
    except (ValueError, PermissionError) as e:
        return {"error": str(e), "mode": client.get_mode()}


def log_request(request: str, channel: str, summary: str, ids: dict | None = None, area: str = "") -> dict:
    """Write the request-level audit record (user request, channel A/B/C/D, what was done, resulting IDs).
    Call once per completed request, in addition to the automatic per-call audit of writes."""
    client.audit({"event": "request", "env": client.get_client().env_name, "request": request,
                  "channel": channel, "summary": summary, "ids": ids or {}, "area": area})
    return {"logged": True}


TOOLS = [
    env_info, switch_environment, disconnect, set_mode, log_request, smoke.smoke_test,
    # generic (most important)
    generic.rest_describe, generic.rest_get, generic.rest_create, generic.rest_update, generic.rest_action,
    generic.rest_delete, generic.rest_batch, generic.soap_call,
    # channel B / C
    *fsm.TOOLS, *fbdi.TOOLS,
    # shortcuts
    *suppliers.TOOLS, *procurement.TOOLS, *locations.TOOLS, *enterprise.TOOLS, *inventory.TOOLS, *bulk.TOOLS, *security.TOOLS, *bi.TOOLS, *workflow.TOOLS,
]
for _fn in TOOLS:
    mcp.tool()(_fn)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
