"""Skill Importers Plugin System

Plugin-based architecture for importing skills from various platforms.
Each platform implements the BaseImporter interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.skill import SkillCreate
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class ImporterStatus(Enum):
    """Status of an importer"""

    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFIGURATION_REQUIRED = "configuration_required"


@dataclass
class ImportResult:
    """Result of importing a skill"""

    success: bool
    skill_id: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False
    reason: Optional[str] = None


@dataclass
class ImportSummary:
    """Summary of an import operation"""

    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BaseImporter(ABC):
    """
    Abstract base class for skill importers.

    Each platform (Coze, Dify, GPTStore, etc.) implements this interface.
    """

    # Platform identifier - must match PlatformType values
    platform: str = "base"

    # Human-readable name
    display_name: str = "Base"

    # Whether this importer requires API configuration
    requires_config: bool = False

    def __init__(self):
        self._status = ImporterStatus.READY
        self._config: dict = {}

    @property
    def status(self) -> ImporterStatus:
        """Get current importer status"""
        return self._status

    @property
    def config(self) -> dict:
        """Get current configuration"""
        return self._config

    @abstractmethod
    async def fetch_skills(self) -> list[dict]:
        """
        Fetch skills from the platform.

        Returns:
            List of skill data dictionaries from the platform
        """
        pass

    @abstractmethod
    def normalize_skill(self, raw_data: dict) -> SkillCreate:
        """
        Normalize platform-specific skill data to SkillCreate format.

        Args:
            raw_data: Raw skill data from the platform

        Returns:
            SkillCreate model ready for import
        """
        pass

    async def validate_config(self) -> bool:
        """
        Validate importer configuration.

        Returns:
            True if configuration is valid
        """
        if self.requires_config and not self._config:
            self._status = ImporterStatus.CONFIGURATION_REQUIRED
            return False
        self._status = ImporterStatus.READY
        return True

    def configure(self, **kwargs) -> None:
        """
        Configure the importer.

        Args:
            **kwargs: Configuration parameters
        """
        self._config.update(kwargs)
        logger.info(f"{self.display_name} importer configured", config=kwargs)

    async def import_skills(
        self,
        skill_service,
        limit: int = 100,
        developer_id: str = "system",
    ) -> ImportSummary:
        """
        Import skills from the platform.

        Args:
            skill_service: SkillService instance for creating skills
            limit: Maximum number of skills to import
            developer_id: Developer ID to assign to imported skills

        Returns:
            ImportSummary with statistics
        """
        summary = ImportSummary()

        try:
            # Validate configuration
            if not await self.validate_config():
                summary.errors.append(f"{self.display_name} requires configuration")
                return summary

            self._status = ImporterStatus.RUNNING
            logger.info(f"Starting {self.display_name} import", limit=limit)

            # Fetch skills from platform
            raw_skills = await self.fetch_skills()
            raw_skills = raw_skills[:limit]  # Apply limit

            summary.total = len(raw_skills)
            logger.info(f"Fetched {summary.total} skills from {self.display_name}")

            # Import each skill
            for raw_data in raw_skills:
                try:
                    # Normalize skill data
                    skill_create = self.normalize_skill(raw_data)

                    # Create skill using SkillService
                    skill = await skill_service.create_skill(skill_create, developer_id)

                    summary.success += 1
                    logger.debug(f"Imported skill: {skill.skill_name}", skill_id=skill.skill_id)

                except Exception as e:
                    summary.failed += 1
                    error_msg = f"Failed to import {raw_data.get('name', 'unknown')}: {str(e)}"
                    summary.errors.append(error_msg)
                    logger.error(error_msg)

            self._status = ImporterStatus.COMPLETED
            logger.info(
                f"{self.display_name} import completed",
                success=summary.success,
                failed=summary.failed,
                skipped=summary.skipped,
            )

        except Exception as e:
            self._status = ImporterStatus.FAILED
            error_msg = f"{self.display_name} import failed: {str(e)}"
            summary.errors.append(error_msg)
            logger.error(error_msg)

        return summary

    def __repr__(self) -> str:
        return f"{self.display_name}Importer(status={self.status.value})"


# Importer Registry
_importer_registry: dict[str, BaseImporter] = {}


def register_importer(importer: BaseImporter) -> None:
    """Register an importer plugin"""
    _importer_registry[importer.platform] = importer
    logger.info(f"Registered importer: {importer.display_name}", platform=importer.platform)


def get_importer(platform: str) -> Optional[BaseImporter]:
    """Get an importer by platform name"""
    return _importer_registry.get(platform)


def list_importers() -> list[dict]:
    """List all registered importers"""
    return [
        {
            "platform": importer.platform,
            "display_name": importer.display_name,
            "requires_config": importer.requires_config,
            "status": importer.status.value,
        }
        for importer in _importer_registry.values()
    ]


def get_all_importers() -> list[BaseImporter]:
    """Get all registered importers"""
    return list(_importer_registry.values())
