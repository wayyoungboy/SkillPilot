"""Hugging Face Spaces Importer

Imports AI agents and spaces from Hugging Face (https://huggingface.co/spaces)
"""

import httpx

from skillpilot.core.importers.base import BaseImporter
from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import SkillCreate, Pricing
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class HuggingFaceImporter(BaseImporter):
    """
    Importer for Hugging Face Spaces.

    Uses the Hugging Face Hub API to fetch AI spaces and agents.
    """

    platform = "huggingface"
    display_name = "Hugging Face"
    requires_config = False  # Can use anonymous access

    # HF API endpoint
    HF_API_BASE = "https://huggingface.co/api"

    async def fetch_skills(self) -> list[dict]:
        """
        Fetch popular AI spaces from Hugging Face Hub API.

        Documentation: https://huggingface.co/docs/hub/api
        """
        spaces = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch trending/popular spaces
                # Sort by likes or trending score
                params = {
                    "limit": self._config.get("limit", 100),
                    "sort": self._config.get("sort", "likes"),
                    "direction": -1,  # Descending
                }

                # Filter by SDK if specified (gradio, streamlit, docker)
                if self._config.get("sdk"):
                    params["sdk"] = self._config["sdk"]

                # Fetch spaces
                response = await client.get(
                    f"{self.HF_API_BASE}/spaces",
                    params=params,
                )
                response.raise_for_status()
                spaces = response.json()

                logger.info(f"Fetched {len(spaces)} spaces from Hugging Face")

                # Optionally fetch additional space details
                if self._config.get("fetch_details", False):
                    spaces = await self._fetch_space_details(client, spaces)

        except Exception as e:
            logger.error(f"Failed to fetch Hugging Face spaces: {str(e)}")

        return spaces

    async def _fetch_space_details(
        self, client: httpx.AsyncClient, spaces: list[dict]
    ) -> list[dict]:
        """Fetch additional details for each space"""
        detailed_spaces = []

        for space in spaces[:20]:  # Limit detail fetching
            try:
                space_id = space.get("id") or space.get("modelId")
                if not space_id:
                    continue

                response = await client.get(
                    f"{self.HF_API_BASE}/spaces/{space_id}"
                )
                if response.status_code == 200:
                    detailed_spaces.append(response.json())
                else:
                    detailed_spaces.append(space)

                # Rate limiting
                await __import__("asyncio").sleep(0.5)

            except Exception as e:
                logger.debug(f"Failed to fetch details for space: {e}")
                detailed_spaces.append(space)

        return detailed_spaces

    def normalize_skill(self, raw_data: dict) -> SkillCreate:
        """
        Normalize Hugging Face Space data to SkillCreate format.

        Expected raw_data structure:
        {
            "id": "author/space-name",
            "author": "...",
            "cardData": {...},
            "likes": 123,
            "sdk": "gradio"|"streamlit"|"docker",
            "tags": [...],
        }
        """
        space_id = raw_data.get("id", "unknown/space")
        space_name = space_id.split("/")[-1] if "/" in space_id else space_id

        # Extract metadata
        card_data = raw_data.get("cardData", {}) or {}
        title = card_data.get("title") or raw_data.get("title") or space_name
        description = card_data.get("description") or raw_data.get("description", "")

        # Extract tags
        tags = raw_data.get("tags", [])
        sdk = raw_data.get("sdk", "unknown")
        tags.extend(["huggingface", "space", sdk])

        # Infer capabilities from tags and description
        capabilities = self._infer_capabilities(tags, description)

        # Extract author
        author = raw_data.get("author") or card_data.get("author", "unknown")

        return SkillCreate(
            skill_name=title[:100],
            platform=PlatformType.CUSTOM,  # HF Spaces are custom platform
            description=description[:1000] if description else f"HF Space: {title}",
            capabilities=capabilities[:10],
            tags=list(set(tags))[:20],
            pricing=Pricing(type="free"),  # Most HF Spaces are free
        )

    def _infer_capabilities(self, tags: list[str], description: str) -> list[str]:
        """Infer capabilities from tags and description"""
        capabilities = []
        tags_lower = [t.lower() for t in (tags or [])]
        desc_lower = (description or "").lower()
        all_text = " ".join(tags_lower + [desc_lower])

        # Text generation
        if any(k in all_text for k in ["text-generation", "llm", "language-model", "gpt"]):
            capabilities.append("text_generation")

        # Image generation
        if any(k in all_text for k in ["image-generation", "stable-diffusion", "diffusers"]):
            capabilities.append("image_generation")

        # Audio/Speech
        if any(k in all_text for k in ["speech", "audio", "tts", "text-to-speech"]):
            capabilities.append("audio_processing")

        # Translation
        if "translation" in all_text:
            capabilities.append("translation")

        # Question Answering
        if any(k in all_text for k in ["question-answering", "qa", "question answering"]):
            capabilities.append("question_answering")

        # Summarization
        if "summarization" in all_text or "summary" in all_text:
            capabilities.append("summarization")

        # Chat/Conversation
        if any(k in all_text for k in ["conversational", "chatbot", "chat"]):
            capabilities.append("conversation")

        # Code generation
        if any(k in all_text for k in ["code", "programming", "codex"]):
            capabilities.append("code_generation")

        # Vision
        if any(k in all_text for k in ["vision", "image-classification", "object-detection"]):
            capabilities.append("vision")

        # Default
        if not capabilities:
            capabilities.append("general_assistant")

        return capabilities
