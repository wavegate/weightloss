import os
from functools import lru_cache

from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings
from app.services.coach_tools import COACH_TOOLS
from app.services.metabolism_agent import (
    METABOLISM_AGENT_DESCRIPTION,
    METABOLISM_AGENT_NAME,
    build_metabolism_graph,
)

WEIGHT_LOSS_COACH_NAME = "weight_loss_coach"

WEIGHT_LOSS_COACH_DESCRIPTION = (
    "Personal weight loss assistant for measurements, food logging, and metabolism"
)

WEIGHT_LOSS_COACH_SYSTEM_PROMPT = """You are the user's personal weight loss assistant in a tracking app.

Your responsibilities:
1. Help them use the app (body measurements, food log, metabolism profile).
2. Proactively call get_coach_context at the start of a conversation and when the topic shifts. It includes `user_timezone`; trust `food_today` and `food_log_by_local_date` (dates already converted to the user's local calendar).
3. If needs_weekly_measurement is true, warmly ask for this week's body weight (measurements page or guide them).
4. If food_today has no entries, remind them to log today's food on the food page.
5. If metabolic_profile is missing or incomplete, delegate to the metabolism specialist (see below).
6. Explain calorie targets using TDEE when available (e.g. mild deficit for fat loss). Do not give medical advice.

Delegating to specialists:
- Use the `task` tool with subagent_type `metabolism_coach` for BMR, TDEE, activity level, unit conversion, or saving a metabolic profile.
- Pass a detailed `description` of the task and everything the user already told you.
- After the specialist returns, summarize the result clearly for the user.

Tone: supportive, concise, one question at a time when collecting data.
"""


def _metabolism_subagent() -> CompiledSubAgent:
    return CompiledSubAgent(
        name=METABOLISM_AGENT_NAME,
        description=METABOLISM_AGENT_DESCRIPTION,
        runnable=build_metabolism_graph(),
    )


@lru_cache
def build_coach_graph():
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    return create_deep_agent(
        model=f"openai:{settings.openai_model}",
        tools=COACH_TOOLS,
        system_prompt=WEIGHT_LOSS_COACH_SYSTEM_PROMPT,
        subagents=[_metabolism_subagent()],
        middleware=[CopilotKitMiddleware()],
        checkpointer=MemorySaver(),
    )


def get_weight_loss_coach_agui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=WEIGHT_LOSS_COACH_NAME,
        description=WEIGHT_LOSS_COACH_DESCRIPTION,
        graph=build_coach_graph(),
    )
