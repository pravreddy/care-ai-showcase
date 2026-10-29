"""
Care AI Engine - LLM Service
Multi-provider LLM client: Groq (cloud, fast, free tier) or Ollama (self-hosted, private).

Switch provider via environment variable:
  LLM_PROVIDER=groq    → Uses Groq API (fast, free tier, cloud)
  LLM_PROVIDER=ollama  → Uses Ollama (self-hosted, private, your server)

When you have revenue and need full privacy:
  Switch back to Ollama on a dedicated GPU server.
"""

import time
from typing import Optional, AsyncGenerator

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("llm")

# Small multilingual models (Llama, Mistral, Qwen, etc.) sometimes drift into
# another language mid-generation — usually when the input contains non-English
# names or text, which is common for healthcare candidate data. This directive is
# injected into every system prompt (see generate()) to hard-pin the output
# language; combined with a low temperature it reliably stops the drift.
ENGLISH_ONLY_DIRECTIVE = (
    "CRITICAL: Write your entire response in English (en-GB) only. "
    "No matter what language appears in the input — names, documents, "
    "qualifications, or any other text — always respond in English. "
    "Never switch to, mix in, or output any other language "
    "(for example Urdu, Hindi, or Arabic). If the input is in another "
    "language, translate it in your head and still respond only in English."
)


class LLMService:
    """
    Manages communication with the LLM — Groq or Ollama.
    Same interface regardless of provider.
    """

    def __init__(self):
        self._settings = get_settings()
        self._provider = getattr(self._settings, 'llm_provider', 'ollama').lower()
        self._timeout = self._settings.ollama_timeout
        self._max_tokens = self._settings.ollama_max_tokens

        if self._provider == 'groq':
            self._base_url = getattr(self._settings, 'groq_base_url', 'https://api.groq.com/openai/v1')
            self._api_key = getattr(self._settings, 'groq_api_key', '')
            self._model = getattr(self._settings, 'groq_model', 'llama-3.3-70b-versatile')
            logger.info(f"LLM provider: Groq ({self._model})")
        else:
            self._base_url = self._settings.ollama_base_url
            self._model = self._settings.ollama_model
            logger.info(f"LLM provider: Ollama ({self._model})")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_retries: int = 2,
    ) -> dict:
        """
        Generate a response from the LLM.
        Returns dict with 'response', 'model', 'duration_ms'.
        Works identically for both Groq and Ollama.

        Every call gets an 'English only' directive injected into its system
        prompt so small multilingual models can't drift into another language
        (the Urdu/Hindi output seen on candidate data with non-English names).
        """
        effective_system = (
            f"{system_prompt.strip()}\n\n{ENGLISH_ONLY_DIRECTIVE}"
            if system_prompt and system_prompt.strip()
            else ENGLISH_ONLY_DIRECTIVE
        )

        if self._provider == 'groq':
            return await self._generate_groq(prompt, effective_system, temperature, max_retries)
        else:
            return await self._generate_ollama(prompt, effective_system, temperature, max_retries)

    # ================================================================
    # Groq (OpenAI-compatible API)
    # ================================================================

    async def _generate_groq(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_retries: int,
    ) -> dict:
        """Send request to Groq's OpenAI-compatible API."""
        start = time.monotonic()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self._max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )

                    # Handle rate limiting (Groq returns 429)
                    if resp.status_code == 429:
                        retry_after = float(resp.headers.get("retry-after", 2))
                        logger.warning(f"Groq rate limited, waiting {retry_after}s")
                        await _sleep(retry_after)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                duration_ms = (time.monotonic() - start) * 1000

                # Extract response from OpenAI format
                choices = data.get("choices", [])
                response_text = choices[0]["message"]["content"] if choices else ""
                usage = data.get("usage", {})

                logger.info(
                    "LLM generation complete (Groq)",
                    extra={
                        "model": self._model,
                        "duration_ms": round(duration_ms, 1),
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                    },
                )

                return {
                    "response": response_text,
                    "model": self._model,
                    "provider": "groq",
                    "duration_ms": round(duration_ms, 1),
                    "tokens_used": usage.get("total_tokens", 0),
                }

            except httpx.TimeoutException:
                last_error = "Groq request timed out"
                logger.warning(f"Groq timeout (attempt {attempt + 1})")
            except httpx.HTTPStatusError as e:
                last_error = f"Groq HTTP error: {e.response.status_code}"
                logger.error(f"Groq HTTP error: {e}")
                # Don't retry on auth errors
                if e.response.status_code in (401, 403):
                    break
            except httpx.ConnectError:
                last_error = "Cannot connect to Groq API"
                logger.error("Cannot connect to Groq")
            except Exception as e:
                last_error = f"Groq error: {str(e)}"
                logger.error(f"Unexpected Groq error: {e}")

            if attempt < max_retries:
                await _sleep(2 ** attempt)

        raise LLMError(last_error or "Unknown Groq error")

    # ================================================================
    # Ollama (self-hosted)
    # ================================================================

    async def _generate_ollama(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_retries: int,
    ) -> dict:
        """Send request to Ollama's local API."""
        start = time.monotonic()

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": self._max_tokens,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{self._base_url}/api/generate",
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                duration_ms = (time.monotonic() - start) * 1000

                logger.info(
                    "LLM generation complete (Ollama)",
                    extra={
                        "model": self._model,
                        "duration_ms": round(duration_ms, 1),
                        "prompt_length": len(prompt),
                    },
                )

                return {
                    "response": data.get("response", ""),
                    "model": self._model,
                    "provider": "ollama",
                    "duration_ms": round(duration_ms, 1),
                    "tokens_used": data.get("eval_count", 0),
                }

            except httpx.TimeoutException:
                last_error = "LLM request timed out"
                logger.warning(f"Ollama timeout (attempt {attempt + 1})")
            except httpx.HTTPStatusError as e:
                last_error = f"LLM HTTP error: {e.response.status_code}"
                logger.error(f"Ollama HTTP error: {e}")
            except httpx.ConnectError:
                last_error = "Cannot connect to LLM server"
                logger.error("Cannot connect to Ollama")
            except Exception as e:
                last_error = f"LLM error: {str(e)}"
                logger.error(f"Unexpected LLM error: {e}")

            if attempt < max_retries:
                await _sleep(2 ** attempt)

        raise LLMError(last_error or "Unknown LLM error")

    # ================================================================
    # Health check
    # ================================================================

    async def health_check(self) -> bool:
        """Check if the LLM provider is reachable."""
        try:
            if self._provider == 'groq':
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"{self._base_url}/models",
                        headers={"Authorization": f"Bearer {self._api_key}"},
                    )
                    return resp.status_code == 200
            else:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(f"{self._base_url}/api/tags")
                    if resp.status_code == 200:
                        models = resp.json().get("models", [])
                        model_names = [m.get("name", "") for m in models]
                        return any(self._model in name for name in model_names)
                return False
        except Exception:
            return False

    @property
    def provider_info(self) -> dict:
        """Return info about current provider — useful for the /health endpoint."""
        return {
            "provider": self._provider,
            "model": self._model,
            "base_url": self._base_url if self._provider == 'ollama' else 'groq.com',
        }


class LLMError(Exception):
    """Raised when LLM generation fails after retries."""
    pass


async def _sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)


# Global instance
llm_service = LLMService()
