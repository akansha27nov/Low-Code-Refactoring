"""Meal plan generation logic, split into focused, testable steps."""

import time
from pydantic import ValidationError
from langsmith import traceable
from langchain_core.output_parsers import JsonOutputParser

from .prompts import MEAL_PLAN_PROMPT, get_llm
from .json_utils import parse_json_response
from .models import MealPlan


class MealPlanGenerator:
    """Generates weekly themed meal plans."""

    def __init__(self):
        self.llm = get_llm()
        self.parser = JsonOutputParser(pydantic_object=MealPlan)

    def _build_recipe_chain(self):
        return MEAL_PLAN_PROMPT | self.llm

    def _invoke_llm(self, chain, dietary_preference: str, theme_requests: str,
                     additional_preferences: str) -> str:
        try:
            result = chain.invoke({
                "dietary_preference": dietary_preference,
                "theme_requests": theme_requests or "random diverse cuisines",
                "additional_preferences": additional_preferences or "none",
                "format_instructions": self.parser.get_format_instructions(),
            })
            print("=== RAW LLM OUTPUT ===")
            print(result.content)
            print("=== END RAW OUTPUT ===")
            return result.content
        except Exception as e:
            raise RuntimeError(
                f"[_invoke_llm] {type(e).__name__}: {e}\n"
                f"Context: LLM call failed for dietary_preference='{dietary_preference}'.\n"
                f"Suggestion: check API key validity, rate limits, or network connection."
            ) from e

    def _parse_and_validate(self, content: str) -> MealPlan:
        """Parse LLM output as JSON (already normalized in json_utils) and validate."""
        data = parse_json_response(content)
        return MealPlan(**data)

    @traceable(name="generate_meal_plan")
    def generate(self, dietary_preference: str, theme_requests: str = "random",
                 additional_preferences: str = "none") -> dict:
        start_time = time.time()
        chain = self._build_recipe_chain()

        try:
            raw_content = self._invoke_llm(chain, dietary_preference, theme_requests,
                                            additional_preferences)
        except RuntimeError as e:
            return {"success": False, "meal_plan": None, "error": str(e)}

        try:
            meal_plan = self._parse_and_validate(raw_content)
        except ValidationError as e:
            return {
                "success": False, "meal_plan": None,
                "error": f"[generate] ValidationError: schema validation failed.\n"
                         f"Context: {e.error_count()} field(s) invalid.\n"
                         f"Details: {e}\n"
                         f"Suggestion: check the LLM's raw output against the MealPlan schema."
            }
        except Exception as e:
            return {"success": False, "meal_plan": None, "error": str(e)}

        return {
            "success": True,
            "meal_plan": meal_plan.model_dump(),
            "generation_time": round(time.time() - start_time, 2),
            "error": None,
        }