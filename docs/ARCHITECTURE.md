# StoryClaw 架构说明（Agent 收敛 + 薄网关版）

本文件记录一次结构性重构后的目标架构：**Agent 能力全部收敛进
`packages/storyclaw` 包，backend 瘦身为薄网关，单一运行时代理 LangGraph**。

## 1. 分层

```
frontend/                      React SPA（单一站点，按 user.version 条件渲染）
backend/app/                   薄网关：鉴权 / CRUD / 计费 / 转发
  ├── api/                     路由层（REST，不含 agent 编排逻辑）
  ├── services/                服务封装（llm/memory/skill_loader/embedding_config）
  └── main.py                  生命周期：注入 deps + 重建 agent 图
packages/storyclaw/src/storyclaw/   ★ Agent 运行时（唯一实现地）
  ├── config.py                设置（skills 目录解析、Milvus/Neo4j/embedding 连接）
  ├── deps.py                  StoryClawDeps：依赖注入容器（llm/memory/context/rag/checkpointer）
  ├── graph.py                 图编排：outline_graph + 主 agent 图（9 节点 17 边）
  ├── nodes/                   7 个节点（supervisor/writer/reviewer/researcher/analyst/assistant/chat）
  ├── runtime.py               run_agent / stream_agent / sse / get_graph
  ├── llm.py                   build_chat_client（openai_chat/anthropic/openai_responses 三格式）
  ├── memory.py                短期/长期记忆编解码与合并
  ├── context.py               写作上下文（字数/前文摘要/大纲定位）
  ├── skills.py                DeerFlow 风格 skill 发现/描述/加载
  ├── prompts.py               system prompt 集中管理
  ├── checkpointer.py          build_checkpointer：PostgresSaver（失败降级 InMemorySaver）
  └── rag/
      ├── chunker.py / embedding.py   文本切片 / embedding 解析
      ├── milvus_store.py      Milvus 向量库（collection: chunks_u{user}_b{book}）
      ├── neo4j_store.py       Neo4j 图谱（StoryEntity/Book/Chapter/User + REL/APPEARS_IN…）
      ├── memory_store.py      连接失败时内存降级
      └── service.py           ingest_text / query_context / get_status / related_to_name
```

## 2. 单一运行时（去掉 langgraph-server）

- 旧结构：docker-compose 里独立 `langgraph-server` + backend 又直接 import
  `storyclaw.graph`，形成“两套”运行时。
- 新结构：**只有 backend 进程加载 `storyclaw` 包**。`main.py` lifespan 里
  `storyclaw.deps.configure(...)` 注入 llm 工厂 / 记忆 / 上下文 / embedding /
  checkpointer，然后 `rebuild_graph()` 用真实依赖编译图。
- docker-compose 已删除 `langgraph-server` 服务与 `langgraph.Dockerfile`。

## 3. RAG 存储

- Milvus：`chunks_u{user_id}_b{book_id}`，dim 默认 1024（env `MILVUS_VECTOR_DIM`），
  IVF_FLAT + COSINE。
- Neo4j：`StoryEntity{user_id,book_id,name,entity_type,description}`，关系
  `REL{type,chapter_id}` / `APPEARS_IN{chapter_id}` / `HAS_CHAPTER` / `WROTE`，
  跨章同名实体 MERGE 合并。
- 连接失败自动降级到内存 store（开发环境无 Milvus/Neo4j 也能跑）。
- 旧的 PG 三张 RAG 表（rag_chunks/rag_entities/rag_relations）与 `models/rag.py`
  保留（兼容历史数据），但新数据写入走 Milvus/Neo4j。

## 4. 断点恢复

- `checkpointer.py::build_checkpointer(dsn)`：优先 `AsyncPostgresSaver`（复用
  backend 同一 PG 实例，`+asyncpg` 后缀剥离），失败降级 `InMemorySaver`。
- 依赖：`langgraph-checkpoint-postgres>=2.0,<3` + `psycopg[binary]>=3.1,<4`。

## 5. 依赖注意事项（踩坑记录）

- pymilvus 2.4 依赖 `pkg_resources` → **setuptools 必须 `<81`**（81+ 已移除）。
- pymilvus 2.4 需要 **marshmallow<4**。
- `storyclaw` 包内 `__init__.py` 导出编译图为 `storyclaw.agent_graph`；
  `storyclaw.graph` 保持为模块（含 `outline_graph`，兼容 `api/outlines.py`）。
- 旧公开名迁移：`set_llm_factory`→`storyclaw.llm`；`describe_skill/list_skill_index/list_skills`→`storyclaw.skills`。

## 6. 前端（单一网站）

- `frontend/src/App.tsx` 是单一 SPA 路由；`components/Layout.tsx` 按注册的
  `user.version`（local/business）条件渲染：本地版显示“LLM 配置”，商业版右上角
  显示剩余积分 + 充值入口。不拆两套站点。
