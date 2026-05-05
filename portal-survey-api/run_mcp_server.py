#!/usr/bin/env python3
"""
Standalone MCP Server for Survey Tools
Run this separately from the FastAPI REST API.
Usage: python run_mcp_server.py
"""
import sys
import os

# Add parent directory to path to import mcp_tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path is set
from mcp_tools import mcp

if __name__ == "__main__":
    print("Starting MCP Survey Tools Server...")
    print("Transport: SSE (Server-Sent Events)")
    print("Available tools:")
    print("  - create_survey")
    print("  - list_surveys")
    print("  - get_survey_by_id")
    print("  - search_surveys")
    print("  - update_survey")
    print("  - delete_survey")
    print("\nServer running on http://localhost:8002")
    print("Agent should connect to: http://localhost:8002/sse")
    print("\nPress CTRL+C to stop\n")
    
    try:
        # Run the MCP server with SSE transport
        # This method handles its own event loop
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        print("\n\nShutting down MCP server...")
        sys.exit(0)
