from dataclasses import dataclass
from typing import Optional
from ..prompts.intent_schema import AIResponse


@dataclass
class AIProviderConfig:
    api_key: str = ""
    endpoint: str = ""
    model: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 60


class AIProvider:
    def __init__(self, config: AIProviderConfig):
        self.config = config

    def chat(self, messages: list[dict], system_prompt: str) -> AIResponse:
        raise NotImplementedError

    def validate_config(self) -> Optional[str]:
        if not self.config.api_key:
            return "API Key 未设置"
        if not self.config.endpoint:
            return "API 端点未设置"
        if not self.config.model:
            return "模型名称未设置"
        return None
