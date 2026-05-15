# 📖 用户指南

本文档介绍如何使用 NovelWrite AI 进行小说创作。

## 目录

- [快速开始](#快速开始)
- [创建第一本书](#创建第一本书)
- [生成大纲](#生成大纲)
- [续写章节](#续写章节)
- [使用Orchestrator智能编排](#使用orchestrator智能编排)
- [管理工作流](#管理工作流)
- [查看Checkpoint状态](#查看checkpoint状态)
- [API调用示例](#api调用示例)

## 快速开始

### 1. 启动服务

```bash
cd backend
python run.py
```

服务启动后：
- API文档: http://localhost:8000/docs
- 前端界面: http://localhost:3000

### 2. 创建书籍并生成内容

```bash
# 创建书籍
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的玄幻小说",
    "genre": "玄幻",
    "platform": "起点",
    "chapter_words": 3000,
    "target_chapters": 100
  }'

# 使用Orchestrator生成大纲
curl -X POST "http://localhost:8000/api/v1/orchestrator/generate-outline" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "use_llm": true}'

# 续写章节
curl -X POST "http://localhost:8000/api/v1/orchestrator/write-chapter" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "chapter_num": 1, "use_llm": true}'
```

## 创建第一本书

### 通过API创建

```bash
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "书名",
    "genre": "玄幻",  # 支持26种类型
    "platform": "起点",
    "chapter_words": 3000,
    "target_chapters": 100,
    "outline": "可选的初始大纲"
  }'
```

### 支持的小说类型

**男频（15种）**: 玄幻、奇幻、武侠、仙侠、都市、现实、历史、军事、游戏、体育、科幻、悬疑灵幻、轻小说、短篇、诸天无限

**女频（11种）**: 古代言情、现代言情、玄幻言情、悬疑推理、浪漫青春、仙侠奇缘、科幻空间、游戏竞技、轻小说、短篇、现实生活

## 生成大纲

### 方式一：使用Orchestrator（推荐）

```bash
curl -X POST "http://localhost:8000/api/v1/orchestrator/generate-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "use_llm": true  # true使用真实LLM，false使用模拟数据
  }'
```

Orchestrator会自动：
1. 调用Architect Agent生成大纲
2. 保存到数据库
3. 返回完整的大纲内容

### 方式二：使用工作流

```bash
# 启动生成大纲工作流
curl -X POST "http://localhost:8000/api/v1/workflows/generate-outline" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1}'

# 返回: {"workflow_id": "xxx", "status": "started"}

# 查询状态
curl "http://localhost:8000/api/v1/workflows/{workflow_id}/status"
```

### 大纲包含的内容

生成的大纲包含9个文件：
- `story_bible` - 世界观设定
- `volume_outline` - 卷纲规划
- `book_rules` - 创作规则
- `current_state` - 当前状态
- `pending_hooks` - 伏笔池
- `character_matrix` - 角色矩阵
- `emotional_arcs` - 情感弧线

## 续写章节

### 使用Orchestrator写单章

```bash
curl -X POST "http://localhost:8000/api/v1/orchestrator/write-chapter" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "chapter_num": 1,
    "use_llm": true
  }'
```

Orchestrator会自动执行：
1. 规划章节内容
2. 写作章节
3. 审核章节质量
4. 检查连续性
5. 保存章节

### 批量续写多章

```bash
curl -X POST "http://localhost:8000/api/v1/orchestrator/continue-chapters" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "start_chapter": 1,
    "count": 5,
    "use_llm": true
  }'
```

### 使用工作流续写

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/continue-chapters" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "start_chapter": 1,
    "count": 3
  }'
```

## 使用Orchestrator智能编排

Orchestrator是系统的核心编排层，负责：

### 智能决策

- **审核分数低于70分** → 自动重写（最多3次）
- **连续性问题** → 记录并提示
- **章节类型自动判断** → 开篇/发展/高潮/结尾采用不同策略

### 进度追踪

```bash
# 获取书籍上下文
curl "http://localhost:8000/api/v1/orchestrator/books/1/context"

# 返回包含：
# - 当前写作进度
# - 角色信息
# - 伏笔状态
# - 上下文哈希
```

### 支持的API

| API | 功能 |
|-----|------|
| `POST /orchestrator/generate-outline` | 生成大纲 |
| `POST /orchestrator/write-chapter` | 写单章 |
| `POST /orchestrator/continue-chapters` | 续写多章 |
| `GET /orchestrator/books/{id}/context` | 获取上下文 |

## 管理工作流

### 查看工作流列表

```bash
# 获取书籍的所有工作流
curl "http://localhost:8000/api/v1/books/1/workflows"
```

### 暂停和恢复

```bash
# 暂停工作流
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/pause"

# 恢复工作流
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/resume"

# 从指定节点恢复
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/resume?from_node_id=node_2"
```

### 重试失败节点

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/retry/{node_id}"
```

## 查看Checkpoint状态

### 获取工作流节点列表

```bash
curl "http://localhost:8000/api/v1/workflows/{workflow_id}/nodes"
```

### 获取节点详情

```bash
curl "http://localhost:8000/api/v1/workflows/{workflow_id}/nodes/{node_id}"
```

### SSE流式更新

```javascript
// 前端连接SSE获取实时更新
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/workflows/{workflow_id}/stream'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Workflow status:', data.status);
};
```

## API调用示例

### 完整创作流程

```bash
#!/bin/bash

# 1. 创建书籍
echo "Creating book..."
BOOK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "修仙之路",
    "genre": "仙侠",
    "platform": "起点",
    "chapter_words": 3000,
    "target_chapters": 100
  }')
BOOK_ID=$(echo $BOOK_RESPONSE | jq -r '.id')
echo "Book created: $BOOK_ID"

# 2. 生成大纲
echo "Generating outline..."
curl -s -X POST "http://localhost:8000/api/v1/orchestrator/generate-outline" \
  -H "Content-Type: application/json" \
  -d "{\"book_id\": $BOOK_ID, \"use_llm\": true}"

# 3. 续写前3章
echo "Writing chapters..."
for i in 1 2 3; do
  echo "Writing chapter $i..."
  curl -s -X POST "http://localhost:8000/api/v1/orchestrator/write-chapter" \
    -H "Content-Type: application/json" \
    -d "{\"book_id\": $BOOK_ID, \"chapter_num\": $i, \"use_llm\": true}"
done

echo "Done!"
```

### Python示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 创建书籍
book = requests.post(f"{BASE_URL}/api/v1/books", json={
    "title": "我的小说",
    "genre": "玄幻",
    "platform": "起点"
}).json()

book_id = book["id"]

# 生成大纲
outline = requests.post(
    f"{BASE_URL}/api/v1/orchestrator/generate-outline",
    json={"book_id": book_id, "use_llm": True}
).json()

print(f"Story Bible: {outline['story_bible'][:200]}...")

# 写章节
chapter = requests.post(
    f"{BASE_URL}/api/v1/orchestrator/write-chapter",
    json={"book_id": book_id, "chapter_num": 1, "use_llm": True}
).json()

print(f"Chapter 1: {chapter['title']}")
print(f"Word count: {chapter['word_count']}")
print(f"Audit score: {chapter['audit_score']}")
```

## 常见问题

### Q: LLM调用失败怎么办？

检查：
1. `.env` 文件中API密钥是否正确配置
2. 网络连接是否正常
3. 使用 `use_llm: false` 进行测试

### Q: 如何查看生成的内容？

```bash
# 查看书籍详情
curl "http://localhost:8000/api/v1/books/1"

# 查看章节内容
curl "http://localhost:8000/api/v1/books/1/chapters/1"
```

### Q: 工作流卡住了怎么办？

```bash
# 查看工作流状态
curl "http://localhost:8000/api/v1/workflows/{workflow_id}/status"

# 如果状态是failed，查看错误信息
# 如果是paused，可以resume或retry
```
