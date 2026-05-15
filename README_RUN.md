# NovelWrite 项目启动指南

## 环境要求
- Python 3.10+
- 已配置好 `.env` 文件（已为您创建）

## 启动步骤

### 方式一：使用启动脚本（推荐）

```bash
cd /path/to/your/project
chmod +x start_server.sh
./start_server.sh
```

### 方式二：手动启动

```bash
cd /path/to/your/project/backend

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
python run.py
```

### 方式三：使用 uvicorn 直接启动

```bash
cd /path/to/your/project/backend

source .venv/bin/activate

uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 验证服务

启动后，在浏览器中访问：
- http://localhost:8000/ - 首页
- http://localhost:8000/docs - API文档
- http://localhost:8000/health - 健康检查

## 配置说明

`.env` 文件已配置好以下信息：
- LLM提供商：ModelScope (OpenAI兼容)
- 模型：Qwen/Qwen3.5-35B-A3B
- API密钥：您的密钥已填入
- 数据库：SQLite (本地文件)

## 常见问题

1. **端口被占用**：修改 `run.py` 中的 `port=8000` 为其他端口
2. **依赖缺失**：运行 `pip install -r requirements.txt`
3. **虚拟环境不存在**：运行 `python -m venv .venv`
