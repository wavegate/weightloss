import os
from functools import lru_cache

from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings
from app.services.coach_handoff_middleware import apply_active_agent_config
from app.services.coach_prompts import WEIGHT_LOSS_COACH_SYSTEM_PROMPT
from app.services.coach_tools import COACH_TOOLS
from app.services.handoff_tools import (
    WeightLossAssistantState,
    transfer_to_metabolism_coach,
    transfer_to_weight_loss_coach,
)
from app.services.handoff_tools import METABOLISM_AGENT_NAME
from app.services.metabolism_tools import METABOLISM_TOOLS

WEIGHT_LOSS_COACH_NAME = "weight_loss_coach"

WEIGHT_LOSS_COACH_DESCRIPTION = (
    "Personal weight loss assistant for measurements, food logging, and metabolism"
)

# Register every tool up front; middleware only changes which subset the model sees.
_ALL_ASSISTANT_TOOLS = [
    *COACH_TOOLS,
    transfer_to_metabolism_coach,
    *METABOLISM_TOOLS,
    transfer_to_weight_loss_coach,
]


@lru_cache
def build_coach_graph():
    """Single AG-UI graph with LangChain handoffs (active_agent state + middleware)."""
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    return create_agent(
        model=f"openai:{settings.openai_model}",
        tools=_ALL_ASSISTANT_TOOLS,
        system_prompt=WEIGHT_LOSS_COACH_SYSTEM_PROMPT,
        state_schema=WeightLossAssistantState,
        middleware=[
            CopilotKitMiddleware(),
            apply_active_agent_config,
        ],
        checkpointer=MemorySaver(),
    )


def get_weight_loss_coach_agui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=WEIGHT_LOSS_COACH_NAME,
        description=WEIGHT_LOSS_COACH_DESCRIPTION,
        graph=build_coach_graph(),
    )


# Re-export for handoff_tools / UI
METABOLISM_COACH_NAME = METABOLISM_AGENT_NAME
