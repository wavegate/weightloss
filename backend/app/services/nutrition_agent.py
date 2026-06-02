import os
from functools import lru_cache

from deepagents import create_deep_agent
from langchain_community.tools import DuckDuckGoSearchRun
from pydantic import BaseModel, Field

from app.config import get_settings

NUTRITION_SYSTEM_PROMPT = """You are a nutrition estimation assistant.

Given a food name and description (portion size, preparation, ingredients), you must:
1. Use the web_search tool to look up nutrition facts or comparable foods online.
2. Combine search results with reasonable assumptions when exact data is unavailable.
3. Return estimated totals for the described portion only (not per 100g unless the description is per 100g).

Be conservative when uncertain. Prefer USDA-style labels and reputable nutrition databases from search results.
"""


class NutritionEstimate(BaseModel):
    calories: float = Field(gt=0, description="Estimated calories (kcal)")
    protein_g: float = Field(ge=0, description="Estimated protein in grams")
    carbs_g: float = Field(ge=0, description="Estimated carbohydrates in grams")
    fat_g: float = Field(ge=0, description="Estimated fat in grams")
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


def estimate_nutrition(food_name: str, description: str) -> NutritionEstimate:
    agent = _get_agent()
    prompt = (
        f"Food name: {food_name}\n"
        f"Description: {description}\n\n"
        "Search for nutrition information, then estimate calories and macros "
        "for this food as described."
    )

    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})

    structured = result.get("structured_response")
    if isinstance(structured, NutritionEstimate):
        return structured
    if isinstance(structured, dict):
        return NutritionEstimate.model_validate(structured)

    raise RuntimeError("Nutrition agent did not return structured output")
