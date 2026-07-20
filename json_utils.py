"""JSON extraction utilities for parsing LLM responses.

Consolidates two near-duplicate fence-stripping implementations that
previously lived in MealPlanGenerator.generate() and parse_llm_json().
"""

import json

def strip_markdown_json_fences(content: str) -> str:
    """Remove markdown code fences from LLM response text."""
    if content is None:
        raise ValueError(
            "[strip_markdown_json_fences] ValueError: content is None.\n"
            "Context: expected a string LLM response."
        )

    content = content.strip()
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0]
    return content.strip()

def normalize_meal_plan_dict(data: dict) -> dict:
    """Restructures malformed LLM outputs into a valid MealPlan schema dictionary."""
    if not isinstance(data, dict):
        return data

    # 1. Strip top-level wrapper keys if the LLM added them
    if "MealPlan" in data and isinstance(data["MealPlan"], dict):
        data = data["MealPlan"]
    elif "meal_plan" in data and isinstance(data["meal_plan"], dict):
        data = data["meal_plan"]

    # 2. Convert day-based dictionary ("Monday": {...}) into the required "recipes" list
    if "recipes" not in data or not isinstance(data["recipes"], list):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        recipes = []
        for day in days:
            # Find the day ignoring case
            day_data = next((v for k, v in data.items() if k.lower() == day.lower() and isinstance(v, dict)), None)
            
            if day_data:
                # Normalize ingredients dict {"salt": "1 tsp"} -> [{"name": "salt", "quantity": "1 tsp"}]
                raw_ing = day_data.get("ingredients", [])
                ing_list = []
                if isinstance(raw_ing, dict):
                    ing_list = [{"name": str(k), "quantity": str(v)} for k, v in raw_ing.items()]
                elif isinstance(raw_ing, list):
                    ing_list = raw_ing

                recipes.append({
                    "day": day,
                    "theme": day_data.get("theme", "General"),
                    "dish_name": day_data.get("dish_name", day_data.get("dish", "Special Dish")),
                    "ingredients": ing_list,
                    "instructions": day_data.get("instructions", "Cook as directed.")
                })
        
        # Only overwrite if we successfully extracted daily recipes
        if recipes:
            data["recipes"] = recipes

    # 3. Ensure required root fields are present
    if "dietary_preference" not in data:
        data["dietary_preference"] = "Omnivore"

    # 4. Auto-generate shopping list if omitted by LLM
    if "shopping_list" not in data or not isinstance(data["shopping_list"], list):
        shopping_map = {}
        for recipe in data.get("recipes", []):
            dish = recipe.get("dish_name", "Recipe")
            for ing in recipe.get("ingredients", []):
                if isinstance(ing, dict) and "name" in ing:
                    name = ing["name"]
                    qty = ing.get("quantity", "1")
                    if name not in shopping_map:
                        shopping_map[name] = {"total_quantity": qty, "used_in": [dish]}
                    elif dish not in shopping_map[name]["used_in"]:
                        shopping_map[name]["used_in"].append(dish)
        data["shopping_list"] = [
            {"name": k, "total_quantity": v["total_quantity"], "used_in": v["used_in"]}
            for k, v in shopping_map.items()
        ]

    return data

def parse_json_response(content: str) -> dict:
    """Extract, parse, and repair JSON from an LLM response."""
    cleaned = strip_markdown_json_fences(content)
    try:
        data = json.loads(cleaned)
        return normalize_meal_plan_dict(data)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"[parse_json_response] JSONDecodeError: {e.msg}\n"
            f"Context: failed at line {e.lineno}, column {e.colno}\n"
            f"Raw content (first 200 chars): {cleaned[:200]}",
            e.doc,
            e.pos,
        ) from e