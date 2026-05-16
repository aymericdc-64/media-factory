"""Smoke tests — verify the app boots and routes are mounted."""
from __future__ import annotations

import os

import pytest

# Ensure minimal env before importing the app
os.environ.setdefault("SKILLS_AUTH_SECRET", "test-secret-changeme")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("NOTION_API_KEY", "ntn_test")
for k in (
    "NOTION_DS_CONTENT_CATALOG",
    "NOTION_DS_PRODUCTION_PIPELINE",
    "NOTION_DS_PERFORMANCE_TRACKER",
    "NOTION_DS_CHANNELS",
    "NOTION_DS_CONTENT_THEMES",
    "NOTION_DS_ASSET_TEMPLATES",
    "NOTION_DS_PROMPTS_LIBRARY",
):
    os.environ.setdefault(k, "00000000-0000-0000-0000-000000000000")

from fastapi.testclient import TestClient  # noqa: E402

from src.main import app  # noqa: E402

client = TestClient(app)


def test_health_endpoint_public():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_tools_endpoint_public():
    r = client.get("/tools")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) >= {"strategist", "producer", "scorer", "publisher", "analyst"}
    # Each agent has at least one tool
    for agent, tools in body.items():
        assert len(tools) >= 1, f"agent {agent} has no tools"
        for t in tools:
            assert "name" in t and "input_schema" in t


def test_protected_route_requires_auth():
    r = client.post("/strategist/read_content_catalog", json={"status": "À produire"})
    assert r.status_code == 401


def test_protected_route_rejects_wrong_token():
    r = client.post(
        "/strategist/read_content_catalog",
        json={"status": "À produire"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert r.status_code == 403


@pytest.mark.parametrize(
    "agent_path,payload",
    [
        ("/producer/generate_image", {"prompt": "test"}),
        ("/scorer/read_production_pipeline", {"status": "Produced"}),
        ("/publisher/read_channels_active", {}),
        ("/analyst/compute_engagement_rate", {"views": 100, "likes": 10, "comments": 2, "shares": 1}),
    ],
)
def test_routes_exist_with_auth(agent_path, payload):
    """We don't expect a 200 (network would fail), but at least no 401/403/404."""
    r = client.post(
        agent_path,
        json=payload,
        headers={"Authorization": "Bearer test-secret-changeme"},
    )
    assert r.status_code not in (401, 403, 404), f"{agent_path} → {r.status_code} {r.text[:200]}"
