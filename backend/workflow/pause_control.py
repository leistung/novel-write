"""
工作流暂停控制模块

提供全局工作流暂停状态管理，支持：
- 暂停指定工作流
- 继续指定工作流
- 查询暂停状态
- 工作流执行时检查暂停状态
"""
import asyncio
import time
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class PauseStatus(Enum):
    """暂停状态"""
    RUNNING = "running"      # 正常运行
    PAUSING = "pausing"      # 正在暂停（等待当前节点完成）
    PAUSED = "paused"        # 已暂停
    RESUMING = "resuming"    # 正在恢复


@dataclass
class WorkflowPauseState:
    """工作流暂停状态"""
    workflow_id: str
    status: PauseStatus = PauseStatus.RUNNING
    paused_at: Optional[float] = None
    resumed_at: Optional[float] = None
    pause_reason: str = ""
    current_node: str = ""
    progress: float = 0.0
    # 用于协程间通信的事件
    _resume_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    def __post_init__(self):
        if self.status == PauseStatus.PAUSED:
            self._resume_event.clear()
        else:
            self._resume_event.set()


class WorkflowPauseManager:
    """
    工作流暂停管理器（单例模式）
    
    管理所有运行中工作流的暂停状态
    """
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # 存储所有工作流的暂停状态
        self._states: Dict[str, WorkflowPauseState] = {}
        # 清理过期工作流的任务
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动管理器，开始定期清理过期状态"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """停止管理器"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """定期清理已完成的过期工作流状态"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                current_time = time.time()
                expired_workflows = []
                
                for workflow_id, state in self._states.items():
                    # 清理已完成超过1小时的工作流
                    if state.status == PauseStatus.RUNNING:
                        if hasattr(state, '_last_activity'):
                            if current_time - state._last_activity > 3600:
                                expired_workflows.append(workflow_id)
                
                for workflow_id in expired_workflows:
                    del self._states[workflow_id]
                    print(f"[PauseManager] 清理过期工作流状态: {workflow_id}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[PauseManager] 清理循环错误: {e}")
    
    def register_workflow(self, workflow_id: str, current_node: str = "") -> WorkflowPauseState:
        """
        注册新工作流
        
        Args:
            workflow_id: 工作流ID
            current_node: 当前节点名称
            
        Returns:
            WorkflowPauseState: 工作流暂停状态
        """
        state = WorkflowPauseState(
            workflow_id=workflow_id,
            status=PauseStatus.RUNNING,
            current_node=current_node
        )
        self._states[workflow_id] = state
        print(f"[PauseManager] 注册工作流: {workflow_id}")
        return state
    
    def unregister_workflow(self, workflow_id: str):
        """注销工作流"""
        if workflow_id in self._states:
            state = self._states[workflow_id]
            # 确保恢复事件被设置，避免阻塞
            state._resume_event.set()
            del self._states[workflow_id]
            print(f"[PauseManager] 注销工作流: {workflow_id}")
    
    async def pause_workflow(self, workflow_id: str, reason: str = "用户暂停") -> bool:
        """
        暂停工作流
        
        Args:
            workflow_id: 工作流ID
            reason: 暂停原因
            
        Returns:
            bool: 是否成功暂停
        """
        if workflow_id not in self._states:
            print(f"[PauseManager] 工作流不存在: {workflow_id}")
            return False
        
        state = self._states[workflow_id]
        
        if state.status in [PauseStatus.PAUSED, PauseStatus.PAUSING]:
            print(f"[PauseManager] 工作流已在暂停中: {workflow_id}")
            return True
        
        if state.status == PauseStatus.RUNNING:
            state.status = PauseStatus.PAUSING
            state.pause_reason = reason
            print(f"[PauseManager] 正在暂停工作流: {workflow_id}, 原因: {reason}")
            return True
        
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        继续工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功继续
        """
        if workflow_id not in self._states:
            print(f"[PauseManager] 工作流不存在: {workflow_id}")
            return False
        
        state = self._states[workflow_id]
        
        if state.status == PauseStatus.RUNNING:
            print(f"[PauseManager] 工作流已在运行中: {workflow_id}")
            return True
        
        if state.status in [PauseStatus.PAUSED, PauseStatus.PAUSING]:
            state.status = PauseStatus.RESUMING
            state.resumed_at = time.time()
            state._resume_event.set()  # 触发恢复信号
            print(f"[PauseManager] 继续工作流: {workflow_id}")
            return True
        
        return False
    
    async def check_and_wait(self, workflow_id: str, node_name: str = "") -> bool:
        """
        检查暂停状态，如果被暂停则等待恢复
        
        在工作流的每个节点之间调用此方法
        
        Args:
            workflow_id: 工作流ID
            node_name: 当前节点名称（用于显示）
            
        Returns:
            bool: 是否应该继续执行（False表示工作流已被取消）
        """
        if workflow_id not in self._states:
            return True  # 工作流未注册，继续执行
        
        state = self._states[workflow_id]
        
        # 更新当前节点
        if node_name:
            state.current_node = node_name
        
        # 如果正在暂停，转换为已暂停状态
        if state.status == PauseStatus.PAUSING:
            state.status = PauseStatus.PAUSED
            state.paused_at = time.time()
            print(f"[PauseManager] 工作流已暂停: {workflow_id}, 节点: {node_name}")
        
        # 如果已暂停，等待恢复信号
        if state.status == PauseStatus.PAUSED:
            print(f"[PauseManager] 等待工作流恢复: {workflow_id}")
            try:
                await state._resume_event.wait()
                # 恢复后重置事件（为下次暂停做准备）
                state._resume_event.clear()
                state.status = PauseStatus.RUNNING
                print(f"[PauseManager] 工作流已恢复: {workflow_id}")
            except asyncio.CancelledError:
                print(f"[PauseManager] 工作流等待被取消: {workflow_id}")
                return False
        
        return state.status == PauseStatus.RUNNING
    
    def get_status(self, workflow_id: str) -> Optional[PauseStatus]:
        """获取工作流暂停状态"""
        if workflow_id not in self._states:
            return None
        return self._states[workflow_id].status
    
    def get_state(self, workflow_id: str) -> Optional[WorkflowPauseState]:
        """获取工作流完整状态"""
        return self._states.get(workflow_id)
    
    def update_progress(self, workflow_id: str, progress: float, node: str = ""):
        """更新工作流进度"""
        if workflow_id in self._states:
            state = self._states[workflow_id]
            state.progress = progress
            if node:
                state.current_node = node
    
    def list_active_workflows(self) -> Dict[str, dict]:
        """列出所有活跃工作流"""
        return {
            workflow_id: {
                "status": state.status.value,
                "current_node": state.current_node,
                "progress": state.progress,
                "paused_at": state.paused_at,
                "pause_reason": state.pause_reason
            }
            for workflow_id, state in self._states.items()
        }


# 全局暂停管理器实例
pause_manager = WorkflowPauseManager()


async def check_pause(workflow_id: str, node_name: str = "") -> bool:
    """
    便捷函数：检查工作流是否被暂停，如果被暂停则等待恢复
    
    使用示例：
        # 在每个节点执行前调用
        should_continue = await check_pause(workflow_id, "规划章节")
        if not should_continue:
            return  # 工作流被取消
    
    Args:
        workflow_id: 工作流ID
        node_name: 当前节点名称
        
    Returns:
        bool: 是否应该继续执行
    """
    return await pause_manager.check_and_wait(workflow_id, node_name)
