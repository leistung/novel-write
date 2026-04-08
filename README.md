# novel-write AI 小说写作助手

一个基于 Streamlit 和 LangChain 的 AI 小说写作项目，提供了友好的 Web 界面。

## 功能特性

- **创建新书**：支持多种题材和平台的小说创建，可配置标题、类型、平台、大纲、文笔参考、每章字数和总章节数
- **续写章节**：基于前情自动生成新章节，确保字数达标和风格匹配
- **审计章节**：从多维度检查章节内容，包括字数、质量、题材符合度、平台规则等
- **修订章节**：根据审计结果自动修订章节内容
- **查看状态**：查看书籍的创作状态和进度
- **导出功能**：支持将章节导出为 txt 文件

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写你的 API 密钥：

```bash
cp .env.example .env
# 编辑 .env 文件，填写你的 API 密钥
```

### 启动应用

```bash
streamlit run app.py
```

## 项目结构

```
novel-write/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖文件
├── .env.example        # 环境变量示例
├── README.md           # 项目说明
├── test/               # 测试脚本
│   ├── test_full_workflow.py  # 完整工作流程测试
│   ├── test_pipeline.py       # 核心pipeline测试
│   ├── test_llm.py            # LLM客户端测试
│   ├── test_database.py       # 数据库操作测试
│   ├── test_export.py         # 导出功能测试
│   ├── test_agents.py         # Agent功能测试
│   └── run_all_tests.py       # 运行所有测试
└── src/
    ├── llm/            # LLM 相关模块
    │   └── provider.py # LLM 客户端配置
    ├── models/         # 数据模型
    │   ├── book.py     # 书籍模型
    │   ├── chapter.py  # 章节模型
    │   ├── state.py    # 状态模型
    │   └── project.py  # 项目配置模型
    ├── agents/         # AI 代理
    │   ├── base.py     # 基础代理类
    │   ├── architect.py # 架构师代理
    │   ├── writer.py   # 作家代理
    │   ├── auditor.py  # 审计员代理
    │   ├── detector.py # AI内容检测器
    │   ├── continuity.py # 连续性审计员
    │   ├── reviser.py  # 修订者代理
    │   └── radar.py    # 雷达代理
    └── utils/          # 工具类
        └── file_manager.py # 文件管理器
```

## 技术栈

- **前端**：Streamlit
- **后端**：Python
- **LLM 框架**：LangChain
- **LLM 提供商**：OpenAI（支持自定义提供商）
- **数据库**：SQLite

## Agent 介绍

### 1. 架构师 Agent (ArchitectAgent)

**功能**：生成小说的基础设定，包括故事圣经、卷纲、书籍规则等。

**主要方法**：
- `generate_foundation(book: Dict[str, Any], external_context: Optional[str] = None) -> ArchitectOutput`：生成完整的基础设定
  - **参数**：
    - `book`：书籍信息，包括标题、题材、平台等
    - `external_context`：外部创作指令（可选）
  - **返回值**：`ArchitectOutput` 对象，包含故事圣经、卷纲、书籍规则、当前状态和伏笔池

**输出结构**：
- `story_bible`：故事圣经，包含世界观、主角、势力与人物、地理与环境等详细设定
- `volume_outline`：卷纲，包含各卷的主要内容和章节规划
- `book_rules`：书籍规则，包含写作风格、题材特征等要求
- `current_state`：当前状态，描述故事的当前进展
- `pending_hooks`：伏笔池，包含未回收的伏笔

### 2. 作家 Agent (WriterAgent)

**功能**：生成小说章节内容，确保字数达标和风格匹配。

**主要方法**：
- `write_chapter(input: WriteChapterInput) -> WriteChapterOutput`：生成章节内容
  - **参数**：
    - `input`：`WriteChapterInput` 对象，包含书籍信息、章节号、外部上下文等
  - **返回值**：`WriteChapterOutput` 对象，包含章节标题、内容、字数等信息

**输入结构**：
- `book`：书籍信息
- `chapter_number`：章节号
- `external_context`：外部创作指令（可选）
- `word_count_override`：字数覆盖（可选）
- `temperature_override`：温度覆盖（可选）

**输出结构**：
- `chapter_number`：章节号
- `title`：章节标题
- `content`：章节内容
- `word_count`：章节字数
- `pre_write_check`：写作前检查
- `post_settlement`：写作后结算
- `updated_state`：更新后的状态
- `updated_ledger`：更新后的资源账本
- `updated_hooks`：更新后的伏笔池
- `chapter_summary`：章节摘要
- `updated_subplots`：更新后的支线
- `updated_emotional_arcs`：更新后的情感弧线
- `updated_character_matrix`：更新后的角色矩阵
- `post_write_errors`：写作后错误
- `post_write_warnings`：写作后警告
- `token_usage`：令牌使用情况

### 3. 审计员 Agent (AuditorAgent)

**功能**：从多维度审核章节内容，生成改进建议。

**主要方法**：
- `run(input: Dict[str, Any]) -> Dict[str, Any]`：运行审核
  - **参数**：
    - `input`：包含内容、书籍信息和章节号的字典
  - **返回值**：包含审核结果的字典

**审核维度**：
1. 字数检查：确保章节字数达到要求
2. 内容质量：检查内容是否流畅，情节是否合理
3. 题材符合度：检查内容是否符合题材特征
4. 平台规则：检查内容是否符合平台规则
5. 语法错误：检查是否有语法错误
6. 逻辑连贯：检查情节是否逻辑连贯
7. 人物刻画：检查人物刻画是否鲜明
8. 场景描写：检查场景描写是否生动
9. 写作风格：检查是否符合指定的写作风格
10. 创新程度：检查内容是否有创新点

### 4. 检测器 Agent (DetectorAgent)

**功能**：检测章节内容是否为 AI 生成。

**主要方法**：
- `run(context: Dict[str, Any]) -> Dict[str, Any]`：运行检测器
  - **参数**：
    - `context`：包含内容和检测配置的字典
  - **返回值**：包含检测结果的字典

- `detect_ai_content(config: Dict[str, Any], content: str) -> DetectionResult`：检测 AI 生成的内容
  - **参数**：
    - `config`：检测配置，包含提供商、API URL 等
    - `content`：要检测的内容
  - **返回值**：`DetectionResult` 对象，包含检测分数、提供商等信息

**支持的检测提供商**：
- gptzero
- originality
- custom（自定义 API）

## 工作流程

1. **创建书籍**：
   - 用户填写书籍信息，包括标题、题材、平台、大纲、文笔参考、每章字数和总章节数
   - 系统在数据库中创建书籍记录
   - 系统调用架构师 Agent 生成基础设定

2. **生成章节**：
   - 用户选择要续写的书籍，输入创作指导
   - 系统调用作家 Agent 生成章节内容
   - 系统调用检测器 Agent 检测 AI 内容
   - 系统调用审计员 Agent 审核章节内容
   - 系统将章节保存到数据库

3. **审计章节**：
   - 用户选择要审计的书籍和章节
   - 系统调用审计员 Agent 审核章节内容
   - 系统显示审核结果和改进建议

4. **修订章节**：
   - 用户选择要修订的书籍和章节
   - 系统根据审计结果调用修订者 Agent 修订章节内容
   - 系统将修订后的章节保存到数据库

5. **查看状态**：
   - 用户选择要查看的书籍
   - 系统显示书籍的创作状态和进度
   - 系统显示章节列表和基本信息

6. **导出章节**：
   - 用户选择要导出的书籍和章节
   - 系统将章节内容导出为 txt 文件

## 测试

项目包含多个测试脚本，用于验证各个组件的功能：

- `test_full_workflow.py`：测试完整的工作流程
- `test_pipeline.py`：测试核心 pipeline
- `test_llm.py`：测试 LLM 客户端
- `test_database.py`：测试数据库操作
- `test_export.py`：测试导出功能
- `test_agents.py`：测试各个 Agent 的功能
- `run_all_tests.py`：运行所有测试

运行测试：

```bash
python test/run_all_tests.py
```

## 注意事项

- 请确保你的 API 密钥有效，并且有足够的配额。
- 生成章节可能需要较长时间，请耐心等待。
- 审计和修订功能可能会调用多次 LLM，请注意 API 调用成本。
- 检测 AI 内容需要配置相应的 API 密钥。
