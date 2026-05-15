import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message } from 'antd';
import {
  ArrowLeftOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  DashboardOutlined,
  CloseOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons';
import {
  getWorkflowStatus,
  getNodeDetail,
  pauseWorkflow,
  resumeWorkflow,
  retryNode,
} from '../services/api';
import type { WorkflowExecution, WorkflowNode } from '../types';

// ==================== 样式常量 ====================

const COLORS = {
  bgPrimary: '#0f172a',
  bgSecondary: '#1e293b',
  bgCard: 'rgba(255,255,255,0.04)',
  bgCardHover: 'rgba(255,255,255,0.06)',
  bgCardActive: 'rgba(99,102,241,0.08)',
  bgTopBar: 'rgba(255,255,255,0.03)',
  bgDetailPanel: 'rgba(255,255,255,0.02)',
  bgControlBar: 'rgba(255,255,255,0.03)',
  bgCodeBlock: 'rgba(0,0,0,0.3)',
  border: 'rgba(255,255,255,0.06)',
  borderHover: 'rgba(255,255,255,0.1)',
  borderActive: '#6366f1',
  textPrimary: '#e2e8f0',
  textSecondary: '#94a3b8',
  textTertiary: '#64748b',
  accentIndigo: '#6366f1',
  accentIndigoLight: '#818cf8',
  accentViolet: '#8b5cf6',
  accentGreen: '#22c55e',
  accentGreenLight: '#4ade80',
  accentRed: '#ef4444',
  accentRedLight: '#f87171',
  accentOrange: '#f59e0b',
  accentOrangeLight: '#fbbf24',
  accentSlate: '#475569',
  codeText: '#a5b4fc',
  connectorLine: 'rgba(255,255,255,0.08)',
  connectorDot: 'rgba(255,255,255,0.15)',
};

// ==================== 工具函数 ====================

/** 节点状态对应左侧竖条颜色 */
function nodeBarColor(status: WorkflowNode['status']): string {
  const map: Record<WorkflowNode['status'], string> = {
    pending: COLORS.accentSlate,
    running: COLORS.accentIndigo,
    completed: COLORS.accentGreen,
    failed: COLORS.accentRed,
    skipped: COLORS.accentSlate,
  };
  return map[status] || COLORS.accentSlate;
}

/** 节点状态中文标签 */
function nodeStatusLabel(status: WorkflowNode['status']): string {
  const map: Record<WorkflowNode['status'], string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    skipped: '已跳过',
  };
  return map[status] || status;
}

/** 工作流状态中文标签 */
function workflowStatusLabel(status: WorkflowExecution['status']): string {
  const map: Record<WorkflowExecution['status'], string> = {
    pending: '等待中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
  };
  return map[status] || status;
}

/** 工作流类型中文标签 */
function workflowTypeLabel(type: string): string {
  const map: Record<string, string> = {
    'generate-outline': '大纲生成',
    'continue-chapters': '续写章节',
    'rewrite-chapter': '重写章节',
    'audit-chapter': '审核章节',
  };
  return map[type] || type;
}

/** 格式化毫秒为秒 */
function formatDuration(ms: number): string {
  if (!ms || ms <= 0) return '--';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/** 格式化 Token 用量 */
function formatTokens(tokens: number): string {
  if (!tokens || tokens <= 0) return '--';
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
  return String(tokens);
}

/** 工作流状态 Badge 样式 */
function workflowBadgeStyle(status: WorkflowExecution['status']): React.CSSProperties {
  const map: Record<WorkflowExecution['status'], { bg: string; color: string }> = {
    running: { bg: 'rgba(34,197,94,0.15)', color: COLORS.accentGreenLight },
    paused: { bg: 'rgba(245,158,11,0.15)', color: COLORS.accentOrangeLight },
    completed: { bg: 'rgba(34,197,94,0.15)', color: COLORS.accentGreenLight },
    failed: { bg: 'rgba(239,68,68,0.15)', color: COLORS.accentRedLight },
    pending: { bg: 'rgba(255,255,255,0.06)', color: COLORS.textSecondary },
  };
  const style = map[status] || map.pending;
  return {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '3px 10px',
    borderRadius: 4,
    background: style.bg,
    color: style.color,
    fontSize: 12,
    fontWeight: 500,
    lineHeight: '20px',
    animation: status === 'running' ? 'wf-pulse 2s ease-in-out infinite' : undefined,
  };
}

// ==================== 注入全局 CSS ====================

const globalStyles = `
@keyframes wf-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
@keyframes wf-bar-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
`;

// ==================== 主组件 ====================

const WorkflowPanel: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();

  // ========== 数据状态 ==========
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [nodeList, setNodeList] = useState<WorkflowNode[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [nodeLoading, setNodeLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // ========== 详情面板折叠 ==========
  const [detailPanelOpen, setDetailPanelOpen] = useState(true);

  // ========== 迷你窗口状态 ==========
  const [miniOpen, setMiniOpen] = useState(false);
  const [miniExpanded, setMiniExpanded] = useState(false);
  const [miniPos, setMiniPos] = useState({ x: window.innerWidth - 360, y: window.innerHeight - 200 });
  const miniDragging = useRef(false);
  const miniDragOffset = useRef({ x: 0, y: 0 });

  // ========== 详情面板 Tab ==========
  const [detailTab, setDetailTab] = useState<'input' | 'output' | 'stream'>('input');

  // ========== 轮询定时器 ==========
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ========== 加载工作流状态 ==========
  const loadWorkflowStatus = useCallback(async () => {
    if (!workflowId) return;
    try {
      setLoading(true);
      const data = await getWorkflowStatus(workflowId);
      setExecution(data as WorkflowExecution);

      // 将 nodes Record 转为数组并保持顺序
      if (data.nodes) {
        const nodes: WorkflowNode[] = Object.values(data.nodes) as WorkflowNode[];
        setNodeList(nodes);
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载工作流状态失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  // ========== 加载节点详情 ==========
  const loadNodeDetail = useCallback(async (nodeId: string) => {
    if (!workflowId || !nodeId) return;
    try {
      setNodeLoading(true);
      const data = await getNodeDetail(workflowId, nodeId);
      setSelectedNode(data as WorkflowNode);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载节点详情失败';
      message.error(errorMsg);
    } finally {
      setNodeLoading(false);
    }
  }, [workflowId]);

  // ========== 轮询逻辑（工作流完成或失败时自动停止） ==========
  useEffect(() => {
    loadWorkflowStatus();

    pollTimerRef.current = setInterval(() => {
      loadWorkflowStatus();
    }, 3000);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [loadWorkflowStatus]);

  // ========== 工作流完成/失败时停止轮询 ==========
  useEffect(() => {
    if (execution?.status === 'completed' || execution?.status === 'failed') {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    }
  }, [execution?.status]);

  // ========== 选中节点时自动加载详情 ==========
  useEffect(() => {
    if (selectedNodeId) {
      loadNodeDetail(selectedNodeId);
    }
  }, [selectedNodeId, loadNodeDetail]);

  // ========== 如果正在运行，自动选中当前节点 ==========
  useEffect(() => {
    if (execution?.current_node && !selectedNodeId) {
      setSelectedNodeId(execution.current_node);
    }
  }, [execution?.current_node]); // eslint-disable-line react-hooks/exhaustive-deps

  // ========== 操作：暂停 ==========
  const handlePause = async () => {
    if (!workflowId) return;
    try {
      setActionLoading(true);
      await pauseWorkflow(workflowId);
      message.success('工作流已暂停');
      loadWorkflowStatus();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '暂停失败';
      message.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  // ========== 操作：继续 ==========
  const handleResume = async () => {
    if (!workflowId) return;
    try {
      setActionLoading(true);
      await resumeWorkflow(workflowId, selectedNodeId || undefined);
      message.success('工作流已继续');
      loadWorkflowStatus();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '继续失败';
      message.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  // ========== 操作：重试节点 ==========
  const handleRetry = async () => {
    if (!workflowId || !selectedNodeId) return;
    try {
      setActionLoading(true);
      await retryNode(workflowId, selectedNodeId);
      message.success('节点重试已启动');
      loadWorkflowStatus();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '重试失败';
      message.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  // ========== 迷你窗口拖拽处理 ==========
  const handleMiniMouseDown = (e: React.MouseEvent) => {
    if (miniExpanded) return;
    miniDragging.current = true;
    miniDragOffset.current = {
      x: e.clientX - miniPos.x,
      y: e.clientY - miniPos.y,
    };

    const handleMouseMove = (ev: MouseEvent) => {
      if (!miniDragging.current) return;
      setMiniPos({
        x: ev.clientX - miniDragOffset.current.x,
        y: ev.clientY - miniDragOffset.current.y,
      });
    };

    const handleMouseUp = () => {
      miniDragging.current = false;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  // ==================== 渲染：节点卡片 ====================
  const renderNodeCard = (node: WorkflowNode, index: number) => {
    const isActive = selectedNodeId === node.node_id;
    const isRunning = node.status === 'running';
    const barColor = nodeBarColor(node.status);

    return (
      <div key={node.node_id} style={{ position: 'relative' }}>
        {/* 连接线 */}
        {index > 0 && (
          <div
            style={{
              position: 'absolute',
              left: 19,
              top: -24,
              width: 2,
              height: 24,
              background: COLORS.connectorLine,
              zIndex: 1,
            }}
          />
        )}

        {/* 连接线上的圆点 */}
        {index > 0 && (
          <div
            style={{
              position: 'absolute',
              left: 17,
              top: -24,
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: COLORS.connectorDot,
              zIndex: 2,
            }}
          />
        )}

        {/* 节点卡片 */}
        <div
          onClick={() => {
            setSelectedNodeId(node.node_id);
            if (!detailPanelOpen) setDetailPanelOpen(true);
          }}
          style={{
            marginLeft: 40,
            marginBottom: 12,
            padding: '16px 20px',
            borderRadius: 10,
            background: isActive ? COLORS.bgCardActive : COLORS.bgCard,
            border: `1px solid ${isActive ? COLORS.borderActive : COLORS.border}`,
            borderLeft: `3px solid ${barColor}`,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            position: 'relative',
          }}
          onMouseEnter={(e) => {
            if (!isActive) {
              (e.currentTarget as HTMLDivElement).style.background = COLORS.bgCardHover;
              (e.currentTarget as HTMLDivElement).style.borderColor = COLORS.borderHover;
            }
          }}
          onMouseLeave={(e) => {
            if (!isActive) {
              (e.currentTarget as HTMLDivElement).style.background = COLORS.bgCard;
              (e.currentTarget as HTMLDivElement).style.borderColor = COLORS.border;
            }
          }}
        >
          {/* 节点名称行 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span
              style={{
                fontSize: 14,
                fontWeight: 500,
                color: COLORS.textPrimary,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                flex: 1,
                minWidth: 0,
              }}
            >
              {node.node_name || node.node_type}
            </span>
            <span
              style={{
                fontSize: 12,
                color: COLORS.textSecondary,
                flexShrink: 0,
                animation: isRunning ? 'wf-pulse 2s ease-in-out infinite' : undefined,
              }}
            >
              {nodeStatusLabel(node.status)}
            </span>
          </div>

          {/* 状态文字 */}
          <div style={{ fontSize: 12, color: COLORS.textSecondary, marginBottom: 8 }}>
            {node.node_type}
          </div>

          {/* 底部信息：耗时和 Token */}
          <div style={{ display: 'flex', gap: 16 }}>
            <span style={{ fontSize: 12, color: COLORS.textTertiary }}>
              {formatDuration(node.duration_ms)}
            </span>
            {node.token_usage?.total_tokens > 0 && (
              <span style={{ fontSize: 12, color: COLORS.textTertiary }}>
                {formatTokens(node.token_usage.total_tokens)} tokens
              </span>
            )}
          </div>

          {/* 错误信息 */}
          {node.status === 'failed' && node.error_message && (
            <div
              style={{
                marginTop: 8,
                padding: '6px 10px',
                background: 'rgba(239,68,68,0.1)',
                borderRadius: 6,
                borderLeft: `2px solid ${COLORS.accentRed}`,
              }}
            >
              <span style={{ fontSize: 12, color: COLORS.accentRedLight }}>
                {node.error_message}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ==================== 渲染：JSON 代码块 ====================
  const renderJsonBlock = (data: Record<string, unknown> | undefined) => {
    if (!data || Object.keys(data).length === 0) {
      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: 200,
            color: COLORS.textTertiary,
            fontSize: 13,
          }}
        >
          暂无数据
        </div>
      );
    }
    return (
      <pre
        style={{
          margin: 0,
          padding: 16,
          background: COLORS.bgCodeBlock,
          borderRadius: 8,
          color: COLORS.codeText,
          fontSize: 13,
          lineHeight: 1.6,
          maxHeight: 400,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  // ==================== 渲染：Stream 输出 ====================
  const renderStreamOutput = (text: string | undefined) => {
    if (!text) {
      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: 200,
            color: COLORS.textTertiary,
            fontSize: 13,
          }}
        >
          暂无流式输出
        </div>
      );
    }
    return (
      <pre
        style={{
          margin: 0,
          padding: 16,
          background: COLORS.bgCodeBlock,
          borderRadius: 8,
          color: COLORS.codeText,
          fontSize: 13,
          lineHeight: 1.8,
          maxHeight: 400,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}
      >
        {text}
      </pre>
    );
  };

  // ==================== 渲染：右侧详情面板 ====================
  const renderDetailPanel = () => {
    if (!detailPanelOpen) return null;

    if (!selectedNodeId) {
      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            minHeight: 300,
            color: COLORS.textTertiary,
            fontSize: 13,
          }}
        >
          点击左侧节点查看详情
        </div>
      );
    }

    if (nodeLoading) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
          <LoadingOutlined style={{ fontSize: 24, color: COLORS.accentIndigo }} />
        </div>
      );
    }

    const node = selectedNode || nodeList.find((n) => n.node_id === selectedNodeId);

    const tabs: Array<{ key: 'input' | 'output' | 'stream'; label: string }> = [
      { key: 'input', label: '输入' },
      { key: 'output', label: '输出' },
      { key: 'stream', label: 'Stream' },
    ];

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* 详情头部 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 20px',
            borderBottom: `1px solid ${COLORS.border}`,
          }}
        >
          <span style={{ color: '#ffffff', fontSize: 15, fontWeight: 600 }}>
            {node?.node_name || node?.node_type || '节点详情'}
          </span>
          <button
            onClick={() => {
              setSelectedNodeId(null);
              setSelectedNode(null);
            }}
            style={{
              background: 'none',
              border: 'none',
              color: COLORS.textTertiary,
              cursor: 'pointer',
              padding: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 4,
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.color = COLORS.textSecondary;
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.color = COLORS.textTertiary;
            }}
          >
            <CloseOutlined style={{ fontSize: 14 }} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ padding: '0 20px', borderBottom: `1px solid ${COLORS.border}` }}>
          <div style={{ display: 'flex', gap: 0 }}>
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setDetailTab(tab.key)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '10px 0',
                  marginRight: 24,
                  fontSize: 13,
                  color: detailTab === tab.key ? COLORS.textPrimary : COLORS.textSecondary,
                  fontWeight: detailTab === tab.key ? 500 : 400,
                  cursor: 'pointer',
                  position: 'relative',
                  transition: 'color 0.2s',
                  borderBottom: detailTab === tab.key
                    ? `2px solid ${COLORS.accentIndigo}`
                    : '2px solid transparent',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab 内容 */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px 20px' }}>
          {detailTab === 'input' && renderJsonBlock(node?.input_data)}
          {detailTab === 'output' && renderJsonBlock(node?.output_data)}
          {detailTab === 'stream' && renderStreamOutput(node?.stream_output)}
        </div>

        {/* 底部控制栏 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 8,
            padding: '12px 20px',
            background: COLORS.bgControlBar,
            borderTop: `1px solid ${COLORS.border}`,
          }}
        >
          {/* 暂停按钮 */}
          <button
            disabled={!execution || execution.status !== 'running' || actionLoading}
            onClick={handlePause}
            style={{
              padding: '6px 16px',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 500,
              cursor:
                !execution || execution.status !== 'running' || actionLoading
                  ? 'not-allowed'
                  : 'pointer',
              background: 'rgba(245,158,11,0.1)',
              border: '1px solid rgba(245,158,11,0.3)',
              color: COLORS.accentOrangeLight,
              opacity:
                !execution || execution.status !== 'running' || actionLoading ? 0.5 : 1,
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <PauseCircleOutlined style={{ fontSize: 14 }} />
            暂停
          </button>

          {/* 继续按钮 */}
          <button
            disabled={!execution || execution.status !== 'paused' || actionLoading}
            onClick={handleResume}
            style={{
              padding: '6px 16px',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 500,
              cursor:
                !execution || execution.status !== 'paused' || actionLoading
                  ? 'not-allowed'
                  : 'pointer',
              background:
                !execution || execution.status !== 'paused' || actionLoading
                  ? 'rgba(99,102,241,0.3)'
                  : `linear-gradient(135deg, ${COLORS.accentIndigo}, ${COLORS.accentViolet})`,
              border: 'none',
              color: '#ffffff',
              opacity:
                !execution || execution.status !== 'paused' || actionLoading ? 0.5 : 1,
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <PlayCircleOutlined style={{ fontSize: 14 }} />
            继续
          </button>

          {/* 重试按钮 */}
          <button
            disabled={
              !selectedNode ||
              (selectedNode.status !== 'failed' && selectedNode.status !== 'completed') ||
              actionLoading
            }
            onClick={handleRetry}
            style={{
              padding: '6px 16px',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 500,
              cursor:
                !selectedNode ||
                (selectedNode.status !== 'failed' && selectedNode.status !== 'completed') ||
                actionLoading
                  ? 'not-allowed'
                  : 'pointer',
              background: COLORS.bgCard,
              border: `1px solid ${COLORS.border}`,
              color: COLORS.textSecondary,
              opacity:
                !selectedNode ||
                (selectedNode.status !== 'failed' && selectedNode.status !== 'completed') ||
                actionLoading
                  ? 0.5
                  : 1,
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <ReloadOutlined style={{ fontSize: 14 }} />
            重试
          </button>
        </div>
      </div>
    );
  };

  // ==================== 渲染：迷你窗口 ====================
  const renderMiniWindow = () => {
    if (!miniOpen) {
      return (
        <button
          onClick={() => setMiniOpen(true)}
          style={{
            position: 'fixed',
            right: 32,
            bottom: 32,
            width: 48,
            height: 48,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${COLORS.accentIndigo}, ${COLORS.accentViolet})`,
            border: 'none',
            color: '#ffffff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(99,102,241,0.4)',
            zIndex: 1000,
            fontSize: 20,
            transition: 'transform 0.2s, box-shadow 0.2s',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.05)';
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              '0 6px 24px rgba(99,102,241,0.5)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)';
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              '0 4px 20px rgba(99,102,241,0.4)';
          }}
        >
          <DashboardOutlined />
        </button>
      );
    }

    const currentNode = nodeList.find((n) => n.node_id === execution?.current_node);

    if (miniExpanded) {
      return (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: COLORS.bgPrimary,
            zIndex: 1100,
            padding: 24,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* 全屏头部 */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 24,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <DashboardOutlined style={{ fontSize: 20, color: COLORS.accentIndigoLight }} />
              <span style={{ fontSize: 18, fontWeight: 600, color: COLORS.textPrimary }}>
                工作流状态
              </span>
              {execution && (
                <span style={workflowBadgeStyle(execution.status)}>
                  {execution.status === 'running' && (
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: '50%',
                        background: COLORS.accentGreenLight,
                        display: 'inline-block',
                        animation: 'wf-pulse 2s ease-in-out infinite',
                      }}
                    />
                  )}
                  {workflowStatusLabel(execution.status)}
                </span>
              )}
            </div>
            <button
              onClick={() => setMiniExpanded(false)}
              style={{
                background: 'none',
                border: 'none',
                color: COLORS.textSecondary,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 13,
                padding: '6px 12px',
                borderRadius: 6,
                transition: 'background 0.2s',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = COLORS.bgCard;
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = 'none';
              }}
            >
              <FullscreenExitOutlined />
              退出全屏
            </button>
          </div>

          {/* 全屏内容：节点列表 */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            {nodeList.length === 0 ? (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: 200,
                  color: COLORS.textTertiary,
                  fontSize: 13,
                }}
              >
                暂无节点数据
              </div>
            ) : (
              nodeList.map((node, idx) => renderNodeCard(node, idx))
            )}
          </div>

          {/* 全屏底部进度 */}
          {execution && (
            <div
              style={{
                padding: '16px 0 0',
                borderTop: `1px solid ${COLORS.border}`,
                display: 'flex',
                alignItems: 'center',
                gap: 16,
              }}
            >
              <div style={{ flex: 1, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${execution.progress}%`,
                    borderRadius: 2,
                    background: `linear-gradient(90deg, ${COLORS.accentIndigo}, ${COLORS.accentViolet})`,
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
              <span style={{ color: COLORS.textSecondary, fontSize: 13, fontWeight: 600, flexShrink: 0 }}>
                {execution.progress}%
              </span>
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        onMouseDown={handleMiniMouseDown}
        style={{
          position: 'fixed',
          left: miniPos.x,
          top: miniPos.y,
          width: 320,
          background: COLORS.bgSecondary,
          borderRadius: 12,
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          zIndex: 1000,
          border: `1px solid ${COLORS.border}`,
          overflow: 'hidden',
          cursor: 'grab',
          userSelect: 'none',
        }}
      >
        {/* 迷你窗口头部 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '10px 14px',
            borderBottom: `1px solid ${COLORS.border}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DashboardOutlined style={{ color: COLORS.accentIndigoLight, fontSize: 14 }} />
            <span style={{ color: COLORS.textPrimary, fontSize: 13, fontWeight: 500 }}>
              工作流状态
            </span>
          </div>
          <div style={{ display: 'flex', gap: 2 }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMiniExpanded(true);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: COLORS.textTertiary,
                cursor: 'pointer',
                width: 28,
                height: 28,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 4,
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = COLORS.textSecondary;
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = COLORS.textTertiary;
              }}
            >
              <FullscreenOutlined style={{ fontSize: 12 }} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMiniOpen(false);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: COLORS.textTertiary,
                cursor: 'pointer',
                width: 28,
                height: 28,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 4,
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = COLORS.textSecondary;
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color = COLORS.textTertiary;
              }}
            >
              <CloseOutlined style={{ fontSize: 12 }} />
            </button>
          </div>
        </div>

        {/* 迷你窗口内容 */}
        <div style={{ padding: 14 }}>
          {/* 进度条 */}
          {execution && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: COLORS.textSecondary }}>进度</span>
                <span style={{ fontSize: 12, color: COLORS.textPrimary, fontWeight: 600 }}>
                  {execution.progress}%
                </span>
              </div>
              <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${execution.progress}%`,
                    borderRadius: 2,
                    background: `linear-gradient(90deg, ${COLORS.accentIndigo}, ${COLORS.accentViolet})`,
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </div>
          )}

          {/* 当前节点 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {execution?.status === 'running' ? (
              <LoadingOutlined style={{ color: COLORS.accentIndigoLight, fontSize: 14 }} />
            ) : execution?.status === 'completed' ? (
              <CheckCircleOutlined style={{ color: COLORS.accentGreenLight, fontSize: 14 }} />
            ) : execution?.status === 'failed' ? (
              <CloseCircleOutlined style={{ color: COLORS.accentRedLight, fontSize: 14 }} />
            ) : execution?.status === 'paused' ? (
              <WarningOutlined style={{ color: COLORS.accentOrangeLight, fontSize: 14 }} />
            ) : (
              <MinusCircleOutlined style={{ color: COLORS.textTertiary, fontSize: 14 }} />
            )}
            <span
              style={{
                fontSize: 12,
                color: COLORS.textSecondary,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {currentNode?.node_name || execution?.current_node || '暂无运行节点'}
            </span>
          </div>

          {/* 状态 Badge */}
          {execution && (
            <div style={{ marginTop: 8 }}>
              <span style={workflowBadgeStyle(execution.status)}>
                {execution.status === 'running' && (
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: COLORS.accentGreenLight,
                      display: 'inline-block',
                      animation: 'wf-pulse 2s ease-in-out infinite',
                    }}
                  />
                )}
                {workflowStatusLabel(execution.status)}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ==================== 主渲染 ====================
  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: COLORS.bgPrimary,
        padding: 0,
        overflow: 'hidden',
      }}
    >
      {/* 注入全局动画样式 */}
      <style>{globalStyles}</style>

      {/* ========== 顶部栏 ========== */}
      <div
        style={{
          height: 56,
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          background: COLORS.bgTopBar,
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        {/* 返回按钮 */}
        <button
          onClick={() => navigate(-1)}
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.06)',
            border: 'none',
            color: '#ffffff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 16,
            transition: 'background 0.2s',
            flexShrink: 0,
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.1)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.06)';
          }}
        >
          <ArrowLeftOutlined />
        </button>

        {execution && (
          <>
            {/* 工作流类型 Tag */}
            <span
              style={{
                marginLeft: 12,
                padding: '3px 10px',
                borderRadius: 4,
                background: 'rgba(99,102,241,0.15)',
                color: COLORS.accentIndigoLight,
                fontSize: 12,
                fontWeight: 500,
                lineHeight: '20px',
              }}
            >
              {workflowTypeLabel(execution.workflow_type)}
            </span>

            {/* 状态 Badge */}
            <span style={{ ...workflowBadgeStyle(execution.status), marginLeft: 8 }}>
              {execution.status === 'running' && (
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: COLORS.accentGreenLight,
                    display: 'inline-block',
                    animation: 'wf-pulse 2s ease-in-out infinite',
                  }}
                />
              )}
              {workflowStatusLabel(execution.status)}
            </span>

            {/* 右侧进度 */}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  width: 120,
                  height: 4,
                  borderRadius: 2,
                  background: 'rgba(255,255,255,0.1)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${execution.progress}%`,
                    borderRadius: 2,
                    background: `linear-gradient(90deg, ${COLORS.accentIndigo}, ${COLORS.accentViolet})`,
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
              <span style={{ color: '#ffffff', fontSize: 14, fontWeight: 500 }}>
                {execution.progress}%
              </span>
            </div>
          </>
        )}
      </div>

      {/* ========== 主体内容：左右分栏 ========== */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        {/* 左侧：节点流程图 */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '24px 24px 24px 40px',
          }}
        >
          {loading && !execution ? (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: 300,
              }}
            >
              <LoadingOutlined style={{ fontSize: 28, color: COLORS.accentIndigo }} />
            </div>
          ) : nodeList.length === 0 ? (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: 300,
                color: COLORS.textTertiary,
                fontSize: 13,
              }}
            >
              暂无节点数据
            </div>
          ) : (
            <div style={{ paddingTop: 4, maxWidth: 600, margin: '0 auto' }}>
              {nodeList.map((node, idx) => renderNodeCard(node, idx))}
            </div>
          )}
        </div>

        {/* 右侧：节点详情面板 */}
        {detailPanelOpen && (
          <div
            style={{
              width: 420,
              flexShrink: 0,
              background: COLORS.bgDetailPanel,
              borderLeft: `1px solid ${COLORS.border}`,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {renderDetailPanel()}
          </div>
        )}
      </div>

      {/* 浮动迷你窗口 */}
      {renderMiniWindow()}
    </div>
  );
};

export default WorkflowPanel;
