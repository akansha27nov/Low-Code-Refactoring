## Refactoring Checklist

## Path 1 - Product list generator

### Issues Found:
- [ ] `generate_product_listing()` mixes API call + JSON parsing + error handling (monolithic)
- [ ] Dataset-loading `try/except` produces two incompatible schemas (HF dataset vs hardcoded fallback) — silent structural bug
- [ ] `encode_image_to_base64` + prompt creation logic duplicated between the "Step 5 test" block and "Step 6 batch" loop
- [ ] Hardcoded magic numbers: `i >= 100`, `max_tokens=500`, `temperature=0.6`
- [ ] No validation that `OPENAI_API_KEY` exists before making calls — fails deep inside first API call instead of at startup
- [ ] `except Exception as e: continue` in batch loop swallows errors with no structured logging
- [ ] No `if __name__ == "__main__":` guard — importing the file triggers dataset download + API calls
- [ ] File I/O (saving images, writing JSON) not wrapped in error handling

### Priority:
1. Fix silent schema-mismatch bug + add explicit error handling (biggest risk)
2. Modularize: separate load / encode / prompt / API-call / save into distinct functions
3. Extract config constants + add API key validation at startup

## Path 2 - meal planner
### Issues Found:
- [ ] `MealPlanGenerator.generate()` is monolithic — builds prompt chain, invokes LLM, 
      strips markdown fences, parses JSON, validates with Pydantic, times execution, 
      and formats the return dict, all in one method
- [ ] Overly broad error handling: `except Exception as e: return {"success": False, "error": str(e)}` 
      treats Pydantic ValidationError, network errors, and API errors identically — no 
      distinction, no location context
- [ ] Repeated JSON-extraction logic: the "strip ```json fences" pattern is duplicated 
      almost identically in `generate()` and again in `parse_llm_json()`
- [ ] Config is Colab-only and unvalidated: `OPENAI_API_KEY = userdata.get('openai_key')` 
      only works in Google Colab, and nothing checks if it's None before use
- [ ] Hardcoded secret placeholder in a config cell: `EMAIL_PASSWORD = "your-app-password"`
- [ ] `send_meal_plan_email()` catches all exceptions the same way — SMTP auth failure, 
      network failure, and bad recipient address all produce the same generic message
- [ ] The three LangSmith evaluators (`shopping_list_completeness`, `theme_uniqueness`, 
      `dietary_compliance`) repeat the same "call LLM judge → parse JSON → return dict" 
      pattern three times with only the prompt text differing
- [ ] Module-level side effects: `generator = MealPlanGenerator()` and `ls_client = Client()` 
      run on import/execution, not inside a guarded entrypoint — makes the code hard to 
      test without triggering real API/network calls

### Priority:
1. Fix the generate() monolith + its broad exception handling
2. Deduplicate JSON-extraction logic into a shared helper
3. Make config portable (env vars instead of Colab-only) + validate at startup
4. Deduplicate the evaluator pattern
