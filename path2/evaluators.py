"""LangSmith LLM-as-judge evaluators, built on a shared judge helper
to eliminate the 3x-repeated 'call LLM, parse JSON response' pattern."""

from .json_utils import parse_json_response
from .prompts import get_llm


def _run_llm_judge(prompt: str, eval_key: str) -> dict:
    """
    Shared helper: send a judge prompt to the LLM and parse its verdict.

    Returns:
        dict with 'key', 'score', 'comment' — falls back to score=0 with an
        explanatory comment if the judge's response can't be parsed, rather
        than silently returning a misleading pass/fail.
    """
    eval_llm = get_llm()
    try:
        response = eval_llm.invoke(prompt)
        result = parse_json_response(response.content)
        return {"key": eval_key, "score": result.get("score", 0), "comment": result.get("reason", "")}
    except Exception as e:
        return {
            "key": eval_key, "score": 0,
            "comment": f"[_run_llm_judge] {type(e).__name__}: judge response could not be parsed: {e}"
        }


def shopping_list_completeness(run, example) -> dict:
    """Check if shopping list contains all recipe ingredients."""
    output = run.outputs
    if not output or not output.get("success"):
        return {"key": "shopping_list_completeness", "score": 0, "comment": "Generation failed"}

    meal_plan = output["meal_plan"]
    recipe_ingredients = [ing["name"] for r in meal_plan["recipes"] for ing in r["ingredients"]]
    shopping_items = [item["name"] for item in meal_plan["shopping_list"]]

    prompt = f"""Check if this shopping list contains all the recipe ingredients.

RECIPE INGREDIENTS: {recipe_ingredients}
SHOPPING LIST: {shopping_items}

Does the shopping list include every ingredient?
Respond with JSON only: {{"score": 1, "reason": "..."}} if complete, {{"score": 0, "reason": "missing: X, Y"}} if not."""

    return _run_llm_judge(prompt, "shopping_list_completeness")


def theme_uniqueness(run, example) -> dict:
    """Check if all 7 themes are unique and each has 5 ingredients."""
    output = run.outputs
    if not output or not output.get("success"):
        return {"key": "theme_uniqueness", "score": 0, "comment": "Generation failed"}

    meal_plan = output["meal_plan"]
    themes = [r["theme"] for r in meal_plan["recipes"]]
    ingredient_counts = [len(r["ingredients"]) for r in meal_plan["recipes"]]

    prompt = f"""Evaluate this meal plan structure.

THEMES (should all be different): {themes}
INGREDIENT COUNTS (should all be 5): {ingredient_counts}

Check: Are all 7 themes unique cuisines? Does each recipe have exactly 5 ingredients?
Respond with JSON only: {{"score": 1, "reason": "..."}} if valid, {{"score": 0, "reason": "..."}} if not."""

    return _run_llm_judge(prompt, "theme_uniqueness")


def dietary_compliance(run, example) -> dict:
    """Check for hallucinated ingredients and dietary violations."""
    output = run.outputs
    if not output or not output.get("success"):
        return {"key": "dietary_compliance", "score": 0, "comment": "Generation failed"}

    meal_plan = output["meal_plan"]
    dietary_pref = example.inputs.get("dietary_preference", "omnivore")
    all_ingredients = [ing["name"] for r in meal_plan["recipes"] for ing in r["ingredients"]]

    prompt = f"""Check if these ingredients comply with a {dietary_pref} diet.

DIET: {dietary_pref}
- Vegan: No animal products (meat, fish, dairy, eggs, honey)
- Vegetarian: No meat or fish
- Keto: No grains, sugar, starchy vegetables, most fruits
- Omnivore: Anything allowed

INGREDIENTS: {all_ingredients}

Are all ingredients real foods that comply with the {dietary_pref} diet?
Respond with JSON only: {{"score": 1, "reason": "all compliant"}} or {{"score": 0, "reason": "violation: X"}}"""

    return _run_llm_judge(prompt, "dietary_compliance")