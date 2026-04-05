"""Smoke tests: verify MCP server registrations are complete.

These tests do not start the server or send MCP RPCs — they inspect
the FastMCP instance to confirm that all expected resources, tools,
and prompts are registered and none have been accidentally removed.
"""

from __future__ import annotations

from pakunoda_mcp.server import mcp


# ── Expected registrations ──────────────────────────────────────────

EXPECTED_TOOLS = {
    # read-only
    "validate_project",
    "enumerate_candidates",
    "get_candidate_details",
    "get_candidate_problem",
    "get_candidate_result",
    "get_candidate_score",
    "summarize_search",
    "recommend_model",
    # write
    "run_search",
    "refresh_project_state",
}

EXPECTED_PROMPTS = {
    "inspect_project",
    "compare_candidates",
}

# Static resources (non-template)
EXPECTED_RESOURCES = {
    "pakunoda://project/config",
    "pakunoda://project/graph",
    "pakunoda://project/candidates",
    "pakunoda://project/summary",
    "pakunoda://search/summary",
    "pakunoda://search/trials",
}

# Resource templates (contain {param})
EXPECTED_TEMPLATES = {
    "pakunoda://candidate/{candidate_id}/problem",
}


# ── Tests ───────────────────────────────────────────────────────────

def test_all_tools_registered() -> None:
    registered = {t.name for t in mcp._tool_manager.list_tools()}
    assert EXPECTED_TOOLS == registered


def test_all_prompts_registered() -> None:
    registered = {p.name for p in mcp._prompt_manager.list_prompts()}
    assert EXPECTED_PROMPTS == registered


def test_all_resources_registered() -> None:
    registered = {
        str(r.uri) for r in mcp._resource_manager.list_resources()
    }
    assert EXPECTED_RESOURCES == registered


def test_all_templates_registered() -> None:
    registered = {
        str(t.uri_template) for t in mcp._resource_manager.list_templates()
    }
    assert EXPECTED_TEMPLATES == registered


def test_server_name() -> None:
    assert mcp.name == "Pakunoda-MCP"


def test_entrypoint_callable() -> None:
    from pakunoda_mcp.server import main
    assert callable(main)
