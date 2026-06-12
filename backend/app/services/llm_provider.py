"""
LLM Provider Service
Abstracts LLM API calls with proper error handling and token tracking.
"""

import os
from typing import Optional, Dict, Any

from app.core.config import settings


class LLMProvider:
    """
    LLM provider with support for multiple backends.
    Currently supports OpenAI, extensible for other providers.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.OPENAI_MODEL

        if self.provider == "openai":
            try:
                import openai

                openai.api_key = settings.OPENAI_API_KEY
                self.client = openai.ChatCompletion
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")

    def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate LLM completion.

        Args:
            prompt: Input prompt
            temperature: Generation temperature
            max_tokens: Max output tokens
            model: Override model selection

        Returns:
            Response dict with choices and usage
        """
        model = model or self.model

        if self.provider == "openai":
            return self._complete_openai(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _complete_openai(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> Dict[str, Any]:
        """OpenAI API call."""
        try:
            import openai

            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "choices": [{"text": response.choices[0].message.content}],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            }
        except Exception as e:
            # Fallback response for development
            print(f"OpenAI API error: {e}")
            return {
                "choices": [{"text": "[Mock response] Unable to reach OpenAI API"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            }
