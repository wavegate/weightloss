from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from copilotkit.sdk import COPILOTKIT_SDK_VERSION

from app.auth.clerk import get_current_user_id
from app.services.coach_agent import get_weight_loss_coach_agui_agent
from app.services.event_manager_agent import get_event_manager_agui_agent
from app.services.user_date import (
    resolve_user_local_date_from_header,
    resolve_user_timezone_from_header,
)

router = APIRouter(tags=["copilot"])


async def _stream_ag_ui_agent(
    *,
    input_data: RunAgentInput,
    request: Request,
    user_id: str,
    get_agent,
) -> StreamingResponse:
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)

    configurable: dict[str, str] = {
        "user_id": user_id,
        "user_local_date": resolve_user_local_date_from_header(
            request.headers.get("x-user-local-date")
        ).isoformat(),
        "user_timezone": resolve_user_timezone_from_header(
            request.headers.get("x-user-timezone")
        ),
    }

    agent = get_agent().clone()
    agent.config = {"configurable": configurable}

    async def event_generator():
        async for event in agent.run(input_data):
            yield encoder.encode(event)

    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type(),
    )


@router.post("/copilotkit/ag-ui")
async def weight_loss_coach_ag_ui(
    input_data: RunAgentInput,
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """AG-UI endpoint for CopilotKit HttpAgent (not CopilotKitRemoteEndpoint)."""
    return await _stream_ag_ui_agent(
        input_data=input_data,
        request=request,
        user_id=user_id,
        get_agent=get_weight_loss_coach_agui_agent,
    )


@router.post("/copilotkit/event-manager/ag-ui")
async def event_manager_ag_ui(
    input_data: RunAgentInput,
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """AG-UI endpoint for the event discovery deep agent."""
    return await _stream_ag_ui_agent(
        input_data=input_data,
        request=request,
        user_id=user_id,
        get_agent=get_event_manager_agui_agent,
    )


def _copilot_runtime_info() -> dict:
    return {
        "actions": [],
        "agents": {},
        "version": COPILOTKIT_SDK_VERSION,
        "sdkVersion": COPILOTKIT_SDK_VERSION,
    }


@router.get("/copilotkit/ag-ui/info")
async def weight_loss_coach_ag_ui_info() -> JSONResponse:
    """CopilotKit runtime discovery — agents run via HttpAgent, not remote proxy."""
    return JSONResponse(_copilot_runtime_info())


@router.get("/copilotkit/event-manager/ag-ui/info")
async def event_manager_ag_ui_info() -> JSONResponse:
    """CopilotKit runtime discovery for the event manager agent."""
    return JSONResponse(_copilot_runtime_info())


@router.get("/copilotkit/ag-ui/health")
def weight_loss_coach_ag_ui_health() -> dict:
    agent = get_weight_loss_coach_agui_agent()
    return {"status": "ok", "agent": {"name": agent.name}}


@router.get("/copilotkit/event-manager/ag-ui/health")
def event_manager_ag_ui_health() -> dict:
    agent = get_event_manager_agui_agent()
    return {"status": "ok", "agent": {"name": agent.name}}
