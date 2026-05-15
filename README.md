# NovelWrite - AI驱动的网络小说创作系统

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal.svg)
![React](https://img.shields.io/badge/React-18.2-blue.svg)

**一个企业级的AI小说创作平台，支持多种题材、智能大纲生成、章节续写、内容审核等功能**

</div>

---

## 📖 目录

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [核心模块](#核心模块)
- [快速开始](#快速开始)
- [API文档](#api文档)
- [配置说明](#配置说明)
- [开发指南](#开发指南)

---

## 项目概述

NovelWrite 是一个基于大语言模型（LLM）的网络小说创作辅助系统，旨在帮助作者：

- 🎯 **智能大纲生成** - 根据题材和创意自动生成世界观、人物设定、剧情大纲
- ✍️ **章节续写** - 基于大纲和前文自动续写章节，保持剧情连贯性
- 🔍 **内容审核** - 自动审核章节质量、检查剧情连续性
- 📚 **题材专家** - 内置25种题材技能包（玄幻、仙侠、都市、科幻等）
- 🔄 **工作流管理** - 支持断点续写、暂停恢复、进度追踪

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React + Ant Design)                 │
│                     http://localhost:5173                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                              │
│                     http://localhost:8000                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  API     │  │ Workflow │  │  Agent   │  │  Prompts │        │
│  │ Routes   │→ │ Engine   │→ │ System   │→ │ Templates│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
        │                │                │
        ▼                ▼                ▼
┌───────────┐   ┌───────────┐   ┌───────────────────┐
│ PostgreSQL│   │   Redis   │   │  LLM API          │
│  数据库   │   │ 队列/缓存 │   │ OpenAI/Anthropic  │
└───────────┘   └───────────┘   └───────────────────┘
```

### 请求流程

```
用户请求 → API路由 → Celery异步任务 → 工作流引擎 → Agent执行 → LLM生成 → 结果返回
                ↓
         WebSocket实时推送进度
```

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.109 | Web框架 |
| SQLAlchemy | 2.0 | ORM |
| Celery | - | 异步任务队列 |
| Redis | 7 | 缓存/消息队列 |
| PostgreSQL | 15 | 主数据库 |
| OpenAI SDK | 1.10 | LLM调用 |
| ChromaDB | 0.4 | 向量数据库 |
| Jinja2 | 3.1 | 模板渲染 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2 | UI框架 |
| TypeScript | 5.3 | 类型安全 |
| Ant Design | 5.13 | UI组件库 |
| Vite | 5.0 | 构建工具 |
| Axios | 1.6 | HTTP客户端 |

---

## 核心模块

### 1. Agent 系统 (`backend/agents/`)

Agent 是系统的核心执行单元，每个 Agent 负责特定任务：

```
agents/
├── base.py          # Agent基类，提供LLM调用和提示词渲染
├── architect.py     # 架构师Agent - 大纲生成、章节规划、状态更新
├── writer.py        # 写手Agent - 章节撰写、重写、大纲扩写
├── auditor.py       # 审核Agent - 内容质量评分
└── continuity.py    # 连续性Agent - 剧情连贯性检查
```

**Agent 职责划分**：

| Agent | 职责 | 主要方法 |
|-------|------|----------|
| ArchitectAgent | 整体架构规划 | `generate_foundation`, `plan_chapter`, `analyze_outline_impact`, `update_book_state` |
| WriterAgent | 内容创作 | `write_chapter`, `rewrite_chapter`, `expand_outline` |
| AuditorAgent | 质量审核 | `audit_chapter`, `score_chapter` |
| ContinuityAuditor | 连续性检查 | `check_continuity` |

### 2. 提示词系统 (`backend/prompts/`)

企业级提示词工程框架，支持：

- **YAML模板** - 提示词与代码分离，易于维护
- **Jinja2渲染** - 动态变量替换
- **版本控制** - 支持多版本提示词管理
- **输入净化** - 防止Prompt注入攻击
- **输出验证** - JSON Schema验证

```
prompts/
├── templates/           # YAML模板文件
│   ├── architect/       # 架构师提示词
│   │   ├── foundation.yaml
│   │   ├── plan_chapter.yaml
│   │   ├── analyze_impact.yaml
│   │   └── update_state.yaml
│   ├── writer/          # 写手提示词
│   │   ├── chapter.yaml
│   │   ├── rewrite.yaml
│   │   └── expand_outline.yaml
│   └── auditor/         # 审核提示词
│       └── review.yaml
├── registry/            # 提示词注册中心
├── renderer/            # Jinja2渲染器
├── security/            # 输入净化
├── schemas/             # 输出验证
└── loader.py            # 简化加载接口
```

**使用示例**：

```python
from prompts.loader import render_prompt

system_prompt, user_prompt = render_prompt("architect/foundation", {
    "genre": "玄幻",
    "theme": "修仙"
})
```

### 3. 工作流引擎 (`backend/workflow/`)

协调多个 Agent 完成复杂任务：

```
workflow/
└── engine.py           # 工作流引擎
```

**支持的工作流**：

| 工作流 | 功能 | API端点 |
|--------|------|---------|
| `run_generate_outline` | 生成基础设定 | `POST /api/v1/workflows/generate-outline` |
| `run_continue_chapters` | 批量续写章节 | `POST /api/v1/workflows/continue-chapters` |
| `run_rewrite_chapter` | 重写单章 | `POST /api/v1/workflows/rewrite-chapter` |
| `run_protect_and_update` | 保护章节更新大纲 | `POST /api/v1/workflows/protect-and-update` |
| `run_extract_outline` | 从已有内容提取大纲 | `POST /api/v1/workflows/extract-outline` |
| `run_expand_skill` | 扩写大纲为章节规划 | `POST /api/v1/workflows/expand-skill` |

### 4. 题材技能包 (`skills/`)

内置 25 种题材专家知识：

```
skills/
├── xuanhuan-novelist/          # 玄幻
├── xianxia-novelist/           # 仙侠
├── wuxia-novelist/             # 武侠
├── urban-novelist/             # 都市
├── scifi-novelist/             # 科幻
├── historical-novelist/        # 历史
├── game-novelist/              # 游戏
├── ancient-romance-novelist/   # 古代言情
├── modern-romance-novelist/    # 现代言情
└── ...                         # 更多题材
```

每个技能包包含：
- 核心智模型（题材特征）
- 表达DNA（文风指导）
- 决策启发式（创作规则）

### 5. 数据模型 (`backend/db/`)

```
db/
├── models.py           # SQLAlchemy模型定义
├── database.py         # 数据库连接管理
└── crud.py             # CRUD操作
```

**核心数据表**：

| 表名 | 说明 |
|------|------|
| `books` | 书籍主表 |
| `chapters` | 章节表 |
| `book_outlines` | 大纲版本表 |
| `book_states` | 动态状态表 |
| `story_hooks` | 伏笔追踪表 |
| `characters` | 角色表 |
| `workflow_executions` | 工作流执行记录 |
| `workflow_nodes` | 节点执行记录 |
| `checkpoints` | 检查点表 |

---

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+ (或使用 Docker)
- Redis 7+ (或使用 Docker)

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-repo/novel-write.git
cd novel-write

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 填入 OPENAI_API_KEY

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

访问：
- 前端：http://localhost
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 方式二：本地开发

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 启动后端
python run.py

# 前端（新终端）
cd frontend
npm install
npm run dev
```

---

## API文档

### 核心接口

#### 书籍管理

```http
# 创建书籍
POST /api/v1/books
{
  "title": "我的玄幻小说",
  "genre": "玄幻",
  "platform": "起点",
  "chapter_words": 3000,
  "target_chapters": 100
}

# 获取书籍列表
GET /api/v1/books

# 获取书籍详情
GET /api/v1/books/{book_id}
```

#### 工作流

```http
# 生成大纲
POST /api/v1/workflows/generate-outline
{
  "book_id": 1
}

# 续写章节
POST /api/v1/workflows/continue-chapters
{
  "book_id": 1,
  "start_chapter": 1,
  "count": 5,
  "external_context": ""
}

# 重写章节
POST /api/v1/workflows/rewrite-chapter
{
  "book_id": 1,
  "chapter_num": 3,
  "rewrite_requirements": "增加主角内心戏",
  "keep_plot": true
}

# 查询工作流状态
GET /api/v1/workflows/{workflow_id}/status

# 暂停工作流
POST /api/v1/workflows/{workflow_id}/pause

# 恢复工作流
POST /api/v1/workflows/{workflow_id}/resume
```

#### WebSocket 实时进度

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflow/{workflow_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度:', data.progress);
};
```

---

## 配置说明

### 环境变量 (`backend/.env`)

```bash
# 应用配置
APP_NAME=NovelWrite
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/novel_write

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# LLM配置
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 安全
SECRET_KEY=your-secret-key
```

---

## 开发指南

### 项目结构

```
novel-write/
├── backend/                # 后端代码
│   ├── agents/             # Agent系统
│   ├── api/                # FastAPI路由
│   │   └── routes/         # 各模块路由
│   ├── checkpoint/         # 检查点管理
│   ├── config/             # 配置管理
│   ├── core/               # 核心工具（异常、响应）
│   ├── db/                 # 数据库模型和CRUD
│   ├── llm/                # LLM客户端
│   ├── prompts/            # 提示词工程系统
│   ├── skills/             # 题材技能加载器
│   ├── store/              # 文件存储管理
│   ├── tasks/              # Celery异步任务
│   ├── utils/              # 工具函数
│   └── workflow/           # 工作流引擎
├── frontend/               # 前端代码
│   └── src/
│       ├── App.tsx         # 主应用
│       └── main.tsx        # 入口
├── skills/                 # 题材技能包（25种）
├── docs/                   # 文档
├── docker-compose.yml      # Docker编排
├── Dockerfile.backend      # 后端镜像
└── Dockerfile.frontend     # 前端镜像
```

### 添加新题材

1. 在 `skills/` 目录创建新文件夹：
```bash
mkdir skills/new-genre-novelist
```

2. 创建 `SKILL.md` 文件：
```markdown
# 新题材专家

## 核心智模型
[题材特征描述]

## 表达DNA
[文风指导]

## 决策启发式
[创作规则]
```

3. 在 `skills/loader.py` 的 `GENRE_TO_SKILL_MAP` 中添加映射：
```python
"new_genre": "new-genre-novelist",
```

### 添加新提示词

1. 在 `prompts/templates/` 创建 YAML 文件：
```yaml
name: agent/new_prompt
version: "1.0.0"
description: 新提示词描述

parameters:
  param1:
    type: string
    required: true

system_template: |
  系统提示词内容

user_template: |
  用户提示词 {{ param1 }}

activate: true
```

2. 在 Agent 中使用：
```python
system, user = self._render_prompt("agent/new_prompt", {"param1": "value"})
```

### 运行测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端测试
cd frontend
npm run test
```

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！
