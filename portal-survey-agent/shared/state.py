"""
shared/state.py
---------------
Single source of truth for the AgentState TypedDict that flows
through every node in every agent graph.

WHY A SHARED STATE?
-------------------
LangGraph passes one dict (the "state") between every node.
Each node reads what it needs and writes only its own keys.
Putting all keys in ONE TypedDict here means:
  - No import cycles between agent files
  - The supervisor and every sub-agent speak the same schema
  - Adding a new field is a one-file change
"""
from __future__ import annotations

from typing import Any, Literal
from typing_extensions import TypedDict

# The four sub-agent names used as routing targets in the supervisor
AgentName = Literal["crud", "analytics", "campus_info", "insight"]


class AgentState(TypedDict, total=False):
    # ── INPUT ─────────────────────────────────────────────────────
    user_query: str           # raw message from the user
    session: dict[str, Any]  # server-side session dict (persists across turns)

    # ── SUPERVISOR PLAN ───────────────────────────────────────────
    # After classification this holds which agents to run.
    # e.g. ["campus_info", "analytics"]
    agents_to_invoke: list[AgentName]

    # ── PER-AGENT RESULTS ─────────────────────────────────────────
    # Each sub-agent writes ONLY its own result key.
    # The supervisor reads all of them in _synthesize_node.
    crud_result: dict[str, Any]
    analytics_result: dict[str, Any]
    campus_result: dict[str, Any]
    insight_result: dict[str, Any]

    # ── FINAL RESPONSE ────────────────────────────────────────────
    response: str                         # plain-text answer shown in chat
    ui_hints: dict[str, Any]             # rich rendering metadata for React UI
    agent_tags: list[str]                # e.g. ["Campus info agent", "Analytics agent"]
    quick_actions: list[dict[str, str]]  # [{label, prompt}, ...] for suggestion buttons

    # ── MULTI-TURN / CONFIRMATION ─────────────────────────────────
    requires_confirmation: bool   # tells UI to show Yes / No buttons
    pending_action: str | None    # which action is waiting for confirmation

    # ── CRUD AGENT INTERNALS (kept for backward compat) ──────────
    intent: str
    tool_name: str | None
    tool_args: dict[str, Any]
    tool_output: dict[str, Any]
    draft: dict[str, Any]
    changes: dict[str, Any]
    selected_survey: dict[str, Any] | None