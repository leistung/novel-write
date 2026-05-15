/**
 * 工作流执行页面
 * 
 * 大厂级工作流可视化 + SSE 实时输出
 * 修复：添加心跳检测、重连机制、超时处理
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Button, Modal, InputNumber, Input, Switch, message } from 'antd';
import {
  PlayCircleOutlined,
  StopOutlined,
  CloseOutlined,
  SettingOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
  PauseCircleOutlined,
  PlayCircleFilled,
} from '@ant-design/icons';
import WorkflowVisualizer from './WorkflowVisualizer';
import NodeDetailPanel from './NodeDetailPanel';
import StreamingOutput from './StreamingOutput';
import type { Workflow, WorkflowNode, WorkflowSSEEvent, NodeStatus } from '../../types/workflow';
import { pauseWorkflow, resumeWorkflow } from '../../services/api';

const { TextArea } = Input;

// ==================== 设计令牌 ====================
const colors = {
  bg: '#0f172a',
  card: '#1e293b',
  primary: '#6366f1',
  primaryLight: '#818cf8',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  border: '#334155',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
};

// ==================== 工作流模板 ====================

const createInitialWorkflow = (type: Workflow['type']): Workflow => ({
  id: `wf_${Date.now()}`,
  name: type === 'generate-outline' ? '生成大纲' :
        type === 'continue-chapters' ? '续写章节' : '重写章节',
  type,
  status: 'idle',
  progress: 0,
  nodes: [],
  connections: [],
  streamingContent: '',
});

// ==================== Props ====================

interface WorkflowExecutionProps {
  bookId: number;
  type: Workflow['type'];
  startChapter?: number;
  count?: number;
  chapterNum?: number;
  rewriteRequirements?: string;
  keepPlot?: boolean;
  onComplete?: () => void;
  onError?: (error: string) => void;
  onClose?: () => void;
}

// ==================== 主组件 ====================

const WorkflowExecution: React.FC<WorkflowExecutionProps> = ({
  bookId,
  type,
  startChapter: initialStartChapter = 1,
  count: initialCount = 1,
  chapterNum: initialChapterNum = 1,
  rewriteRequirements: initialRewriteRequirements = '',
  keepPlot: initialKeepPlot = true,
  onComplete,
  onError,
  onClose,
}) => {
  // 工作流状态
  const [workflow, setWorkflow] = useState<Workflow>(() => createInitialWorkflow(type));
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isPausing, setIsPausing] = useState(false);
  const [canPause, setCanPause] = useState(false);
  
  // 设置参数
  const [startChapter, setStartChapter] = useState(initialStartChapter);
  const [count, setCount] = useState(initialCount);
  const [chapterNum, setChapterNum] = useState(initialChapterNum);
  const [rewriteRequirements, setRewriteRequirements] = useState(initialRewriteRequirements);
  const [keepPlot, setKeepPlot] = useState(initialKeepPlot);
  
  // UI 状态
  const [showSettings, setShowSettings] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // SSE 连接
  const eventSourceRef = useRef<EventSource | null>(null);
  const nodeContentRef = useRef<Record<string, string>>({});
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastMessageTimeRef = useRef<number>(0);
  const reconnectAttemptsRef = useRef<number>(0);
  const MAX_RECONNECT_ATTEMPTS = 3;
  const HEARTBEAT_INTERVAL = 30000; // 30秒心跳检测
  const MESSAGE_TIMEOUT = 60000; // 60秒无消息则认为断开

  // 获取选中的节点
  const selectedNode = workflow.nodes.find(n => n.id === selectedNodeId) || null;

  // ==================== SSE 事件处理 ====================

  const handleSSEEvent = useCallback((event: WorkflowSSEEvent) => {
    // 更新最后消息时间
    lastMessageTimeRef.current = Date.now();
    
    setWorkflow(prev => {
      const newWorkflow = { ...prev };

      switch (event.type) {
        case 'workflow_start':
          newWorkflow.status = 'running';
          newWorkflow.startedAt = new Date().toISOString();
          newWorkflow.nodes = [];
          newWorkflow.streamingContent = '';
          nodeContentRef.current = {};
          // 使用后端返回的 workflow ID
          if (event.workflowId) {
            newWorkflow.id = event.workflowId;
          }
          // 检查工作流是否支持暂停
          if (event.canPause) {
            setCanPause(true);
          }
          break;

        case 'node_start':
          if (event.nodeId && event.nodeName) {
            const newNode: WorkflowNode = {
              id: event.nodeId,
              name: event.nodeName,
              type: event.nodeType || 'llm',
              status: 'running',
              startedAt: new Date().toISOString(),
            };
            newWorkflow.nodes = [...prev.nodes, newNode];
            newWorkflow.currentNodeId = event.nodeId;
            nodeContentRef.current[event.nodeId] = '';
            // 自动选中新节点
            setSelectedNodeId(event.nodeId);
          }
          break;

        case 'node_token':
          if (event.nodeId && event.token) {
            nodeContentRef.current[event.nodeId] = 
              (nodeContentRef.current[event.nodeId] || '') + event.token;
            
            newWorkflow.nodes = prev.nodes.map(node =>
              node.id === event.nodeId
                ? { ...node, generatedContent: nodeContentRef.current[event.nodeId] }
                : node
            );
            
            newWorkflow.streamingContent = nodeContentRef.current[event.nodeId] || '';
          }
          break;

        case 'node_end':
          if (event.nodeId) {
            newWorkflow.nodes = prev.nodes.map(node =>
              node.id === event.nodeId
                ? {
                    ...node,
                    status: 'completed' as NodeStatus,
                    completedAt: new Date().toISOString(),
                    input: event.input,
                    output: event.output,
                    systemPrompt: event.systemPrompt,
                    userPrompt: event.userPrompt,
                    tokenUsage: event.tokenUsage,
                    duration: event.duration,
                    generatedContent: nodeContentRef.current[event.nodeId] || node.generatedContent,
                  }
                : node
            );
          }
          break;

        case 'node_error':
          if (event.nodeId) {
            newWorkflow.nodes = prev.nodes.map(node =>
              node.id === event.nodeId
                ? {
                    ...node,
                    status: 'error' as NodeStatus,
                    error: event.error,
                    completedAt: new Date().toISOString(),
                  }
                : node
            );
            newWorkflow.status = 'error';
          }
          break;

        case 'workflow_end':
          newWorkflow.status = 'completed';
          newWorkflow.completedAt = new Date().toISOString();
          newWorkflow.progress = 100;
          newWorkflow.currentNodeId = undefined;
          break;

        case 'progress':
          if (event.progress !== undefined) {
            newWorkflow.progress = event.progress;
          }
          break;
      }

      return newWorkflow;
    });
  }, []);

  // ==================== 心跳检测 ====================

  const startHeartbeatCheck = useCallback(() => {
    // 清除旧的心跳检测
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
    }
    
    lastMessageTimeRef.current = Date.now();
    
    heartbeatTimerRef.current = setInterval(() => {
      const now = Date.now();
      const timeSinceLastMessage = now - lastMessageTimeRef.current;
      
      // 如果超过60秒没有收到消息，认为连接已断开
      if (timeSinceLastMessage > MESSAGE_TIMEOUT && isRunning) {
        console.log('[SSE] 心跳超时，尝试重连...');
        handleReconnect();
      }
    }, HEARTBEAT_INTERVAL);
  }, [isRunning]);

  const stopHeartbeatCheck = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // ==================== 重连机制 ====================

  const handleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      message.error('连接失败，请稍后重试');
      setIsRunning(false);
      setIsReconnecting(false);
      reconnectAttemptsRef.current = 0;
      return;
    }

    reconnectAttemptsRef.current++;
    setIsReconnecting(true);
    message.info(`连接中断，正在重试 (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`);

    // 关闭旧连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // 延迟重连
    setTimeout(() => {
      connectSSE();
    }, 2000 * reconnectAttemptsRef.current); // 递增延迟
  }, []);

  // ==================== SSE 连接管理 ====================

  const connectSSE = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    let url: string;
    const baseParams = `book_id=${bookId}`;

    switch (type) {
      case 'generate-outline':
        url = `/api/v1/stream/generate-outline?${baseParams}`;
        break;
      case 'continue-chapters':
        url = `/api/v1/stream/continue-chapters?${baseParams}&start_chapter=${startChapter}&count=${count}`;
        break;
      case 'rewrite-chapter':
        url = `/api/v1/stream/rewrite-chapter?${baseParams}&chapter_num=${chapterNum}&rewrite_requirements=${encodeURIComponent(rewriteRequirements)}&keep_plot=${keepPlot}`;
        break;
      default:
        return;
    }

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      console.log('[SSE] 连接已建立');
      setIsReconnecting(false);
      reconnectAttemptsRef.current = 0;
      startHeartbeatCheck();
    };

    es.onmessage = (e) => {
      try {
        // 忽略心跳注释
        if (e.data.startsWith(':')) {
          console.log('[SSE] 收到心跳:', e.data);
          lastMessageTimeRef.current = Date.now();
          return;
        }

        const data = JSON.parse(e.data) as WorkflowSSEEvent;
        handleSSEEvent(data);

        if (data.type === 'workflow_end') {
          setIsRunning(false);
          stopHeartbeatCheck();
          es.close();
          onComplete?.();
        } else if (data.type === 'node_error' || data.type === 'error') {
          setIsRunning(false);
          stopHeartbeatCheck();
          es.close();
          onError?.(data.error || '未知错误');
        }
      } catch (err) {
        console.error('SSE 解析错误:', err);
      }
    };

    es.onerror = (error) => {
      console.error('[SSE] 连接错误:', error);
      
      // 如果是正在运行中出错，尝试重连
      if (isRunning) {
        handleReconnect();
      } else {
        setIsRunning(false);
        stopHeartbeatCheck();
        es.close();
        message.error('连接中断');
      }
    };
  }, [bookId, type, startChapter, count, chapterNum, rewriteRequirements, keepPlot, handleSSEEvent, onComplete, onError, isRunning, startHeartbeatCheck, stopHeartbeatCheck, handleReconnect]);

  // ==================== 控制函数 ====================

  const start = () => {
    reconnectAttemptsRef.current = 0;
    setIsRunning(true);
    setIsPaused(false);
    setIsPausing(false);
    setCanPause(false);
    setWorkflow(createInitialWorkflow(type));
    setSelectedNodeId(null);
    connectSSE();
    message.info('工作流已启动');
  };

  const stop = () => {
    stopHeartbeatCheck();
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsRunning(false);
    setIsReconnecting(false);
    setIsPaused(false);
    setCanPause(false);
    setWorkflow(prev => ({ ...prev, status: 'error' }));
    message.warning('工作流已停止');
  };

  // 暂停工作流
  const handlePause = async () => {
    if (!workflow.id) return;
    
    setIsPausing(true);
    try {
      await pauseWorkflow(workflow.id);
      setIsPaused(true);
      setIsPausing(false);
      message.info('工作流将在当前节点完成后暂停');
    } catch (error) {
      setIsPausing(false);
      message.error('暂停失败');
    }
  };

  // 继续工作流
  const handleResume = async () => {
    if (!workflow.id) return;
    
    setIsPausing(true);
    try {
      await resumeWorkflow(workflow.id);
      setIsPaused(false);
      setIsPausing(false);
      message.success('工作流已恢复');
    } catch (error) {
      setIsPausing(false);
      message.error('继续失败');
    }
  };

  // 清理
  useEffect(() => {
    return () => {
      stopHeartbeatCheck();
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [stopHeartbeatCheck]);

  // ==================== 状态样式 ====================

  const statusConfig = {
    idle: { color: colors.textSecondary, bg: 'rgba(148,163,184,0.1)', text: '待执行' },
    running: { 
      color: isPaused ? colors.warning : colors.primary, 
      bg: isPaused ? 'rgba(245,158,11,0.15)' : 'rgba(99,102,241,0.15)', 
      text: isPaused ? '已暂停' : (isReconnecting ? '重连中...' : '执行中') 
    },
    completed: { color: colors.success, bg: 'rgba(16,185,129,0.15)', text: '已完成' },
    error: { color: colors.error, bg: 'rgba(239,68,68,0.15)', text: '出错' },
    paused: { color: colors.warning, bg: 'rgba(245,158,11,0.15)', text: '已暂停' },
  }[workflow.status];

  // ==================== 渲染 ====================

  const containerStyle: React.CSSProperties = isFullscreen ? {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
    background: colors.bg,
    padding: 16,
  } : {
    background: colors.bg,
    borderRadius: 16,
    border: `1px solid ${colors.border}`,
    overflow: 'hidden',
  };

  return (
    <div style={containerStyle}>
      {/* 顶部控制栏 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        background: colors.card,
        borderBottom: `1px solid ${colors.border}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ThunderboltOutlined style={{ fontSize: 20, color: colors.primary }} />
          <span style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>
            {workflow.name}
          </span>
          <span style={{
            padding: '2px 10px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 500,
            color: statusConfig.color,
            background: statusConfig.bg,
          }}>
            {statusConfig.text}
          </span>
          {workflow.status === 'running' && !isReconnecting && (
            <span style={{ fontSize: 13, color: colors.textSecondary }}>
              {workflow.nodes.filter(n => n.status === 'completed').length}/{workflow.nodes.length} 节点
            </span>
          )}
          {isReconnecting && (
            <ReloadOutlined spin style={{ color: colors.warning }} />
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {!isRunning ? (
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={start}
              style={{
                height: 36,
                borderRadius: 8,
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                border: 'none',
                fontWeight: 500,
              }}
            >
              开始执行
            </Button>
          ) : (
            <>
              {/* 暂停/继续按钮 */}
              {canPause && (
                isPaused ? (
                  <Button
                    type="primary"
                    icon={<PlayCircleFilled />}
                    onClick={handleResume}
                    loading={isPausing}
                    style={{
                      height: 36,
                      borderRadius: 8,
                      background: colors.success,
                      border: 'none',
                    }}
                  >
                    继续
                  </Button>
                ) : (
                  <Button
                    icon={<PauseCircleOutlined />}
                    onClick={handlePause}
                    loading={isPausing}
                    style={{
                      height: 36,
                      borderRadius: 8,
                      borderColor: colors.warning,
                      color: colors.warning,
                    }}
                  >
                    暂停
                  </Button>
                )
              )}
              <Button
                danger
                icon={<StopOutlined />}
                onClick={stop}
                loading={isReconnecting}
                style={{ height: 36, borderRadius: 8 }}
              >
                {isReconnecting ? '重连中...' : '停止'}
              </Button>
            </>
          )}
          <Button
            icon={<SettingOutlined />}
            onClick={() => setShowSettings(true)}
            style={{ height: 36, borderRadius: 8, borderColor: colors.border }}
          />
          <Button
            icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={() => setIsFullscreen(!isFullscreen)}
            style={{ height: 36, borderRadius: 8, borderColor: colors.border }}
          />
          {/* 工作流完成后显示关闭按钮 */}
          {(workflow.status === 'completed' || workflow.status === 'error') && onClose && (
            <Button
              icon={<CloseOutlined />}
              onClick={onClose}
              style={{ height: 36, borderRadius: 8, borderColor: colors.border }}
            >
              关闭
            </Button>
          )}
          {isFullscreen && (
            <Button
              icon={<CloseOutlined />}
              onClick={() => setIsFullscreen(false)}
              style={{ height: 36, borderRadius: 8, borderColor: colors.border }}
            />
          )}
        </div>
      </div>

      {/* 主内容区 */}
      <div style={{
        display: 'flex',
        gap: 16,
        padding: 16,
        height: isFullscreen ? 'calc(100% - 60px)' : 520,
      }}>
        {/* 左侧：节点流程图 */}
        <div style={{
          width: 320,
          flexShrink: 0,
          background: colors.card,
          borderRadius: 12,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}>
          <WorkflowVisualizer
            workflow={workflow}
            selectedNodeId={selectedNodeId ?? undefined}
            onNodeSelect={(id) => setSelectedNodeId(id ?? null)}
            streamingContent={workflow.streamingContent}
          />
        </div>

        {/* 右侧：节点详情 + 实时输出 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>
          {/* 节点详情 */}
          <div style={{ flex: 1, minHeight: 0 }}>
            <NodeDetailPanel node={selectedNode} />
          </div>

          {/* 实时输出 */}
          <div style={{
            height: 200,
            background: colors.card,
            borderRadius: 12,
            border: `1px solid ${colors.border}`,
            overflow: 'hidden',
          }}>
            <StreamingOutput
              content={workflow.streamingContent}
              isStreaming={isRunning}
              nodeName={workflow.nodes.find(n => n.id === workflow.currentNodeId)?.name}
            />
          </div>
        </div>
      </div>

      {/* 设置弹窗 */}
      <Modal
        title={<span style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>工作流参数</span>}
        open={showSettings}
        onCancel={() => setShowSettings(false)}
        onOk={() => setShowSettings(false)}
        okText="确定"
        width={480}
        styles={{
          content: { background: colors.card, borderRadius: 16 },
          header: { background: colors.card, borderBottom: `1px solid ${colors.border}` },
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, padding: '16px 0' }}>
          {type === 'continue-chapters' && (
            <>
              <div>
                <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
                  起始章节
                </label>
                <InputNumber
                  min={1}
                  value={startChapter}
                  onChange={(v) => setStartChapter(v || 1)}
                  style={{ width: '100%', borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
                  续写数量
                </label>
                <InputNumber
                  min={1}
                  max={10}
                  value={count}
                  onChange={(v) => setCount(Math.min(10, Math.max(1, v || 1)))}
                  style={{ width: '100%', borderRadius: 8 }}
                />
              </div>
            </>
          )}
          {type === 'rewrite-chapter' && (
            <>
              <div>
                <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
                  重写章节
                </label>
                <InputNumber
                  min={1}
                  value={chapterNum}
                  onChange={(v) => setChapterNum(v || 1)}
                  style={{ width: '100%', borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
                  改写要求
                </label>
                <TextArea
                  rows={4}
                  value={rewriteRequirements}
                  onChange={(e) => setRewriteRequirements(e.target.value)}
                  placeholder="描述需要改写的内容和方向..."
                  style={{ borderRadius: 8 }}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>保持剧情连贯</label>
                <Switch checked={keepPlot} onChange={setKeepPlot} />
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default WorkflowExecution;
