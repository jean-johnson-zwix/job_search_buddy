import os
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from .llm_config import get_llm_task_config, PROVIDER_TIMEOUTS
import httpx

logger = logging.getLogger(__name__)

GROQ_JSON_SUPPORTED_MODELS = {
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "qwen/qwen3-32b",
    "deepseek-r1-distill-llama-70b",
}

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.timeout = 30
        self.max_retries = 2
        self.retry_base_delay = 1.0
        self._last_usage: dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def call(
        self,
        model: str,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        response_format: str = "text",
    ) -> str:
        provider = provider.lower()

        if provider == "gemini":
            return self._call_gemini(
                system_prompt, user_prompt, model, response_format, max_tokens, temperature
            )
        if provider == "openrouter":
            return self._call_openrouter(
                system_prompt, user_prompt, model, response_format, max_tokens, temperature
            )
        if provider == "groq":
            return self._call_groq(
                system_prompt, user_prompt, model, response_format, max_tokens, temperature
            )

        raise ValueError(f"Unsupported provider {provider}")

    def call_with_fallback(
        self,
        model: str,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        response_format: str = "text",
        fallbacks: Optional[List[Tuple[str, str]]] = None,
    ) -> str:
        attempts: List[Tuple[str, str]] = [(provider, model)]
        if fallbacks:
            attempts.extend(fallbacks)

        errors = []

        for current_provider, current_model in attempts:
            try:
                logger.info(
                    "LLM attempt starting",
                    extra={
                        "provider": current_provider,
                        "model": current_model,
                        "response_format": response_format,
                    },
                )

                return self._call_with_retry(
                    provider=current_provider,
                    model=current_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format=response_format,
                )

            except Exception as e:
                errors.append(f"{current_provider}/{current_model}: {repr(e)}")
                logger.warning(
                    "LLM attempt failed, trying next fallback if available",
                    extra={
                        "provider": current_provider,
                        "model": current_model,
                        "error": repr(e),
                    },
                )

        raise RuntimeError(
            "All LLM providers/models failed. Attempts: " + " | ".join(errors)
        )

    def _call_with_retry(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        response_format: str,
    ) -> str:
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return self.call(
                    model=model,
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format=response_format,
                )
            except Exception as e:
                last_error = e

                if not self._is_retryable_error(e):
                    raise

                if attempt >= self.max_retries:
                    raise

                delay = self.retry_base_delay * (2 ** attempt)
                logger.warning(
                    "Retryable LLM error, backing off before retry",
                    extra={
                        "provider": provider,
                        "model": model,
                        "attempt": attempt + 1,
                        "delay_seconds": delay,
                        "error": repr(e),
                    },
                )
                time.sleep(delay)

        raise last_error

    def _is_retryable_error(self, error: Exception) -> bool:
        if isinstance(error, httpx.TimeoutException):
            return True

        if isinstance(error, httpx.NetworkError):
            return True

        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            return status == 429 or 500 <= status < 600

        return False

    def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        response_format: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload: Dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json" if response_format == "json" else "text/plain",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key,
        }
        timeout = PROVIDER_TIMEOUTS.get("gemini", 30)
        r = httpx.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usageMetadata", {})
        self._last_usage = {
            "prompt_tokens":     usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens":      usage.get("totalTokenCount", 0),
        }
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_openrouter(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        response_format: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        url = "https://openrouter.ai/api/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        timeout = PROVIDER_TIMEOUTS.get('openrouter', 30)
        r = httpx.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        self._last_usage = {
            "prompt_tokens":     usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens":      usage.get("total_tokens", 0),
        }
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise ValueError(f"Empty response content from {model}")
        return content

    def _call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        response_format: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not set")

        url = "https://api.groq.com/openai/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json" and model in GROQ_JSON_SUPPORTED_MODELS:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

        timeout = PROVIDER_TIMEOUTS.get("groq", 30)
        r = httpx.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        self._last_usage = {
            "prompt_tokens":     usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens":      usage.get("total_tokens", 0),
        }
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise ValueError(f"Empty response content from {model}")
        return content


# ---------------------------------------------------------------------------
# Module-level usage accumulator — reset each pipeline run
# ---------------------------------------------------------------------------
_usage_log: list[dict] = []


def get_usage_log() -> list[dict]:
    return list(_usage_log)


def reset_usage_log() -> None:
    global _usage_log
    _usage_log = []


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def call_llm(
    model=None,
    provider=None,
    system_prompt=None,
    user_prompt=None,
    max_tokens=None,
    temperature=None,
    response_format: str = "text",
    fallbacks: Optional[List[Tuple[str, str]]] = None,
    task: Optional[str] = None,
):
    start = time.perf_counter()
    if task and any([model, provider, max_tokens, temperature]):
        raise ValueError(
            "Pass either task= or explicit model/provider/max_tokens/temperature, not both"
        )
    # read from llm config
    if task:
        llm_config=get_llm_task_config(task)
        model = llm_config["model"]
        provider = llm_config["provider"]
        max_tokens = llm_config["max_tokens"]
        temperature = llm_config["temperature"]
        response_format = llm_config["response_format"]
        fallbacks = llm_config["fallbacks"]
    if not all([model, provider, system_prompt, user_prompt]):
        raise ValueError("Missing required LLM parameters")
    # generate response
    response = get_llm().call_with_fallback(
        model=model,
        provider=provider,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=temperature,
        fallbacks=fallbacks,
    )
    end = time.perf_counter()
    duration_ms = round((end - start) * 1000, 2)
    logger.info(
        "LLM call success | task=%s provider=%s model=%s duration_ms=%s",
        task, provider, model, duration_ms,
    )
    last = get_llm()._last_usage
    _usage_log.append({
        "task":              task or "unknown",
        "provider":          provider,
        "model":             model,
        "prompt_tokens":     last["prompt_tokens"],
        "completion_tokens": last["completion_tokens"],
        "total_tokens":      last["total_tokens"],
        "duration_ms":       duration_ms,
    })
    return response