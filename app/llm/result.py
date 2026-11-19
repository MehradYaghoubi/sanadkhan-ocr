from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResult:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
