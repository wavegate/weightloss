from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from copilotkit.sdk import COPILOTKIT_SDK_VERSION

from app.auth.clerk import get_current_user_id
from app.services.coach_agent import get_weight_loss_coach_agui_agent

router = APIRouter(tags=["copilot"])


@router.post("/copilotkit/ag-ui")
async def weight_loss_coach_ag_ui(
    input_data: RunAgentInput,
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """AG-UI endpoint for CopilotKit HttpAgent (not CopilotKitRemoteEndpoint)."""
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)

    agent = get_weight_loss_coach_agui_agent().clone()
    agent.config = {
        "configurable": {
            "user_id": user_id,
        }
    }

    async def event_generator():
        async for event in agent.run(input_data):
            yield encoder.encode(event)

    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type(),
    )


@router.get("/copilotkit/ag-ui/info")
async def weight_loss_coach_ag_ui_info() -> JSONResponse:
    """CopilotKit runtime discovery — agents run via HttpAgent, not remote proxy."""
    return JSONResponse(
        {
            "actions": [],
            "agents": {},
            "version": COPILOTKIT_SDK_VERSION,
            "sdkVersion": COPILOTKIT_SDK_VERSION,
        }
    )


@router.get("/copilotkit/ag-ui/health")
def weight_loss_coach_ag_ui_health() -> dict:
    agent = get_weight_loss_coach_agui_agent()
    return {"status": "ok", "agent": {"name": agent.name}}
