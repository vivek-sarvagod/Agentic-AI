import os
from typing import Any

import httpx

from config import settings


class SurveyToolClient:
    def __init__(self) -> None:
        self.api_base_url = settings.API_BASE_URL.rstrip("/")
        self.mcp_server_url = settings.MCP_SERVER_URL

    async def call(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if os.getenv("USE_MCP_TOOLS", "false").lower() == "true":
            try:
                return await self._call_mcp(tool_name, arguments)
            except Exception:
                pass

        try:
            return await self._call_rest(tool_name, arguments)
        except Exception as exc:
            return {
                "ok": False,
                "message": (
                    f"Could not execute {tool_name}. Make sure the API service is running "
                    f"at {self.api_base_url} and MySQL is available. Details: {exc}"
                ),
            }

    async def _call_mcp(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        from fastmcp import Client

        async with Client(self.mcp_server_url) as client:
            result = await client.call_tool(tool_name, arguments)

        if hasattr(result, "data") and isinstance(result.data, dict):
            return result.data
        if hasattr(result, "structured_content") and isinstance(result.structured_content, dict):
            return result.structured_content
        return {"ok": True, "result": str(result)}

    async def _call_rest(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            if tool_name == "create_survey":
                response = await client.post(
                    f"{self.api_base_url}/api/surveys",
                    json=arguments["payload"],
                )
                return self._handle_response(response, "survey")

            if tool_name == "list_surveys":
                response = await client.get(f"{self.api_base_url}/api/surveys")
                return self._handle_response(response)

            if tool_name == "get_survey_by_id":
                response = await client.get(
                    f"{self.api_base_url}/api/surveys/{arguments['survey_id']}"
                )
                return self._handle_response(response, "survey")

            if tool_name == "search_surveys":
                all_surveys = await client.get(f"{self.api_base_url}/api/surveys")
                payload = self._handle_response(all_surveys)
                surveys = payload.get("surveys", [])
                filtered = self._filter_surveys(surveys, arguments)
                return {"ok": True, "total": len(filtered), "surveys": filtered}

            if tool_name == "update_survey":
                response = await client.put(
                    f"{self.api_base_url}/api/surveys/{arguments['survey_id']}",
                    json=arguments["changes"],
                )
                return self._handle_response(response, "survey")

            if tool_name == "delete_survey":
                response = await client.delete(
                    f"{self.api_base_url}/api/surveys/{arguments['survey_id']}"
                )
                return self._handle_response(response)

        return {"ok": False, "message": f"Unsupported tool: {tool_name}"}

    @staticmethod
    def _handle_response(response: httpx.Response, wrapper_key: str | None = None) -> dict[str, Any]:
        if response.status_code >= 400:
            return {"ok": False, "message": response.text, "status_code": response.status_code}
        data = response.json()
        if wrapper_key and wrapper_key not in data:
            return {"ok": True, wrapper_key: data}
        return {"ok": True, **data}

    @staticmethod
    def _filter_surveys(
        surveys: list[dict[str, Any]],
        arguments: dict[str, Any],
    ) -> list[dict[str, Any]]:
        def matches(survey: dict[str, Any]) -> bool:
            for key in ("first_name", "last_name", "interest_source", "recommendation"):
                value = arguments.get(key)
                if value and value.lower() not in str(survey.get(key, "")).lower():
                    return False
            liked = arguments.get("liked_most")
            if liked:
                values = [item.lower() for item in survey.get("liked_most", [])]
                if liked.lower() not in values:
                    return False
            return True

        return [survey for survey in surveys if matches(survey)]
