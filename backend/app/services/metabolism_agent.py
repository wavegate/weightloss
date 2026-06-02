import os
from functools import lru_cache

from copilotkit import LangGraphAGUIAgent
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings
from app.services.coach_prompts import METABOLISM_SYSTEM_PROMPT
from app.services.handoff_tools import (
    METABOLISM_AGENT_NAME,
    WeightLossAssistantState,
    transfer_to_weight_loss_coach,
)
from app.services.metabolism_tools import METABOLISM_TOOLS

METABOLISM_AGENT_DESCRIPTION = (
    "Saves metabolic profiles and weight-loss plans, estimates BMR/TDEE, "
    "previews deficits, and suggests goal timelines"
)


@lru_cache
def build_metabolism_graph():
    """Standalone metabolism graph (e.g. tests). Production chat uses build_coach_graph handoffs."""
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    return create_agent(
        model=f"openai:{settings.openai_model}",
        tools=[*METABOLISM_TOOLS, transfer_to_weight_loss_coach],
        system_prompt=METABOLISM_SYSTEM_PROMPT,
        state_schema=WeightLossAssistantState,
        checkpointer=MemorySaver(),
    )


def get_metabolism_agui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=METABOLISM_AGENT_NAME,
        description=METABOLISM_AGENT_DESCRIPTION,
        graph=build_metabolism_graph(),
    )
