from pydantic import BaseModel, Field


class StylingImageResult(BaseModel):
    label: str
    b64_png: str
    media_type: str = "image/png"


class StylingVisualizationRead(BaseModel):
    disclaimer: str
    current_weight_lbs: float
    target_weight_lbs: float
    lbs_to_lose: float = Field(ge=0)
    images: list[StylingImageResult]
