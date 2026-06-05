import os
from functools import lru_cache

from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from deepagents import create_deep_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings
from app.services.event_manager_tools import EVENT_MANAGER_TOOLS

EVENT_MANAGER_AGENT_NAME = "event_manager"

EVENT_MANAGER_AGENT_DESCRIPTION = (
    "Helps users discover events, activities, and things to do near them"
)

EVENT_MANAGER_SYSTEM_PROMPT = """You are an event discovery assistant focused on the SF Bay Area
(South Bay default: Cupertino, Mountain View, Palo Alto, Sunnyvale, San Jose; widen to SF/Oakland
when asked).

Help users find concerts, festivals, meetups, sports, theater, food events, and local activities.

Tools:
- get_event_preferences: Load saved defaults (home area, distance, timing, date range, free-only, budget, categories).
- get_event_preference_options: Valid location, timing, and category IDs (only if an update might fail validation).
- update_event_preferences: Persist prefs — call whenever the user states or implies them, not only on explicit "save" requests.
- search_events: Primary discovery — all platforms in parallel; empty args use saved prefs (including date-range).
- web_search: Only if search_events returns few results or the user needs niche sources.

Workflow:
1. Call get_event_preferences once early in a session (or when unsure what is saved).
2. Whenever the user mentions location, timing, budget, cost limits, categories, or interests — even casually
   while asking for events — call update_event_preferences first with only the fields you inferred, then search.
   Examples: "hackathons in SF this weekend" → home_location san-francisco, default_timing weekend,
   interest_keywords hackathon; "free music near Palo Alto" → palo-alto, free_only true, categories music.
   Do not ask permission to save; treat stated prefs as the new defaults silently (briefly note what you saved).
3. search_events: pass keyword/timing/location overrides for this turn; saved prefs fill in anything omitted.
4. Reply with 3–7 options: title, when, where, cost, link, source, and why they fit.
   Mention source errors from the tool payload if a platform failed.

Never invent events. Only list items returned by tools, with their URLs.
"""


@lru_cache
def build_event_manager_graph():
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    ddg_search = DuckDuckGoSearchRun()

    def web_search(query: str) -> str:
        """Search the web for events, venues, meetups, and local activities (DuckDuckGo)."""
        return ddg_search.invoke(query)

    return create_deep_agent(
        model=f"openai:{settings.openai_model}",
        tools=[*EVENT_MANAGER_TOOLS, web_search],
        middleware=[CopilotKitMiddleware()],
        system_prompt=EVENT_MANAGER_SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )


def get_event_manager_agui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=EVENT_MANAGER_AGENT_NAME,
        description=EVENT_MANAGER_AGENT_DESCRIPTION,
        graph=build_event_manager_graph(),
    )
