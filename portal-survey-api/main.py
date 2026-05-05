from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_db_and_tables
from api import survey_router
from mcp_tools import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Student Survey API",
    description="REST API for managing student campus-visit survey data.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(survey_router)


# MCP endpoints
@app.get("/mcp", tags=["MCP"])
async def mcp_info():
    """MCP server information and available endpoints."""
    return {
        "name": "Student Survey MCP Server",
        "version": "1.0.0",
        "description": "Model Context Protocol server for student campus-visit survey management",
        "endpoints": {
            "tools": "/mcp/tools - List all available MCP tools",
            "call": "/mcp/call?tool_name=<name> - Execute an MCP tool"
        },
        "available_tools": [
            "create_survey",
            "list_surveys",
            "get_survey_by_id",
            "search_surveys",
            "update_survey",
            "delete_survey"
        ]
    }


@app.get("/mcp/tools", tags=["MCP"])
async def list_mcp_tools():
    """List all available MCP tools."""
    return await mcp.list_tools()


@app.post("/mcp/call", tags=["MCP"])
async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool by name with arguments."""
    return await mcp.call_tool(tool_name, arguments)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
