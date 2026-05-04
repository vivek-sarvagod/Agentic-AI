"""
agents/insight_agent.py
------------------------
Uses an LLM (OpenAI GPT or Claude) to read survey data and generate
a qualitative, natural-language summary of student sentiment.

WHAT THIS AGENT DOES
--------------------
1. Fetches all surveys from the API
2. Formats them into a compact text block
3. Sends that block + a summary instruction to the LLM
4. Returns the LLM's response as a structured dict

WHY A SEPARATE AGENT FOR THIS?
-------------------------------
Analytics agents count and compute — they don't interpret.
"How many students liked dorms?" → AnalyticsAgent (27 out of 50)
"What DO students FEEL about dorms?" → InsightAgent (LLM reads all
comments and liked_most lists, then synthesises a paragraph)

These are fundamentally different tasks and keeping them separate
means you can swap or tune the LLM prompt without touching analytics.

GRACEFUL DEGRADATION
---------------------
If OPENAI_API_KEY is not set, the agent builds a rule-based summary
from the raw data instead of calling the LLM.
This means the system works in demo mode with zero API cost.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from config import settings
from shared.state import AgentState
from shared.tools.survey_client import SurveyToolClient

# How many surveys to send to the LLM. Keeps token cost predictable.
MAX_SURVEYS_FOR_LLM = 30

INSIGHT_SYSTEM_PROMPT = """
You are an analyst for a university campus portal.
You will receive a list of student survey responses about a campus visit.
Write a concise 3-4 sentence qualitative summary covering:
  1. What students liked most
  2. How likely they are to recommend the campus
  3. Any patterns in how they heard about the campus
  4. One sentence of overall sentiment

Be specific, reference actual numbers where helpful, and write in a
professional but warm tone. Do not use bullet points — write prose only.
""".strip()


class InsightAgent:
    def __init__(self) -> None:
        self.client = SurveyToolClient()

    async def run(self, state: AgentState) -> AgentState:
        # Step 1 — fetch surveys
        raw = await self.client.call("list_surveys")
        if not raw.get("ok"):
            state["insight_result"] = {
                "ok": False,
                "summary": "Could not fetch survey data to generate insights.",
            }
            return state

        surveys: list[dict[str, Any]] = raw.get("surveys", [])
        if not surveys:
            state["insight_result"] = {
                "ok": True,
                "summary": "No surveys available yet to generate insights from.",
            }
            return state

        # Step 2 — generate summary (LLM if key present, else rule-based)
        if settings.OPENAI_API_KEY:
            summary = await self._llm_summary(surveys, state.get("user_query", ""))
        else:
            summary = self._rule_based_summary(surveys)

        state["insight_result"] = {
            "ok": True,
            "summary": summary,
            "total_surveys_analysed": len(surveys),
        }
        return state

    # ── LLM path ──────────────────────────────────────────────────────────────

    async def _llm_summary(
        self, surveys: list[dict[str, Any]], user_query: str
    ) -> str:
        """Send survey data to OpenAI and return the summary string."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0.3,   # slight creativity for natural language
                max_tokens=300,
            )

            # Format surveys as readable text — not JSON (LLMs read prose better)
            survey_text = self._format_surveys_for_llm(surveys[:MAX_SURVEYS_FOR_LLM])
            user_message = (
                f"User question: {user_query}\n\n"
                f"Survey data ({len(surveys)} total, showing {min(len(surveys), MAX_SURVEYS_FOR_LLM)}):\n"
                f"{survey_text}"
            )

            response = await model.ainvoke([
                SystemMessage(content=INSIGHT_SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ])
            return str(response.content).strip()

        except Exception as exc:
            # Fallback to rule-based if LLM fails
            return self._rule_based_summary(surveys) + f"\n\n(Note: LLM insight unavailable: {exc})"

    # ── Rule-based fallback (no API key required) ─────────────────────────────

    def _rule_based_summary(self, surveys: list[dict[str, Any]]) -> str:
        """
        Generates a readable summary using only Counter logic.
        Produces output nearly as useful as the LLM version for demo purposes.
        """
        total = len(surveys)

        liked_counter: Counter = Counter()
        for s in surveys:
            for item in s.get("liked_most", []):
                liked_counter[item.lower()] += 1

        rec_counter = Counter(s.get("recommendation", "Unknown") for s in surveys)
        src_counter = Counter(s.get("interest_source", "unknown") for s in surveys)

        top_liked = liked_counter.most_common(3)
        top_rec = rec_counter.most_common(1)
        top_src = src_counter.most_common(1)

        liked_str = (
            ", ".join(f"{k.replace('_', ' ')} ({v})" for k, v in top_liked)
            if top_liked else "various features"
        )
        rec_str = f"{top_rec[0][0]} ({top_rec[0][1]} students)" if top_rec else "mixed"
        src_str = top_src[0][0] if top_src else "various sources"

        likely_count = rec_counter.get("Very Likely", 0) + rec_counter.get("Likely", 0)
        likely_pct = round(likely_count / total * 100) if total else 0

        return (
            f"Across {total} student surveys, the most appreciated campus features were "
            f"{liked_str}. The majority of students ({likely_pct}%) would recommend "
            f"the campus, with the top recommendation being {rec_str}. "
            f"Most students learned about the campus through {src_str}. "
            f"Overall sentiment is {'positive' if likely_pct >= 60 else 'mixed'}, "
            f"suggesting the campus experience resonates well with visitors."
        )

    # ── formatting helper ─────────────────────────────────────────────────────

    @staticmethod
    def _format_surveys_for_llm(surveys: list[dict[str, Any]]) -> str:
        """
        Convert survey list to compact readable text for LLM context.
        We deliberately keep this concise to stay within token limits.
        """
        lines = []
        for s in surveys:
            liked = ", ".join(s.get("liked_most", []))
            lines.append(
                f"- {s.get('first_name')} {s.get('last_name')}: "
                f"liked {liked or 'nothing specified'}; "
                f"recommendation: {s.get('recommendation', 'N/A')}; "
                f"source: {s.get('interest_source', 'N/A')}"
            )
        return "\n".join(lines)