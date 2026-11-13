import pytest
import respx

from oracle_fusion_mcp import client, generic

BASE = "https://pod.example.com"
FSCM_URL = BASE + client.FSCM
HCM_URL = BASE + client.HCM


def make_client(env: str = "TEST") -> client.FusionClient:
    return client.FusionClient({"ORACLE_BASE_URL": BASE, "ORACLE_ENV_NAME": env, "ORACLE_AUTH_MODE": "basic",
                                "ORACLE_USERNAME": "AI_SCM_AGENT", "ORACLE_PASSWORD": "pw", "_profile": env.lower()})


@pytest.fixture
def fusion(monkeypatch, tmp_path):
    """Active TEST client + respx router rooted at /fscmRestApi/resources/11.13.18.05. No real HTTP."""
    monkeypatch.setenv("ORACLE_AGENT_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(client.time, "sleep", lambda s: None)
    client.set_client(make_client())
    client._state["mode"] = "confirm"
    generic._describe_cache.clear()
    with respx.mock(base_url=FSCM_URL, assert_all_called=False) as router:
        router.log_dir = tmp_path / "logs"
        yield router
    client.set_client(None)


def describe(name: str, attrs: list, children: dict | None = None, item_actions: list | None = None) -> dict:
    """Build a minimal ADF describe document."""
    def node(a, ch, acts):
        return {"title": name, "attributes": [x if isinstance(x, dict) else {"name": x, "type": "string"} for x in a],
                "collection": {"finders": [{"name": "PrimaryKey", "attributes": [{"name": "Id"}]}], "actions": []},
                "item": {"actions": [{"name": "get"}] + [{"name": n, "parameters": []} for n in (acts or [])]},
                "children": {k: node(v, None, None) for k, v in (ch or {}).items()}}
    return {"Resources": {name: node(attrs, children, item_actions)}}
