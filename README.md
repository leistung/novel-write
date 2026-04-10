# novel-write - AI 小说写作助手

一个基于LangChain和LangGraph的智能小说写作系统，通过多Agent协作完成小说的创作、续写、重写和审核等任务。

## 📋 项目概述

novel-write 是一个功能强大的AI小说写作助手，它利用LangChain和LangGraph框架实现多个专业Agent（架构师、写手、连续性检查器、审核编辑）的协同工作，帮助用户创建和管理小说。系统采用SQLAlchemy ORM进行数据库管理，支持多种工作流，包括创建新书、续写下一章、重写章节、从指定章节开始重写以及修改故事大纲等。

## 🚀 核心功能

### 1. 多Agent协作
- **架构师 (Architect)**：负责根据大纲的演进，制定本章节内容，发给写手
- **写手 (Writer)**：负责根据当前状态，大纲和前面的章节，判断大纲是否合理，续写下一章
- **连续性检查 (Consistency)**：检查最新章节，如果是重写需要检查前后章节，和之前章节的连贯性
- **审核编辑 (Author)**：负责打分，从连贯性等维度进行评价

### 2. 工作流设计
- **创建新书**：根据输入的标题、类型、参考资料、参考文笔，生成各个md文件
- **续写1章**：可输入提示词增加人物，经过架构师规划、写手生成、检查器检查、审核评分等步骤
- **重写1章**：参考各个md不动，只修改章节内容
- **从第n章开始重写**：n章后的内容全删除
- **修改故事大纲**：分析大纲变化对现有章节的影响，给出建议

### 3. 数据管理
- **数据库存储**：使用SQLAlchemy ORM管理书籍和章节数据
- **文件系统存储**：保存小说的MD文件，包括静态设定和动态状态
- **日志管理**：每日生成Agent日志和工作流日志

### 4. 小说参考MD文件

#### 静态设定文件
- **story_bible**：小说设定，世界观，男女主角，修炼体系/都市体系，规则等
- **volume_outline**：所有章节划分，几卷，每卷多少章，什么内容，大纲，所有支线等
- **book_rules**：写作规则、禁止出现的内容、写作特点等

#### 动态状态文件
- **current_state**：当前状态，所处地点，涉及的人物，所处支线
- **pending_hooks**：设定的钩子和伏笔，预计哪里填坑，当前状态是否填坑
- **subplot_board**：支线进度
- **emotional_arcs**：角色的情感状态，各个主角当前的情感状态，以及造成的原因
- **character_matrix**：角色矩阵，各个角色的交集和关系

#### 章节文件
- **content**：每一章的内容

## 🏗️ 项目结构

```
novel-write/
├── app.py              # 主应用文件，Streamlit前端界面
├── requirements.txt    # 依赖文件
├── .env                # 环境变量配置
├── .env.example        # 环境变量示例
├── README.md           # 项目说明
├── test/               # 测试脚本
│   └── test_workflow.py          # 工作流测试脚本
├── data/               # 数据目录
│   └── book_X/         # 书籍数据，X为书籍ID
│       ├── chapter_Y/  # 章节数据，Y为章节号
│       ├── story_bible.md
│       ├── volume_outline.md
│       ├── book_rules.md
│       ├── current_state.md
│       ├── pending_hooks.md
│       ├── subplot_board.md
│       ├── emotional_arcs.md
│       └── character_matrix.md
├── logs/               # 日志文件
│   ├── agent_YYYY-MM-DD.log      # Agent日志
│   └── workflow_YYYY-MM-DD.log   # 工作流日志
├── novel_write.db      # SQLite数据库文件
└── src/                # 源代码
    ├── agents/         # Agent实现
    │   ├── base.py              # BaseAgent基类，使用LangChain
    │   ├── architect.py         # 架构师Agent
    │   ├── writer.py            # 写手Agent
    │   ├── continuity.py        # 连续性检查器Agent
    │   └── auditor.py           # 审核Agent
    ├── db/              # 数据库管理
    │   ├── models.py            # 数据库模型（Book, Chapter）
    │   ├── crud.py              # CRUD操作
    │   ├── config.py            # 数据库配置
    │   └── init_db.py           # 数据库初始化
    ├── llm/             # LLM客户端
    │   └── provider.py          # LLM提供商
    ├── prompts/         # 提示词管理
    │   ├── architect.py         # 架构师提示词
    │   ├── writer.py            # 写手提示词
    │   ├── continuity.py        # 连续性检查器提示词
    │   └── auditor.py           # 审核提示词
    ├── utils/           # 工具类
    │   ├── file_manager.py      # 文件管理，处理MD文件的读写
    │   └── log_manager.py       # 日志管理，记录系统运行状态
    └── workflow/        # 工作流管理
        ├── workflow.py          # 工作流实现（使用LangGraph）
        └── config.py            # 工作流配置
```

## 📁 目录文件功能说明

### 主应用文件
- **app.py**：Streamlit前端界面，负责用户交互和展示，只与workflow层交互

### 依赖和配置文件
- **requirements.txt**：项目依赖包列表
- **.env**：环境变量配置文件
- **.env.example**：环境变量配置示例

### 测试目录
- **test/test_workflow.py**：工作流测试脚本，测试创建书籍和续写下一章功能

### 数据目录
- **data/book_X/**：存储每本书的MD文件和章节内容
- **logs/**：存储系统运行日志，每日生成Agent日志和工作流日志

### 数据库文件
- **novel_write.db**：SQLite数据库文件，存储书籍和章节的基本信息

### 源代码目录

#### agents/
包含四个核心Agent的实现，所有Agent继承自BaseAgent，使用LangChain进行LLM交互

- **base.py**：BaseAgent基类，封装LangChain的LLM调用逻辑
- **architect.py**：架构师Agent，负责章节规划和大纲分析
- **writer.py**：写手Agent，负责生成章节内容
- **continuity.py**：连续性检查器Agent，检查章节连贯性
- **auditor.py**：审核Agent，对章节内容进行评分

#### db/
数据库管理模块，使用SQLAlchemy ORM

- **models.py**：定义Book和Chapter数据模型
- **crud.py**：提供数据库的CRUD操作
- **config.py**：数据库配置和会话管理
- **init_db.py**：数据库初始化脚本

#### llm/
LLM客户端实现

- **provider.py**：封装LLM API调用

#### prompts/
提示词管理模块，按Agent类型分类

- **architect.py**：架构师Agent的所有提示词
- **writer.py**：写手Agent的所有提示词
- **continuity.py**：连续性检查器Agent的所有提示词
- **auditor.py**：审核Agent的所有提示词

#### utils/
工具类

- **file_manager.py**：处理MD文件的读写操作，同时保存到数据库和文件系统
- **log_manager.py**：管理系统日志，生成每日日志文件

#### workflow/
工作流管理，使用LangGraph实现

- **workflow.py**：实现各种工作流，如创建新书、续写下一章等
- **config.py**：工作流配置

## 🗄️ 数据库模型

### Book模型
```python
class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=False)
    platform = Column(String(100), nullable=False)
    chapter_words = Column(Integer, nullable=False, default=3000)
    target_chapters = Column(Integer, nullable=False, default=20)
    outline = Column(Text, nullable=False)
    story_bible = Column(Text, nullable=False)
    volume_outline = Column(Text, nullable=False)
    book_rules = Column(Text, nullable=False)
    current_state = Column(Text)
    pending_hooks = Column(Text)
    subplot_board = Column(Text)
    emotional_arcs = Column(Text)
    character_matrix = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Chapter模型
```python
class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    chapter_outline = Column(Text)
    word_count = Column(Integer, nullable=False)
    audit_score = Column(Float)
    continuity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## 🤖 Agent 详细说明

### 1. 架构师 (ArchitectAgent)

**核心方法**：
- `generate_foundation(book_data, external_context)`：生成书籍基础设定，包括故事圣经、卷纲等
- `plan_chapter(book_data, chapter_num, current_state, previous_chapter_summary, external_context)`：规划章节内容
- `analyze_outline_impact(old_outline, new_outline, book_data, outline_context)`：分析大纲变化对现有章节的影响
- `update_book_state(book_data, chapter_num, chapter_content, chapter_summary, current_state, pending_hooks)`：更新书籍状态文件

**职责**：
- 负责根据大纲和现有内容，规划章节内容
- 分析大纲变化对现有章节的影响
- 更新书籍的各种状态文件

### 2. 写手 (WriterAgent)

**核心方法**：
- `write_chapter(input_data)`：生成章节内容，输入为WriteChapterInput对象
- `check_chapter_outline(chapter_outline, book_data)`：检查章节大纲是否合理
- `_settle(data)`：状态结算，更新各种状态
- `_validate_post_write(content, genre_profile, book_rules)`：写后验证，检查规则违反

**职责**：
- 根据架构师的规划，生成章节内容
- 检查大纲是否合理，不合理则给出建议
- 更新角色情感状态、伏笔等

### 3. 连续性检查器 (ContinuityAuditor)

**核心方法**：
- `check_consistency(chapter_content, previous_chapter_content, book)`：检查章节连续性

**职责**：
- 检查章节之间的情节连贯性
- 检查角色行为和情感的一致性
- 检查场景描述的一致性

### 4. 审核编辑 (AuditorAgent)

**核心方法**：
- `score_chapter(content, book)`：给章节打分

**职责**：
- 对章节内容进行多维度评分
- 分析语言质量、情节结构、角色深度等
- 给出改进建议

## 🔄 工作流执行顺序

### 1. 创建新书

**执行顺序**：
1. **用户输入**：书名、题材、平台、每章字数、总章节数等
2. **架构师**：根据输入生成基础设定，包括故事圣经、卷纲、书籍规则等
3. **系统**：
   - 保存书籍信息到数据库
   - 创建书籍目录结构
   - 保存基础设定文件到文件系统

### 2. 续写下一章

**执行顺序**：
1. **用户输入**：可选的创作指导、本章字数
2. **架构师**：根据现有MD文件和创作指导，规划本章内容
3. **写手**：检查章节大纲是否合理
4. **写手**：根据架构师的规划，生成章节内容
5. **连续性检查器**：检查章节与前一章的连贯性
6. **审核编辑**：对章节内容进行评分，检查是否符合要求
7. **架构师**：根据章节内容，更新各种状态文件
8. **系统**：
   - 保存章节信息到数据库
   - 保存章节内容和更新后的状态文件到文件系统

### 3. 重写1章

**执行顺序**：
1. **用户输入**：要重写的章节、可选的创作指导
2. **架构师**：根据现有MD文件和创作指导，重新规划章节内容
3. **写手**：检查章节大纲是否合理
4. **写手**：根据架构师的规划，生成新的章节内容
5. **连续性检查器**：检查章节与前后章节的连贯性
6. **审核编辑**：对章节内容进行评分，检查是否符合要求
7. **架构师**：根据章节内容，更新各种状态文件
8. **系统**：
   - 更新数据库中的章节信息
   - 保存重写后的章节内容和更新后的状态文件到文件系统

### 4. 从第n章开始重写

**执行顺序**：
1. **用户输入**：开始重写的章节、可选的创作指导
2. **系统**：删除数据库和文件系统中n章及以后的所有章节内容
3. **架构师**：根据现有MD文件和创作指导，重新规划第n章内容
4. **写手**：检查章节大纲是否合理
5. **写手**：根据架构师的规划，生成第n章内容
6. **连续性检查器**：检查章节与前一章的连贯性
7. **审核编辑**：对章节内容进行评分，检查是否符合要求
8. **架构师**：根据章节内容，更新各种状态文件
9. **系统**：
   - 保存第n章信息到数据库
   - 保存第n章内容和更新后的状态文件到文件系统

### 5. 修改故事大纲

**执行顺序**：
1. **用户输入**：新的大纲内容
2. **架构师**：分析大纲变化对现有章节的影响
3. **系统**：根据架构师的分析，给出建议
   - 如果影响超过50%，建议重开一本书
   - 如果影响较大，建议删除后面的章节并重新生成
   - 如果影响较小，直接修改大纲
4. **用户确认**：确认是否修改大纲
5. **系统**：根据用户确认，执行相应操作
6. **架构师**：更新相关的MD文件

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <项目地址>
cd novel-write
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写相应的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下内容：

- `INKOS_LLM_API_KEY`：LLM API密钥
- `INKOS_LLM_BASE_URL`：LLM API基础URL
- `INKOS_LLM_MODEL`：LLM模型名称

### 4. 初始化数据库

```bash
python -m src.db.init_db
```

## 🎯 使用方法

### 1. 启动应用

```bash
streamlit run app.py
```

### 2. 创建新书

- 输入书名、题材、平台、每章字数、总章节数等信息
- 可选：参考大纲、参考作者文笔
- 点击「创建书籍」按钮

### 3. 续写小说

- 选择已创建的书籍
- 输入可选的提示词（如增加人物等）
- 点击「续写下一章」按钮

### 4. 重写章节

- 选择已创建的书籍
- 选择要重写的章节
- 输入可选的提示词
- 点击「重写章节」按钮

### 5. 从指定章节开始重写

- 选择已创建的书籍
- 选择开始重写的章节
- 输入可选的提示词
- 点击「从该章节开始重写」按钮

### 6. 修改故事大纲

- 选择已创建的书籍
- 输入新的大纲内容
- 点击「修改大纲」按钮

## 🧪 运行测试

### 运行工作流测试

```bash
python test/test_workflow.py
```

测试脚本会执行以下操作：
1. 创建一本新书
2. 续写下一章
3. 验证所有步骤是否成功完成

## 📝 日志管理

系统会在 `logs` 目录下生成以下日志文件：

- `agent_YYYY-MM-DD.log`：Agent日志，记录各个Agent的执行情况
- `workflow_YYYY-MM-DD.log`：工作流日志，记录工作流的执行步骤和数据库操作

## 📚 MD文件管理

在应用的「MD文件管理」标签页中，您可以查看和编辑所有的MD文件，包括：

### 静态设定文件
- **故事圣经**：小说设定、世界观、男女主角、修炼体系/都市体系、规则等
- **卷纲**：所有章节划分、几卷、每卷多少章、什么内容、大纲、所有支线等
- **书籍规则**：写作规则、禁止出现的内容、写作特点等

### 动态状态文件
- **当前状态**：当前状态、所处地点、涉及的人物、所处支线
- **伏笔池**：设定的钩子和伏笔、预计哪里填坑、当前状态是否填坑
- **支线进度板**：支线进度
- **情感弧线**：角色的情感状态、各个主角当前的情感状态、以及造成的原因
- **角色交互矩阵**：角色矩阵、各个角色的交集和关系

## 🔧 技术栈

- **前端**：Streamlit
- **后端**：Python
- **LLM集成**：LangChain + LangGraph
- **数据库**：SQLite + SQLAlchemy ORM
- **文件存储**：本地文件系统（MD文件）

## 🏛️ 架构设计

### 分层架构
1. **前端层**：Streamlit界面，只与workflow层交互
2. **工作流层**：使用LangGraph实现工作流，协调各个Agent
3. **Agent层**：使用LangChain实现各个专业Agent
4. **数据层**：SQLAlchemy ORM + 文件系统

### Agent继承体系
- **BaseAgent**：基类，封装LangChain的LLM调用逻辑
- **ArchitectAgent**：继承自BaseAgent，负责章节规划
- **WriterAgent**：继承自BaseAgent，负责内容生成
- **ContinuityAuditor**：继承自BaseAgent，负责连续性检查
- **AuditorAgent**：继承自BaseAgent，负责内容审核

### 工作流状态管理
- 使用LangGraph的状态图管理复杂工作流
- 每个工作流节点返回完整的状态字典
- 确保状态在节点间正确传播

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证。
