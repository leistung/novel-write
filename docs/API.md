# 📚 API 文档

本文档介绍 NovelWrite AI 的所有 API 接口。

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **API 文档**: `http://localhost:8000/docs` (Swagger UI)
- **Content-Type**: `application/json`

## 目录

- [Books API](#books-api)
- [Chapters API](#chapters-api)
- [Workflows API](#workflows-api)
- [Checkpoints API](#checkpoints-api)
- [Skills API](#skills-api)
- [Orchestrator API](#orchestrator-api)

---

## Books API

### 创建书籍

```http
POST /books
```

**请求体**:
```json
{
  "title": "书名",
  "genre": "玄幻",
  "platform": "起点",
  "chapter_words": 3000,
  "target_chapters": 100,
  "outline": "可选的初始大纲"
}
```

**响应**:
```json
{
  "id": 1,
  "title": "书名",
  "genre": "玄幻",
  "platform": "起点",
  "chapter_words": 3000,
  "target_chapters": 100,
  "outline": "",
  "created_at": "2024-01-01T00:00:00"
}
```

### 获取书籍列表

```http
GET /books
```

**查询参数**:
- `skip`: 跳过数量 (默认: 0)
- `limit`: 返回数量 (默认: 100)

### 获取单本书籍

```http
GET /books/{book_id}
```

### 更新书籍

```http
PUT /books/{book_id}
```

**请求体**:
```json
{
  "title": "新书名",
  "outline": "更新后的大纲"
}
```

### 删除书籍

```http
DELETE /books/{book_id}
```

### 获取大纲文件

```http
GET /books/{book_id}/outline?key={file_key}
```

**file_key 可选值**:
- `worldview` - 世界观
- `character_profiles` - 角色设定
- `power_system` - 力量体系
- `story_structure` - 故事结构
- `volume_outline` - 卷纲
- `chapter_plan` - 章节规划
- `subplot_board` - 支线板
- `foreshadowing` - 伏笔
- `writing_style` - 文风

### 更新大纲文件

```http
PUT /books/{book_id}/outline
```

**请求体**:
```json
{
  "key": "worldview",
  "content": "# 世界观设定\n\n这是一个修仙世界..."
}
```

---

## Chapters API

### 获取章节列表

```http
GET /books/{book_id}/chapters
```

**查询参数**:
- `skip`: 跳过数量
- `limit`: 返回数量

### 获取单章详情

```http
GET /books/{book_id}/chapters/{chapter_num}
```

### 更新章节

```http
PUT /books/{book_id}/chapters/{chapter_num}
```

**请求体**:
```json
{
  "title": "新标题",
  "content": "新内容",
  "status": "published"
}
```

### 删除章节

```http
DELETE /books/{book_id}/chapters/{chapter_num}
```

---

## Workflows API

### 生成大纲工作流

```http
POST /workflows/generate-outline
```

**请求体**:
```json
{
  "book_id": 1
}
```

**响应**:
```json
{
  "workflow_id": "uuid-string",
  "status": "started",
  "message": "大纲生成工作流已启动"
}
```

### 续写章节工作流

```http
POST /workflows/continue-chapters
```

**请求体**:
```json
{
  "book_id": 1,
  "start_chapter": 1,
  "count": 3,
  "external_context": "可选的外部上下文"
}
```

### 重写章节工作流

```http
POST /workflows/rewrite-chapter
```

**请求体**:
```json
{
  "book_id": 1,
  "chapter_num": 5,
  "rewrite_requirements": "增加更多战斗描写",
  "keep_plot": true
}
```

### 保护章节并更新大纲

```http
POST /workflows/protect-and-update
```

**请求体**:
```json
{
  "book_id": 1,
  "protected_chapter": 10,
  "new_outline": "更新后的大纲内容"
}
```

### 提取大纲工作流

```http
POST /workflows/extract-outline
```

**请求体**:
```json
{
  "book_id": 1
}
```

### 扩写大纲工作流

```http
POST /workflows/expand-skill
```

**请求体**:
```json
{
  "book_id": 1
}
```

### 获取工作流状态

```http
GET /workflows/{workflow_id}/status
```

### 暂停工作流

```http
POST /workflows/{workflow_id}/pause
```

### 恢复工作流

```http
POST /workflows/{workflow_id}/resume?from_node_id={node_id}
```

### 重试节点

```http
POST /workflows/{workflow_id}/retry/{node_id}
```

---

## Checkpoints API

### 获取工作流节点列表

```http
GET /workflows/{workflow_id}/nodes
```

### 获取节点详情

```http
GET /workflows/{workflow_id}/nodes/{node_id}
```

### 获取检查点列表

```http
GET /workflows/{workflow_id}/checkpoints
```

### SSE流式更新

```http
GET /workflows/{workflow_id}/stream
```

**Content-Type**: `text/event-stream`

---

## Skills API

### 获取Skill列表

```http
GET /skills
```

**查询参数**:
- `category`: `male` 或 `female`

### 获取Skill详情

```http
GET /skills/{skill_name}
```

### 创建Skill

```http
POST /skills
```

**请求体**:
```json
{
  "name": "custom-novelist",
  "genre": "自定义",
  "category": "male",
  "description": "描述",
  "skill_content": "Skill内容"
}
```

### 获取小说类型列表

```http
GET /skills/genres/list
```

**响应**:
```json
{
  "male": [
    {"key": "xuanhuan", "name": "玄幻", "category": "male"},
    ...
  ],
  "female": [
    {"key": "ancient_romance", "name": "古代言情", "category": "female"},
    ...
  ]
}
```

### 同步Skill到数据库

```http
POST /skills/sync
```

### 获取文件系统Skill列表

```http
GET /skills/filesystem/list
```

---

## Orchestrator API

### 智能生成大纲

```http
POST /orchestrator/generate-outline
```

**请求体**:
```json
{
  "book_id": 1,
  "use_llm": true
}
```

**响应**:
```json
{
  "book_id": 1,
  "outline_generated": true,
  "story_bible": "世界观设定内容...",
  "volume_outline": "卷纲规划内容...",
  "book_rules": "创作规则内容...",
  "current_state": "当前状态内容...",
  "pending_hooks": "伏笔池内容...",
  "character_matrix": "角色矩阵内容...",
  "emotional_arcs": "情感弧线内容...",
  "message": "大纲生成成功"
}
```

### 智能写单章

```http
POST /orchestrator/write-chapter
```

**请求体**:
```json
{
  "book_id": 1,
  "chapter_num": 1,
  "use_llm": true
}
```

**响应**:
```json
{
  "book_id": 1,
  "chapter_num": 1,
  "title": "第一章 初入异世",
  "content": "章节内容...",
  "word_count": 3000,
  "audit_score": 85.5,
  "continuity_score": 90.0,
  "audit_passed": true,
  "message": "章节写作成功"
}
```

### 智能续写多章

```http
POST /orchestrator/continue-chapters
```

**请求体**:
```json
{
  "book_id": 1,
  "start_chapter": 1,
  "count": 5,
  "use_llm": true
}
```

**响应**:
```json
{
  "book_id": 1,
  "start_chapter": 1,
  "end_chapter": 5,
  "chapters_written": 5,
  "results": [
    {
      "chapter_num": 1,
      "title": "第一章 初入异世",
      "word_count": 3000,
      "audit_score": 85.5,
      "audit_passed": true
    },
    ...
  ],
  "message": "成功续写5章"
}
```

### 获取书籍上下文

```http
GET /orchestrator/books/{book_id}/context
```

**响应**:
```json
{
  "book_id": 1,
  "title": "书名",
  "genre": "玄幻",
  "platform": "起点",
  "outline": "大纲内容",
  "story_bible": "世界观设定",
  "volume_outline": "卷纲规划",
  "current_state": "当前状态",
  "context_hash": "abc123"
}
```

### 刷新书籍上下文

```http
POST /orchestrator/books/{book_id}/context/refresh
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见HTTP状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

---

## 完整示例

### 使用curl创建完整小说

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

# 1. 创建书籍
echo "Creating book..."
BOOK=$(curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "修仙之路",
    "genre": "仙侠",
    "platform": "起点",
    "chapter_words": 3000,
    "target_chapters": 100
  }')
BOOK_ID=$(echo $BOOK | jq -r '.id')
echo "Book ID: $BOOK_ID"

# 2. 生成大纲
echo "Generating outline..."
curl -s -X POST "$BASE_URL/orchestrator/generate-outline" \
  -H "Content-Type: application/json" \
  -d "{\"book_id\": $BOOK_ID, \"use_llm\": true}" | jq

# 3. 写前3章
for i in 1 2 3; do
  echo "Writing chapter $i..."
  curl -s -X POST "$BASE_URL/orchestrator/write-chapter" \
    -H "Content-Type: application/json" \
    -d "{\"book_id\": $BOOK_ID, \"chapter_num\": $i, \"use_llm\": true}" | jq '.title, .word_count, .audit_score'
done

echo "Done!"
```

### 使用Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 创建书籍
book = requests.post(f"{BASE_URL}/books", json={
    "title": "我的小说",
    "genre": "玄幻",
    "platform": "起点"
}).json()

book_id = book["id"]

# 生成大纲
outline = requests.post(
    f"{BASE_URL}/orchestrator/generate-outline",
    json={"book_id": book_id, "use_llm": True}
).json()

print(f"Story Bible: {outline['story_bible'][:200]}...")

# 写章节
for i in range(1, 4):
    chapter = requests.post(
        f"{BASE_URL}/orchestrator/write-chapter",
        json={"book_id": book_id, "chapter_num": i, "use_llm": True}
    ).json()
    print(f"Chapter {i}: {chapter['title']} - {chapter['word_count']} words - Score: {chapter['audit_score']}")
```
