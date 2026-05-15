"""工作流Celery任务"""
import asyncio
from typing import Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from db.database import AsyncSessionLocal
from checkpoint.manager import checkpoint_manager
from workflow.engine import WorkflowEngine

workflow_engine = WorkflowEngine()


async def _run_workflow_with_session(
    workflow_func,
    workflow_id: str,
    **kwargs
) -> dict:
    """在独立session中运行工作流"""
    async with AsyncSessionLocal() as db:
        try:
            result = await workflow_func(
                workflow_id=workflow_id,
                db=db,
                **kwargs
            )
            await db.commit()
            return {"status": "completed", "result": result}
        except Exception as e:
            await db.rollback()
            # 更新工作流状态为失败
            try:
                await checkpoint_manager.fail_workflow(db, workflow_id, str(e))
            except Exception as log_exc:
                import logging
                logging.error(f"Failed to update workflow {workflow_id} status: {log_exc}")
            raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_outline_task(self, workflow_id: str, book_id: int) -> dict:
    """生成大纲任务"""
    try:
        return asyncio.run(_run_workflow_with_session(
            workflow_engine.run_generate_outline,
            workflow_id=workflow_id,
            book_id=book_id
        ))
    except SoftTimeLimitExceeded:
        self.retry(countdown=120)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def continue_chapters_task(
    self,
    workflow_id: str,
    book_id: int,
    start_chapter: int,
    count: int,
    external_context: str = ""
) -> dict:
    """续写章节任务"""
    try:
        return asyncio.run(_run_workflow_with_session(
            workflow_engine.run_continue_chapters,
            workflow_id=workflow_id,
            book_id=book_id,
            start_chapter=start_chapter,
            count=count,
            external_context=external_context
        ))
    except SoftTimeLimitExceeded:
        self.retry(countdown=120)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def rewrite_chapter_task(
    self,
    workflow_id: str,
    book_id: int,
    chapter_num: int,
    rewrite_requirements: str,
    keep_plot: bool = True
) -> dict:
    """重写章节任务"""
    try:
        return asyncio.run(_run_workflow_with_session(
            workflow_engine.run_rewrite_chapter,
            workflow_id=workflow_id,
            book_id=book_id,
            chapter_num=chapter_num,
            rewrite_requirements=rewrite_requirements,
            keep_plot=keep_plot
        ))
    except SoftTimeLimitExceeded:
        self.retry(countdown=120)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def protect_and_update_task(
    self,
    workflow_id: str,
    book_id: int,
    protected_chapter: int,
    new_outline: str
) -> dict:
    """保护章节并更新大纲任务"""
    try:
        return asyncio.run(_run_workflow_with_session(
            workflow_engine.run_protect_and_update,
            workflow_id=workflow_id,
            book_id=book_id,
            protected_chapter=protected_chapter,
            new_outline=new_outline
        ))
    except SoftTimeLimitExceeded:
        self.retry(countdown=120)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def extract_outline_task(self, workflow_id: str, book_id: int) -> dict:
    """提取大纲任务"""
    try:
        return asyncio.run(_run_workflow_with_session(
            workflow_engine.run_extract_outline,
            workflow_id=workflow_id,
            book_id=book_id
        ))
    except SoftTimeLimitExceeded:
        self.retry(countdown=120)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expand_skill_task(self, workflow_id: str, book_id: int) -> dict:
    """扩写Skill任务"""
    try:
        return asyncio.run(_run_workflow_with_session(
            workflow_engine.run_expand_skill,
            workflow_id=workflow_id,
            book_id=book_id
        ))
    except SoftTimeLimitExceeded:
        self.retry(countdown=120)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise


@shared_task
def cleanup_old_workflows() -> dict:
    """清理旧的工作流记录（定时任务）"""
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            from datetime import datetime, timedelta, timezone
            from sqlalchemy import delete
            from db.models import WorkflowExecution

            # 删除30天前已完成或失败的工作流
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            stmt = delete(WorkflowExecution).where(
                WorkflowExecution.status.in_(["completed", "failed", "cancelled"]),
                WorkflowExecution.completed_at < cutoff_date
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            return {"deleted_count": result.rowcount}
    
    return asyncio.run(_cleanup())
