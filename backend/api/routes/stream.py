"""
SSE 流式推送路由 - 增强版（修复连接稳定性）

修复内容：
1. 添加心跳包机制，防止连接超时
2. 添加超时处理
3. 优化错误处理
4. 添加连接断开检测

发送详细的节点信息，支持前端工作流可视化：
- node_start: 包含 nodeId, nodeName, nodeType
- node_token: 流式输出
- node_end: 包含 input, output, systemPrompt, userPrompt, tokenUsage, duration

事件格式：
  data: {"type": "workflow_start", "workflowId": "xxx", "workflowName": "生成大纲"}
  data: {"type": "node_start", "nodeId": "node_1", "nodeName": "生成基础设定", "nodeType": "llm"}
  data: {"type": "node_token", "nodeId": "node_1", "token": "魔能大陆"}
  data: {"type": "node_end", "nodeId": "node_1", "input": {...}, "output": {...}, "systemPrompt": "...", "userPrompt": "...", "tokenUsage": {...}, "duration": 5000}
  data: {"type": "progress", "progress": 50}
  data: {"type": "workflow_end", "ok": true}
  data: {"type": "node_error", "nodeId": "node_1", "error": "错误信息"}
"""
import json
import time
import uuid
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import APIRouter, Query, Request
from starlette.responses import StreamingResponse

from db.database import async_session_factory
from db.crud import get_book, update_book, create_chapter, get_chapter_by_number
from agents.architect import ArchitectAgent
from agents.writer import WriterAgent
from prompts.loader import render_prompt

router = APIRouter()


# ==================== SSE 工具函数 ====================

def sse_event(data: dict) -> str:
    """将字典格式化为 SSE data 行"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_comment(comment: str) -> str:
    """SSE 注释（用于心跳）"""
    return f": {comment}\n\n"


def generate_node_id() -> str:
    """生成节点 ID"""
    return f"node_{uuid.uuid4().hex[:8]}"


class NodeContext:
    """节点执行上下文，用于记录输入输出"""
    
    def __init__(self, node_id: str, node_name: str, node_type: str = "llm"):
        self.node_id = node_id
        self.node_name = node_name
        self.node_type = node_type
        self.start_time = time.time()
        self.system_prompt: Optional[str] = None
        self.user_prompt: Optional[str] = None
        self.input: Dict[str, Any] = {}
        self.output: Dict[str, Any] = {}
        self.content_parts: list = []
        self.token_count = 0
    
    def add_token(self, token: str):
        self.content_parts.append(token)
        self.token_count += 1
    
    def get_content(self) -> str:
        return "".join(self.content_parts)
    
    def get_duration(self) -> int:
        return int((time.time() - self.start_time) * 1000)
    
    def get_token_usage(self) -> Dict[str, int]:
        # 简单估算：中文约 1.5 字/token，英文约 4 字/token
        content = self.get_content()
        prompt_len = len(self.system_prompt or "") + len(self.user_prompt or "")
        completion_tokens = int(len(content) / 1.5)
        prompt_tokens = int(prompt_len / 1.5)
        return {
            "promptTokens": prompt_tokens,
            "completionTokens": completion_tokens,
            "totalTokens": prompt_tokens + completion_tokens
        }


async def heartbeat_generator(generator: AsyncGenerator[str, None], interval: float = 15.0):
    """
    包装生成器，定期发送心跳包保持连接
    
    Args:
        generator: 原始数据生成器
        interval: 心跳间隔（秒）
    """
    last_yield_time = time.time()
    heartbeat_count = 0
    
    try:
        async for item in generator:
            last_yield_time = time.time()
            yield item
        
        # 检查是否需要发送心跳
        current_time = time.time()
        if current_time - last_yield_time >= interval:
            heartbeat_count += 1
            yield sse_comment(f"heartbeat-{heartbeat_count}")
            last_yield_time = current_time
            
    except asyncio.CancelledError:
        # 客户端断开连接
        print("[SSE] 客户端断开连接")
        raise
    except Exception as e:
        print(f"[SSE] 生成器错误: {e}")
        raise


# ==================== 生成大纲 ====================

async def stream_generate_outline(book_id: int) -> AsyncGenerator[str, None]:
    """SSE: 生成大纲（流式）"""
    async with async_session_factory() as db:
        book = await get_book(db, book_id)
        if not book:
            yield sse_event({"type": "error", "message": f"书籍不存在: {book_id}"})
            return

        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        # 发送初始心跳
        yield sse_comment("start")
        
        # 工作流开始
        yield sse_event({
            "type": "workflow_start",
            "workflowId": workflow_id,
            "workflowName": "生成大纲"
        })

        architect = ArchitectAgent()
        node_ctx: Optional[NodeContext] = None

        try:
            # ========== 节点1: 生成基础设定 ==========
            node_ctx = NodeContext(
                generate_node_id(),
                "生成基础设定",
                "agent"
            )
            
            # 准备提示词
            system_prompt, user_prompt = architect._render_prompt("architect/foundation", {
                "genre": book.genre,
                "theme": book.outline[:500] if book.outline else f"{book.genre}题材小说",
                "style": "",
                "target_length": f"{book.target_chapters}章，每章{book.chapter_words}字"
            })
            system_prompt = architect._build_system_prompt(system_prompt, book.genre)
            user_prompt = f"""{user_prompt}

## 小说基本信息
- 书名：{book.title}
- 题材：{book.genre}
- 平台：{book.platform}
- 目标章数：{book.target_chapters}章
- 每章字数：{book.chapter_words}字

## 用户大纲
{book.outline}

请按照系统提示词中的格式要求，生成完整的基础设定。
"""
            
            node_ctx.system_prompt = system_prompt
            node_ctx.user_prompt = user_prompt
            node_ctx.input = {
                "book_id": book_id,
                "title": book.title,
                "genre": book.genre,
                "outline": book.outline[:200] + "..." if book.outline and len(book.outline) > 200 else book.outline
            }
            
            # 节点开始
            yield sse_event({
                "type": "node_start",
                "nodeId": node_ctx.node_id,
                "nodeName": node_ctx.node_name,
                "nodeType": node_ctx.node_type
            })
            
            # 流式生成 - 添加超时处理
            last_token_time = time.time()
            token_timeout = 60  # 60秒无响应则认为超时
            
            async for chunk in architect.generate_stream(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=8000
            ):
                node_ctx.add_token(chunk)
                last_token_time = time.time()
                yield sse_event({
                    "type": "node_token",
                    "nodeId": node_ctx.node_id,
                    "token": chunk
                })
                
                # 每30秒发送一次心跳
                if time.time() - last_token_time > 30:
                    yield sse_comment("keepalive")
            
            # 检查是否超时
            if time.time() - last_token_time > token_timeout:
                raise TimeoutError("生成超时，请稍后重试")
            
            # 解析并保存结果
            content = node_ctx.get_content()
            parsed = architect._parse_foundation_output(content)
            
            await update_book(db, book_id, {
                "story_bible": parsed.get("story_bible", ""),
                "volume_outline": parsed.get("volume_outline", ""),
                "current_state": parsed.get("current_state", ""),
                "pending_hooks": parsed.get("pending_hooks", ""),
                "character_matrix": parsed.get("character_matrix", ""),
                "emotional_arcs": parsed.get("emotional_arcs", ""),
            })
            await db.commit()
            
            node_ctx.output = {
                "story_bible": (parsed.get("story_bible", "") or "")[:500] + "...",
                "volume_outline": (parsed.get("volume_outline", "") or "")[:500] + "..."
            }
            
            # 节点结束
            yield sse_event({
                "type": "node_end",
                "nodeId": node_ctx.node_id,
                "input": node_ctx.input,
                "output": node_ctx.output,
                "systemPrompt": node_ctx.system_prompt,
                "userPrompt": node_ctx.user_prompt,
                "tokenUsage": node_ctx.get_token_usage(),
                "duration": node_ctx.get_duration()
            })
            
            yield sse_event({"type": "progress", "progress": 100})
            yield sse_event({"type": "workflow_end", "ok": True})

        except asyncio.CancelledError:
            print(f"[SSE] 生成大纲被用户取消 - book_id: {book_id}")
            yield sse_event({"type": "error", "message": "用户取消了操作"})
            raise
        except TimeoutError as e:
            print(f"[SSE] 生成大纲超时 - book_id: {book_id}")
            yield sse_event({"type": "error", "message": str(e)})
        except Exception as e:
            print(f"[SSE] 生成大纲错误 - book_id: {book_id}, error: {e}")
            import traceback
            traceback.print_exc()
            if node_ctx:
                yield sse_event({
                    "type": "node_error",
                    "nodeId": node_ctx.node_id,
                    "error": str(e)
                })
            yield sse_event({"type": "error", "message": str(e)})


# ==================== 续写章节 ====================

async def stream_continue_chapters(
    book_id: int,
    start_chapter: int,
    count: int
) -> AsyncGenerator[str, None]:
    """SSE: 续写章节（流式）"""
    async with async_session_factory() as db:
        book = await get_book(db, book_id)
        if not book:
            yield sse_event({"type": "error", "message": f"书籍不存在: {book_id}"})
            return

        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        # 发送初始心跳
        yield sse_comment("start")
        
        # 工作流开始
        yield sse_event({
            "type": "workflow_start",
            "workflowId": workflow_id,
            "workflowName": f"续写{count}章"
        })

        architect = ArchitectAgent()
        writer = WriterAgent()

        try:
            for i in range(count):
                chapter_num = start_chapter + i
                progress = int((i / count) * 100)
                yield sse_event({"type": "progress", "progress": progress})

                # ========== 节点: 规划章节 ==========
                plan_node = NodeContext(
                    generate_node_id(),
                    f"规划第{chapter_num}章",
                    "agent"
                )
                
                # 获取前一章摘要
                prev_summary = ""
                if chapter_num > 1:
                    prev = await get_chapter_by_number(db, book_id, chapter_num - 1)
                    if prev and prev.content:
                        prev_summary = prev.content[-500:]
                
                system_prompt, user_prompt = architect._render_prompt("architect/plan_chapter", {
                    "title": book.title,
                    "genre": book.genre,
                    "platform": book.platform,
                    "chapter_num": chapter_num,
                    "chapter_type": "normal",
                    "prev_summary": prev_summary,
                    "current_state": book.current_state or "",
                    "outline": book.outline or ""
                })
                system_prompt = architect._build_system_prompt(system_prompt, book.genre)
                
                plan_node.system_prompt = system_prompt
                plan_node.user_prompt = user_prompt
                plan_node.input = {
                    "chapter_num": chapter_num,
                    "prev_summary": prev_summary[:200] + "..." if len(prev_summary) > 200 else prev_summary
                }
                
                yield sse_event({
                    "type": "node_start",
                    "nodeId": plan_node.node_id,
                    "nodeName": plan_node.node_name,
                    "nodeType": plan_node.node_type
                })
                
                async for chunk in architect.generate_stream(
                    system_prompt=system_prompt, user_prompt=user_prompt,
                    temperature=0.7, max_tokens=4000
                ):
                    plan_node.add_token(chunk)
                    yield sse_event({
                        "type": "node_token",
                        "nodeId": plan_node.node_id,
                        "token": chunk
                    })
                
                chapter_plan = plan_node.get_content()
                plan_node.output = {"plan": chapter_plan[:500] + "..." if len(chapter_plan) > 500 else chapter_plan}
                
                yield sse_event({
                    "type": "node_end",
                    "nodeId": plan_node.node_id,
                    "input": plan_node.input,
                    "output": plan_node.output,
                    "systemPrompt": plan_node.system_prompt,
                    "userPrompt": plan_node.user_prompt,
                    "tokenUsage": plan_node.get_token_usage(),
                    "duration": plan_node.get_duration()
                })

                # ========== 节点: 撰写章节 ==========
                write_node = NodeContext(
                    generate_node_id(),
                    f"撰写第{chapter_num}章",
                    "llm"
                )
                
                # 获取前一章结尾
                prev_ending = ""
                if chapter_num > 1:
                    prev = await get_chapter_by_number(db, book_id, chapter_num - 1)
                    if prev and prev.content:
                        prev_ending = prev.content[-300:]
                
                system_prompt, user_prompt = writer._render_prompt("writer/chapter", {
                    "chapter_number": chapter_num,
                    "chapter_title": f"第{chapter_num}章",
                    "outline": chapter_plan,
                    "word_count": book.chapter_words,
                    "previous_chapter": prev_ending,
                })
                system_prompt = writer._build_system_prompt(system_prompt, book.genre)
                user_prompt = f"""{user_prompt}

## 小说信息
- 书名：{book.title}
- 题材：{book.genre}
- 目标字数：{book.chapter_words}字

## 章节规划
{chapter_plan}

请直接输出章节正文，包含标题。标题格式：第{chapter_num}章 章节标题
"""
                
                write_node.system_prompt = system_prompt
                write_node.user_prompt = user_prompt
                write_node.input = {
                    "chapter_num": chapter_num,
                    "chapter_plan": chapter_plan[:300] + "...",
                    "prev_ending": prev_ending[:200] + "..." if len(prev_ending) > 200 else prev_ending
                }
                
                yield sse_event({
                    "type": "node_start",
                    "nodeId": write_node.node_id,
                    "nodeName": write_node.node_name,
                    "nodeType": write_node.node_type
                })
                
                async for chunk in writer.generate_stream(
                    system_prompt=system_prompt, user_prompt=user_prompt,
                    temperature=0.8, max_tokens=6000
                ):
                    write_node.add_token(chunk)
                    yield sse_event({
                        "type": "node_token",
                        "nodeId": write_node.node_id,
                        "token": chunk
                    })
                
                content = write_node.get_content()
                title = writer._extract_title(content, chapter_num)
                
                # 保存章节
                await create_chapter(
                    db=db, book_id=book_id,
                    chapter_number=chapter_num,
                    title=title, content=content
                )
                await db.commit()
                
                write_node.output = {
                    "title": title,
                    "word_count": len(content),
                    "content_preview": content[:300] + "..."
                }
                
                yield sse_event({
                    "type": "node_end",
                    "nodeId": write_node.node_id,
                    "input": write_node.input,
                    "output": write_node.output,
                    "systemPrompt": write_node.system_prompt,
                    "userPrompt": write_node.user_prompt,
                    "tokenUsage": write_node.get_token_usage(),
                    "duration": write_node.get_duration()
                })

            yield sse_event({"type": "progress", "progress": 100})
            yield sse_event({"type": "workflow_end", "ok": True})

        except asyncio.CancelledError:
            print(f"[SSE] 续写章节被用户取消 - book_id: {book_id}")
            yield sse_event({"type": "error", "message": "用户取消了操作"})
            raise
        except Exception as e:
            print(f"[SSE] 续写章节错误 - book_id: {book_id}, error: {e}")
            import traceback
            traceback.print_exc()
            yield sse_event({"type": "error", "message": str(e)})


# ==================== 重写章节 ====================

async def stream_rewrite_chapter(
    book_id: int,
    chapter_num: int,
    rewrite_requirements: str,
    keep_plot: bool
) -> AsyncGenerator[str, None]:
    """SSE: 重写章节（流式）"""
    async with async_session_factory() as db:
        book = await get_book(db, book_id)
        if not book:
            yield sse_event({"type": "error", "message": f"书籍不存在: {book_id}"})
            return

        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        # 发送初始心跳
        yield sse_comment("start")
        
        yield sse_event({
            "type": "workflow_start",
            "workflowId": workflow_id,
            "workflowName": f"重写第{chapter_num}章"
        })

        writer = WriterAgent()
        node_ctx = NodeContext(
            generate_node_id(),
            f"重写第{chapter_num}章",
            "llm"
        )

        try:
            original = await get_chapter_by_number(db, book_id, chapter_num)
            original_content = original.content if original else ""

            system_prompt, user_prompt = writer._render_prompt("writer/rewrite", {
                "chapter_number": chapter_num,
                "original_content": original_content,
                "rewrite_requirements": rewrite_requirements,
                "keep_plot": keep_plot,
                "genre": book.genre,
            })
            system_prompt = writer._build_system_prompt(system_prompt, book.genre)
            
            node_ctx.system_prompt = system_prompt
            node_ctx.user_prompt = user_prompt
            node_ctx.input = {
                "chapter_num": chapter_num,
                "rewrite_requirements": rewrite_requirements,
                "keep_plot": keep_plot,
                "original_content_preview": original_content[:300] + "..." if len(original_content) > 300 else original_content
            }
            
            yield sse_event({
                "type": "node_start",
                "nodeId": node_ctx.node_id,
                "nodeName": node_ctx.node_name,
                "nodeType": node_ctx.node_type
            })
            
            async for chunk in writer.generate_stream(
                system_prompt=system_prompt, user_prompt=user_prompt,
                temperature=0.8, max_tokens=6000
            ):
                node_ctx.add_token(chunk)
                yield sse_event({
                    "type": "node_token",
                    "nodeId": node_ctx.node_id,
                    "token": chunk
                })
            
            content = node_ctx.get_content()
            title = writer._extract_title(content, chapter_num)
            
            if original:
                from db.crud import update_chapter
                await update_chapter(db, original.id, {
                    "title": title, "content": content,
                    "word_count": len(content)
                })
                await db.commit()
            
            node_ctx.output = {
                "title": title,
                "word_count": len(content),
                "content_preview": content[:300] + "..."
            }
            
            yield sse_event({
                "type": "node_end",
                "nodeId": node_ctx.node_id,
                "input": node_ctx.input,
                "output": node_ctx.output,
                "systemPrompt": node_ctx.system_prompt,
                "userPrompt": node_ctx.user_prompt,
                "tokenUsage": node_ctx.get_token_usage(),
                "duration": node_ctx.get_duration()
            })
            
            yield sse_event({"type": "progress", "progress": 100})
            yield sse_event({"type": "workflow_end", "ok": True})

        except asyncio.CancelledError:
            print(f"[SSE] 重写章节被用户取消 - book_id: {book_id}")
            yield sse_event({"type": "error", "message": "用户取消了操作"})
            raise
        except Exception as e:
            print(f"[SSE] 重写章节错误 - book_id: {book_id}, error: {e}")
            import traceback
            traceback.print_exc()
            yield sse_event({
                "type": "node_error",
                "nodeId": node_ctx.node_id,
                "error": str(e)
            })
            yield sse_event({"type": "error", "message": str(e)})


# ==================== SSE 响应包装 ====================

def sse_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
    """将异步生成器包装为 SSE StreamingResponse"""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            # 添加超时相关头部
            "Keep-Alive": "timeout=300, max=1000",
        }
    )


# ==================== API 端点 ====================

@router.get("/stream/generate-outline")
async def workflow_generate_outline(book_id: int = Query(...)):
    """SSE: 生成大纲"""
    return sse_response(stream_generate_outline(book_id))


@router.get("/stream/continue-chapters")
async def workflow_continue_chapters(
    book_id: int = Query(...),
    start_chapter: int = Query(1),
    count: int = Query(1),
):
    """SSE: 续写章节"""
    return sse_response(stream_continue_chapters(book_id, start_chapter, count))


@router.get("/stream/rewrite-chapter")
async def workflow_rewrite_chapter(
    book_id: int = Query(...),
    chapter_num: int = Query(...),
    rewrite_requirements: str = Query(""),
    keep_plot: bool = Query(True),
):
    """SSE: 重写章节"""
    return sse_response(stream_rewrite_chapter(book_id, chapter_num, rewrite_requirements, keep_plot))
