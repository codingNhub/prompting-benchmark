# Sends prompts to Groq or Together.ai API. Handles rate limits and retries. Returns raw response.
# Sends prompts to Groq or Together.ai API. Handles rate limits and retries. Returns raw response.

import time
from openai import OpenAI
from src.logger import get_logger

logger = get_logger("model_wrapper")


def call_model(prompt, config, max_tokens: int = None):
    # Get settings from config
    provider = config.get("api", {}).get("provider", "groq")
    model_key = config.get("models", {}).get("active", "primary")
    model_name = config.get("models", {}).get(model_key, "llama3-8b-8192")
    temperature = config.get("inference", {}).get("temperature_default", 0.0)
    if max_tokens is None:
        max_tokens = config.get("inference", {}).get("max_tokens_classification", 256)
    reasoning_effort = config.get("inference", {}).get("reasoning_effort")
    rate_limit_delay = config.get("api", {}).get("rate_limit_delay", 2.0)
    retry_attempts = config.get("api", {}).get("retry_attempts", 3)
    retry_wait = config.get("api", {}).get("retry_wait", 60)
    seed = config.get("experiment", {}).get("random_seed", 42)

    # Set up API client
    if provider == "groq":
        api_key = config["api"]["groq_key"]
        base_url = "https://api.groq.com/openai/v1"
    else:
        api_key = config["api"]["together_key"]
        base_url = "https://api.together.xyz/v1"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Try sending the prompt with retry logic
    for attempt in range(retry_attempts):
        try:
            # Groq and Together both expose an OpenAI-compatible `seed` param for
            # best-effort reproducibility at temperature 0. Neither provider
            # guarantees bit-identical output across calls (backend routing/
            # sharding can still vary) — this reduces non-determinism, it does
            # not eliminate it.
            extra_args = {"reasoning_effort": reasoning_effort} if reasoning_effort else {}
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
                **extra_args
            )

            raw_text = response.choices[0].message.content
            if not raw_text:
                raw_text = getattr(response.choices[0].message, "refusal", None)
            if not raw_text and response.choices[0].finish_reason == "content_filter":
                raw_text = "[CONTENT_FILTER]: response blocked by safety system"
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            logger.info(f"Response received — input_tokens={input_tokens} output_tokens={output_tokens}")

            # Wait between calls to respect rate limits
            time.sleep(rate_limit_delay)

            return {
                "raw_text": raw_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                logger.error(f"Rate limit hit on attempt {attempt + 1}. Waiting {retry_wait}s.")
                time.sleep(retry_wait)
            else:
                logger.error(f"API error on attempt {attempt + 1}: {error_msg}")
                if attempt == retry_attempts - 1:
                    raise

    raise RuntimeError("All retry attempts failed. Check your API key and internet connection.")
