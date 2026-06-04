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
- search_events: Primary tool — queries Meetup, Eventbrite, Luma, and Funcheap in parallel,
  merges and dedupes. Always call this for event discovery (not separate per-platform tools).
- web_search: Only if search_events returns few results or the user needs niche sources.

Default location cupertino if unspecified.

Workflow:
1. If location, timing, or interests are unclear, ask one short clarifying question.
2. Call search_events with location, optional keywords, and timing (today / weekend / free).
3. Use web_search only when needed.
4. Reply with 3–7 options. Each must include: title, when, where, cost (if known), link, source, and why it fits.
   Mention any source errors from the tool payload if a platform failed.

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
