"""
工作流控制 API - 暂停/继续/状态查询
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from workflow.pause_control import pause_manager, PauseStatus

router = APIRouter(prefix="/workflow", tags=["workflow-control"])


@router.post("/pause")
async def pause_workflow(workflow_id: str = Query(..., description="工作流ID")):
    """
    暂停指定工作流
    
    工作流会在当前节点执行完成后暂停，不会中断正在进行的LLM调用
    """
    success = await pause_manager.pause_workflow(workflow_id, reason="用户暂停")
    if not success:
        raise HTTPException(status_code=404, detail=f"工作流不存在或无法暂停: {workflow_id}")
    
    return {
        "success": True,
        "workflow_id": workflow_id,
        "status": "pausing",
        "message": "工作流将在当前节点完成后暂停"
    }


@router.post("/resume")
async def resume_workflow(workflow_id: str = Query(..., description="工作流ID")):
    """
    继续指定工作流
    
    恢复已暂停的工作流执行
    """
    success = await pause_manager.resume_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"工作流不存在或无法继续: {workflow_id}")
    
    return {
        "success": True,
        "workflow_id": workflow_id,
        "status": "running",
        "message": "工作流已恢复执行"
    }


@router.get("/status")
async def get_workflow_status(workflow_id: str = Query(..., description="工作流ID")):
    """
    获取工作流暂停状态
    
    Returns:
        - status: running/pausing/paused/resuming
        - current_node: 当前执行的节点名称
        - progress: 执行进度 0-100
        - paused_at: 暂停时间戳（如果已暂停）
        - pause_reason: 暂停原因
    """
    state = pause_manager.get_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")
    
    return {
        "workflow_id": workflow_id,
        "status": state.status.value,
        "current_node": state.current_node,
        "progress": state.progress,
        "paused_at": state.paused_at,
        "resumed_at": state.resumed_at,
        "pause_reason": state.pause_reason
    }


@router.get("/list")
async def list_active_workflows():
    """
    列出所有活跃工作流及其状态
    
    用于前端显示当前运行中的工作流列表
    """
    workflows = pause_manager.list_active_workflows()
    return {
        "count": len(workflows),
        "workflows": workflows
    }
