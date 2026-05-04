"""
main.py
--------
FastAPI application for the portal-survey-agent service.

ENDPOINTS
---------
GET  /health          → liveness probe
POST /agent/query     → main chat endpoint (stateless HTTP, session in memory)

SESSION MANAGEMENT
------------------
Sessions are stored in a plain Python dict (sessions: dict[str, dict]).
This is fine for development and single-instance deployments.
For production with multiple replicas, replace with Redis:

  import redis.asyncio as redis
  r = redis.Redis(...)
  session = json.loads(await r.get(session_id) or "{}")
  await r.setex(session_id, 3600, json.dumps(result["session"]))

CORS
----
ALLOWED_ORIGINS in config controls which frontend domains can call this.
Set to "*" locally, restrict in production.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from agents.supervisor import SupervisorAgent
from models import AgentRequest, AgentResponse, new_session_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(
    title="Portal Survey Multi-Agent Service",
    description=(
        "Multi-agent AI workflow for natural-language survey CRUD, "
        "analytics, campus info, and insight generation."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One supervisor instance for the lifetime of the process
supervisor = SupervisorAgent()

# In-memory session store — replace with Redis for multi-replica prod
sessions: dict[str, dict] = {}


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


@app.post("/agent/query", response_model=AgentResponse, tags=["Agent"])
async def query_agent(payload: AgentRequest) -> AgentResponse:
    """
    Main chat endpoint.

    Flow:
      1. Resolve or create session
      2. Run supervisor (plan → dispatch → synthesize)
      3. Persist session mutations
      4. Return structured AgentResponse
    """
    session_id = payload.session_id or new_session_id()
    session = sessions.setdefault(session_id, {})

    result = await supervisor.run(payload.message, session)

    # Persist or clear session based on what the agent left behind
    new_session = result.get("session", {})
    if new_session:
        sessions[session_id] = new_session
    else:
        sessions.pop(session_id, None)

    return AgentResponse(
        session_id=session_id,
        response=result.get("response", "I could not produce a response."),
        intent=result.get("intent", "unknown"),
        requires_confirmation=result.get("requires_confirmation", False),
        pending_action=result.get("pending_action"),
        agent_tags=result.get("agent_tags", []),
        ui_hints=result.get("ui_hints", {}),
        quick_actions=result.get("quick_actions", []),
        data={
            "agents_invoked": result.get("agents_to_invoke", []),
            "crud_result": result.get("crud_result"),
            "analytics_result": result.get("analytics_result"),
            "campus_result": result.get("campus_result"),
            "insight_result": result.get("insight_result"),
        },
    )