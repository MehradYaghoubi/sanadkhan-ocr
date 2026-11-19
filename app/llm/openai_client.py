"""کلاینت سازگار با OpenAI برای API خارجی (Vision LLM) با سشن‌های کاملاً ایزوله (Stateless)."""

import json
import urllib.error
import urllib.request

from app.errors import LlmUnavailableError
from app.llm.result import LLMResult


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout_seconds: int = 120,
        image_detail: str = "auto",
        reasoning_effort: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._image_detail = image_detail
        self._reasoning_effort = reasoning_effort

    def chat_json(
        self,
        model: str,
        prompt: str,
        images_b64: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResult:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if images_b64:
            user_content: object = [{"type": "text", "text": prompt}] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b}",
                        "detail": self._image_detail,
                    },
                }
                for b in images_b64
            ]
        else:
            user_content = prompt

        messages.append({"role": "user", "content": user_content})

        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.0,
            "top_p": 0.01,
            "response_format": {"type": "json_object"},
        }
        if self._reasoning_effort:
            body["reasoning_effort"] = self._reasoning_effort

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            raise LlmUnavailableError(f"Vision API returned HTTP {exc.code}.") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise LlmUnavailableError("Could not reach the Vision API.") from exc

        try:
            text = payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise LlmUnavailableError("ساختار پاسخ API خارجی ناشناخته است")
        if not text.strip():
            raise LlmUnavailableError("پاسخ خالی از مدل")
        usage = payload.get("usage") or {}
        return LLMResult(
            content=text,
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
        )
