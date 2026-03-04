"""GPT Store Importer

Imports GPTs from third-party GPT Store directories.
Sources: gpts24.com, allgpts.io, gptstore.io
"""

import httpx

from skillpilot.core.importers.base import BaseImporter
from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import SkillCreate, Pricing
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class GPTStoreImporter(BaseImporter):
    """
    Importer for GPT Store (via third-party directories).

    Since OpenAI doesn't provide an official GPT Store API,
    this importer uses third-party directory sites.
    """

    platform = "openai"
    display_name = "GPT Store"
    requires_config = False

    # Third-party GPT directory URLs
    SOURCES = [
        {
            "name": "GPTs24",
            "url": "https://gpts24.com/popular",
            "format": "html",
        },
        {
            "name": "AllGPTs",
            "url": "https://allgpts.io/api/gpts",  # If API available
            "format": "json",
        },
    ]

    async def fetch_skills(self) -> list[dict]:
        """
        Fetch GPTs from third-party directories.

        Note: Web scraping may be rate-limited or blocked.
        Respect robots.txt and terms of service.
        """
        all_gpts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try each source
            for source in self.SOURCES:
                try:
                    if source["format"] == "json":
                        gpts = await self._fetch_json_source(client, source)
                    else:
                        gpts = await self._fetch_html_source(client, source)

                    all_gpts.extend(gpts)
                    logger.info(f"Fetched {len(gpts)} GPTs from {source['name']}")

                except Exception as e:
                    logger.warning(f"Failed to fetch from {source['name']}: {e}")

                # Rate limiting
                await __import__("asyncio").sleep(1)

        # Deduplicate by GPT name/slug
        seen = set()
        unique_gpts = []
        for gpt in all_gpts:
            key = gpt.get("slug") or gpt.get("name")
            if key and key not in seen:
                seen.add(key)
                unique_gpts.append(gpt)

        return unique_gpts

    async def _fetch_json_source(self, client: httpx.AsyncClient, source: dict) -> list[dict]:
        """Fetch from JSON API source"""
        response = await client.get(source["url"])
        response.raise_for_status()
        data = response.json()

        # Normalize different API responses
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get("gpts", data.get("data", data.get("items", [])))
        return []

    async def _fetch_html_source(self, client: httpx.AsyncClient, source: dict) -> list[dict]:
        """
        Fetch from HTML source (web scraping).

        Note: HTML structure varies by site and may change.
        This is a placeholder - actual implementation needs
        site-specific parsing.
        """
        response = await client.get(source["url"])
        response.raise_for_status()

        # Placeholder - actual implementation would use
        # BeautifulSoup or similar to parse HTML
        # For now, return empty list
        logger.warning(f"HTML scraping not fully implemented for {source['name']}")
        return []

    def normalize_skill(self, raw_data: dict) -> SkillCreate:
        """
        Normalize GPT data to SkillCreate format.

        Expected raw_data structure:
        {
            "name": "...",
            "slug": "...",
            "description": "...",
            "category": "...",
            "tags": [...],
        }
        """
        name = raw_data.get("name") or "Unknown GPT"
        description = raw_data.get("description") or ""
        category = raw_data.get("category", "general")

        # Extract tags
        tags = raw_data.get("tags", [])
        tags.extend(["gpt", "openai", category])

        # Infer capabilities from category/description
        capabilities = self._infer_capabilities(category, description)

        return SkillCreate(
            skill_name=name,
            platform=PlatformType.CUSTOM,  # OpenAI GPTs don't have a PlatformType
            description=description[:1000] if description else f"GPT: {name}",
            capabilities=capabilities[:10],
            tags=list(set(tags))[:20],
            pricing=Pricing(type="free"),  # Most GPTs are free
        )

    def _infer_capabilities(self, category: str, description: str) -> list[str]:
        """Infer capabilities from category and description"""
        capabilities = []
        desc_lower = (description or "").lower()
        category_lower = (category or "").lower()

        # Category-based inference
        if "writing" in category_lower or "writing" in desc_lower:
            capabilities.append("writing")
        if "code" in category_lower or "code" in desc_lower or "programming" in desc_lower:
            capabilities.append("code_generation")
        if "image" in category_lower or "image" in desc_lower:
            capabilities.append("image_generation")
        if "analysis" in category_lower or "analyze" in desc_lower:
            capabilities.append("data_analysis")
        if "chat" in category_lower or "conversation" in desc_lower:
            capabilities.append("conversation")
        if "search" in category_lower or "web" in desc_lower:
            capabilities.append("web_search")
        if "translation" in category_lower or "translate" in desc_lower:
            capabilities.append("translation")
        if "education" in category_lower or "learn" in desc_lower or "teach" in desc_lower:
            capabilities.append("education")

        # Default if nothing inferred
        if not capabilities:
            capabilities.append("general_assistant")

        return capabilities
