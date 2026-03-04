# SkillPilot 快速参考

## 启动服务

```bash
# 1. 激活环境
source .venv/bin/activate

# 2. 配置 .env 文件（确保有 OPENAI_API_KEY）

# 3. 启动
uvicorn skillpilot.main:app --reload --port 8000
```

## API Endpoints

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/skills/search?q=xxx` | 语义搜索技能 |
| POST | `/recommendations/analyze?task_description=xxx` | 分析任务需求 |
| POST | `/recommendations/skills?task_description=xxx` | 推荐技能 |
| POST | `/recommendations/chain` | 生成技能链（JSON body） |
| GET | `/recommendations/plans` | 查看历史推荐 |

## Python 调用示例

```python
import httpx

# 搜索技能
r = httpx.get("http://localhost:8000/api/v1/skills/search",
              params={"q": "代码审查"},
              headers={"Authorization": "Bearer TOKEN"})
skills = r.json()

# 推荐技能
r = httpx.post("http://localhost:8000/api/v1/recommendations/skills",
               params={"task_description": "数据分析"},
               headers={"Authorization": "Bearer TOKEN"})
recs = r.json()
```

## 在 Claude 中使用

**方式 1：直接 API 调用**
```python
# 在 Claude Code 中
import httpx
skills = httpx.get("http://localhost:8000/api/v1/skills/search?q=数据分析").json()
```

**方式 2：创建 Tool**
```python
from langchain.tools import Tool

skill_search = Tool(
    name="SkillPilot",
    func=lambda q: httpx.get(
        "http://localhost:8000/api/v1/skills/search",
        params={"q": q}
    ).text,
    description="搜索 AI 技能，例如'代码审查'、'数据分析'、'翻译'"
)
```

## 配置 (.env)

```ini
# 必需
SEEKDB_URL=seekdb://localhost:6432
OPENAI_API_KEY=sk-...

# 可选
EMBEDDING_PROVIDER=openai  # 或 local
LLM_PROVIDER=openai        # 或 anthropic
```

## 测试

```bash
# 运行测试
pytest skillpilot/tests/

# 代码检查
ruff check skillpilot/
ruff format skillpilot/
```
