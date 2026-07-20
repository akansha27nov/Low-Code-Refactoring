# Lab Summary

I refactored both Path 1 (my product listing generator) and Path 2 (starter code: `meal_planner.ipynb` from bellabf/mvp-in-one-hour). Full issue tracking is in 
`refactoring_checklist.md`.

**Path 1**: split a single-file OpenAI vision pipeline into `config.py`, `data_loader.py`, 
`image_utils.py`, `prompt_builder.py`, `api_client.py`, and `logging_config.py`. Replaced a 
silent dataset-loading fallback (which produced an incompatible DataFrame schema) with an 
explicit, loud failure, and replaced blanket `except Exception` handling with per-stage, 
per-error-type handling that names the function, error type, and a fix suggestion.

**Path 2**: modularized the meal planner's monolithic `generate()` method into `meal_plan_generator.py`, `meal_planner_config.py`, `models.py`, `prompts.py`, `json_utils.py`, and `email_utils.py`. Added startup config validation, narrowed `send_meal_plan_email`'s error handling to distinguish auth/network/SMTP failures, and deduplicated repeated JSON-fence-stripping logic across the generator and evaluators.

**Main challenge**: the meal planner's LLM output kept violating the `MealPlan` Pydantic schema in different ways across runs (wrapped keys, day-keyed dicts, missing fields) even with explicit format instructions. Diagnosing it required adding raw-output logging, fixing a missing `self` parameter and a variable-use-before-assignment bug, restarting the kernel to clear stale module imports, adding a concrete JSON example to the prompt, and lowering temperature from 0.7 to 0.2.

**What I learned**: modular code makes failures locatable, but LLM output instability is a 
runtime problem no amount of static refactoring alone fixes. It needs logging of raw responses, schema-level defensive parsing, and prompt/parameter tuning together.