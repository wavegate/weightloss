"""Handoff tools — switch the active agent so the user can talk to a specialist directly."""

from typing import Literal

from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command
from typing_extensions import NotRequired

from langchain.agents import AgentState

WEIGHT_LOSS_COACH_AGENT = "weight_loss_coach"
METABOLISM_AGENT_NAME = "metabolism_coach"
DIETICIAN_AGENT_NAME = "dietician_coach"
ActiveAgent = Literal["weight_loss_coach", "metabolism_coach", "dietician_coach"]


class WeightLossAssistantState(AgentState):
    """Shared state for the weight-loss assistant handoff graph."""

    active_agent: NotRequired[ActiveAgent]


@tool
def transfer_to_metabolism_coach(
    reason: str,
    runtime: ToolRuntime[None, WeightLossAssistantState],
) -> Command:
    """Hand off to the metabolism coach (multi-turn).

    Use for BMR/TDEE setup, metabolic profile, weight-loss timelines, plan preview,
    and saving a weight-loss plan. The metabolism coach will ask the user questions
    directly until the work is done.
    """
    return Command(
        update={
            "active_agent": METABOLISM_AGENT_NAME,
            "messages": [
                ToolMessage(
                    content=(
                        f"Now speaking as the metabolism coach. {reason} "
                        "Ask the user one question at a time."
                    ),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@tool
def transfer_to_dietician_coach(
    reason: str,
    runtime: ToolRuntime[None, WeightLossAssistantState],
) -> Command:
    """Hand off to the dietician coach (multi-turn).

    Use for food log updates, meal planning, diet suggestions, hunger/symptom check-ins,
    recipes, and nutrition coaching. The dietician will talk to the user directly.
    """
    return Command(
        update={
            "active_agent": DIETICIAN_AGENT_NAME,
            "messages": [
                ToolMessage(
                    content=(
                        f"Now speaking as the dietician coach. {reason} "
                        "Ask the user one question at a time when gathering details."
                    ),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@tool
def transfer_to_weight_loss_coach(
    reason: str,
    runtime: ToolRuntime[None, WeightLossAssistantState],
) -> Command:
    """Hand back to the main weight loss coach.

    Use after metabolic profile, weight-loss plan, or diet coaching work is complete,
    or when the user wants help with measurements or general app guidance.
    """
    return Command(
        update={
            "active_agent": WEIGHT_LOSS_COACH_AGENT,
            "messages": [
                ToolMessage(
                    content=f"Returned to the weight loss coach. {reason}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
