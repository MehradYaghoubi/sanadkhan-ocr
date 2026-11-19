"""Read vision provider configuration from the server environment."""
import os
from functools import lru_cache

from app.errors import ProviderConfigurationError
from app.llm.openai_client import OpenAICompatibleClient
from app.readers.readers import VlmReader
from app.services.extraction_service import ExtractionService


@lru_cache(maxsize=1)
def get_extraction_service() -> ExtractionService:
    names = ("SANADKHAN_API_BASE", "SANADKHAN_API_KEY", "SANADKHAN_MODEL")
    base_url, api_key, model = (os.getenv(name, "").strip() for name in names)
    if not all((base_url, api_key, model)):
        raise ProviderConfigurationError("Set SANADKHAN_API_BASE, SANADKHAN_API_KEY and SANADKHAN_MODEL on the server.")
    return ExtractionService(reader=VlmReader(
        llm=OpenAICompatibleClient(
            base_url=base_url,
            api_key=api_key,
            image_detail=os.getenv("SANADKHAN_VISION_DETAIL", "auto"),
            reasoning_effort=os.getenv("SANADKHAN_VISION_REASONING_EFFORT") or None,
        ),
        model=model,
    ))
