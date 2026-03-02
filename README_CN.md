# SkillPilot

[![CI](https://github.com/wayyoungboy/SkillPilot/actions/workflows/ci.yml/badge.svg)](https://github.com/wayyoungboy/SkillPilot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**基于 SeekDB 的 AI 技能编排引擎**

[English README](README.md) | 中文文档

---

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- SeekDB (本地或远程服务)

### 安装

```bash
# 克隆项目
git clone git@github.com:wayyoungboy/SkillPilot.git
cd SkillPilot

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 配置

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，配置 SeekDB 连接地址
```

### 运行

```bash
# 启动服务
uvicorn skillpilot.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

### 测试

```bash
# 运行所有测试
pytest skillpilot/tests/ -v

# 运行测试并生成覆盖率报告
pytest skillpilot/tests/ --cov=skillpilot --cov-report=html
```

---

## 核心特性

- **SeekDB 作为唯一存储** - 使用 SeekDB 同时作为向量数据库和关系型数据库，简化技术栈
- **技能统一管理** - 支持多平台技能的统一存储、搜索和管理
- **智能编排引擎** - 基于自然语言任务描述，自动生成技能执行链
- **完整的 RESTful API** - 支持技能管理、用户认证、任务编排
- **高测试覆盖** - 54+ 单元测试和集成测试，确保代码质量

---

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                  SkillPilot 应用层                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Web 前端     │  │ API 服务     │  │ SDK          ││
│  │ (待实现)     │  │ (FastAPI)    │  │ (Python)     ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│              SkillPilot 业务逻辑层                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ 技能搜索     │  │ 技能编排     │  │ 用户认证     ││
│  │ 引擎         │  │ 引擎         │  │ 服务         ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
└────────────────────┬────────────────────────────────┘
                     │ SeekDB Client
┌────────────────────▼────────────────────────────────┐
│         SeekDB 存储引擎 (唯一存储基建)               │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ 向量检索引擎 │  │ 关系存储引擎 │                 │
│  │ - 技能向量   │  │ - 用户数据   │                 │
│  │ - 任务向量   │  │ - 技能数据   │                 │
│  │ - HNSW 索引  │  │ - 编排计划   │                 │
│  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────┘
```

---

## 项目结构

```
SkillPilot/
├── skillpilot/                 # 主程序目录
│   ├── api/routes/          # API 路由层
│   │   ├── auth.py          # 认证路由
│   │   ├── skill.py         # 技能管理路由
│   │   └── orchestration.py # 编排路由
│   ├── core/
│   │   ├── models/          # 数据模型层
│   │   │   ├── common.py    # 通用模型和枚举
│   │   │   ├── user.py      # 用户模型
│   │   │   ├── skill.py     # 技能模型
│   │   │   ├── orchestration.py # 编排模型
│   │   │   └── auth.py      # 认证模型
│   │   ├── services/        # 业务服务层
│   │   │   ├── auth.py      # 认证服务
│   │   │   ├── skill.py     # 技能服务
│   │   │   └── orchestration.py # 编排服务
│   │   └── config.py        # 配置管理
│   ├── db/
│   │   └── seekdb.py        # SeekDB 数据库连接
│   ├── tests/
│   │   ├── unit/            # 单元测试
│   │   └── integration/     # 集成测试
│   └── main.py              # 应用入口
├── .github/workflows/       # GitHub Actions 配置
├── pyproject.toml           # 项目配置
├── .gitignore               # Git 忽略文件
├── README.md                # 英文文档
├── README_CN.md             # 中文文档
└── .env.example             # 环境变量示例
```

---

## API 接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/refresh | 刷新 Token |

### 技能管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/skills | 获取技能列表 |
| GET | /api/v1/skills/{skill_id} | 获取技能详情 |
| POST | /api/v1/skills | 创建技能 |
| PUT | /api/v1/skills/{skill_id} | 更新技能 |
| DELETE | /api/v1/skills/{skill_id} | 删除技能 |
| GET | /api/v1/skills/search | 搜索技能 |

### 技能编排

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/orchestrations | 创建编排任务 |
| GET | /api/v1/orchestrations | 获取编排列表 |
| GET | /api/v1/orchestrations/{plan_id} | 获取编排详情 |
| POST | /api/v1/orchestrations/{plan_id}/execute | 执行编排 |
| DELETE | /api/v1/orchestrations/{plan_id} | 取消编排 |

---

## 数据模型

### SeekDB 表结构

项目使用 SeekDB 作为唯一存储，定义以下数据表：

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| `skills` | 技能目录 | skill_id, skill_name, platform, description, capabilities, rating, pricing |
| `skill_vectors` | 技能向量 | skill_id, skill_vector, capability_vectors |
| `users` | 用户数据 | user_id, email, password_hash, name, role |
| `orchestration_plans` | 编排计划 | plan_id, task_description, skill_chain, status |
| `task_vectors` | 任务向量 | task_id, task_description, task_vector, required_capabilities |

### 向量索引配置

```python
# HNSW 向量索引配置
index_type: hnsw
m: 16
ef_construction: 200
vector_dimension: 1536
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SEEKDB_URL | SeekDB 连接地址 | seekdb://localhost:6432 |
| SEEKDB_VECTOR_DIMENSION | 向量维度 | 1536 |
| SEEKDB_INDEX_TYPE | 索引类型 | hnsw |
| SEEKDB_HNSW_M | HNSW M 参数 | 16 |
| SEEKDB_HNSW_EF_CONSTRUCTION | HNSW ef_construction | 200 |
| JWT_SECRET_KEY | JWT 密钥 | (需自定义) |
| JWT_ALGORITHM | JWT 算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌过期时间 (分钟) | 15 |
| REFRESH_TOKEN_EXPIRE_DAYS | 刷新令牌过期时间 (天) | 7 |
| DEBUG | 调试模式 | false |

---

## 开发指南

### 代码风格

项目使用 Ruff 进行代码检查和格式化：

```bash
# 检查代码
ruff check skillpilot/

# 格式化代码
ruff format skillpilot/
```

### 添加新功能

1. 在对应模块添加模型定义 (`skillpilot/core/models/`)
2. 实现业务逻辑 (`skillpilot/core/services/`)
3. 添加 API 路由 (`skillpilot/api/routes/`)
4. 编写测试用例 (`skillpilot/tests/`)

---

## 路线图

- [ ] SeekDB 向量检索完整实现
- [ ] 跨平台技能适配器 (Coze, Dify, LangChain 等)
- [ ] AI 智能编排引擎（集成 LLM）
- [ ] 技能使用统计和分析
- [ ] Web 管理界面
- [ ] Python SDK
- [ ] 多平台自动发布功能

---

## 常见问题

### SeekDB 是什么？

SeekDB 是一个支持向量检索的数据库，同时提供关系型存储能力。本项目使用 SeekDB 作为唯一的存储基建，简化了技术栈。

### 如何配置 SeekDB？

1. 安装 SeekDB 服务
2. 修改 `.env` 文件中的 `SEEKDB_URL` 配置
3. 启动应用时会自动创建表结构和索引

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

MIT License

---

## 联系方式

- GitHub: [@wayyoungboy](https://github.com/wayyoungboy/SkillPilot)
- Email: wayyoungboy@gmail.com
