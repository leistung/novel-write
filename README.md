# novel-write - AI 小说写作助手

一个基于AI的智能小说写作系统，通过多Agent协作完成小说的创作、续写、重写和审核等任务。

## 📋 项目概述

novel-write 是一个功能强大的AI小说写作助手，它利用多个专业Agent（架构师、写手、连续性检查器、审核编辑）协同工作，帮助用户创建和管理小说。系统支持多种工作流，包括创建新书、续写下一章、重写章节、从指定章节开始重写以及修改故事大纲等。

## 🚀 核心功能

### 1. 多Agent协作
- **架构师 (Architect)**：负责根据大纲的演进，制定本章节内容，发给写手
- **写手 (Writer)**：负责根据当前状态，大纲和前面的章节，判断大纲是否合理，续写下一章
- **情节一致性检查 (Checker)**：检查最新章节，如果是重写需要检查前后章节，和之前章节的连贯性
- **审核的编辑 (Author)**：负责打分，从连贯性等维度进行评价

### 2. 工作流设计
- **创建新书**：根据输入的标题、类型、参考资料、参考文笔，生成各个md文件
- **续写1章**：可输入提示词增加人物，经过架构师规划、写手生成、检查器检查、审核评分等步骤
- **重写1章**：参考各个md不动，只修改章节内容
- **从第n章开始重写**：n章后的内容全删除
- **修改故事大纲**：分析大纲变化对现有章节的影响，给出建议

### 3. 小说参考MD文件
- **content**：目录，每一章的内容
- **story_bible**：小说设定，世界观，男女主角，修炼体系/都市体系，规则等
- **chapter_summarize**：每一章的章节概要
- **character_matrix**：角色矩阵，各个角色的交集和关系
- **current_state**：当前状态，所处地点，涉及的人物，所处支线
- **outline**：所有章节划分，几卷，每卷多少章，什么内容，大纲，所有支线等
- **hooks**：设定的钩子和伏笔，预计哪里填坑，当前状态是否填坑
- **emotional_states**：角色的情感状态，各个主角当前的情感状态，以及造成的原因

## 🏗️ 项目结构

```
novel-write/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖文件
├── .env                # 环境变量配置
├── .env.example        # 环境变量示例
├── README.md           # 项目说明
├── test/               # 测试脚本
│   ├── agents/         # Agent测试
│   │   ├── test_architect.py     # 测试架构师Agent
│   │   ├── test_writer.py        # 测试写手Agent
│   │   ├── test_continuity.py    # 测试连续性检查器Agent
│   │   └── test_auditor.py       # 测试审核Agent
│   ├── pipeline/       # 工作流测试
│   │   └── test_pipeline.py      # 测试Pipeline工作流
│   └── run_all_tests.py          # 运行所有测试的脚本
├── data/               # 数据目录
│   ├── book_X/         # 书籍数据
│   └── log/            # 日志文件
└── src/                # 源代码
    ├── agents/         # Agent实现
    │   ├── prompts/    # 提示词管理
    │   ├── architect.py        # 架构师Agent
    │   ├── writer.py           # 写手Agent
    │   ├── continuity.py       # 连续性检查器Agent
    │   └── auditor.py          # 审核Agent
    ├── llm/            # LLM客户端
    │   └── provider.py         # LLM提供商
    ├── pipeline/       # 工作流管理
    │   └── runner.py           # 工作流运行器
    └── utils/          # 工具类
        ├── file_manager.py     # 文件管理
        └── log_manager.py      # 日志管理
```

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

- `inkos_llm_api_key`：LLM API密钥
- `inkos_llm_base_url`：LLM API基础URL
- `inkos_llm_model`：LLM模型名称

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

### 运行所有测试

```bash
python test/run_all_tests.py
```

### 运行单个测试文件

```bash
# 测试架构师Agent
python test/agents/test_architect.py

# 测试工作流
python test/pipeline/test_pipeline.py
```

## 📝 日志管理

系统会在 `log` 目录下生成以下日志文件：

- `operations.log`：操作日志，记录所有操作的执行情况
- `novel-write_YYYY-MM-DD.log`：完整日志，记录系统运行的详细信息

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 联系

如有问题或建议，请通过以下方式联系：

- 邮箱：<your-email@example.com>
- GitHub：<your-github-profile>

---

**Happy Writing! 📚✨**