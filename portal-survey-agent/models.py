"""
models.py
----------
Request and response Pydantic models for the agent FastAPI endpoints.

AgentRequest  — what the React UI sends in
AgentResponse — what the React UI receives back

The ui_hints field is a free-form dict so we can evolve the
rich rendering protocol (maps, charts, chips) without versioning
the API — the React component reads whatever keys are present.
"""
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, description="The user's natural language message")
    session_id: str | None = Field(
        default=None,
        description="Omit on first turn; echo back on every subsequent turn",
    )


class AgentResponse(BaseModel):
    session_id: str
    response: str                                      # plain-text chat bubble content
    intent: str = "unknown"                            # detected intent (for debugging)
    requires_confirmation: bool = False                # show Yes/No buttons in UI
    pending_action: str | None = None                  # which action awaits confirmation
    agent_tags: list[str] = Field(default_factory=list)  # labels in bubble header
    ui_hints: dict[str, Any] = Field(default_factory=dict)  # rich UI metadata
    quick_actions: list[dict[str, str]] = Field(default_factory=list)  # suggestion buttons
    data: dict[str, Any] = Field(default_factory=dict)   # raw tool output (for debugging)


def new_session_id() -> str:
    return str(uuid4())

# """
# models.py
# ----------
# Request and response Pydantic models for the agent FastAPI endpoints.

# AgentRequest  — what the React UI sends in
# AgentResponse — what the React UI receives back

# The ui_hints field is a free-form dict so we can evolve the
# rich rendering protocol (maps, charts, chips) without versioning
# the API — the React component reads whatever keys are present.
# """
# from typing import Any
# from uuid import uuid4

# from pydantic import BaseModel, Field


# class AgentRequest(BaseModel):
#     message: str = Field(min_length=1, description="The user's natural language message")
#     session_id: str | None = Field(
#         default=None,
#         description="Omit on first turn; echo back on every subsequent turn",
#     )


# class AgentResponse(BaseModel):
#     session_id: str
#     response: str                                      # plain-text chat bubble content
#     intent: str = "unknown"                            # detected intent (for debugging)
#     requires_confirmation: bool = False                # show Yes/No buttons in UI
#     pending_action: str | None = None                  # which action awaits confirmation
#     agent_tags: list[str] = Field(default_factory=list)  # labels in bubble header
#     ui_hints: dict[str, Any] = Field(default_factory=dict)  # rich UI metadata
#     quick_actions: list[dict[str, str]] = Field(default_factory=list)  # suggestion buttons
#     data: dict[str, Any] = Field(default_factory=dict)   # raw tool output (for debugging)


# def new_session_id() -> str:
#     return str(uuid4())