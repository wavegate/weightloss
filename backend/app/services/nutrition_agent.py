import base64
import os
from functools import lru_cache

from deepagents import create_deep_agent
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field

from app.config import get_settings

NUTRITION_SYSTEM_PROMPT = """You are a nutrition estimation assistant.

You may receive a food photo, text (name and description), or both.

When a photo is provided, identify the foods and estimate portions visible in the image.
When text is provided, use it; you may refine the description for clearer nutrition estimation.

You must:
1. Use the web_search tool to look up nutrition facts or comparable foods online.
2. Combine search results with reasonable assumptions when exact data is unavailable.
3. Return estimated totals for the described portion only (not per 100g unless the description is per 100g).
4. Include dietary fiber (fiber_g) in grams when data is available; use 0 only if the food has negligible fiber.
5. Always set name and description to a short food title and a portion-focused description of what you estimated.

Be conservative when uncertain. Prefer USDA-style labels and reputable nutrition databases from search results.
"""


class NutritionEstimate(BaseModel):
    name: str = Field(min_length=1, description="Short food name")
    description: str = Field(
        min_length=1,
        description="Portion size, ingredients, and preparation details",
    )
    calories: float = Field(gt=0, description="Estimated calories (kcal)")
    protein_g: float = Field(ge=0, description="Estimated protein in grams")
    carbs_g: float = Field(
        ge=0, description="Estimated carbohydrates in grams")
    fat_g: float = Field(ge=0, description="Estimated fat in grams")
    fiber_g: float = Field(ge=0, description="Estimated dietary fiber in grams")
    notes: str = Field(
        description="Brief note on how the estimate was derived and key assumptions"
    )


@lru_cache
def _get_agent():
    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    ddg_search = DuckDuckGoSearchRun()

    def web_search(query: str) -> str:
        """Search the web for nutrition facts (DuckDuckGo, no API key)."""
        return ddg_search.invoke(query)

    return create_deep_agent(
        model=f"openai:{settings.openai_model}",
        tools=[web_search],
        system_prompt=NUTRITION_SYSTEM_PROMPT,
        response_format=NutritionEstimate,
    )


def _build_user_message(
    *,
    food_name: str,
    description: str,
    image_bytes: bytes | None,
    image_media_type: str | None,
) -> dict:
    if image_bytes and image_media_type:
        prompt_lines = [
            "Analyze the food in the attached photo and estimate calories, "
            "macros, and dietary fiber for the visible portion.",
        ]
        if food_name.strip():
            prompt_lines.append(f"User-provided name: {food_name.strip()}")
        if description.strip():
            prompt_lines.append(f"User-provided notes: {description.strip()}")
        prompt_lines.append(
            "Search for nutrition information as needed. Set name and "
            "description to what you identified (use user text when provided)."
        )
        text = "\n".join(prompt_lines)
        image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        content: list[dict] = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_media_type};base64,{image_b64}",
                },
            },
            {"type": "text", "text": text},
        ]
        return {"role": "user", "content": content}

    prompt = (
        f"Food name: {food_name}\n"
        f"Description: {description}\n\n"
        "Search for nutrition information, then estimate calories, macros, "
        "and dietary fiber for this food as described. Set name and description in your response "
        "to match the provided food name and description."
    )
    return {"role": "user", "content": prompt}


def estimate_nutrition(
    food_name: str = "",
    description: str = "",
    *,
    image_bytes: bytes | None = None,
    image_media_type: str | None = None,
) -> NutritionEstimate:
    agent = _get_agent()
    message = _build_user_message(
        food_name=food_name,
        description=description,
        image_bytes=image_bytes,
        image_media_type=image_media_type,
    )

    result = agent.invoke({"messages": [message]})

    structured = result.get("structured_response")
    if isinstance(structured, NutritionEstimate):
        return structured
    if isinstance(structured, dict):
        return NutritionEstimate.model_validate(structured)

    raise RuntimeError("Nutrition agent did not return structured output")
