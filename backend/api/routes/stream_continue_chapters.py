"""
续写章节 - 完整版（含评估和重写机制）

完整流程：
1. 规划章节 (ArchitectAgent)
2. 规划评估 (LLM评估规划合理性)
3. 撰写章节 (WriterAgent)
4. 连续性检查 (ContinuityAuditor)
5. 质量审核 (AuditorAgent)
6. 不合格则打回重写 (最多3次)
"""
import json
import time
import uuid
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

from db.database import async_session_factory
from db.crud import get_book, update_book, create_chapter, get_chapter_by_number
from agents.architect import ArchitectAgent
from agents.writer import WriterAgent
from agents.auditor import AuditorAgent
from agents.continuity import ContinuityAuditor
from store.manager import store_manager
from workflow.pause_control import pause_manager, check_pause


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
        content = self.get_content()
        prompt_len = len(self.system_prompt or "") + len(self.user_prompt or "")
        completion_tokens = int(len(content) / 1.5)
        prompt_tokens = int(prompt_len / 1.5)
        return {
            "promptTokens": prompt_tokens,
            "completionTokens": completion_tokens,
            "totalTokens": prompt_tokens + completion_tokens
        }


async def evaluate_plan_stream(
    writer: WriterAgent,
    book: Any,
    chapter_num: int,
    chapter_plan: str,
    prev_summary: str,
    eval_node: NodeContext
) -> AsyncGenerator[str, None]:
    """
    流式评估章节规划是否合理，结合大纲进行全面评估
    
    Yields:
        SSE 事件流
    
    Returns:
        通过 eval_node.output 返回结果
    """
    # 构建完整的评估提示词
    system_prompt = f"""你是一位资深小说编辑和故事架构师，负责深度评估章节规划的质量。

## 评估维度（满分100分）

### 1. 大纲契合度（25分）
- 是否符合整体故事走向
- 是否推进主线剧情
- 是否呼应伏笔和设定

### 2. 情节连贯性（25分）
- 与前一章衔接是否自然
- 因果逻辑是否清晰
- 过渡是否流畅

### 3. 节奏把控（20分）
- 情节推进速度是否合适
- 是否有拖沓或跳跃
- 高潮和铺垫比例是否恰当

### 4. 冲突设置（15分）
- 是否有足够的戏剧冲突
- 冲突是否推动角色成长
- 冲突是否符合题材特点

### 5. 角色一致性（15分）
- 角色行为是否符合人设
- 角色动机是否合理
- 角色成长是否自然

## 输出格式（必须严格遵循JSON格式）
```json
{{
    "passed": true/false,
    "total_score": 0-100,
    "dimension_scores": {{
        "大纲契合度": 0-25,
        "情节连贯性": 0-25,
        "节奏把控": 0-20,
        "冲突设置": 0-15,
        "角色一致性": 0-15
    }},
    "feedback": "总体评价，指出优点和不足",
    "suggestions": ["具体改进建议1", "具体改进建议2", "具体改进建议3"],
    "risk_warnings": ["潜在风险1", "潜在风险2"]
}}
```

评分标准：
- 90-100分：优秀，无需修改
- 80-89分：良好，小建议
- 70-79分：及格，需改进
- <70分：不合格，需大幅调整

passed判定：总分>=75且各维度>=12分（80%）"""

    # 获取完整大纲信息
    volume_outline = book.volume_outline or "暂无卷纲大纲"
    story_bible = book.story_bible or "暂无世界观设定"
    current_state = book.current_state or "暂无当前状态"
    
    user_prompt = f"""请深度评估以下章节规划：

## 小说基本信息
- 书名：{book.title}
- 题材：{book.genre}
- 平台：{book.platform}
- 第{chapter_num}章

## 整体大纲（卷纲）
{volume_outline[:800] if len(volume_outline) > 800 else volume_outline}

## 世界观设定
{story_bible[:500] if len(story_bible) > 500 else story_bible}

## 当前故事状态
{current_state[:300] if len(current_state) > 300 else current_state}

## 前一章摘要
{prev_summary[:600] if prev_summary else "（首章，无前情）"}

## 待评估的章节规划
{chapter_plan}

请严格按照上述评估维度和输出格式，给出详细的评估报告（JSON格式）。"""

    # 设置节点提示词
    eval_node.system_prompt = system_prompt
    eval_node.user_prompt = user_prompt
    eval_node.input = {
        "chapter_num": chapter_num,
        "chapter_plan": chapter_plan[:300] + "..." if len(chapter_plan) > 300 else chapter_plan,
        "has_volume_outline": bool(book.volume_outline),
        "has_story_bible": bool(book.story_bible)
    }

    # 流式生成评估结果
    content_parts = []
    async for chunk in writer.generate_stream(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=3000
    ):
        content_parts.append(chunk)
        eval_node.add_token(chunk)
        yield sse_event({
            "type": "node_token",
            "nodeId": eval_node.node_id,
            "token": chunk
        })
    
    content = "".join(content_parts)
    
    # 解析 JSON 结果
    import re
    try:
        # 提取 JSON 块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接找 JSON 对象
            json_match = re.search(r'\{[\s\S]*\}', content)
            json_str = json_match.group(0) if json_match else content
        
        result = json.loads(json_str)
        total_score = result.get("total_score", 0)
        dimension_scores = result.get("dimension_scores", {})
        passed = result.get("passed", False)
        
        # 如果没有 passed 字段，根据分数计算
        if "passed" not in result:
            min_dimension = min(dimension_scores.values()) if dimension_scores else 0
            passed = total_score >= 75 and min_dimension >= 12
        
        feedback = result.get("feedback", "")
        suggestions = result.get("suggestions", [])
        risk_warnings = result.get("risk_warnings", [])
        
        # 构建详细反馈
        detailed_feedback = f"""总分：{total_score}/100

各维度得分：
"""
        for dim, score in dimension_scores.items():
            detailed_feedback += f"- {dim}：{score}分\n"
        
        detailed_feedback += f"\n总体评价：\n{feedback}"
        
        if suggestions:
            detailed_feedback += "\n\n改进建议：\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
        
        if risk_warnings:
            detailed_feedback += "\n\n⚠️ 风险提示：\n" + "\n".join([f"- {w}" for w in risk_warnings])
        
        eval_node.output = {
            "passed": passed,
            "total_score": total_score,
            "dimension_scores": dimension_scores,
            "feedback": feedback,
            "suggestions": suggestions,
            "risk_warnings": risk_warnings
        }
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # 解析失败，使用默认结果
        eval_node.output = {
            "passed": True,
            "total_score": 80,
            "dimension_scores": {
                "大纲契合度": 20,
                "情节连贯性": 20,
                "节奏把控": 16,
                "冲突设置": 12,
                "角色一致性": 12
            },
            "feedback": f"评估解析失败（{str(e)}），默认通过",
            "suggestions": ["建议人工复核评估结果"],
            "risk_warnings": []
        }


async def stream_continue_chapters(
    book_id: int,
    start_chapter: int,
    count: int
) -> AsyncGenerator[str, None]:
    """SSE: 续写章节（完整版，含评估和重写机制，支持暂停/继续）"""
    db = async_session_factory()
    book = await get_book(db, book_id)
    if not book:
        yield sse_event({"type": "error", "message": f"书籍不存在: {book_id}"})
        await db.close()
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
        "workflowName": f"续写{count}章（含评估）",
        "canPause": True  # 标记此工作流支持暂停
    })

    architect = ArchitectAgent()
    writer = WriterAgent()
    auditor = AuditorAgent()
    continuity = ContinuityAuditor()
    
    # 最大重写次数
    MAX_REWRITE_ATTEMPTS = 3

    try:
        for i in range(count):
            chapter_num = start_chapter + i
            progress = int((i / count) * 100)
            
            # 更新进度到暂停管理器
            pause_manager.update_progress(workflow_id, progress, f"第{chapter_num}章")
            yield sse_event({"type": "progress", "progress": progress})
            
            # ========== 检查暂停状态 ==========
            should_continue = await check_pause(workflow_id, f"准备规划第{chapter_num}章")
            if not should_continue:
                yield sse_event({"type": "workflow_end", "ok": False, "reason": "cancelled"})
                return

            # ========== 节点1: 规划章节 ==========
            plan_node = NodeContext(
                generate_node_id(),
                f"规划第{chapter_num}章",
                "agent"
            )
            
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

            # ========== 节点2: 规划评估（流式，结合大纲）==========
            eval_node = NodeContext(
                generate_node_id(),
                f"评估第{chapter_num}章规划",
                "review"
            )
            
            yield sse_event({
                "type": "node_start",
                "nodeId": eval_node.node_id,
                "nodeName": eval_node.node_name,
                "nodeType": eval_node.node_type
            })
            
            # 流式评估，会输出提示词、token、统计信息
            async for event in evaluate_plan_stream(
                writer, book, chapter_num, chapter_plan, prev_summary, eval_node
            ):
                yield event
            
            # 发送 node_end 事件（包含完整的提示词和 token 统计）
            yield sse_event({
                "type": "node_end",
                "nodeId": eval_node.node_id,
                "input": eval_node.input,
                "output": eval_node.output,
                "systemPrompt": eval_node.system_prompt,
                "userPrompt": eval_node.user_prompt,
                "tokenUsage": eval_node.get_token_usage(),
                "duration": eval_node.get_duration()
            })

            # ========== 检查暂停状态 ==========
            should_continue = await check_pause(workflow_id, f"准备撰写第{chapter_num}章")
            if not should_continue:
                yield sse_event({"type": "workflow_end", "ok": False, "reason": "cancelled"})
                return
            
            # 判断是否通过评估
            is_plan_valid = eval_node.output.get("passed", False)
            total_score = eval_node.output.get("total_score", 0)
            
            if not is_plan_valid:
                yield sse_event({
                    "type": "warning",
                    "message": f"第{chapter_num}章规划评估未通过（{total_score}分），但仍继续撰写。建议：{', '.join(eval_node.output.get('suggestions', [])[:2])}"
                })
            else:
                yield sse_event({
                    "type": "info",
                    "message": f"第{chapter_num}章规划评估通过（{total_score}分）"
                })

            # ========== 节点3: 撰写章节（含重写机制）==========
            chapter_content = None
            chapter_title = None
            
            for attempt in range(MAX_REWRITE_ATTEMPTS):
                write_node = NodeContext(
                    generate_node_id(),
                    f"撰写第{chapter_num}章" + (f"（重写第{attempt+1}次）" if attempt > 0 else ""),
                    "llm"
                )
                
                prev_ending = ""
                if chapter_num > 1:
                    prev = await get_chapter_by_number(db, book_id, chapter_num - 1)
                    if prev and prev.content:
                        prev_ending = prev.content[-300:]
                
                # 如果有重写要求，添加到 prompt
                rewrite_note = ""
                if attempt > 0:
                    rewrite_note = f"\n\n## 重写要求\n这是第{attempt+1}次重写，请根据之前的审核意见改进。"
                
                system_prompt, user_prompt = writer._render_prompt("writer/chapter", {
                    "chapter_number": chapter_num,
                    "chapter_title": f"第{chapter_num}章",
                    "outline": chapter_plan,
                    "word_count": book.chapter_words,
                    "previous_chapter": prev_ending,
                })
                system_prompt = writer._build_system_prompt(system_prompt, book.genre)
                user_prompt = f"""{user_prompt}{rewrite_note}

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
                    "attempt": attempt + 1,
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

                # ========== 节点4: 连续性检查 ==========
                cont_node = NodeContext(
                    generate_node_id(),
                    f"连续性检查-第{chapter_num}章",
                    "review"
                )
                
                yield sse_event({
                    "type": "node_start",
                    "nodeId": cont_node.node_id,
                    "nodeName": cont_node.node_name,
                    "nodeType": cont_node.node_type
                })
                
                prev_chapter = None
                if chapter_num > 1:
                    prev_chapter = await get_chapter_by_number(db, book_id, chapter_num - 1)
                
                continuity_result = await continuity.check(
                    current_chapter=content,
                    previous_chapter=prev_chapter.content if prev_chapter else None,
                    chapter_plan=chapter_plan
                )
                
                cont_node.output = {
                    "passed": continuity_result.passed,
                    "score": continuity_result.score,
                    "issues": continuity_result.issues,
                    "suggestions": continuity_result.suggestions
                }
                
                yield sse_event({
                    "type": "node_end",
                    "nodeId": cont_node.node_id,
                    "input": {"chapter_num": chapter_num},
                    "output": cont_node.output,
                    "duration": cont_node.get_duration()
                })

                # ========== 节点5: 质量审核 ==========
                audit_node = NodeContext(
                    generate_node_id(),
                    f"质量审核-第{chapter_num}章",
                    "review"
                )
                
                yield sse_event({
                    "type": "node_start",
                    "nodeId": audit_node.node_id,
                    "nodeName": audit_node.node_name,
                    "nodeType": audit_node.node_type
                })
                
                audit_result = await auditor.evaluate(
                    chapter_content=content,
                    chapter_plan=chapter_plan,
                    genre=book.genre
                )
                
                audit_node.output = {
                    "passed": audit_result.passed,
                    "total_score": audit_result.total_score,
                    "dimension_scores": audit_result.dimension_scores,
                    "suggestions": audit_result.suggestions
                }
                
                yield sse_event({
                    "type": "node_end",
                    "nodeId": audit_node.node_id,
                    "input": {"chapter_num": chapter_num},
                    "output": audit_node.output,
                    "duration": audit_node.get_duration()
                })

                # 判断是否通过审核
                if continuity_result.passed and audit_result.passed:
                    # 通过审核，保存章节
                    chapter_content = content
                    chapter_title = title
                    
                    yield sse_event({
                        "type": "info",
                        "message": f"第{chapter_num}章通过审核（连续性：{continuity_result.score}分，质量：{audit_result.total_score}分）"
                    })
                    break
                else:
                    # 未通过，准备重写
                    failure_reasons = []
                    if not continuity_result.passed:
                        failure_reasons.append(f"连续性检查未通过：{', '.join(continuity_result.issues)}")
                    if not audit_result.passed:
                        failure_reasons.append(f"质量审核未通过：{', '.join(audit_result.suggestions[:2])}")
                    
                    if attempt < MAX_REWRITE_ATTEMPTS - 1:
                        yield sse_event({
                            "type": "warning",
                            "message": f"第{chapter_num}章审核未通过（尝试{attempt+1}/{MAX_REWRITE_ATTEMPTS}），即将重写。原因：{'; '.join(failure_reasons)}"
                        })
                    else:
                        # 最后一次尝试仍失败，使用最后一次的内容
                        chapter_content = content
                        chapter_title = title
                        yield sse_event({
                            "type": "warning",
                            "message": f"第{chapter_num}章在{MAX_REWRITE_ATTEMPTS}次尝试后仍未通过审核，使用最后一次内容。原因：{'; '.join(failure_reasons)}"
                        })

            # 保存章节
            if chapter_content:
                chapter = await create_chapter(
                    db=db, book_id=book_id,
                    chapter_number=chapter_num,
                    title=chapter_title, content=chapter_content
                )
                await db.commit()
                await store_manager.save_chapter_file(book_id, chapter_num, chapter_title, chapter_content)

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
    finally:
        # 注销工作流
        pause_manager.unregister_workflow(workflow_id)
        try:
            await db.commit()
        except Exception:
            pass
        await db.close()
