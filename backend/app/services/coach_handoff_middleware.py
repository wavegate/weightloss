"""Middleware: swap system prompt and tools based on active_agent (LangChain handoffs)."""

from collections.abc import Awaitable, Callable

from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call

from app.services.coach_prompts import (
    DIETICIAN_SYSTEM_PROMPT,
    METABOLISM_SYSTEM_PROMPT,
    WEIGHT_LOSS_COACH_SYSTEM_PROMPT,
)
from app.services.coach_tools import COACH_TOOLS
from app.services.dietician_tools import DIETICIAN_TOOLS
from app.services.handoff_tools import (
    DIETICIAN_AGENT_NAME,
    WEIGHT_LOSS_COACH_AGENT,
    transfer_to_dietician_coach,
    transfer_to_metabolism_coach,
    transfer_to_weight_loss_coach,
)
from app.services.handoff_tools import METABOLISM_AGENT_NAME
from app.services.metabolism_tools import METABOLISM_TOOLS

_COACH_TOOLS = [
    *COACH_TOOLS,
    transfer_to_metabolism_coach,
    transfer_to_dietician_coach,
]
_METABOLISM_TOOLS = [
    *METABOLISM_TOOLS,
    transfer_to_dietician_coach,
    transfer_to_weight_loss_coach,
]
_DIETICIAN_TOOLS = [
    *DIETICIAN_TOOLS,
    transfer_to_metabolism_coach,
    transfer_to_weight_loss_coach,
]


def _active_agent(request: ModelRequest) -> str:
    return request.state.get("active_agent") or WEIGHT_LOSS_COACH_AGENT


@wrap_model_call
async def apply_active_agent_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
) -> ModelResponse:
    active = _active_agent(request)
    if active == METABOLISM_AGENT_NAME:
        return await handler(
            request.override(
                system_prompt=METABOLISM_SYSTEM_PROMPT,
                tools=_METABOLISM_TOOLS,
            )
        )
    if active == DIETICIAN_AGENT_NAME:
        return await handler(
            request.override(
                system_prompt=DIETICIAN_SYSTEM_PROMPT,
                tools=_DIETICIAN_TOOLS,
            )
        )
    return await handler(
        request.override(
            system_prompt=WEIGHT_LOSS_COACH_SYSTEM_PROMPT,
            tools=_COACH_TOOLS,
        )
    )
