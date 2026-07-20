"""OpenAI API client wrapper with retry logic for the product listing generator."""

import json
import time
from openai import OpenAI, APIError, APIConnectionError, RateLimitError


class OpenAIListingClient:
    """Wraps OpenAI vision API calls with retry/backoff and standardized errors."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini",
                 max_tokens: int = 500, temperature: float = 0.6,
                 max_retries: int = 3, base_delay: float = 1.0):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.base_delay = base_delay

    def generate_listing(self, encoded_image: str, prompt_txt: str) -> dict | None:
        """
        Send image + prompt to OpenAI, with retry on transient failures.

        Returns:
            Parsed JSON dict, or None if all retries are exhausted.
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt_txt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }}
                        ]}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                return json.loads(content)

            except RateLimitError as e:
                last_error = e
                delay = self.base_delay * (2 ** (attempt - 1))
                print(
                    f"[OpenAIListingClient] RateLimitError on attempt {attempt}/{self.max_retries}: {e}\n"
                    f"Suggestion: backing off for {delay:.1f}s before retrying."
                )
                time.sleep(delay)

            except APIConnectionError as e:
                last_error = e
                delay = self.base_delay * (2 ** (attempt - 1))
                print(
                    f"[OpenAIListingClient] APIConnectionError on attempt {attempt}/{self.max_retries}: {e}\n"
                    f"Suggestion: check network connection. Retrying in {delay:.1f}s."
                )
                time.sleep(delay)

            except APIError as e:
                # Non-retryable API errors (bad request, auth, etc.)
                print(
                    f"[OpenAIListingClient] APIError (non-retryable): {e}\n"
                    f"Suggestion: check API key validity and request payload."
                )
                return None

            except json.JSONDecodeError as e:
                print(
                    f"[OpenAIListingClient] JSONDecodeError: response wasn't valid JSON: {e}\n"
                    f"Suggestion: check response_format setting or model output."
                )
                return None

        print(f"[OpenAIListingClient] Failed after {self.max_retries} attempts. Last error: {last_error}")
        return None