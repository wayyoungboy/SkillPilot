# SkillPilot 导入器指南

## 概述

SkillPilot 支持从多个 AI 平台导入 Skills，使用插件化架构。每个平台有一个独立的导入器。

---

## 支持的导入器

| 平台 | 状态 | 需要配置 | SDK |
|------|------|----------|-----|
| Coze | ✅ 已实现 | API Key | `coze` |
| Dify | ✅ 已实现 | API Key | `dify-client` |
| GPT Store | ✅ 已实现 | 无 | 第三方目录 |
| Hugging Face Spaces | ✅ 已实现 | 无 | `huggingface_hub` |

---

## 安装导入器依赖

```bash
# 安装所有导入器
pip install -e ".[import-all]"

# 或单独安装
pip install coze           # Coze 导入器
pip install dify-client    # Dify 导入器
pip install huggingface_hub  # Hugging Face 导入器
```

---

## 使用方法

### 方法 1: 命令行工具

```bash
# 查看可用导入器
python -m scripts.import_skills --list

# 查看配置帮助
python -m scripts.import_skills --help-config coze

# 从 Coze 导入
python -m scripts.import_skills \
  --platform coze \
  --api-key YOUR_COZE_KEY \
  --workspace-id WORKSPACE_ID \
  --limit 50

# 从 Dify 导入
python -m scripts.import_skills \
  --platform dify \
  --api-key YOUR_DIFY_KEY \
  --app-ids app1,app2,app3

# 从 Hugging Face 导入（无需配置）
python -m scripts.import_skills \
  --platform huggingface \
  --limit 100 \
  --sdk gradio

# 从 GPT Store 导入（无需配置）
python -m scripts.import_skills \
  --platform gptstore \
  --limit 50

# 从所有平台导入
python -m scripts.import_skills \
  --all \
  --limit 25
```

### 方法 2: Python 代码

```python
import asyncio
from skillpilot.core.importers.registry import load_all_importers
from skillpilot.core.importers import get_importer
from skillpilot.core.services.skill import skill_service
from skillpilot.db.seekdb import seekdb_client

async def import_skills():
    # 加载所有导入器
    load_all_importers()

    # 获取 Coze 导入器
    importer = get_importer("coze")

    # 配置
    importer.configure(
        api_key="your-coze-api-key",
        workspace_id="your-workspace-id"
    )

    # 连接数据库
    seekdb_client.connect()

    try:
        # 导入技能
        summary = await importer.import_skills(
            skill_service=skill_service,
            limit=100,
            developer_id="system"
        )

        print(f"导入完成：成功 {summary.success}, 失败 {summary.failed}")

    finally:
        seekdb_client.close()

asyncio.run(import_skills())
```

---

## 平台配置说明

### Coze

```bash
# 必需配置
--api-key YOUR_COZE_KEY

# 可选配置
--workspace-id WORKSPACE_ID  # 从指定工作空间导入
```

**配置帮助：**
```
Coze Importer Configuration:
  - api_key: Coze API key (required)
  - workspace_id: Coze workspace ID (optional, for workspace bots)
```

### Dify

```bash
# 必需配置
--api-key YOUR_DIFY_KEY

# 可选配置
--api-base https://api.dify.ai/v1  # API 基础 URL
--app-ids app1,app2,app3           # 指定要导入的 App IDs
--workspace-id WORKSPACE_ID        # 从指定工作空间导入
```

**配置帮助：**
```
Dify Importer Configuration:
  - api_key: Dify API key (required)
  - api_base: Dify API base URL (default: https://api.dify.ai/v1)
  - app_ids: List of specific app IDs to import (optional)
  - workspace_id: Dify workspace ID (optional)
```

### GPT Store

无需配置，使用第三方目录（gpts24.com, allgpts.io）。

```bash
# 直接运行
python -m scripts.import_skills --platform gptstore --limit 50
```

**注意：** HTML 爬取功能可能受网站结构变化影响。

### Hugging Face Spaces

无需配置，支持匿名访问。

```bash
# 基本使用
python -m scripts.import_skills --platform huggingface --limit 100

# 按 SDK 筛选
python -m scripts.import_skills --platform huggingface --limit 50 --sdk gradio

# 获取详细信息
python -m scripts.import_skills --platform huggingface --limit 20 --fetch-details
```

**配置选项：**
- `limit`: 最大空间数（默认：100）
- `sort`: 排序字段（默认：likes）
- `sdk`: 按 SDK 筛选（gradio/streamlit/docker）
- `fetch_details`: 获取详细信息（默认：False）

---

## 自定义导入器

创建新的导入器只需继承 `BaseImporter`：

```python
# skillpilot/core/importers/myplatform.py
from skillpilot.core.importers.base import BaseImporter
from skillpilot.core.models.skill import SkillCreate
from skillpilot.core.models.common import PlatformType

class MyPlatformImporter(BaseImporter):
    platform = "myplatform"
    display_name = "My Platform"
    requires_config = True

    async def fetch_skills(self) -> list[dict]:
        # 实现获取技能的逻辑
        return [...]

    def normalize_skill(self, raw_data: dict) -> SkillCreate:
        # 实现数据标准化
        return SkillCreate(
            skill_name=raw_data["name"],
            platform=PlatformType.CUSTOM,
            description=raw_data["description"],
            capabilities=raw_data.get("tags", []),
        )
```

然后在 `registry.py` 中注册：

```python
from skillpilot.core.importers.mycustom import MyPlatformImporter
register_importer(MyPlatformImporter())
```

---

## 故障排除

### 导入速度慢

导入器会记录详细日志。设置环境变量查看：

```bash
LOG_LEVEL=DEBUG python -m scripts.import_skills --platform coze --api-key ...
```

### API 限流

导入器内置速率限制。如需调整，修改导入器代码中的 `sleep` 时间。

### 数据库连接失败

确保 SeekDB 服务运行：

```bash
# 检查 SeekDB 连接
docker ps | grep seekdb
```

### 导入的技能重复

导入器会尝试去重（基于名称/ID）。如需完全去重，先清空 skills 表：

```sql
-- SeekDB 中执行
DELETE FROM skills;
DELETE FROM skill_vectors;
```

---

## API Key 获取

### Coze API Key

1. 访问 https://www.coze.com
2. 进入 Settings → API
3. 创建新的 API Key

### Dify API Key

1. 访问 https://dify.ai 或你的自托管实例
2. 进入 Settings → API Keys
3. 创建新的 API Key

---

## 统计数据

导入完成后查看统计：

```bash
# 使用 API 查看技能总数
curl http://localhost:8000/api/v1/skills?limit=1 | jq '.pagination.total'
```

---

## 贡献新的导入器

欢迎贡献新平台的导入器！请确保：

1. 继承 `BaseImporter` 类
2. 实现 `fetch_skills()` 和 `normalize_skill()` 方法
3. 添加测试用例
4. 更新本文档
