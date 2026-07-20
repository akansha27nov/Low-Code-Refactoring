"""LangSmith dataset creation and evaluation orchestration.

Fixes: create_or_get_dataset() previously used a bare `except:` that
silently swallowed ALL errors (including ones unrelated to "dataset
doesn't exist yet"), making failures impossible to diagnose.
"""

from langsmith.utils import LangSmithNotFoundError

from meal_plan_generator import MealPlanGenerator
from path2.evaluators import shopping_list_completeness, theme_uniqueness, dietary_compliance

TEST_CASES = [
    {"dietary_preference": "omnivore", "theme_requests": "random", "additional_preferences": "none"},
    {"dietary_preference": "vegetarian", "theme_requests": "Italian, Asian, Mexican", "additional_preferences": "no mushrooms"},
    {"dietary_preference": "vegan", "theme_requests": "random", "additional_preferences": "high protein"},
    {"dietary_preference": "keto", "theme_requests": "Mediterranean, American", "additional_preferences": "none"},
]


def run_basic_validation(meal_plan_result: dict) -> dict:
    """Run quick programmatic validation checks (not LLM-based)."""
    if not meal_plan_result.get("success"):
        return {"passed": False, "errors": [meal_plan_result.get("error")]}

    meal_plan = meal_plan_result["meal_plan"]
    errors = []

    if len(meal_plan["recipes"]) != 7:
        errors.append(f"Expected 7 recipes, got {len(meal_plan['recipes'])}")

    themes = [r["theme"].lower() for r in meal_plan["recipes"]]
    if len(themes) != len(set(themes)):
        duplicates = [t for t in themes if themes.count(t) > 1]
        errors.append(f"Duplicate themes: {set(duplicates)}")

    for recipe in meal_plan["recipes"]:
        if len(recipe["ingredients"]) != 5:
            errors.append(f"{recipe['day']}: {len(recipe['ingredients'])} ingredients (expected 5)")

    return {"passed": len(errors) == 0, "errors": errors}


def create_or_get_dataset(ls_client, dataset_name: str = "meal-planner-eval"):
    """
    Create evaluation dataset in LangSmith if it doesn't exist.

    Raises:
        RuntimeError: if dataset creation fails for a reason OTHER than
        "not found" — e.g. bad API key, network error, permission issue.
    """
    try:
        dataset = ls_client.read_dataset(dataset_name=dataset_name)
        print(f"Using existing dataset: {dataset_name}")
        return dataset
    except LangSmithNotFoundError:
        pass  # expected — dataset genuinely doesn't exist yet, fall through to create

    try:
        dataset = ls_client.create_dataset(dataset_name=dataset_name, description="Meal planner test cases")
        for test_case in TEST_CASES:
            ls_client.create_example(inputs=test_case, dataset_id=dataset.id)
        print(f"Created dataset: {dataset_name} with {len(TEST_CASES)} examples")
        return dataset
    except Exception as e:
        raise RuntimeError(
            f"[create_or_get_dataset] {type(e).__name__}: {e}\n"
            f"Context: failed to create dataset '{dataset_name}' in LangSmith.\n"
            f"Suggestion: check LANGSMITH_API_KEY is valid and LangSmith service is reachable."
        ) from e


def target_function(inputs: dict, generator: MealPlanGenerator) -> dict:
    """Target function for LangSmith evaluation."""
    return generator.generate(
        dietary_preference=inputs["dietary_preference"],
        theme_requests=inputs.get("theme_requests", "random"),
        additional_preferences=inputs.get("additional_preferences", "none"),
    )


def run_langsmith_evaluation(ls_client, generator: MealPlanGenerator):
    """Run LLM-as-judge evaluation in LangSmith."""
    from langsmith.evaluation import evaluate

    dataset = create_or_get_dataset(ls_client)

    results = evaluate(
        lambda inputs: target_function(inputs, generator),
        data=dataset,
        evaluators=[shopping_list_completeness, theme_uniqueness, dietary_compliance],
        experiment_prefix="meal-planner-llm-judge",
    )
    print("\nEvaluation complete! View results in LangSmith dashboard.")
    return results