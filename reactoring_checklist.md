## Refactoring Checklist

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