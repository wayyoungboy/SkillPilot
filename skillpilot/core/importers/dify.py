"""Dify App Importer

Imports AI applications from Dify platform (https://dify.ai/)
"""

from skillpilot.core.importers.base import BaseImporter
from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import SkillCreate, Pricing
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class DifyImporter(BaseImporter):
    """
    Importer for Dify applications.

    Uses the Dify API to fetch public apps/workflows.
    """

    platform = "dify"
    display_name = "Dify"
    requires_config = True  # Requires API key

    async def fetch_skills(self) -> list[dict]:
        """
        Fetch public apps from Dify.

        Note: Dify may not have a public app directory API.
        This importer works with self-hosted Dify instances
        or requires manual app ID list.
        """
        try:
            from dify_client import DifyClient

            # Initialize Dify client
            api_key = self._config.get("api_key")
            api_base = self._config.get("api_base", "https://api.dify.ai/v1")

            if not api_key:
                logger.error("Dify API key not configured")
                return []

            client = DifyClient(api_key=api_key)

            # Fetch apps - adjust based on actual Dify API
            apps = []

            try:
                # Option 1: Get apps from account/workspace
                # Note: Actual Dify API structure may vary
                if self._config.get("app_ids"):
                    # Fetch specific apps by ID
                    for app_id in self._config["app_ids"][:100]:
                        try:
                            app_info = await client.get_app(app_id)
                            apps.append(app_info)
                        except Exception as e:
                            logger.debug(f"Failed to fetch app {app_id}: {e}")

                # Option 2: List from workspace
                elif self._config.get("workspace_id"):
                    response = await client.list_apps(
                        workspace_id=self._config["workspace_id"]
                    )
                    apps = response.get("data", response.get("apps", []))

                else:
                    logger.warning(
                        "Dify API: Provide app_ids or workspace_id "
                        "to fetch specific applications"
                    )

            except Exception as e:
                logger.error(f"Dify API error: {str(e)}")

            return apps

        except ImportError:
            logger.error("Dify SDK not installed. Run: pip install dify-client")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch Dify apps: {str(e)}")
            return []

    def normalize_skill(self, raw_data: dict) -> SkillCreate:
        """
        Normalize Dify app data to SkillCreate format.

        Expected raw_data structure (may vary):
        {
            "id": "...",
            "name": "...",
            "description": "...",
            "mode": "chat|workflow|agent",
            "tags": [...],
        }
        """
        # Extract app ID
        app_id = raw_data.get("id") or raw_data.get("app_id")

        # Extract name and description
        name = raw_data.get("name") or raw_data.get("app_name", "Unknown Dify App")
        description = raw_data.get("description") or ""

        # Extract mode/capabilities
        mode = raw_data.get("mode", "chat")
        capabilities = raw_data.get("tags", [])
        if not capabilities:
            # Infer from mode
            if mode == "workflow":
                capabilities = ["workflow", "automation"]
            elif mode == "agent":
                capabilities = ["agent", "autonomous"]
            else:
                capabilities = ["chat", "conversation"]

        tags = raw_data.get("tags", [])
        tags.extend(["dify", mode])

        # Create SkillCreate model
        return SkillCreate(
            skill_name=name,
            platform=PlatformType.DIFY,
            description=description[:1000] if description else f"Dify {mode} app: {name}",
            capabilities=capabilities[:10],
            tags=list(set(tags))[:20],  # Remove duplicates
            pricing=Pricing(type="free"),
        )
