"""工作流引擎"""
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.architect import ArchitectAgent
from agents.writer import WriterAgent
from agents.auditor import AuditorAgent
from agents.continuity import ContinuityAuditor
from checkpoint.manager import checkpoint_manager
from store.manager import store_manager
from db.crud import get_book, update_book, create_chapter, update_chapter


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.architect = ArchitectAgent()
        self.writer = WriterAgent()
        self.auditor = AuditorAgent()
        self.continuity = ContinuityAuditor()
    
    async def run_generate_outline(
        self,
        workflow_id: str,
        book_id: int,
        db: AsyncSession
    ):
        """运行生成大纲工作流"""
        try:
            # 开始工作流
            await checkpoint_manager.start_workflow(db, workflow_id)
            
            # 获取书籍信息
            book = await get_book(db, book_id)
            
            # Node 1: 生成基础设定
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_1_generate_foundation",
                node_name="生成基础设定",
                agent=self.architect,
                task="generate_foundation",
                db=db,
                book_data={
                    "title": book.title,
                    "genre": book.genre,
                    "platform": book.platform,
                    "outline": book.outline,
                    "target_chapters": book.target_chapters,
                    "chapter_words": book.chapter_words
                }
            )
            
            # 更新书籍
            foundation_result = checkpoint_manager.get_node_status(workflow_id, "node_1_generate_foundation")
            if foundation_result and foundation_result.get("output_data", {}).get("data"):
                data = foundation_result["output_data"]["data"]
                await update_book(db, book_id, {
                    "story_bible": data.get("story_bible", ""),
                    "volume_outline": data.get("volume_outline", ""),
                    "book_rules": data.get("book_rules", ""),
                    "current_state": data.get("current_state", ""),
                    "pending_hooks": data.get("pending_hooks", ""),
                    "character_matrix": data.get("character_matrix", ""),
                    "emotional_arcs": data.get("emotional_arcs", "")
                })
                
                # 保存到 state 目录
                for key in ["story_bible", "volume_outline", "book_rules", 
                           "current_state", "pending_hooks", "character_matrix", "emotional_arcs"]:
                    if data.get(key):
                        await store_manager.save_state_file(book_id, key, data[key])
                
                # 将生成内容映射并保存到 outline/ 目录的标准文件
                outline_mapping = {
                    "01-worldview.md": data.get("story_bible", ""),       # 世界观设定
                    "02-characters.md": data.get("character_matrix", ""),  # 角色设定
                    "03-plot.md": data.get("volume_outline", ""),          # 主线剧情
                    "04-arcs.md": data.get("emotional_arcs", ""),          # 情感弧线
                    "05-hooks.md": data.get("pending_hooks", ""),          # 伏笔设计
                    "08-outline.md": data.get("volume_outline", ""),       # 卷纲大纲
                    "09-rules.md": data.get("book_rules", ""),             # 创作规则
                }
                for filename, file_content in outline_mapping.items():
                    if file_content and file_content.strip():
                        await store_manager.save_outline_file(book_id, filename, file_content)
            
            # 完成工作流
            await checkpoint_manager.complete_workflow(
                db=db,
                workflow_id=workflow_id,
                output_data={"book_id": book_id, "status": "completed"}
            )
            
            # 移除锁
            await store_manager.remove_lock(book_id, "generate_outline")
            
        except Exception as e:
            await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            await store_manager.remove_lock(book_id, "generate_outline")
            raise
    
    async def run_continue_chapters(
        self,
        workflow_id: str,
        book_id: int,
        start_chapter: int,
        count: int,
        external_context: str,
        db: AsyncSession
    ):
        """运行续写章节工作流"""
        try:
            # 开始工作流
            await checkpoint_manager.start_workflow(db, workflow_id)
            
            for i in range(count):
                chapter_num = start_chapter + i
                
                # Node 1: 规划章节
                plan_node_id = f"node_{i*4+1}_plan_chapter"
                await self._execute_node(
                    workflow_id=workflow_id,
                    node_id=plan_node_id,
                    node_name=f"规划第{chapter_num}章",
                    agent=self.architect,
                    task="plan_chapter",
                    db=db,
                    book_id=book_id,
                    chapter_num=chapter_num,
                    chapter_type="auto",
                    external_context=external_context
                )
                
                # 获取章节规划
                plan_result = checkpoint_manager.get_node_status(workflow_id, plan_node_id)
                chapter_plan = plan_result.get("output_data", {}).get("data", {}).get("chapter_plan", "")
                
                # Node 2: 撰写章节
                write_node_id = f"node_{i*4+2}_write_chapter"
                await self._execute_node(
                    workflow_id=workflow_id,
                    node_id=write_node_id,
                    node_name=f"撰写第{chapter_num}章",
                    agent=self.writer,
                    task="write_chapter",
                    db=db,
                    book_id=book_id,
                    chapter_num=chapter_num,
                    chapter_plan=chapter_plan
                )
                
                # 获取章节内容
                write_result = checkpoint_manager.get_node_status(workflow_id, write_node_id)
                chapter_data = write_result.get("output_data", {}).get("data", {})
                
                # 保存章节
                chapter = await create_chapter(
                    db=db,
                    book_id=book_id,
                    chapter_number=chapter_num,
                    title=chapter_data.get("title", f"第{chapter_num}章"),
                    content=chapter_data.get("content", "")
                )
                
                # 保存到store
                await store_manager.save_chapter_file(
                    book_id=book_id,
                    chapter_num=chapter_num,
                    title=chapter_data.get("title", f"第{chapter_num}章"),
                    content=chapter_data.get("content", "")
                )
                
                # Node 3: 审核章节
                audit_node_id = f"node_{i*4+3}_audit_chapter"
                await self._execute_node(
                    workflow_id=workflow_id,
                    node_id=audit_node_id,
                    node_name=f"审核第{chapter_num}章",
                    agent=self.auditor,
                    task="audit_chapter",
                    db=db,
                    book_id=book_id,
                    chapter_num=chapter_num,
                    chapter_content=chapter_data.get("content", "")
                )
                
                # 更新章节审核分数
                audit_result = checkpoint_manager.get_node_status(workflow_id, audit_node_id)
                if audit_result:
                    score = audit_result.get("output_data", {}).get("data", {}).get("total_score", 0)
                    await update_chapter(db, chapter.id, {"audit_score": score})
                
                # Node 4: 检查连续性
                continuity_node_id = f"node_{i*4+4}_check_continuity"
                await self._execute_node(
                    workflow_id=workflow_id,
                    node_id=continuity_node_id,
                    node_name=f"检查第{chapter_num}章连续性",
                    agent=self.continuity,
                    task="check_continuity",
                    db=db,
                    book_id=book_id,
                    chapter_num=chapter_num,
                    chapter_content=chapter_data.get("content", "")
                )
                
                # 更新连续性分数
                continuity_result = checkpoint_manager.get_node_status(workflow_id, continuity_node_id)
                if continuity_result:
                    score = continuity_result.get("output_data", {}).get("data", {}).get("score", 0)
                    await update_chapter(db, chapter.id, {"continuity_score": score})
                
                # 更新进度
                progress = int((i + 1) / count * 100)
                checkpoint_manager._workflows[workflow_id]["progress"] = progress
            
            # 完成工作流
            await checkpoint_manager.complete_workflow(
                db=db,
                workflow_id=workflow_id,
                output_data={
                    "book_id": book_id,
                    "start_chapter": start_chapter,
                    "count": count,
                    "status": "completed"
                }
            )
            
            # 移除锁
            await store_manager.remove_lock(book_id, f"continue_chapter_{start_chapter}")
            
        except Exception as e:
            await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            await store_manager.remove_lock(book_id, f"continue_chapter_{start_chapter}")
            raise
    
    async def run_rewrite_chapter(
        self,
        workflow_id: str,
        book_id: int,
        chapter_num: int,
        rewrite_requirements: str,
        keep_plot: bool,
        db: AsyncSession
    ):
        """运行重写章节工作流"""
        try:
            # 开始工作流
            await checkpoint_manager.start_workflow(db, workflow_id)
            
            # Node 1: 重写章节
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_1_rewrite_chapter",
                node_name=f"重写第{chapter_num}章",
                agent=self.writer,
                task="rewrite_chapter",
                db=db,
                book_id=book_id,
                chapter_num=chapter_num,
                rewrite_requirements=rewrite_requirements,
                keep_plot=keep_plot
            )
            
            # 获取重写结果
            rewrite_result = checkpoint_manager.get_node_status(workflow_id, "node_1_rewrite_chapter")
            chapter_data = rewrite_result.get("output_data", {}).get("data", {})
            
            # 更新章节
            from db.crud import get_chapter_by_number
            chapter = await get_chapter_by_number(db, book_id, chapter_num)
            if chapter:
                await update_chapter(db, chapter.id, {
                    "title": chapter_data.get("title", chapter.title),
                    "content": chapter_data.get("content", chapter.content),
                    "word_count": chapter_data.get("word_count", len(chapter_data.get("content", "")))
                })
            
            # 保存到store
            await store_manager.save_chapter_file(
                book_id=book_id,
                chapter_num=chapter_num,
                title=chapter_data.get("title", f"第{chapter_num}章"),
                content=chapter_data.get("content", "")
            )
            
            # Node 2: 审核
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_2_audit_chapter",
                node_name=f"审核重写后的第{chapter_num}章",
                agent=self.auditor,
                task="audit_chapter",
                db=db,
                book_id=book_id,
                chapter_num=chapter_num,
                chapter_content=chapter_data.get("content", "")
            )
            
            # 完成工作流
            await checkpoint_manager.complete_workflow(
                db=db,
                workflow_id=workflow_id,
                output_data={
                    "book_id": book_id,
                    "chapter_num": chapter_num,
                    "status": "completed"
                }
            )
            
        except Exception as e:
            await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            raise
    
    async def run_protect_and_update(
        self,
        workflow_id: str,
        book_id: int,
        protected_chapter: int,
        new_outline: str,
        db: AsyncSession
    ):
        """工作流④：保护章节并更新大纲"""
        try:
            # 开始工作流
            await checkpoint_manager.start_workflow(db, workflow_id)

            # 获取书籍信息
            book = await get_book(db, book_id)

            # Node 1: 分析大纲变动影响
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_1_analyze_outline_impact",
                node_name="分析大纲变动影响",
                agent=self.architect,
                task="analyze_outline_impact",
                db=db,
                book_id=book_id,
                protected_chapter=protected_chapter,
                new_outline=new_outline
            )

            # 获取分析结果
            impact_result = checkpoint_manager.get_node_status(workflow_id, "node_1_analyze_outline_impact")
            impact_data = impact_result.get("output_data", {}).get("data", {}) if impact_result else {}

            # Node 2: 更新书籍状态（用protected_chapter作为chapter_num，new_outline作为chapter_content）
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_2_update_book_state",
                node_name="更新书籍状态",
                agent=self.architect,
                task="update_book_state",
                db=db,
                book_id=book_id,
                chapter_num=protected_chapter,
                chapter_content=new_outline,
                impact_analysis=impact_data
            )

            # 获取更新结果
            state_result = checkpoint_manager.get_node_status(workflow_id, "node_2_update_book_state")
            state_data = state_result.get("output_data", {}).get("data", {}) if state_result else {}

            # 更新书籍大纲
            await update_book(db, book_id, {
                "outline": new_outline,
                "current_state": state_data.get("current_state", book.current_state or ""),
                "pending_hooks": state_data.get("pending_hooks", book.pending_hooks or ""),
                "character_matrix": state_data.get("character_matrix", book.character_matrix or ""),
                "emotional_arcs": state_data.get("emotional_arcs", book.emotional_arcs or "")
            })

            # 将 protected_chapter 之后的章节标记为需要重写
            from db.crud import get_chapters_by_book
            all_chapters, _ = await get_chapters_by_book(db, book_id)
            chapters_to_rewrite = [c for c in all_chapters if c.chapter_number > protected_chapter]
            for chapter in chapters_to_rewrite:
                await update_chapter(db, chapter.id, {"status": "needs_rewrite"})

            # 保存更新后的状态文件到store
            for key in ["current_state", "pending_hooks", "character_matrix", "emotional_arcs"]:
                if state_data.get(key):
                    await store_manager.save_state_file(book_id, key, state_data[key])

            # 完成工作流
            await checkpoint_manager.complete_workflow(
                db=db,
                workflow_id=workflow_id,
                output_data={
                    "book_id": book_id,
                    "protected_chapter": protected_chapter,
                    "chapters_to_rewrite": len(chapters_to_rewrite),
                    "status": "completed"
                }
            )

            # 移除锁
            await store_manager.remove_lock(book_id, "protect_and_update")

        except Exception as e:
            await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            await store_manager.remove_lock(book_id, "protect_and_update")
            raise

    async def run_extract_outline(
        self,
        workflow_id: str,
        book_id: int,
        db: AsyncSession
    ):
        """工作流⑤：提取大纲"""
        try:
            # 开始工作流
            await checkpoint_manager.start_workflow(db, workflow_id)

            # 获取所有已写章节
            from db.crud import get_chapters_by_book
            all_chapters, _ = await get_chapters_by_book(db, book_id)
            
            if not all_chapters:
                # 没有章节，直接完成
                await checkpoint_manager.complete_workflow(
                    db=db,
                    workflow_id=workflow_id,
                    output_data={
                        "book_id": book_id,
                        "updated_fields": [],
                        "message": "没有已写章节可提取",
                        "status": "completed"
                    }
                )
                await store_manager.remove_lock(book_id, "extract_outline")
                return

            # 合并所有章节内容作为提取素材
            last_chapter = all_chapters[-1]
            merged_content = "\n\n".join(
                f"第{c.chapter_number}章 {c.title}\n{c.content or ''}"
                for c in all_chapters if c.content
            )

            # Node 1: 从现有章节提取状态
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_1_update_book_state",
                node_name="从现有章节提取状态",
                agent=self.architect,
                task="update_book_state",
                db=db,
                book_id=book_id,
                chapter_num=last_chapter.chapter_number,
                chapter_content=merged_content
            )

            # 获取提取结果
            state_result = checkpoint_manager.get_node_status(workflow_id, "node_1_update_book_state")
            state_data = state_result.get("output_data", {}).get("data", {}) if state_result else {}

            # 更新书籍状态
            update_fields = {}
            for key in ["story_bible", "volume_outline", "book_rules",
                        "current_state", "pending_hooks", "character_matrix", "emotional_arcs"]:
                if state_data.get(key):
                    update_fields[key] = state_data[key]
                    await store_manager.save_state_file(book_id, key, state_data[key])

            if update_fields:
                await update_book(db, book_id, update_fields)

            # 完成工作流
            await checkpoint_manager.complete_workflow(
                db=db,
                workflow_id=workflow_id,
                output_data={
                    "book_id": book_id,
                    "updated_fields": list(update_fields.keys()),
                    "status": "completed"
                }
            )

            # 移除锁
            await store_manager.remove_lock(book_id, "extract_outline")

        except Exception as e:
            await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            await store_manager.remove_lock(book_id, "extract_outline")
            raise

    async def run_expand_skill(
        self,
        workflow_id: str,
        book_id: int,
        db: AsyncSession
    ):
        """工作流⑥：扩写大纲为章节规划"""
        try:
            # 开始工作流
            await checkpoint_manager.start_workflow(db, workflow_id)

            # 从store读取9个大纲文件
            outline_keys = [
                "worldview", "character_profiles", "power_system",
                "story_structure", "volume_outline", "chapter_plan",
                "subplot_board", "foreshadowing", "writing_style"
            ]
            outline_files = {}
            for key in outline_keys:
                content = await store_manager.load_state_file(book_id, key)
                if content:
                    outline_files[key] = content

            # 如果没有大纲文件，用book的outline字段
            book = await get_book(db, book_id)
            if not outline_files and book.outline:
                outline_files["outline"] = book.outline

            # Node 1: 将大纲扩写为章节规划
            await self._execute_node(
                workflow_id=workflow_id,
                node_id="node_1_expand_outline",
                node_name="将大纲扩写为章节规划",
                agent=self.writer,
                task="expand_outline",
                db=db,
                book_id=book_id,
                outline_files=outline_files
            )

            # 获取扩写结果
            expand_result = checkpoint_manager.get_node_status(workflow_id, "node_1_expand_outline")
            expand_data = expand_result.get("output_data", {}).get("data", {}) if expand_result else {}

            # 保存扩写结果到store
            if expand_data.get("chapter_plans"):
                await store_manager.save_state_file(
                    book_id, "chapter_plans", expand_data["chapter_plans"]
                )

            # 完成工作流
            await checkpoint_manager.complete_workflow(
                db=db,
                workflow_id=workflow_id,
                output_data={
                    "book_id": book_id,
                    "status": "completed"
                }
            )

            # 移除锁
            await store_manager.remove_lock(book_id, "expand_skill")

        except Exception as e:
            await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            await store_manager.remove_lock(book_id, "expand_skill")
            raise

    async def _execute_node(
        self,
        workflow_id: str,
        node_id: str,
        node_name: str,
        agent,
        task: str,
        db: AsyncSession,
        **kwargs
    ):
        """执行节点"""
        # 等待如果暂停
        await checkpoint_manager.wait_if_paused(workflow_id)
        
        # 创建节点
        node = await checkpoint_manager.create_node(
            db=db,
            workflow_id=workflow_id,
            node_id=node_id,
            node_type="agent",
            node_name=node_name,
            input_data={"task": task, "kwargs": kwargs}
        )
        
        # 开始节点
        await checkpoint_manager.start_node(db, workflow_id, node_id)
        
        # 执行Agent
        result = await agent.execute(task, db=db, **kwargs)
        
        # 完成节点
        await checkpoint_manager.complete_node(
            db=db,
            workflow_id=workflow_id,
            node_id=node_id,
            output_data=result.to_dict(),
            token_usage=result.token_usage
        )
        
        # 创建检查点
        await checkpoint_manager.create_checkpoint(
            workflow_id=workflow_id,
            node_id=node_id,
            state_data={"task": task, "result": result.to_dict()},
            description=f"完成: {node_name}"
        )
