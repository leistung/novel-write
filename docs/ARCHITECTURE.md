# 🏗️ 架构设计

本文档介绍 NovelWrite AI 的系统架构和组件设计。

## 目录

- [系统概览](#系统概览)
- [核心组件](#核心组件)
- [数据流](#数据流)
- [Agent设计](#agent设计)
- [Skill系统](#skill系统)
- [工作流引擎](#工作流引擎)
- [Orchestrator编排层](#orchestrator编排层)
- [存储层](#存储层)

## 系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                │
│                    (React + Ant Design)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                         Backend                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   API路由    │  │ Orchestrator│  │    Workflow Engine      │ │
│  │  (FastAPI)   │  │  (编排层)    │  │      (工作流)            │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                     │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌───────────▼─────────────┐ │
│  │    Books    │  │  Architect  │  │      Writer             │ │
│  │   Chapters  │  │    Agent    │  │      Agent              │ │
│  │    Skills   │  │  (大纲设计)  │  │    (章节写作)            │ │
│  │  Checkpoints│  └─────────────┘  └─────────────────────────┘ │
│  └─────────────┘         │                     │               │
│                          │        ┌────────────▼─────────────┐ │
│                          │        │       Auditor            │ │
│                          │        │       Agent              │ │
│                          │        │    (质量审核)             │ │
│                          │        └────────────┬─────────────┘ │
│                          │                     │               │
│                          │        ┌────────────▼─────────────┐ │
│                          │        │    Continuity            │ │
│                          │        │       Agent              │ │
│                          │        │   (连续性检查)            │ │
│                          │        └──────────────────────────┘ │
│                          │                                     │
│  ┌───────────────────────▼───────────────────────────────────┐ │
│  │                    Skill Loader                            │ │
│  │              (26种小说类型知识库)                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                         Storage                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  SQLite     │  │   Store     │  │      Checkpoint         │ │
│  │  (数据库)    │  │  (文件系统)  │  │       (状态)             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. API路由层 (FastAPI)

负责HTTP请求处理和路由分发：

| 路由模块 | 功能 |
|---------|------|
| `books.py` | 书籍CRUD、大纲文件管理 |
| `chapters.py` | 章节CRUD |
| `workflows.py` | 工作流管理（启动、暂停、恢复） |
| `checkpoints.py` | Checkpoint节点状态查询 |
| `skills.py` | Skill管理、类型列表 |
| `orchestrator.py` | 智能编排API |

### 2. Orchestrator编排层

系统的智能调度中心：

```
┌─────────────────────────────────────────┐
│           NovelOrchestrator             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      OrchestratorService        │   │
│  │  - generate_outline()           │   │
│  │  - write_chapter()              │   │
│  │  - continue_chapters()          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      OrchestratorStrategy       │   │
│  │  - QualityThresholdStrategy     │   │
│  │  - ConsistencyStrategy          │   │
│  │  - ProgressStrategy             │   │
│  │  - CompositeStrategy            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         BookContext             │   │
│  │  - 角色管理                      │   │
│  │  - 伏笔追踪                      │   │
│  │  - 章节历史                      │   │
│  │  - 状态共享                      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 3. Agent层

4个专业Agent，每个都有特定的职责：

#### Architect Agent (架构师)

```python
class ArchitectAgent:
    # 核心方法
    generate_foundation()     # 生成完整大纲体系
    plan_chapter()            # 规划单章内容
    analyze_outline_impact()  # 分析大纲变动影响
    update_book_state()       # 更新书籍状态
```

**职责**：
- 设计世界观、角色、剧情结构
- 规划每章的内容要点
- 管理伏笔和角色关系
- 维护书籍整体一致性

#### Writer Agent (作家)

```python
class WriterAgent:
    # 核心方法
    write_chapter()      # 撰写章节
    rewrite_chapter()    # 重写章节
    expand_outline()     # 扩写大纲为章节规划
```

**职责**：
- 根据规划撰写章节内容
- 控制字数和节奏
- 保持文风一致
- 处理重写需求

#### Auditor Agent (审核员)

```python
class AuditorAgent:
    # 核心方法
    audit_chapter()      # 审核单章
    audit_book()         # 审核整本书
    compare_versions()   # 比较版本
```

**职责**：
- 评估章节质量（剧情、角色、文笔、爽点）
- 给出改进建议
- 打分并判断是否通过

#### Continuity Auditor (连续性审核员)

```python
class ContinuityAuditor:
    # 核心方法
    check_continuity()           # 检查连续性
    check_character_consistency() # 检查角色一致性
```

**职责**：
- 检查时间线一致性
- 验证角色行为一致性
- 追踪伏笔回收情况
- 检测设定矛盾

### 4. Skill系统

26种小说类型知识库：

```
skills/
├── xuanhuan-novelist/          # 玄幻
│   ├── SKILL.md                # 核心Skill文件
│   └── references/
│       └── research/
│           ├── 01-writings.md      # 著作研究
│           ├── 02-conversations.md # 对话风格
│           ├── 03-expression-dna.md # 表达DNA
│           ├── 04-external-views.md # 外部视角
│           ├── 05-decisions.md     # 决策启发式
│           └── 06-timeline.md      # 时间线
├── qihuan-novelist/            # 奇幻
├── wuxia-novelist/             # 武侠
├── ... (共26个)
```

**Skill调用机制**：

```python
# 1. 根据genre加载对应Skill
skill_content = skill_loader.load_skill_content("xuanhuan")

# 2. 提取核心智模型、表达DNA、决策启发式
prompt_suffix = skill_loader.get_skill_prompt_suffix("xuanhuan")

# 3. 注入到Agent的system_prompt
system_prompt = base_prompt + "\n\n## 题材专家知识库\n" + prompt_suffix
```

## 数据流

### 创作流程数据流

```
1. 创建书籍
   User → POST /books → Database
   
2. 生成大纲
   User → POST /orchestrator/generate-outline
        → OrchestratorService
        → ArchitectAgent.generate_foundation()
        → LLM API
        → Database + Store
        → Response
   
3. 续写章节
   User → POST /orchestrator/write-chapter
        → OrchestratorService
        → ArchitectAgent.plan_chapter()
        → WriterAgent.write_chapter()
        → AuditorAgent.audit_chapter()
        → [Decision: pass/rewrite]
        → ContinuityAuditor.check_continuity()
        → [Decision: pass/adjust]
        → Database + Store
        → Response
```

### 工作流状态流转

```
pending → running → [completed/failed/paused]
                    ↓
              [retry/resume]
```

## Agent设计

### BaseAgent

所有Agent的基类：

```python
class BaseAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def execute(self, task: str, **kwargs) -> AgentResult:
        # 统一执行入口
        method = getattr(self, task)
        return await method(**kwargs)
    
    def _build_system_prompt(self, base_prompt: str, genre: str = None) -> str:
        # 注入Skill知识
        if genre:
            suffix = skill_loader.get_skill_prompt_suffix(genre)
            return base_prompt + "\n\n## 题材专家知识库\n" + suffix
        return base_prompt
```

### Agent执行流程

```
Agent.execute(task, **kwargs)
    ↓
获取对应方法 (getattr)
    ↓
构建system_prompt (注入Skill)
    ↓
调用LLM API
    ↓
解析输出
    ↓
返回 AgentResult(ok, data, feedback)
```

## Skill系统

### Skill文件结构

每个Skill包含：

| 文件 | 内容 |
|------|------|
| `SKILL.md` | 核心Skill定义（角色扮演规则、核心智模型、决策启发式、表达DNA等） |
| `01-writings.md` | 该类型经典著作分析 |
| `02-conversations.md` | 对话风格研究 |
| `03-expression-dna.md` | 表达DNA（句式、节奏、修辞） |
| `04-external-views.md` | 外部视角（读者期待、市场分析） |
| `05-decisions.md` | 决策启发式（何时转折、何时高潮） |
| `06-timeline.md` | 该类型发展历程 |

### Skill内容示例（玄幻）

```markdown
---
name: xuanhuan-novelist
description: 玄幻小说创作专家
---

## 角色扮演规则

你是一位拥有20年经验的玄幻小说大神作家...

## 核心智模型

### 1. 修炼体系金字塔模型
- 底层：基础功法（炼气、筑基）
- 中层：进阶功法（金丹、元婴）
- 顶层：绝世功法（化神、渡劫）

### 2. 爽点节奏模型
- 压抑期：30%（主角受辱/困境）
- 爆发期：20%（打脸/突破）
- 收获期：30%（奖励/成长）
- 铺垫期：20%（新目标/新冲突）

## 决策启发式

- IF 主角连续3章没有成长 THEN 安排突破或获得宝物
- IF 反派压迫感不足 THEN 增加实力差距或伤害主角亲友
```

## 工作流引擎

### 工作流定义

6个工作流覆盖完整创作周期：

| 工作流 | 节点数 | 功能 |
|--------|--------|------|
| `generate-outline` | 1 | 生成完整大纲体系 |
| `continue-chapters` | 4×N | 续写N章（规划→写作→审核→连续性） |
| `rewrite-chapter` | 2 | 重写章节（写作→审核） |
| `protect-and-update` | 2 | 保护章节并更新大纲 |
| `extract-outline` | 1 | 从已有章节提取大纲 |
| `expand-skill` | 1 | 扩写大纲为章节规划 |

### Checkpoint机制

Dify风格的节点状态追踪：

```python
class CheckpointManager:
    def start_workflow(self, workflow_id)
    def start_node(self, workflow_id, node_id, node_name)
    def complete_node(self, workflow_id, node_id, output_data)
    def fail_node(self, workflow_id, node_id, error_message)
    def get_workflow_status(self, workflow_id)
```

每个节点记录：
- 状态：pending/running/completed/failed/skipped
- 输入/输出数据
- 开始/完成时间
- 执行时长
- Token消耗

## Orchestrator编排层

### 调度策略

```python
class OrchestratorStrategy:
    # 质量阈值策略
    def should_audit_rewrite(score: float, threshold: float = 70.0) -> bool
    
    # 连续性策略
    def should_adjust_for_consistency(issues: List[str]) -> Decision
    
    # 进度策略
    def get_chapter_type(chapter_num: int, total: int) -> str
```

### 决策流程

```
Writer写章节
    ↓
Auditor审核
    ↓
IF score < 70 THEN
    IF rewrite_count < 3 THEN
        重写
    ELSE
        标记人工介入
ELSE
    通过
    ↓
Continuity检查
    ↓
IF 有问题 THEN
    记录问题
    IF 问题严重 THEN
        调整大纲
ELSE
    通过
    ↓
保存章节
```

## 存储层

### 数据库存储

SQLite + SQLAlchemy：

| 表 | 用途 |
|---|------|
| `books` | 书籍基本信息 |
| `chapters` | 章节内容、审核分数 |
| `workflow_executions` | 工作流执行记录 |
| `workflow_nodes` | 工作流节点状态 |
| `skill_templates` | Skill模板（可选） |

### 文件系统存储

```
store/
├── books/
│   └── {book_id}/
│       ├── chapters/
│       │   └── {chapter_num}.md
│       ├── state/
│       │   ├── worldview.md
│       │   ├── character_profiles.md
│       │   ├── power_system.md
│       │   ├── story_structure.md
│       │   ├── volume_outline.md
│       │   ├── chapter_plan.md
│       │   ├── subplot_board.md
│       │   ├── foreshadowing.md
│       │   └── writing_style.md
│       └── locks/
│           └── {lock_name}.json
```

### 锁机制

防止并发冲突：

```python
class StoreManager:
    async def acquire_lock(book_id, lock_name, timeout=300)
    async def release_lock(book_id, lock_name)
    async def is_locked(book_id, lock_name)
```

锁类型：
- `generate_outline` - 生成大纲
- `continue_chapter_{n}` - 续写第n章
- `protect_and_update` - 保护更新
- `extract_outline` - 提取大纲
- `expand_skill` - 扩写Skill
