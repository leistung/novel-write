"""WebSocket路由 - 实时工作流状态推送"""
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from checkpoint.manager import checkpoint_manager

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/workflow/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """工作流状态WebSocket"""
    await websocket.accept()
    
    # 添加到活跃连接
    if workflow_id not in active_connections:
        active_connections[workflow_id] = set()
    active_connections[workflow_id].add(websocket)
    
    # 注册回调
    async def on_workflow_update(event_type: str, data: dict):
        """工作流更新回调"""
        await websocket.send_json({
            "type": event_type,
            "data": data
        })
    
    checkpoint_manager.register_callback(workflow_id, on_workflow_update)
    
    try:
        while True:
            # 接收客户端消息
            message = await websocket.receive_json()
            
            # 处理客户端命令
            if message.get("action") == "pause":
                # 暂停工作流
                pass
            elif message.get("action") == "resume":
                # 恢复工作流
                pass
            elif message.get("action") == "get_status":
                # 获取当前状态
                status = checkpoint_manager.get_workflow_status(workflow_id)
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })
                
    except WebSocketDisconnect:
        # 断开连接
        active_connections[workflow_id].discard(websocket)
        if not active_connections[workflow_id]:
            del active_connections[workflow_id]


@router.websocket("/node/{workflow_id}/{node_id}")
async def node_websocket(websocket: WebSocket, workflow_id: str, node_id: str):
    """节点状态WebSocket - 用于实时查看Stream输出"""
    await websocket.accept()
    
    try:
        while True:
            # 获取节点状态
            node = checkpoint_manager.get_node_status(workflow_id, node_id)
            if node:
                await websocket.send_json({
                    "node_id": node_id,
                    "status": node.get("status"),
                    "stream_output": node.get("stream_output", ""),
                    "output_data": node.get("output_data", {})
                })
            
            # 等待一段时间再更新
            import asyncio
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        pass
