"""Meal plan generation logic, split into focused, testable steps.

Previously: MealPlanGenerator.generate() did chain-building, LLM invocation,
JSON extraction, Pydantic validation, and timing all in one method, with a
single broad `except Exception` that hid what actually failed.
"""

import time
from pydantic import ValidationError
from langsmith import traceable
from prompts import MEAL_PLAN_PROMPT, get_llm
from json_utils import parse_json_response
from models import MealPlan
from langchain_core.output_parsers import JsonOutputParser

            
class MealPlanGenerator:
    """Generates weekly themed meal plans."""

    def __init__(self):
        self.llm = get_llm()
        self.parser = JsonOutputParser(pydantic_object=MealPlan)

    def _build_recipe_chain(self):
        """Build the prompt-to-LLM chain. Isolated so it can be tested/mocked separately."""
        return MEAL_PLAN_PROMPT | self.llm

    def _invoke_llm(self, chain, dietary_preference: str, theme_requests: str,
                     additional_preferences: str) -> str:
        try:
            result = chain.invoke({
                "dietary_preference": dietary_preference,
                "theme_requests": theme_requests or "random diverse cuisines",
                "additional_preferences": additional_preferences or "none",
                "format_instructions": self.parser.get_format_instructions(),  # real instructions
            })
            return result.content
        except Exception as e:
            raise RuntimeError(
                f"[_invoke_llm] {type(e).__name__}: {e}\n"
                f"Context: LLM call failed for dietary_preference='{dietary_preference}'.\n"
                f"Suggestion: check API key validity, rate limits, or network connection."
            ) from e

    def _parse_and_validate(self, content: str) -> MealPlan:
        """
        Parse LLM output as JSON and validate it against the MealPlan schema.

        Raises:
            (re-raised as-is) json.JSONDecodeError: if content isn't valid JSON
                — already carries line/column context from json_utils.
            ValidationError: if JSON is valid but doesn't match the schema
                — Pydantic's own error already names the invalid field(s).
        """
        data = parse_json_response(content)  # raises json.JSONDecodeError with context
        return MealPlan(**data)  # raises pydantic.ValidationError with field context

    @traceable(name="generate_meal_plan")
    def generate(self, dietary_preference: str, theme_requests: str = "random",
                 additional_preferences: str = "none") -> dict:
        """
        Generate a complete weekly meal plan. Orchestrates the steps above and
        catches each failure mode separately so callers know exactly what broke.
        """
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
        except Exception as e:  # json.JSONDecodeError already has context baked in
            return {"success": False, "meal_plan": None, "error": str(e)}

        return {
            "success": True,
            "meal_plan": meal_plan.model_dump(),
            "generation_time": round(time.time() - start_time, 2),
            "error": None,
        }