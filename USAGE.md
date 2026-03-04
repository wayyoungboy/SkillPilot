# SkillPilot 使用指南

SkillPilot 是一个 AI Skill 搜索引擎，提供语义搜索、技能推荐和任务分析功能。

---

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/wayyoungboy/SkillPilot.git
cd SkillPilot

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -e ".[ai-all]"
```

### 2. 配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，配置必要的 API Key
```

**.env 配置说明：**

```ini
# SeekDB 配置（必需）
SEEKDB_URL=seekdb://localhost:6432

# OpenAI API Key（必需，用于 Embedding 和 AI 推荐）
OPENAI_API_KEY=sk-your-openai-api-key-here

# Embedding 和 LLM 配置
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
```

### 3. 启动服务

```bash
# 启动开发服务器
uvicorn skillpilot.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Python 直接运行
python -m skillpilot.main
```

访问 http://localhost:8000/docs 查看 API 文档。

---

## 核心 API 使用

### 1. 技能搜索

```bash
# 语义搜索技能
curl -X GET "http://localhost:8000/api/v1/skills/search?q=代码审查&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例：**
```json
[
  {
    "skill_id": "sk_abc123",
    "skill_name": "Code Review Pro",
    "platform": "coze",
    "description": "专业的代码审查 AI 助手",
    "capabilities": ["code_review", "bug_detection"],
    "similarity": 0.89
  }
]
```

### 2. 任务分析

```bash
# 分析任务需要的能力
curl -X POST "http://localhost:8000/api/v1/recommendations/analyze?task_description=帮我分析这个网站的内容并生成报告" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例：**
```json
{
  "required_capabilities": [
    "web_scraping",
    "content_analysis",
    "document_generation"
  ],
  "complexity": "complex"
}
```

### 3. 技能推荐

```bash
# 根据任务推荐技能
curl -X POST "http://localhost:8000/api/v1/recommendations/skills?task_description=创建一个数据分析报告&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例：**
```json
{
  "skills": [
    {
      "skill_id": "sk_data_viz",
      "skill_name": "Data Visualization Expert",
      "platform": "dify",
      "similarity": 0.92
    }
  ],
  "count": 1
}
```

### 4. 生成技能链

```bash
# 生成完成任务的技能链
curl -X POST "http://localhost:8000/api/v1/recommendations/chain" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"task_description": "分析竞争对手网站并生成市场报告"}'
```

**响应示例：**
```json
[
  {
    "step": 1,
    "skill_id": "sk_web_scraper",
    "skill_name": "Web Scraper Pro",
    "platform": "coze",
    "input": {"url": "input_url"},
    "output_format": "JSON"
  },
  {
    "step": 2,
    "skill_id": "sk_analyzer",
    "skill_name": "Market Analyst",
    "platform": "dify",
    "depends_on": [1]
  }
]
```

---

## 在 Claude 中使用

### 方式 1：作为外部工具集成

如果你使用 Claude Desktop 或 Claude Code，可以通过 MCP Server 方式集成：

```javascript
// claude-config.js 示例
module.exports = {
  mcpServers: {
    skillpilot: {
      command: "npx",
      args: ["-y", "mcp-server-http", "--url", "http://localhost:8000/api/v1"]
    }
  }
}
```

### 方式 2：Python 代码调用

```python
import httpx

async def search_skills_for_claude(task: str):
    """在 Claude 对话中调用 SkillPilot 搜索技能"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/skills/search",
            params={"q": task, "limit": 5},
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )
        return response.json()

# Claude 可以这样使用:
# "帮我搜索适合做数据分析的 AI 技能"
# → 调用 search_skills_for_claude("数据分析")
# → 返回技能列表给用户
```

### 方式 3：作为 Claude 的 Tool/Function

```python
from fastapi import FastAPI, Depends
from skillpilot.core.services import recommendation_service

app = FastAPI()

@app.get("/tools/skill-search")
async def claude_skill_search(query: str):
    """
    供 Claude 调用的技能搜索工具
    当用户询问"有什么 AI 技能可以做 X"时使用
    """
    skills = await recommendation_service.recommend_skills(
        task_description=query,
        limit=5
    )
    return {
        "query": query,
        "recommendations": [
            {
                "name": s.skill_name,
                "platform": s.platform,
                "description": s.description,
                "match_score": s.similarity
            }
            for s in skills
        ]
    }
```

**Claude 提示词示例：**

```
你可以使用 skill_search 工具来查找适合用户需求的 AI 技能。

当用户问：
- "有什么工具可以做 X？"
- "推荐一个能处理 Y 的 AI"
- "我需要一个可以 Z 的技能"

调用 skill_search(query="用户需求的简洁描述") 来获取推荐。
```

---

## Python SDK 使用示例

```python
# 使用 httpx 调用 API
import httpx

class SkillPilotClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def search(self, query: str, limit: int = 10):
        """搜索技能"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/skills/search",
                params={"q": query, "limit": limit},
                headers=self.headers
            )
            return resp.json()

    async def analyze_task(self, task: str):
        """分析任务"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/recommendations/analyze",
                params={"task_description": task},
                headers=self.headers
            )
            return resp.json()

    async def recommend(self, task: str, limit: int = 5):
        """推荐技能"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/recommendations/skills",
                params={"task_description": task, "limit": limit},
                headers=self.headers
            )
            return resp.json()

# 使用示例
async def main():
    client = SkillPilotClient(
        base_url="http://localhost:8000/api/v1",
        api_key="your-token"
    )

    # 搜索技能
    skills = await client.search("代码审查")
    print(f"找到 {len(skills)} 个技能")

    # 分析任务
    analysis = await client.analyze_task("分析网站并生成报告")
    print(f"需要能力：{analysis['required_capabilities']}")

    # 获取推荐
    recs = await client.recommend("数据可视化")
    for skill in recs['skills']:
        print(f"- {skill['skill_name']} ({skill['platform']})")
```

---

## 与 LangChain 集成

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent
import httpx

def create_skill_search_tool(base_url: str, api_key: str):
    """创建 LangChain Tool"""

    def search_skills(query: str) -> str:
        """搜索适合特定任务的 AI 技能"""
        with httpx.Client() as client:
            resp = client.get(
                f"{base_url}/skills/search",
                params={"q": query, "limit": 3},
                headers={"Authorization": f"Bearer {api_key}"}
            )
            skills = resp.json()
            return "\n".join([
                f"- {s['skill_name']}: {s['description']}"
                for s in skills
            ])

    return Tool(
        name="Skill Search",
        func=search_skills,
        description="搜索 AI 技能库，找到适合特定任务的工具"
    )

# 在 LangChain Agent 中使用
tool = create_skill_search_tool("http://localhost:8000/api/v1", "your-token")
agent = initialize_agent([tool], llm, agent="zero-shot-react-description")

# 现在 Agent 可以自动调用技能搜索
agent.run("我需要一个能帮我做代码审查的 AI 工具")
```

---

## 数据库初始化

SkillPilot 使用 SeekDB 作为存储：

```bash
# 1. 启动 SeekDB 服务（本地或 Docker）
docker run -d -p 6432:6432 seekdb/seekdb:latest

# 2. 启动 SkillPilot 时会自动初始化数据库表
# 表结构：
# - skills: 技能元数据
# - skill_vectors: 技能向量嵌入
# - users: 用户数据
# - orchestration_plans: 推荐计划
```

---

## 常见问题

### Q: 如何添加新的技能？

```python
# 通过 API 创建
curl -X POST "http://localhost:8000/api/v1/skills" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "skill_name": "My Custom Skill",
    "platform": "custom",
    "description": "技能描述",
    "capabilities": ["capability1", "capability2"],
    "tags": ["tag1", "tag2"]
  }'
```

### Q: 没有 OpenAI API Key 能用吗？

可以使用本地 Embedding 模型：

```ini
# .env 配置
EMBEDDING_PROVIDER=local
```

```bash
# 安装本地 Embedding 依赖
pip install sentence-transformers
```

### Q: 如何部署到生产环境？

```bash
# 使用 Gunicorn + Uvicorn
pip install gunicorn

gunicorn skillpilot.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## 联系支持

- GitHub Issues: https://github.com/wayyoungboy/SkillPilot/issues
- Email: wayyoungboy@gmail.com
