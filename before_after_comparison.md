# Before/After Code Comparison

This document highlights the structural and error-handling improvements made during the refactoring of Path 1 (Product Listing Generator) and Path 2 (Meal Planner).

---

## Path 1: Product Listing Generator Before & After

This document highlights the structural and error-handling improvements made during the refactoring of the AI Product Listing Generator.

### From Silent Failures to Explicit Error Handling (Dataset Loader)
**Before:** The original script swallowed dataset loading errors and returned an empty or fallback DataFrame. If the dataset failed to load (e.g., due to network issues), the script would continue running but crash later with a cryptic `KeyError` during iteration, making the root cause difficult to trace.

# BEFORE: Silent failure and broad exception handling
def load_data():
    try:
        dataset = load_dataset("ashraq/fashion-product-images-small", split="train")
        return dataset.to_pandas()
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        # Returns a dummy dataframe that will crash downstream processing
        return pd.DataFrame()

**After:** The refactored version in `data_loader.py` traps the specific operational error (`OSError`), logs exactly what failed, and raises a loud exception with actionable context. The program halts immediately with a clear error message instead of entering an unpredictable state.

# AFTER: Explicit error handling with context
def load_data() -> pd.DataFrame:
    try:
        dataset = load_dataset("ashraq/fashion-product-images-small", split="train")
        return dataset.to_pandas()
    except OSError as e:
        raise RuntimeError(
            f"[load_data] OSError: {e}\n"
            f"Context: Failed to connect to HuggingFace to download the dataset.\n"
            f"Suggestion: Check your internet connection or HuggingFace status."
        ) from e

## Path 2: Meal Planner Before & After

This document highlights the structural and error-handling improvements made during the refactoring of the LangChain Meal Planner starter code.

### From Monolithic Pipeline to Defensive Orchestration
**Before:** The starter code featured a massive, multi-responsibility `generate()` function. It built the prompt chain, invoked the LLM, manually stripped JSON markdown fences, parsed the JSON string, and validated the schema—all inside a single `try/except Exception` block. When validation failed, it was impossible to tell if the API broke, the JSON was malformed, or the Pydantic schema was violated.

# BEFORE: Monolithic method with broad exception swallowing
class MealPlanGenerator:
    def generate(self, dietary_preference, theme_requests="random", additional_preferences="none"):
        start_time = time.time()
        try:
            # 1. Build chain
            chain = MEAL_PLAN_PROMPT | self.llm
            
            # 2. Invoke LLM
            result = chain.invoke({...})
            content = result.content
            
            # 3. Strip fences and parse (duplicated inline logic)
            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0]
            data = json.loads(content)
            
            # 4. Validate against Pydantic schema
            meal_plan = MealPlan(**data)
            
            return {"success": True, "meal_plan": meal_plan.model_dump(), "error": None}
        except Exception as e:
            # Hides whether the network failed, JSON was invalid, or Schema was broken
            return {"success": False, "meal_plan": None, "error": str(e)}

**After:** The refactored `generate()` method acts purely as an orchestrator, calling single-responsibility helper methods (`_invoke_llm`, `_parse_and_validate`). Error handling is now stratified: API network errors (`RuntimeError`) are caught separately from schema failures (`ValidationError`), providing precise debugging context. Additionally, parsing logic is offloaded to a defensive, self-healing utility (`json_utils.py`) to handle LLM schema drift.

# AFTER: Orchestrated pipeline with stratified error handling
class MealPlanGenerator:
    @traceable(name="generate_meal_plan")
    def generate(self, dietary_preference: str, theme_requests: str = "random",
                 additional_preferences: str = "none") -> dict:
        start_time = time.time()
        chain = self._build_recipe_chain()

        # Step 1: Network/API call isolated
        try:
            raw_content = self._invoke_llm(chain, dietary_preference, theme_requests, additional_preferences)
        except RuntimeError as e:
            return {"success": False, "meal_plan": None, "error": str(e)}

        # Step 2: Parsing & Schema validation isolated (uses self-healing json_utils)
        try:
            meal_plan = self._parse_and_validate(raw_content)
        except ValidationError as e:
            return {
                "success": False, "meal_plan": None,
                "error": f"[generate] ValidationError: schema validation failed.\nDetails: {e}"
            }
        except Exception as e:
            return {"success": False, "meal_plan": None, "error": str(e)}

        return {
            "success": True,
            "meal_plan": meal_plan.model_dump(),
            "generation_time": round(time.time() - start_time, 2),
            "error": None,
        }