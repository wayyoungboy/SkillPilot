"""AI Service for intelligent orchestration and decision making"""

from typing import Any

from skillpilot.core.config import settings
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
    """

    def __init__(self):
        self.provider = "openai"  # Default provider
        self._client = None

    def _get_client(self):
        """Get or create LLM client"""
        if self._client is None:
            if self.provider == "openai":
                try:
                    from openai import AsyncOpenAI

                    self._client = AsyncOpenAI()
                    logger.info("OpenAI LLM client initialized")
                except ImportError:
                    logger.warning("OpenAI not installed, using rule-based fallback")
                    self._client = None
            elif self.provider == "anthropic":
                try:
                    from anthropic import AsyncAnthropic

                    self._client = AsyncAnthropic()
                    logger.info("Anthropic LLM client initialized")
                except ImportError:
                    logger.warning("Anthropic not installed, using rule-based fallback")
                    self._client = None

        return self._client

    async def analyze_task(self, task_description: str) -> dict[str, Any]:
        """
        Analyze a task description to extract requirements.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Analysis results including required capabilities, complexity, etc.
        """
        client = self._get_client()
        
        if client is None:
            return self._rule_based_analysis(task_description)
        
        try:
            if self.provider == "openai":
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
                
                import json
                analysis = json.loads(response.choices[0].message.content)
                logger.info("Task analyzed with AI", task=task_description[:50])
                return analysis
                
            elif self.provider == "anthropic":
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
                
                import json
                analysis = json.loads(response.content[0].text)
                logger.info("Task analyzed with Anthropic", task=task_description[:50])
                return analysis
                
        except Exception as e:
            logger.error("AI task analysis failed", error=str(e))
            return self._rule_based_analysis(task_description)

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
        """
        client = self._get_client()
        
        if client is None or len(available_skills) == 0:
            return self._rule_based_chain_generation(task_description, available_skills)
        
        try:
            if self.provider == "openai":
                # Prepare skills context
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
                                "Respond with a JSON array of skill chain steps."
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
                
                import json
                result = json.loads(response.choices[0].message.content)
                
                # Parse into SkillChainStep objects
                chain = []
                steps_data = result.get("steps", [])
                for idx, step_data in enumerate(steps_data, 1):
                    step = SkillChainStep(
                        step=idx,
                        skill_id=step_data.get("skill_id", "unknown"),
                        skill_name=step_data.get("skill_name", "Unknown Skill"),
                        platform=step_data.get("platform", "custom"),
                        input=step_data.get("input", {}),
                        output_format=step_data.get("output_format", "JSON"),
                        depends_on=step_data.get("depends_on", []),
                    )
                    chain.append(step)
                
                logger.info("Skill chain generated with AI", steps=len(chain))
                return chain
                
        except Exception as e:
            logger.error("AI skill chain generation failed", error=str(e))
            return self._rule_based_chain_generation(task_description, available_skills)

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

    def _rule_based_analysis(self, task_description: str) -> dict[str, Any]:
        """Fallback rule-based task analysis"""
        task_lower = task_description.lower()
        
        capabilities = []
        complexity = "simple"
        output_format = "JSON"
        
        # Detect capabilities
        if any(k in task_lower for k in ["scrape", "crawl", "extract", "website", "url"]):
            capabilities.append("web_scraping")
            complexity = "medium"
        
        if any(k in task_lower for k in ["analyze", "analysis", "sentiment", "classify"]):
            capabilities.append("content_analysis")
            complexity = "medium"
        
        if any(k in task_lower for k in ["summarize", "summary", "brief"]):
            capabilities.append("summarization")
        
        if any(k in task_lower for k in ["translate", "translation"]):
            capabilities.append("translation")
            complexity = "medium"
        
        if any(k in task_lower for k in ["report", "document", "pdf"]):
            capabilities.append("document_generation")
            output_format = "PDF"
            complexity = "complex"
        
        if any(k in task_lower for k in ["image", "picture", "visual"]):
            capabilities.append("image_processing")
            complexity = "complex"
        
        return {
            "required_capabilities": capabilities,
            "complexity": complexity,
            "output_format": output_format,
            "dependencies": [],
        }

    def _rule_based_chain_generation(
        self, task_description: str, available_skills: list[dict]
    ) -> list[SkillChainStep]:
        """Fallback rule-based skill chain generation"""
        from skillpilot.core.models.common import PlatformType
        
        analysis = self._rule_based_analysis(task_description)
        capabilities = analysis["required_capabilities"]
        
        chain = []
        step_num = 1
        
        # Match skills to capabilities
        for capability in capabilities:
            matching_skills = [
                s for s in available_skills if capability in s.get("capabilities", [])
            ]
            
            if matching_skills:
                skill = matching_skills[0]
                chain.append(
                    SkillChainStep(
                        step=step_num,
                        skill_id=skill["skill_id"],
                        skill_name=skill["skill_name"],
                        platform=PlatformType(skill.get("platform", "custom")),
                        input={"data": f"input_for_{capability}"},
                        output_format="JSON",
                        depends_on=[step_num - 1] if step_num > 1 else [],
                    )
                )
                step_num += 1
        
        # Default skill if no matches
        if not chain and available_skills:
            skill = available_skills[0]
            chain.append(
                SkillChainStep(
                    step=1,
                    skill_id=skill["skill_id"],
                    skill_name=skill["skill_name"],
                    platform=PlatformType(skill.get("platform", "custom")),
                    output_format="JSON",
                )
            )
        
        logger.info("Skill chain generated (rule-based)", steps=len(chain))
        return chain

    def set_provider(self, provider: str) -> None:
        """Set the LLM provider"""
        if provider not in ["openai", "anthropic", "mock"]:
            raise ValueError(f"Unknown provider: {provider}")
        
        self.provider = provider
        self._client = None
        logger.info("AI provider set", provider=provider)


ai_service = AIService()
