"""Anthropic Tool Use schemas — loaded by /tools endpoint and at agent boot time."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent


def _load_json(name: str) -> list[dict[str, Any]]:
    p = _HERE / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_tool_definitions() -> dict[str, list[dict[str, Any]]]:
    """Return {agent_name: [tool_def, ...]} merged from disk."""
    return {
        "strategist": _load_json("strategist.json"),
        "producer": _load_json("producer.json"),
        "scorer": _load_json("scorer.json"),
        "publisher": _load_json("publisher.json"),
        "analyst": _load_json("analyst.json"),
    }
