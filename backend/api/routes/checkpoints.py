"""Checkpoint API路由"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from checkpoint.manager import checkpoint_manager

router = APIRouter()


class ResumeRequest(BaseModel):
    """恢复工作流请求"""
    from_node_id: Optional[str] = None


@router.get("/workflows/{workflow_id}/nodes")
async def list_workflow_nodes(workflow_id: str):
    """获取工作流所有节点"""
    status = checkpoint_manager.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return {
        "workflow_id": workflow_id,
        "nodes": status.get("nodes", {})
    }


@router.get("/workflows/{workflow_id}/nodes/{node_id}")
async def get_node_detail(workflow_id: str, node_id: str):
    """获取节点详情"""
    node = checkpoint_manager.get_node_status(workflow_id, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    
    return node


@router.get("/workflows/{workflow_id}/checkpoints")
async def list_checkpoints(workflow_id: str):
    """获取工作流所有检查点"""
    checkpoints = checkpoint_manager.get_checkpoints(workflow_id)
    return {
        "workflow_id": workflow_id,
        "checkpoints": checkpoints
    }


@router.post("/workflows/{workflow_id}/retry/{node_id}")
async def retry_node(
    workflow_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """重试指定节点"""
    # TODO: 实现重试逻辑
    return {"message": f"节点 {node_id} 已加入重试队列"}


@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow(workflow_id: str):
    """流式获取工作流更新（用于前端实时显示）"""
    from fastapi.responses import StreamingResponse
    import asyncio
    import json
    from datetime import datetime
    
    def json_serial(obj):
        """JSON序列化datetime对象"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    async def event_generator():
        """生成SSE事件"""
        last_status = None
        
        while True:
            status = checkpoint_manager.get_workflow_status(workflow_id)
            if not status:
                yield f"data: {json.dumps({'error': '工作流不存在'})}\n\n"
                break
            
            # 只在状态变化时发送
            if status != last_status:
                yield f"data: {json.dumps(status, default=json_serial)}\n\n"
                last_status = status
            
            # 如果工作流完成或失败，停止
            if status.get("status") in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
