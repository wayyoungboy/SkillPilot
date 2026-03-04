"""Orchestration Service for AI-powered skill matching and task execution"""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from skillpilot.core.models.common import PlatformType
from skillpilot.core.models.orchestration import (
    Orchestration,
    OrchestrationCreate,
    SkillChainStep,
)
from skillpilot.core.services.ai_service import ai_service
from skillpilot.core.services.vector_search import vector_search_service
from skillpilot.core.utils.logger import get_logger
from skillpilot.db.seekdb import seekdb_client

logger = get_logger(__name__)


class OrchestrationService:
    """
    Orchestration service for managing task execution plans.

    Provides:
    - Create orchestration plans
    - Get/List plans
    - Execute and cancel plans
    - Skill chain generation
    """

    async def create_plan(
        self, user_id: str, task_data: OrchestrationCreate
    ) -> Orchestration | None:
        """Create a new orchestration plan."""
        plan_id = f"op_{uuid4().hex[:12]}"
        now = datetime.now(UTC)

        skill_chain = await self._generate_skill_chain(task_data.task_description)

        plan_dict = {
            "plan_id": plan_id,
            "user_id": user_id,
            "task_description": task_data.task_description,
            "skill_chain": [step.model_dump() for step in skill_chain],
            "status": "pending_confirmation",
            "created_at": now,
            "executed_at": None,
        }

        await seekdb_client.insert("orchestration_plans", plan_dict)
        logger.info("Orchestration plan created", plan_id=plan_id, user_id=user_id)

        return self._parse_plan(plan_dict)

    async def get_plan(self, plan_id: str) -> Orchestration | None:
        """Get orchestration plan by ID"""
        plan_data = await seekdb_client.get("orchestration_plans", plan_id)
        if not plan_data:
            logger.debug("Plan not found", plan_id=plan_id)
            return None
        return self._parse_plan(plan_data)

    async def list_plans(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> tuple[list, dict]:
        """List orchestration plans for a user"""
        offset = (page - 1) * limit
        plans_data = await seekdb_client.query(
            "orchestration_plans",
            filters={"user_id": user_id},
            limit=limit,
            offset=offset,
        )
        plans = [self._parse_plan(p) for p in plans_data]
        return plans, {"page": page, "limit": limit}

    async def execute_plan(self, plan_id: str) -> Orchestration:
        """Execute an orchestration plan"""
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Orchestration plan not found")
        if plan.status == "running":
            raise ValueError("Orchestration plan is already running")

        await seekdb_client.update("orchestration_plans", plan_id, {"status": "running"})
        asyncio.create_task(self._execute_steps(plan))
        plan.status = "running"
        return plan

    async def _execute_steps(self, plan: Orchestration) -> None:
        """Execute skill chain steps asynchronously"""
        try:
            for step in plan.skill_chain:
                logger.info("Executing step", step=step.step, skill_id=step.skill_id)
                await asyncio.sleep(0.1)
            await seekdb_client.update(
                "orchestration_plans",
                plan.plan_id,
                {"status": "completed", "executed_at": datetime.now(UTC)},
            )
        except Exception as e:
            logger.error("Execution failed", plan_id=plan.plan_id, error=str(e))
            await seekdb_client.update("orchestration_plans", plan.plan_id, {"status": "failed"})

    async def cancel_plan(self, plan_id: str) -> bool:
        """Cancel an orchestration plan"""
        plan = await self.get_plan(plan_id)
        if not plan or plan.status in ["completed", "cancelled"]:
            return False
        await seekdb_client.update("orchestration_plans", plan_id, {"status": "cancelled"})
        return True

    async def _generate_skill_chain(self, task_description: str) -> list[SkillChainStep]:
        """Generate skill chain based on task description"""
        task_lower = task_description.lower()
        chain = []
        step_num = 1

        if any(k in task_lower for k in ["scrape", "crawl", "extract", "website", "url"]):
            chain.append(
                SkillChainStep(
                    step=step_num,
                    skill_id="sk_web_scraper",
                    skill_name="Web Scraper",
                    platform=PlatformType.CUSTOM,
                    input={"url": "https://example.com"},
                    output_format="JSON",
                    depends_on=[],
                )
            )
            step_num += 1

        if any(k in task_lower for k in ["analyze", "analysis", "sentiment", "classify"]):
            chain.append(
                SkillChainStep(
                    step=step_num,
                    skill_id="sk_analyzer",
                    skill_name="Analyzer",
                    platform=PlatformType.CUSTOM,
                    input={"data": "input_data"},
                    output_format="JSON",
                    depends_on=[step_num - 1] if step_num > 1 else [],
                )
            )
            step_num += 1

        if any(k in task_lower for k in ["report", "document", "pdf", "generate"]):
            chain.append(
                SkillChainStep(
                    step=step_num,
                    skill_id="sk_report_generator",
                    skill_name="Report Generator",
                    platform=PlatformType.CUSTOM,
                    input={"analysis": "analysis_result"},
                    output_format="PDF",
                    depends_on=[step_num - 1] if step_num > 1 else [],
                )
            )
            step_num += 1

        if not chain:
            chain.append(
                SkillChainStep(
                    step=1,
                    skill_id="sk_default",
                    skill_name="General Assistant",
                    platform=PlatformType.CUSTOM,
                    input={"task": task_description},
                    output_format="JSON",
                    depends_on=[],
                )
            )

        return chain

    def _parse_plan(self, data: dict) -> Orchestration:
        """Parse plan data from database format"""
        skill_chain = []
        if data.get("skill_chain"):
            for step_data in data["skill_chain"]:
                skill_chain.append(SkillChainStep(**step_data))
        return Orchestration(
            plan_id=data["plan_id"],
            user_id=data["user_id"],
            task_description=data["task_description"],
            skill_chain=skill_chain,
            status=data.get("status", "pending_confirmation"),
            created_at=data.get("created_at"),
            executed_at=data.get("executed_at"),
        )


class RecommendationService:
    """
    Recommendation service for AI-powered skill matching and task analysis.
    """

    async def analyze_task(self, task_description: str) -> dict:
        """Analyze a task description to identify required capabilities."""
        try:
            analysis = await ai_service.analyze_task(task_description)
            logger.info("Task analyzed", task=task_description[:50])
            return analysis
        except Exception as e:
            logger.error("Task analysis failed", error=str(e))
            return self._rule_based_analysis(task_description)

    async def recommend_skills(self, task_description: str, limit: int = 10) -> list:
        """Recommend skills for a given task."""
        results = await vector_search_service.match_skills_to_task(
            task_description, top_k=limit
        )
        logger.info("Skills recommended for task", task=task_description[:50], count=len(results))
        return results

    async def generate_skill_chain(self, task_description: str) -> list[SkillChainStep]:
        """Generate a recommended skill chain for completing a task."""
        try:
            all_skills_data = await seekdb_client.query("skills", filters={}, limit=100)
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
            if available_skills:
                skill_chain = await ai_service.generate_skill_chain(
                    task_description, available_skills
                )
                logger.info("AI-generated skill chain", steps=len(skill_chain))
                return skill_chain
        except Exception as e:
            logger.error("AI skill chain generation failed", error=str(e))
        return self._rule_based_skill_chain(task_description)

    async def save_recommendation(
        self, user_id: str, task_description: str, skill_chain: list[SkillChainStep]
    ) -> str:
        """Save a recommendation plan for reference."""
        plan_id = f"op_{uuid4().hex[:12]}"
        now = datetime.now(UTC)
        plan_dict = {
            "plan_id": plan_id,
            "user_id": user_id,
            "task_description": task_description,
            "skill_chain": [step.model_dump() for step in skill_chain],
            "status": "recommended",
            "created_at": now,
        }
        await seekdb_client.insert("orchestration_plans", plan_dict)
        logger.info("Recommendation saved", plan_id=plan_id, user_id=user_id, steps=len(skill_chain))
        return plan_id

    async def get_plan(self, plan_id: str) -> dict | None:
        """Get saved recommendation plan by ID"""
        plan_data = await seekdb_client.get("orchestration_plans", plan_id)
        if not plan_data:
            return None
        return self._parse_plan(plan_data)

    async def list_plans(self, user_id: str, page: int = 1, limit: int = 20) -> tuple[list, dict]:
        """List saved recommendation plans for a user"""
        offset = (page - 1) * limit
        plans_data = await seekdb_client.query(
            "orchestration_plans", filters={"user_id": user_id}, limit=limit, offset=offset
        )
        plans = [self._parse_plan(p) for p in plans_data]
        return plans, {"page": page, "limit": limit}

    def _rule_based_analysis(self, task_description: str) -> dict:
        """Fallback rule-based task analysis"""
        task_lower = task_description.lower()
        capabilities = []
        if any(k in task_lower for k in ["scrape", "crawl", "extract", "website", "url"]):
            capabilities.append("web_scraping")
        if any(k in task_lower for k in ["analyze", "analysis", "sentiment", "classify"]):
            capabilities.append("content_analysis")
        if any(k in task_lower for k in ["summarize", "summary", "brief"]):
            capabilities.append("summarization")
        if any(k in task_lower for k in ["translate", "translation"]):
            capabilities.append("translation")
        if any(k in task_lower for k in ["report", "document", "pdf"]):
            capabilities.append("document_generation")
        if any(k in task_lower for k in ["image", "picture", "visual"]):
            capabilities.append("image_processing")
        return {
            "required_capabilities": capabilities,
            "complexity": "complex" if len(capabilities) > 2 else "medium" if capabilities else "simple",
        }

    def _rule_based_skill_chain(self, task_description: str) -> list[SkillChainStep]:
        """Fallback rule-based skill chain generation"""
        task_lower = task_description.lower()
        capabilities = self._rule_based_analysis(task_description).get("required_capabilities", [])
        chain = []
        step_num = 1
        capability_keywords = {
            "web_scraping": ["website", "webpage", "url", "scrape", "crawl"],
            "content_analysis": ["analyze", "analysis", "sentiment", "classify"],
            "document_generation": ["report", "document", "pdf", "generate"],
        }
        for capability in capabilities:
            keywords = capability_keywords.get(capability, [])
            if any(kw in task_lower for kw in keywords):
                chain.append(
                    SkillChainStep(
                        step=step_num,
                        skill_id=f"sk_{capability}",
                        skill_name=capability.replace("_", " ").title(),
                        platform=PlatformType.CUSTOM,
                        input={"data": f"input_for_{capability}"},
                        output_format="JSON",
                        depends_on=[step_num - 1] if step_num > 1 else [],
                    )
                )
                step_num += 1
        if not chain:
            chain.append(
                SkillChainStep(
                    step=1,
                    skill_id="sk_default",
                    skill_name="General Assistant",
                    platform=PlatformType.CUSTOM,
                    output_format="JSON",
                )
            )
        return chain

    def _parse_plan(self, data: dict) -> dict:
        """Parse plan data from database format"""
        skill_chain = []
        if data.get("skill_chain"):
            for step_data in data["skill_chain"]:
                skill_chain.append(SkillChainStep(**step_data))
        return {
            "plan_id": data["plan_id"],
            "user_id": data["user_id"],
            "task_description": data["task_description"],
            "skill_chain": skill_chain,
            "status": data.get("status", "recommended"),
            "created_at": data.get("created_at"),
        }


# Singleton instances
orchestration_service = OrchestrationService()
recommendation_service = RecommendationService()
