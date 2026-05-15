# 🔧 开发指南

本文档介绍如何在本地开发和调试 NovelWrite AI。

## 目录

- [环境准备](#环境准备)
- [项目结构](#项目结构)
- [本地开发](#本地开发)
- [运行测试](#运行测试)
- [调试技巧](#调试技巧)
- [添加新功能](#添加新功能)

## 环境准备

### 1. 安装Python

需要 Python 3.10+

```bash
python --version
# Python 3.10.0 or higher
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd novel-write
```

### 3. 创建虚拟环境

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

**必需配置**:
```env
# LLM API配置（至少配置一个）
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_PROVIDER=openai

# 或 Anthropic
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

## 项目结构

```
novel-write/
├── backend/                    # FastAPI后端
│   ├── api/                    # API路由
│   │   ├── main.py            # FastAPI应用入口
│   │   └── routes/            # 路由模块
│   │       ├── books.py
│   │       ├── chapters.py
│   │       ├── workflows.py
│   │       ├── checkpoints.py
│   │       ├── skills.py
│   │       └── orchestrator.py
│   ├── agents/                 # Agent实现
│   │   ├── base.py            # BaseAgent基类
│   │   ├── architect.py       # Architect Agent
│   │   ├── writer.py          # Writer Agent
│   │   ├── auditor.py         # Auditor Agent
│   │   └── continuity.py      # Continuity Auditor
│   ├── orchestrator/           # Orchestrator编排层
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # 核心编排器
│   │   ├── context.py         # BookContext
│   │   └── strategies.py      # 调度策略
│   ├── workflow/               # 工作流引擎
│   │   └── engine.py
│   ├── checkpoint/             # Checkpoint管理
│   │   └── manager.py
│   ├── store/                  # 文件存储
│   │   └── manager.py
│   ├── skill/                  # Skill加载器
│   │   └── loader.py
│   ├── db/                     # 数据库
│   │   ├── database.py
│   │   ├── models.py
│   │   └── crud.py
│   ├── llm/                    # LLM客户端
│   │   └── client.py
│   ├── config/                 # 配置
│   │   └── settings.py
│   ├── tests/                  # 测试
│   │   ├── conftest.py
│   │   ├── test_books.py
│   │   ├── test_chapters.py
│   │   ├── test_workflows.py
│   │   ├── test_skills.py
│   │   └── test_orchestrator.py
│   ├── run.py                  # 启动脚本
│   ├── requirements.txt
│   └── .env
├── frontend/                   # React前端
│   ├── src/
│   ├── package.json
│   └── ...
├── skills/                     # 26种小说类型Skill
│   ├── xuanhuan-novelist/
│   ├── wuxia-novelist/
│   └── ...
├── docs/                       # 文档
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── ...
└── README.md
```

## 本地开发

### 启动后端服务

```bash
cd backend
python run.py
```

服务启动后：
- API: http://localhost:8000
- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 启动前端（可选）

```bash
cd frontend
npm install
npm run dev
```

前端地址: http://localhost:3000

### 使用IDE调试

**VS Code配置** (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

## 运行测试

### 运行所有测试

```bash
cd backend
python -m pytest tests/ -v
```

### 运行特定测试

```bash
# 只测试Books API
python -m pytest tests/test_books.py -v

# 只测试Orchestrator
python -m pytest tests/test_orchestrator.py -v

# 排除LLM测试（更快）
python -m pytest tests/ -v -k "not WithLLM"
```

### 测试覆盖率

```bash
python -m pytest tests/ --cov=backend --cov-report=html
```

### 调试测试

```bash
# 遇到错误时停止
python -m pytest tests/ -x --pdb

# 显示print输出
python -m pytest tests/ -v -s
```

## 调试技巧

### 1. 查看API请求/响应

在 `api/main.py` 中添加中间件：

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response
```

### 2. 调试Agent

在Agent方法中添加断点：

```python
async def write_chapter(self, ...):
    # 断点1: 查看输入参数
    print(f"Writing chapter {chapter_num} for book {book_id}")
    
    # ... 构建prompt ...
    
    # 断点2: 查看prompt
    print(f"System prompt: {system_prompt[:500]}...")
    
    # 调用LLM
    result = await self.llm.generate(...)
    
    # 断点3: 查看LLM输出
    print(f"LLM output: {result}")
    
    return result
```

### 3. 查看数据库

使用SQLite浏览器或命令行：

```bash
# 命令行
sqlite3 backend/data/novel_write.db

# 查看表结构
.schema

# 查看书籍
SELECT * FROM books;

# 查看章节
SELECT * FROM chapters WHERE book_id = 1;
```

### 4. 查看Store文件

```bash
# 查看书籍存储结构
ls -la store/books/1/

# 查看章节内容
cat store/books/1/chapters/1.md

# 查看状态文件
cat store/books/1/state/worldview.md
```

### 5. 调试工作流

```python
# 在测试中添加调试信息
async def test_workflow(client):
    response = await client.post("/workflows/generate-outline", json={"book_id": 1})
    workflow_id = response.json()["workflow_id"]
    
    # 循环查询状态
    for i in range(10):
        status = await client.get(f"/workflows/{workflow_id}/status")
        print(f"Status {i}: {status.json()}")
        await asyncio.sleep(1)
```

## 添加新功能

### 添加新Agent方法

1. 在 `agents/{agent}.py` 中添加方法：

```python
async def new_method(self, param1: str, db: AsyncSession) -> AgentResult:
    """新方法描述"""
    try:
        # 1. 获取数据
        book = await get_book(db, book_id)
        
        # 2. 构建prompt
        system_prompt = self._get_system_prompt()
        user_prompt = f"输入: {param1}"
        
        # 3. 调用LLM
        result = await self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        # 4. 解析结果
        data = self._parse_result(result)
        
        return AgentResult(ok=True, data=data)
    except Exception as e:
        return AgentResult(ok=False, feedback=str(e))
```

2. 在 `workflow/engine.py` 中添加工作流节点：

```python
async def _execute_node(self, ..., task="new_method"):
    result = await agent.execute(task=task, ...)
```

3. 添加测试：

```python
# tests/test_agents.py
async def test_new_method():
    agent = ArchitectAgent()
    result = await agent.new_method("test", db)
    assert result.ok
```

### 添加新API端点

1. 在 `api/routes/{module}.py` 中添加：

```python
@router.post("/new-endpoint")
async def new_endpoint(
    request: NewRequest,
    db: AsyncSession = Depends(get_db)
):
    """端点描述"""
    # 业务逻辑
    result = await service.do_something(request.book_id)
    return {"result": result}
```

2. 添加请求/响应模型：

```python
class NewRequest(BaseModel):
    book_id: int
    param: str
```

3. 添加测试：

```python
# tests/test_{module}.py
async def test_new_endpoint(client):
    response = await client.post("/new-endpoint", json={"book_id": 1, "param": "test"})
    assert response.status_code == 200
```

### 添加新Skill

1. 创建目录结构：

```bash
mkdir -p skills/new-genre-novelist/references/research
```

2. 创建 `SKILL.md`：

```markdown
---
name: new-genre-novelist
description: 新类型小说创作专家
---

## 角色扮演规则
...

## 核心智模型
...
```

3. 创建research文件：
- `01-writings.md` - 著作研究
- `02-conversations.md` - 对话风格
- ...

4. 更新 `api/routes/skills.py` 中的 `GENRE_DEFINITIONS`

## 常见问题

### Q: 修改代码后没有生效？

确保：
1. 保存了文件
2. 使用了 `--reload` 参数（开发模式自动重载）
3. 重启了服务（如果没有使用reload）

### Q: 数据库连接失败？

检查：
1. `.env` 中的 `DATABASE_URL` 配置
2. 数据库文件目录是否有写入权限
3. 数据库迁移是否完成（首次运行会自动创建）

### Q: LLM调用超时？

在 `.env` 中增加超时时间：
```env
LLM_TIMEOUT=120
```

### Q: 如何查看日志？

```bash
# 查看详细日志
python run.py --log-level debug

# 或修改 .env
LOG_LEVEL=DEBUG
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'Add xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

### 代码规范

- 使用 Black 格式化代码
- 添加类型注解
- 编写 docstring
- 保持测试覆盖率
