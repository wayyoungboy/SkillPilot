"""Coze Bot Importer

Imports AI bots from Coze platform (https://www.coze.com/)
"""

from skillpilot.core.importers.base import BaseImporter
from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import SkillCreate, Pricing
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class CozeImporter(BaseImporter):
    """
    Importer for Coze bots.

    Uses the official Coze API to fetch public bots.
    """

    platform = "coze"
    display_name = "Coze"
    requires_config = True  # Requires API key

    async def fetch_skills(self) -> list[dict]:
        """
        Fetch public bots from Coze.

        Note: Coze API for public bot discovery may require authentication.
        If direct API is not available, this may need to be implemented
        via web scraping or using a bot directory.
        """
        try:
            from coze import Coze

            # Initialize Coze client
            api_key = self._config.get("api_key")
            if not api_key:
                logger.error("Coze API key not configured")
                return []

            client = Coze(api_key=api_key)

            # Fetch bots - adjust based on actual Coze API
            # This is a placeholder - actual API may differ
            bots = []

            # Try to get published bots
            # Note: Actual Coze API structure may vary
            try:
                # Option 1: Get from workspace
                if self._config.get("workspace_id"):
                    response = await client.bots.list(
                        workspace_id=self._config["workspace_id"]
                    )
                    bots = response.get("bots", [])

                # Option 2: Get public bots (if API supports)
                else:
                    # This would need the actual Coze API endpoint
                    logger.warning(
                        "Coze public bot API not fully supported, "
                        "provide workspace_id for best results"
                    )

            except Exception as e:
                logger.error(f"Coze API error: {str(e)}")

            return bots

        except ImportError:
            logger.error("Coze SDK not installed. Run: pip install coze")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch Coze bots: {str(e)}")
            return []

    def normalize_skill(self, raw_data: dict) -> SkillCreate:
        """
        Normalize Coze bot data to SkillCreate format.

        Expected raw_data structure (may vary based on API):
        {
            "bot_id": "...",
            "name": "...",
            "description": "...",
            "tags": [...],
            "capabilities": [...],
        }
        """
        # Extract bot ID for reference
        bot_id = raw_data.get("bot_id") or raw_data.get("id")

        # Extract name and description
        name = raw_data.get("name") or raw_data.get("bot_name", "Unknown Coze Bot")
        description = raw_data.get("description") or ""

        # Extract tags/capabilities
        capabilities = raw_data.get("capabilities", [])
        if not capabilities:
            # Try to infer from bot info
            capabilities = raw_data.get("tags", [])

        tags = raw_data.get("tags", [])
        tags.append("coze")  # Add platform tag

        # Create SkillCreate model
        return SkillCreate(
            skill_name=name,
            platform=PlatformType.COZE,
            description=description[:1000] if description else f"Coze bot: {name}",
            capabilities=capabilities[:10] if capabilities else ["general_assistant"],
            tags=tags[:20] if tags else ["coze", "bot"],
            pricing=Pricing(type="free"),  # Coze bots are typically free
        )
