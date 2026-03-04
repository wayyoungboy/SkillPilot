"""Skill Importers Registry

Auto-discover and register all importer plugins.
"""

from skillpilot.core.importers.base import register_importer, get_all_importers
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


def load_all_importers():
    """Load and register all available importers"""
    # Import all importer modules to trigger registration
    from skillpilot.core.importers import coze, dify, gptstore, huggingface

    # Register importers
    register_importer(coze.CozeImporter())
    register_importer(dify.DifyImporter())
    register_importer(gptstore.GPTStoreImporter())
    register_importer(huggingface.HuggingFaceImporter())

    logger.info(
        f"Loaded {len(get_all_importers())} skill importers",
        importers=[i.display_name for i in get_all_importers()],
    )


def get_importer_config_help(platform: str) -> str:
    """Get configuration help for a specific importer"""
    help_text = {
        "coze": """
Coze Importer Configuration:
  - api_key: Coze API key (required)
  - workspace_id: Coze workspace ID (optional, for workspace bots)

Example:
  importer.configure(api_key="your-coze-api-key", workspace_id="xxx")
""",
        "dify": """
Dify Importer Configuration:
  - api_key: Dify API key (required)
  - api_base: Dify API base URL (default: https://api.dify.ai/v1)
  - app_ids: List of specific app IDs to import (optional)
  - workspace_id: Dify workspace ID (optional)

Example:
  importer.configure(api_key="your-dify-api-key", app_ids=["app1", "app2"])
""",
        "gptstore": """
GPT Store Importer Configuration:
  - No configuration required
  - Uses third-party directories (gpts24.com, allgpts.io)
""",
        "huggingface": """
Hugging Face Importer Configuration:
  - limit: Max spaces to fetch (default: 100)
  - sort: Sort field (default: "likes")
  - sdk: Filter by SDK (gradio/streamlit/docker, optional)
  - fetch_details: Fetch detailed info (default: False)

Example:
  importer.configure(limit=50, sdk="gradio", fetch_details=True)
""",
    }
    return help_text.get(platform, f"No help available for {platform}")


__all__ = ["load_all_importers", "get_importer_config_help"]
