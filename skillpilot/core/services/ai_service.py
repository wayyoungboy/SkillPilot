"""AI Service for intelligent orchestration and decision making"""

import json
from typing import Any

from skillpilot.core.config import settings
from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.orchestration import SkillChainStep
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class AIService:
    """
    AI Service for intelligent task analysis and skill chain generation.

    Uses LLMs to:
    - Analyze task descriptions
    - Generate optimal skill chains
    - Suggest skill combinations
    - Optimize execution plans

    Supported providers:
    - OpenAI (gpt-4o-mini)
    - Anthropic (claude-3-haiku-20240307)
    - Mock (for development/testing without API keys)
    """

    def __init__(self):
        self.provider = settings.llm_provider
        self._client = None

    def _get_client(self):
        """Get or create LLM client"""
        if self._client is None:
            if self.provider == "openai":
                try:
                    from openai import AsyncOpenAI

                    if not settings.openai_api_key:
                        raise ValueError("OPENAI_API_KEY not configured")

                    self._client = AsyncOpenAI(api_key=settings.openai_api_key)
                    logger.info("OpenAI LLM client initialized")
                except ImportError:
                    logger.error("OpenAI SDK not installed. Run: pip install openai")
                    raise
                except Exception as e:
                    logger.error("Failed to initialize OpenAI client", error=str(e))
                    raise

            elif self.provider == "anthropic":
                try:
                    from anthropic import AsyncAnthropic

                    if not settings.anthropic_api_key:
                        raise ValueError("ANTHROPIC_API_KEY not configured")

                    self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
                    logger.info("Anthropic LLM client initialized")
                except ImportError:
                    logger.error("Anthropic SDK not installed. Run: pip install anthropic")
                    raise
                except Exception as e:
                    logger.error("Failed to initialize Anthropic client", error=str(e))
                    raise

            # Mock provider doesn't need a client
            elif self.provider == "mock":
                logger.info("Mock LLM provider initialized (no API key required)")

        return self._client

    async def analyze_task(self, task_description: str) -> dict[str, Any]:
        """
        Analyze a task description to extract requirements.

        Args:
            task_description: Natural language task description

        Returns:
            Analysis results including required capabilities, complexity, etc.

        Raises:
            ValueError: If analysis fails
        """
        # Mock provider - return basic analysis without LLM
        if self.provider == "mock":
            logger.info("Task analyzed with Mock provider", task=task_description[:50])
            return {
                "required_capabilities": ["general"],
                "complexity": "medium",
                "output_format": "JSON",
                "dependencies": [],
            }

        client = self._get_client()

        try:
            if self.provider == "openai":
                analysis = await self._analyze_with_openai(client, task_description)
                logger.info("Task analyzed with OpenAI", task=task_description[:50])
                return analysis

            elif self.provider == "anthropic":
                analysis = await self._analyze_with_anthropic(client, task_description)
                logger.info("Task analyzed with Anthropic", task=task_description[:50])
                return analysis

        except Exception as e:
            logger.error("AI task analysis failed", provider=self.provider, error=str(e))
            raise

    async def generate_skill_chain(
        self, task_description: str, available_skills: list[dict]
    ) -> list[SkillChainStep]:
        """
        Generate an optimal skill chain for a task.

        Args:
            task_description: Task to accomplish
            available_skills: List of available skills to choose from

        Returns:
            Ordered list of skill chain steps

        Raises:
            ValueError: If skill chain generation fails
        """
        # Mock provider - return first available skill as a simple chain
        if self.provider == "mock":
            if not available_skills:
                logger.warning("No available skills provided for mock chain generation")
                return []
            # Simple mock: just use the first skill
            first_skill = available_skills[0]
            logger.info("Skill chain generated with Mock provider", steps=1)
            return [
                SkillChainStep(
                    step=1,
                    skill_id=first_skill.get("skill_id", "mock-skill"),
                    skill_name=first_skill.get("skill_name", "Mock Skill"),
                    platform=first_skill.get("platform", "custom"),
                    input={"task": task_description},
                    output_format="JSON",
                    depends_on=[],
                )
            ]

        client = self._get_client()

        if not available_skills:
            logger.warning("No available skills provided for chain generation")
            return []

        try:
            if self.provider == "openai":
                chain = await self._generate_chain_with_openai(
                    client, task_description, available_skills
                )
                logger.info("Skill chain generated with OpenAI", steps=len(chain))
                return chain

            elif self.provider == "anthropic":
                chain = await self._generate_chain_with_anthropic(
                    client, task_description, available_skills
                )
                logger.info("Skill chain generated with Anthropic", steps=len(chain))
                return chain

        except Exception as e:
            logger.error("AI skill chain generation failed", provider=self.provider, error=str(e))
            raise

    async def optimize_execution_plan(self, skill_chain: list[SkillChainStep]) -> list[SkillChainStep]:
        """
        Optimize an existing skill chain for better performance.

        Args:
            skill_chain: Original skill chain

        Returns:
            Optimized skill chain
        """
        # For now, return as-is
        # TODO: Implement AI-based optimization
        logger.info("Execution plan optimization (not yet implemented)")
        return skill_chain

    async def _analyze_with_openai(self, client, task_description: str) -> dict[str, Any]:
        """Analyze task using OpenAI"""
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a task analysis expert. Analyze the task and extract: "
                        "1. Required capabilities (list of skills needed) "
                        "2. Complexity level (simple/medium/complex) "
                        "3. Expected output format "
                        "4. Dependencies between steps "
                        "Respond in JSON format."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this task: {task_description}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        analysis = json.loads(response.choices[0].message.content)
        return analysis

    async def _analyze_with_anthropic(self, client, task_description: str) -> dict[str, Any]:
        """Analyze task using Anthropic"""
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Analyze this task and provide a JSON response with "
                        f"required_capabilities, complexity, output_format, and dependencies: "
                        f"{task_description}"
                    ),
                }
            ],
        )

        analysis = json.loads(response.content[0].text)
        return analysis

    async def _generate_chain_with_openai(
        self, client, task_description: str, available_skills: list[dict]
    ) -> list[SkillChainStep]:
        """Generate skill chain using OpenAI"""
        skills_context = "\n".join(
            [
                f"- {s['skill_id']}: {s['skill_name']} ({s['platform']}) - {s.get('description', '')}"
                for s in available_skills
            ]
        )

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a skill orchestration expert. Given a task and available skills, "
                        "create an optimal execution chain. Consider: "
                        "1. Skill capabilities and compatibility "
                        "2. Execution order and dependencies "
                        "3. Input/output format matching "
                        "Respond with a JSON object containing a 'steps' array."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {task_description}\n\n"
                        f"Available Skills:\n{skills_context}\n\n"
                        "Generate an optimal skill chain."
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return self._parse_skill_chain(result.get("steps", []))

    async def _generate_chain_with_anthropic(
        self, client, task_description: str, available_skills: list[dict]
    ) -> list[SkillChainStep]:
        """Generate skill chain using Anthropic"""
        skills_context = "\n".join(
            [
                f"- {s['skill_id']}: {s['skill_name']} ({s['platform']}) - {s.get('description', '')}"
                for s in available_skills
            ]
        )

        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {task_description}\n\n"
                        f"Available Skills:\n{skills_context}\n\n"
                        "Generate an optimal skill chain as a JSON array of steps. "
                        "Each step should have: skill_id, skill_name, platform, input, output_format, depends_on."
                    ),
                }
            ],
        )

        result = json.loads(response.content[0].text)
        steps = result if isinstance(result, list) else result.get("steps", [])
        return self._parse_skill_chain(steps)

    def _parse_skill_chain(self, steps_data: list) -> list[SkillChainStep]:
        """Parse raw step data into SkillChainStep objects"""
        chain = []
        for idx, step_data in enumerate(steps_data, 1):
            platform_value = step_data.get("platform", "custom")
            if isinstance(platform_value, dict):
                platform_value = platform_value.get("value", "custom")

            step = SkillChainStep(
                step=idx,
                skill_id=step_data.get("skill_id", "unknown"),
                skill_name=step_data.get("skill_name", "Unknown Skill"),
                platform=platform_value,
                input=step_data.get("input", {}),
                output_format=step_data.get("output_format", "JSON"),
                depends_on=step_data.get("depends_on", []),
            )
            chain.append(step)

        return chain

    def set_provider(self, provider: str) -> None:
        """Set the LLM provider"""
        if provider not in ["openai", "anthropic", "mock"]:
            raise ValueError(f"Unknown provider: {provider}")

        self.provider = provider
        self._client = None
        logger.info("AI provider set", provider=provider)


ai_service = AIService()
