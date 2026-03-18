import json
import urllib.request
import urllib.error

from ai.provider import AIProvider, AIProviderConfig
from prompts.intent_schema import AIResponse, parse_ai_response


class OpenAICompatAdapter(AIProvider):
    """OpenAI-compatible chat adapter using only urllib (no external dependencies)."""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)

    def chat(self, messages: list[dict], system_prompt: str) -> AIResponse:
        """
        Send a chat request to an OpenAI-compatible endpoint and return a parsed AIResponse.

        Prepends system_prompt as a system message, then appends the provided messages.
        On any error, returns an AIResponse with an error message and no intents.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + list(messages)

        payload = {
            "model": self.config.model,
            "messages": full_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        request = urllib.request.Request(
            url=self.config.endpoint,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                raw_bytes = response.read()
            raw_text = raw_bytes.decode("utf-8")
            response_data = json.loads(raw_text)
            content = response_data["choices"][0]["message"]["content"]
            return parse_ai_response(content)

        except urllib.error.HTTPError as exc:
            error_msg = f"HTTP 错误 {exc.code}: {exc.reason}"
            return AIResponse(reply=error_msg, intents=[], raw="")

        except urllib.error.URLError as exc:
            error_msg = f"网络错误: {exc.reason}"
            return AIResponse(reply=error_msg, intents=[], raw="")

        except Exception as exc:
            error_msg = f"请求失败: {exc}"
            return AIResponse(reply=error_msg, intents=[], raw="")
