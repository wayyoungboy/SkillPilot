"""Orchestration Service"""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.orchestration import Orchestration, OrchestrationCreate, SkillChainStep
from skillpilot.core.services.ai_service import ai_service
from skillpilot.core.services.vector_search import vector_search_service
from skillpilot.core.utils.logger import get_logger
from skillpilot.db.seekdb import seekdb_client

logger = get_logger(__name__)


class OrchestrationService:
    """Orchestration service for managing AI skill execution plans"""

    async def create_plan(self, user_id: str, task_data: OrchestrationCreate) -> Orchestration:
        """Create a new orchestration plan"""
        plan_id = f"op_{uuid4().hex[:12]}"
        now = datetime.now(UTC)

        # Generate skill chain using AI service
        skill_chain = await self._generate_skill_chain(task_data.task_description)

        plan_dict = {
            "plan_id": plan_id,
            "user_id": user_id,
            "task_description": task_data.task_description,
            "skill_chain": [step.model_dump() for step in skill_chain],
            "status": "pending_confirmation",
            "estimated_duration": len(skill_chain) * 30,  # Estimate 30 seconds per step
            "created_at": now,
            "executed_at": None,
        }

        await seekdb_client.insert("orchestration_plans", plan_dict)
        logger.info(
            "Orchestration plan created", plan_id=plan_id, user_id=user_id, steps=len(skill_chain)
        )

        return Orchestration(
            plan_id=plan_id,
            task_description=task_data.task_description,
            skill_chain=skill_chain,
            status="pending_confirmation",
            estimated_duration=len(skill_chain) * 30,
            created_at=now,
        )

    async def get_plan(self, plan_id: str) -> Orchestration | None:
        """Get orchestration plan by ID"""
        plan_data = await seekdb_client.get("orchestration_plans", plan_id)
        if not plan_data:
            logger.debug("Orchestration plan not found", plan_id=plan_id)
            return None

        return self._parse_plan(plan_data)

    async def execute_plan(self, plan_id: str) -> Orchestration:
        """Execute an orchestration plan"""
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Orchestration plan not found")

        if plan.status == "running":
            raise ValueError("Orchestration plan is already running")

        # Update status to running
        await seekdb_client.update(
            "orchestration_plans",
            plan_id,
            {"status": "running", "executed_at": datetime.now(UTC)},
        )

        # Execute skill chain asynchronously
        asyncio.create_task(self._execute_skill_chain(plan_id, plan.skill_chain))

        plan.status = "running"
        plan.executed_at = datetime.now(UTC)

        logger.info("Orchestration plan execution started", plan_id=plan_id)
        return plan

    async def cancel_plan(self, plan_id: str) -> bool:
        """Cancel an orchestration plan"""
        plan = await self.get_plan(plan_id)
        if not plan:
            return False

        if plan.status in ["completed", "failed"]:
            logger.warning(
                "Cannot cancel plan in terminal state", plan_id=plan_id, status=plan.status
            )
            return False

        await seekdb_client.update("orchestration_plans", plan_id, {"status": "cancelled"})
        logger.info("Orchestration plan cancelled", plan_id=plan_id)
        return True

    async def list_plans(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> tuple[list[Orchestration], dict]:
        """List orchestration plans for a user"""
        offset = (page - 1) * limit

        plans_data = await seekdb_client.query(
            "orchestration_plans", filters={"user_id": user_id}, limit=limit, offset=offset
        )

        plans = [self._parse_plan(p) for p in plans_data]
        logger.debug("Listed orchestration plans", user_id=user_id, count=len(plans))

        return plans, {"page": page, "limit": limit}

    async def _generate_skill_chain(self, task_description: str) -> list[SkillChainStep]:
        """
        Generate skill chain based on task description using AI.
        
        Uses AI service to analyze task and match with available skills.
        """
        try:
            # Get available skills from database
            all_skills_data = await seekdb_client.query("skills", filters={}, limit=100)
            
            # Convert to dict format for AI service
            available_skills = []
            for skill_data in all_skills_data:
                from skillpilot.core.services.skill import skill_service
                skill = skill_service._parse_skill(skill_data)
                available_skills.append({
                    "skill_id": skill.skill_id,
                    "skill_name": skill.skill_name,
                    "platform": skill.platform.value,
                    "description": skill.description,
                    "capabilities": skill.capabilities,
                })
            
            # Use AI to generate optimal skill chain
            if available_skills:
                skill_chain = await ai_service.generate_skill_chain(
                    task_description, available_skills
                )
                logger.info("AI-generated skill chain", steps=len(skill_chain))
                return skill_chain
            
        except Exception as e:
            logger.error("AI skill chain generation failed, using fallback", error=str(e))
        
        # Fallback to rule-based generation
        return await self._rule_based_skill_chain(task_description)

    async def _rule_based_skill_chain(self, task_description: str) -> list[SkillChainStep]:
        """
        Fallback rule-based skill chain generation.
        
        Uses keyword matching to determine required skills.
        """
        task_lower = task_description.lower()

        chain = []
        step_num = 1

        # Web scraping step
        if any(
            keyword in task_lower
            for keyword in ["website", "webpage", "url", "http", "https", "scrape", "crawl"]
        ):
            chain.append(
                SkillChainStep(
                    step=step_num,
                    skill_id="sk_web_scraper",
                    skill_name="Web Scraper Pro",
                    platform=PlatformType.COZE,
                    input={"url": "input_url"},
                    output_format="JSON",
                )
            )
            step_num += 1

        # Content analysis step
        if any(keyword in task_lower for keyword in ["analyze", "analysis"]):
            chain.append(
                SkillChainStep(
                    step=step_num,
                    skill_id="sk_content_analyzer",
                    skill_name="Content Analyzer",
                    platform=PlatformType.DIFY,
                    input_format="JSON",
                    output_format="JSON",
                    depends_on=[step_num - 1] if step_num > 1 else [],
                )
            )
            step_num += 1

        # Report generation step
        if any(keyword in task_lower for keyword in ["report", "generate"]):
            chain.append(
                SkillChainStep(
                    step=step_num,
                    skill_id="sk_report_generator",
                    skill_name="Report Generator",
                    platform=PlatformType.LANGCHAIN,
                    input_format="JSON",
                    output_format="PDF",
                    depends_on=[step_num - 1] if step_num > 1 else [],
                )
            )

        # Default: return at least one skill
        if not chain:
            chain.append(
                SkillChainStep(
                    step=1,
                    skill_id="sk_default",
                    skill_name="Default Skill",
                    platform=PlatformType.CUSTOM,
                    output_format="JSON",
                )
            )

        logger.debug("Generated skill chain (rule-based)", steps=len(chain), task=task_description[:50])
        return chain

    async def _execute_skill_chain(self, plan_id: str, skill_chain: list[SkillChainStep]) -> None:
        """Execute skill chain steps sequentially"""
        try:
            logger.info("Executing skill chain", plan_id=plan_id, steps=len(skill_chain))

            # Import platform adapters
            from skillpilot.core.adapters import get_adapter
            from skillpilot.core.adapters.base import SkillExecutionRequest

            execution_results = []
            
            # Execute each step
            for step in skill_chain:
                # Get appropriate platform adapter
                adapter = get_adapter(step.platform.value if hasattr(step.platform, 'value') else str(step.platform))
                
                # Prepare execution request
                request = SkillExecutionRequest(
                    skill_id=step.skill_id,
                    skill_name=step.skill_name,
                    input_data=step.input or {},
                    platform_config=None,  # Can be extended to load from skill config
                )
                
                # Execute skill
                response = await adapter.execute_skill(request)
                execution_results.append({
                    "step": step.step,
                    "skill_id": step.skill_id,
                    "success": response.success,
                    "output": response.output,
                    "error": response.error,
                })
                
                if not response.success:
                    raise Exception(f"Step {step.step} failed: {response.error}")
                
                logger.info("Skill executed", plan_id=plan_id, step=step.step, skill_id=step.skill_id)

            # Execution completed
            await seekdb_client.update(
                "orchestration_plans",
                plan_id,
                {"status": "completed", "execution_results": execution_results},
            )
            logger.info("Skill chain execution completed", plan_id=plan_id)

        except Exception as e:
            # Execution failed
            logger.error("Skill chain execution failed", plan_id=plan_id, error=str(e))
            await seekdb_client.update(
                "orchestration_plans", plan_id, {"status": "failed", "error": str(e)}
            )

    def _parse_plan(self, data: dict) -> Orchestration:
        """Parse orchestration plan data from database format"""
        skill_chain = []
        if data.get("skill_chain"):
            for step_data in data["skill_chain"]:
                skill_chain.append(SkillChainStep(**step_data))

        return Orchestration(
            plan_id=data["plan_id"],
            task_description=data["task_description"],
            skill_chain=skill_chain,
            status=data.get("status", "pending_confirmation"),
            estimated_duration=data.get("estimated_duration", 0),
            created_at=data.get("created_at", datetime.now(UTC)),
            executed_at=data.get("executed_at"),
        )


orchestration_service = OrchestrationService()
