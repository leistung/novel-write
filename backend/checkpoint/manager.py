"""Checkpoint管理系统 - Dify风格"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import (
    create_workflow_execution, update_workflow_status,
    create_workflow_node, update_workflow_node
)
from db.models import WorkflowNode


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class NodeExecution:
    """节点执行记录"""
    node_id: str
    node_type: str  # agent/function/condition
    node_name: str
    status: NodeStatus = NodeStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    stream_output: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    workflow_id: str
    node_id: str
    state_data: Dict[str, Any]
    created_at: datetime
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "state_data": self.state_data,
            "created_at": self.created_at.isoformat(),
            "description": self.description
        }


class CheckpointManager:
    """Checkpoint管理器"""
    
    def __init__(self):
        self._workflows: Dict[str, Dict[str, Any]] = {}
        self._nodes: Dict[str, Dict[str, NodeExecution]] = {}
        self._checkpoints: Dict[str, List[Checkpoint]] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._paused_events: Dict[str, asyncio.Event] = {}
    
    async def create_workflow(
        self,
        db: AsyncSession,
        book_id: int,
        workflow_type: str,
        input_data: Dict[str, Any]
    ) -> str:
        """创建工作流"""
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        
        # 创建数据库记录
        workflow = await create_workflow_execution(
            db=db,
            workflow_id=workflow_id,
            book_id=book_id,
            workflow_type=workflow_type,
            input_data=input_data
        )
        
        # 初始化内存状态
        self._workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "book_id": book_id,
            "workflow_type": workflow_type,
            "status": WorkflowStatus.PENDING,
            "current_node": "",
            "progress": 0,
            "input_data": input_data,
            "output_data": {},
            "started_at": None,
            "db_id": workflow.id
        }
        self._nodes[workflow_id] = {}
        self._checkpoints[workflow_id] = []
        self._paused_events[workflow_id] = asyncio.Event()
        self._paused_events[workflow_id].set()  # 默认不暂停
        
        return workflow_id
    
    async def start_workflow(self, db: AsyncSession, workflow_id: str):
        """开始工作流"""
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        self._workflows[workflow_id]["status"] = WorkflowStatus.RUNNING
        self._workflows[workflow_id]["started_at"] = datetime.utcnow()
        
        # 更新数据库
        await update_workflow_status(
            db=db,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow()
        )
    
    async def create_node(
        self,
        db: AsyncSession,
        workflow_id: str,
        node_id: str,
        node_type: str,
        node_name: str,
        input_data: Dict[str, Any]
    ) -> NodeExecution:
        """创建节点执行记录"""
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        node = NodeExecution(
            node_id=node_id,
            node_type=node_type,
            node_name=node_name,
            input_data=input_data
        )
        
        self._nodes[workflow_id][node_id] = node
        self._workflows[workflow_id]["current_node"] = node_id
        
        # 创建数据库记录
        await create_workflow_node(
            db=db,
            workflow_execution_id=self._workflows[workflow_id]["db_id"],
            node_id=node_id,
            node_type=node_type,
            node_name=node_name,
            input_data=input_data
        )
        
        # 触发回调
        await self._trigger_callback(workflow_id, "node_created", node.to_dict())
        
        return node
    
    async def start_node(self, db: AsyncSession, workflow_id: str, node_id: str):
        """开始执行节点"""
        if workflow_id not in self._nodes:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        if node_id not in self._nodes[workflow_id]:
            raise ValueError(f"节点不存在: {node_id}")
        
        node = self._nodes[workflow_id][node_id]
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.utcnow()
        
        # 更新数据库
        result = await db.execute(
            select(WorkflowNode.id).where(
                WorkflowNode.workflow_id == self._workflows[workflow_id]["db_id"],
                WorkflowNode.node_id == node_id
            )
        )
        row = result.scalar_one_or_none()
        if row:
            await update_workflow_node(
                db=db,
                node_id=row,
                status="running",
                started_at=datetime.utcnow()
            )
        
        # 触发回调
        await self._trigger_callback(workflow_id, "node_started", node.to_dict())
    
    async def update_node_stream(
        self,
        workflow_id: str,
        node_id: str,
        chunk: str
    ):
        """更新节点流式输出"""
        if workflow_id not in self._nodes or node_id not in self._nodes[workflow_id]:
            return
        
        node = self._nodes[workflow_id][node_id]
        node.stream_output += chunk
        
        # 触发回调
        await self._trigger_callback(workflow_id, "node_stream", {
            "node_id": node_id,
            "chunk": chunk,
            "stream_output": node.stream_output
        })
    
    async def complete_node(
        self,
        db: AsyncSession,
        workflow_id: str,
        node_id: str,
        output_data: Dict[str, Any],
        token_usage: Dict[str, int] = None
    ):
        """完成节点执行"""
        if workflow_id not in self._nodes or node_id not in self._nodes[workflow_id]:
            return
        
        node = self._nodes[workflow_id][node_id]
        node.status = NodeStatus.COMPLETED
        node.output_data = output_data
        node.token_usage = token_usage or {}
        node.completed_at = datetime.utcnow()
        
        if node.started_at:
            node.duration_ms = int((node.completed_at - node.started_at).total_seconds() * 1000)
        
        # 更新数据库
        result = await db.execute(
            select(WorkflowNode.id).where(
                WorkflowNode.workflow_id == self._workflows[workflow_id]["db_id"],
                WorkflowNode.node_id == node_id
            )
        )
        row = result.scalar_one_or_none()
        if row:
            await update_workflow_node(
                db=db,
                node_id=row,
                status="completed",
                output_data=output_data,
                completed_at=node.completed_at,
                duration_ms=node.duration_ms,
                token_usage=token_usage or {}
            )
        
        # 触发回调
        await self._trigger_callback(workflow_id, "node_completed", node.to_dict())
    
    async def fail_node(
        self,
        db: AsyncSession,
        workflow_id: str,
        node_id: str,
        error_message: str
    ):
        """节点执行失败"""
        if workflow_id not in self._nodes or node_id not in self._nodes[workflow_id]:
            return
        
        node = self._nodes[workflow_id][node_id]
        node.status = NodeStatus.FAILED
        node.error_message = error_message
        node.completed_at = datetime.utcnow()
        
        # 更新数据库
        result = await db.execute(
            select(WorkflowNode.id).where(
                WorkflowNode.workflow_id == self._workflows[workflow_id]["db_id"],
                WorkflowNode.node_id == node_id
            )
        )
        row = result.scalar_one_or_none()
        if row:
            await update_workflow_node(
                db=db,
                node_id=row,
                status="failed",
                error_message=error_message,
                completed_at=node.completed_at
            )
        
        # 触发回调
        await self._trigger_callback(workflow_id, "node_failed", node.to_dict())
    
    async def create_checkpoint(
        self,
        workflow_id: str,
        node_id: str,
        state_data: Dict[str, Any],
        description: str = ""
    ) -> Checkpoint:
        """创建检查点"""
        checkpoint = Checkpoint(
            checkpoint_id=f"cp_{uuid.uuid4().hex[:12]}",
            workflow_id=workflow_id,
            node_id=node_id,
            state_data=state_data,
            created_at=datetime.utcnow(),
            description=description
        )
        
        if workflow_id not in self._checkpoints:
            self._checkpoints[workflow_id] = []
        
        self._checkpoints[workflow_id].append(checkpoint)
        
        # 触发回调
        await self._trigger_callback(workflow_id, "checkpoint_created", checkpoint.to_dict())
        
        return checkpoint
    
    async def pause_workflow(self, db: AsyncSession, workflow_id: str):
        """暂停工作流"""
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        self._workflows[workflow_id]["status"] = WorkflowStatus.PAUSED
        self._paused_events[workflow_id].clear()
        
        # 更新数据库
        await update_workflow_status(db, workflow_id, "paused")
        
        # 触发回调
        await self._trigger_callback(workflow_id, "workflow_paused", {
            "workflow_id": workflow_id
        })
    
    async def resume_workflow(self, db: AsyncSession, workflow_id: str, from_node_id: str = None):
        """恢复工作流"""
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        self._workflows[workflow_id]["status"] = WorkflowStatus.RUNNING
        self._paused_events[workflow_id].set()
        
        # 更新数据库
        await update_workflow_status(db, workflow_id, "running")
        
        # 触发回调
        await self._trigger_callback(workflow_id, "workflow_resumed", {
            "workflow_id": workflow_id,
            "from_node_id": from_node_id
        })
    
    async def wait_if_paused(self, workflow_id: str):
        """如果工作流暂停则等待"""
        if workflow_id in self._paused_events:
            await self._paused_events[workflow_id].wait()
    
    async def complete_workflow(
        self,
        db: AsyncSession,
        workflow_id: str,
        output_data: Dict[str, Any]
    ):
        """完成工作流"""
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        self._workflows[workflow_id]["status"] = WorkflowStatus.COMPLETED
        self._workflows[workflow_id]["output_data"] = output_data
        self._workflows[workflow_id]["progress"] = 100
        
        # 更新数据库
        await update_workflow_status(
            db=db,
            workflow_id=workflow_id,
            status="completed",
            output_data=output_data,
            completed_at=datetime.utcnow()
        )
        
        # 触发回调
        await self._trigger_callback(workflow_id, "workflow_completed", {
            "workflow_id": workflow_id,
            "output_data": output_data
        })
    
    async def fail_workflow(
        self,
        db: AsyncSession,
        workflow_id: str,
        error_message: str
    ):
        """工作流失败"""
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        self._workflows[workflow_id]["status"] = WorkflowStatus.FAILED
        
        # 更新数据库
        await update_workflow_status(
            db=db,
            workflow_id=workflow_id,
            status="failed",
            error_message=error_message
        )
        
        # 触发回调
        await self._trigger_callback(workflow_id, "workflow_failed", {
            "workflow_id": workflow_id,
            "error_message": error_message
        })
    
    def register_callback(self, workflow_id: str, callback: Callable):
        """注册状态变更回调"""
        if workflow_id not in self._callbacks:
            self._callbacks[workflow_id] = []
        self._callbacks[workflow_id].append(callback)
    
    async def _trigger_callback(self, workflow_id: str, event_type: str, data: Dict[str, Any]):
        """触发回调"""
        if workflow_id in self._callbacks:
            for callback in self._callbacks[workflow_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, data)
                    else:
                        callback(event_type, data)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        if workflow_id not in self._workflows:
            return None
        
        workflow = self._workflows[workflow_id].copy()
        workflow["status"] = workflow["status"].value
        workflow["nodes"] = {
            node_id: node.to_dict()
            for node_id, node in self._nodes.get(workflow_id, {}).items()
        }
        return workflow
    
    def get_node_status(self, workflow_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点状态"""
        if workflow_id not in self._nodes or node_id not in self._nodes[workflow_id]:
            return None
        
        return self._nodes[workflow_id][node_id].to_dict()
    
    def get_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取所有检查点"""
        if workflow_id not in self._checkpoints:
            return []
        
        return [cp.to_dict() for cp in self._checkpoints[workflow_id]]


# 全局Checkpoint管理器
checkpoint_manager = CheckpointManager()
