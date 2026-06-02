import os
from functools import lru_cache

from copilotkit import CopilotKitMiddleware, LangGraphAGUIAgent
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings
from app.services.metabolism_tools import METABOLISM_TOOLS

METABOLISM_AGENT_NAME = "metabolism_coach"

METABOLISM_AGENT_DESCRIPTION = (
    "Metabolic coach for BMR/TDEE estimation and profile setup"
)

METABOLISM_SYSTEM_PROMPT = """You are a metabolic coach for a weight-loss tracking app.

Your job is to help the user estimate their daily calorie needs (BMR and TDEE) through a friendly conversation.

Guidelines:
1. Call get_user_context early to see if they already have a profile, recent weight, or food logs.
2. Collect missing inputs one at a time—never ask "tell me about yourself." Ask specific questions: sex, age, height, weight (use convert_units if they give lb/in), then activity level.
3. Use compute_bmr and compute_tdee_from_bmr for all math — never estimate calories in your head.
4. Explain results in plain language: what BMR and TDEE mean, and how activity level affects TDEE.
5. Offer practical next steps (e.g. mild deficit for fat loss) but do not prescribe medical advice.
6. Only call save_metabolic_profile after summarizing the numbers and the user agrees to save.
7. Prefer weight from their latest body measurement log when available.

Activity levels:
- sedentary: desk job, little exercise
- light: light exercise 1–3 days/week
- moderate: moderate exercise 3–5 days/week
- active: hard exercise 6–7 days/week
- very_active: very hard exercise or physical job
"""


@lru_cache
def build_metabolism_graph():
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    return create_agent(
        model=f"openai:{settings.openai_model}",
        tools=METABOLISM_TOOLS,
        system_prompt=METABOLISM_SYSTEM_PROMPT,
        middleware=[CopilotKitMiddleware()],
        checkpointer=MemorySaver(),
    )


def get_metabolism_agui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=METABOLISM_AGENT_NAME,
        description=METABOLISM_AGENT_DESCRIPTION,
        graph=build_metabolism_graph(),
    )
