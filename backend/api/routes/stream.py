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
from store.manager import store_manager
from workflow.pause_control import pause_manager, check_pause

# 导入完整版续写章节（含评估和重写机制）
from .stream_continue_chapters import stream_continue_chapters

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
    """SSE: 生成大纲（流式，支持暂停/继续）"""
    db = async_session_factory()
    try:
        book = await get_book(db, book_id)
        if not book:
            yield sse_event({"type": "error", "message": f"书籍不存在: {book_id}"})
            return

        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        # 注册工作流到暂停管理器
        pause_manager.register_workflow(workflow_id, "初始化")
        
        # 发送初始心跳
        yield sse_comment("start")
        
        # 工作流开始
        yield sse_event({
            "type": "workflow_start",
            "workflowId": workflow_id,
            "workflowName": "生成大纲",
            "canPause": True  # 标记此工作流支持暂停
        })

        architect = ArchitectAgent()
        node_ctx: Optional[NodeContext] = None
        
        # 检查暂停状态
        should_continue = await check_pause(workflow_id, "准备生成基础设定")
        if not should_continue:
            yield sse_event({"type": "workflow_end", "ok": False, "reason": "cancelled"})
            return

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
            
            # 1. 更新数据库字段
            await update_book(db, book_id, {
                "story_bible": parsed.get("story_bible", ""),
                "volume_outline": parsed.get("volume_outline", ""),
                "current_state": parsed.get("current_state", ""),
                "pending_hooks": parsed.get("pending_hooks", ""),
                "character_matrix": parsed.get("character_matrix", ""),
                "emotional_arcs": parsed.get("emotional_arcs", ""),
            })
            
            # 2. 将生成内容映射并保存到 outline/ 目录的标准文件
            #    工作流生成的字段 -> 前端期望的9个大纲文件
            outline_mapping = {
                "01-worldview.md": parsed.get("story_bible", ""),       # 世界观设定
                "02-characters.md": parsed.get("character_matrix", ""),  # 角色设定
                "03-plot.md": parsed.get("volume_outline", ""),          # 主线剧情
                "04-arcs.md": parsed.get("emotional_arcs", ""),          # 情感弧线
                "05-hooks.md": parsed.get("pending_hooks", ""),          # 伏笔设计
                "08-outline.md": parsed.get("volume_outline", ""),       # 卷纲大纲
                "09-rules.md": parsed.get("book_rules", ""),             # 创作规则
            }
            for filename, file_content in outline_mapping.items():
                if file_content and file_content.strip():
                    await store_manager.save_outline_file(book_id, filename, file_content)
            
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
        finally:
            try:
                await db.commit()
            except Exception:
                pass
    except Exception as e:
        print(f"[SSE] 生成大纲外层错误 - book_id: {book_id}, error: {e}")
        yield sse_event({"type": "error", "message": str(e)})
    finally:
        # 注销工作流
        pause_manager.unregister_workflow(workflow_id)
        await db.close()


# ==================== 重写章节 ====================

async def stream_rewrite_chapter(
    book_id: int,
    chapter_num: int,
    rewrite_requirements: str,
    keep_plot: bool
) -> AsyncGenerator[str, None]:
    """SSE: 重写章节（流式）"""
    db = async_session_factory()
    book = await get_book(db, book_id)
    if not book:
        yield sse_event({"type": "error", "message": f"书籍不存在: {book_id}"})
        await db.close()
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
            # 同时保存到文件系统
            await store_manager.save_chapter_file(book_id, chapter_num, title, content)
        
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
    finally:
        try:
            await db.commit()
        except Exception:
            pass
        await db.close()


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
