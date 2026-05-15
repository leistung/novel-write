/**
 * 工作流可视化组件
 * 
 * 类似 Dify 的节点流程图 + 实时执行状态
 */
import React from 'react';
import { Progress, Typography, Empty } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ArrowDownOutlined,
  RobotOutlined,
  BulbOutlined,
  ToolOutlined,
  ThunderboltOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { Workflow, WorkflowNode, NodeStatus, NodeType } from '../../types/workflow';

const { Text } = Typography;

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

// ==================== 节点图标映射 ====================
const NodeIcon: React.FC<{ type: NodeType; status: NodeStatus }> = ({ type, status }) => {
  const iconColor = status === 'running' ? colors.primary : 
                    status === 'completed' ? colors.success : 
                    status === 'error' ? colors.error : colors.textSecondary;
  
  const iconStyle = { fontSize: 18, color: iconColor };
  
  switch (type) {
    case 'agent':
      return <RobotOutlined style={iconStyle} />;
    case 'llm':
      return <BulbOutlined style={iconStyle} />;
    case 'tool':
      return <ToolOutlined style={iconStyle} />;
    case 'condition':
      return <ThunderboltOutlined style={iconStyle} />;
    case 'start':
    case 'end':
      return <FileTextOutlined style={iconStyle} />;
    default:
      return <BulbOutlined style={iconStyle} />;
  }
};

const statusColors: Record<NodeStatus, string> = {
  pending: colors.textSecondary,
  running: colors.primary,
  completed: colors.success,
  error: colors.error,
  skipped: colors.border,
};

// ==================== 单个节点组件 ====================
interface NodeCardProps {
  node: WorkflowNode;
  isActive: boolean;
  isSelected: boolean;
  onClick: () => void;
}

const NodeCard: React.FC<NodeCardProps> = ({ node, isActive, isSelected, onClick }) => {
  const statusIcon = {
    pending: null,
    running: <LoadingOutlined style={{ color: colors.primary, fontSize: 14 }} spin />,
    completed: <CheckCircleOutlined style={{ color: colors.success, fontSize: 14 }} />,
    error: <CloseCircleOutlined style={{ color: colors.error, fontSize: 14 }} />,
    skipped: null,
  }[node.status];

  return (
    <div
      onClick={onClick}
      style={{
        position: 'relative',
        padding: '12px 16px',
        borderRadius: 12,
        cursor: 'pointer',
        transition: 'all 0.2s',
        background: isActive 
          ? 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(129,140,248,0.1))' 
          : isSelected 
            ? 'rgba(99,102,241,0.1)' 
            : 'transparent',
        border: `1px solid ${isSelected ? colors.primary : isActive ? 'rgba(99,102,241,0.3)' : 'transparent'}`,
        boxShadow: isSelected ? `0 0 0 2px rgba(99,102,241,0.2)` : 'none',
      }}
    >
      {/* 状态指示条 */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 8,
          bottom: 8,
          width: 3,
          borderRadius: 2,
          background: statusColors[node.status],
          transition: 'background 0.3s',
        }}
      />

      {/* 节点内容 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginLeft: 8 }}>
        <div style={{
          width: 36,
          height: 36,
          borderRadius: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: isActive ? 'rgba(99,102,241,0.2)' : 'rgba(51,65,85,0.5)',
          transition: 'background 0.3s',
        }}>
          <NodeIcon type={node.type} status={node.status} />
        </div>
        
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Text strong style={{ color: colors.text, fontSize: 14 }}>
              {node.name}
            </Text>
            {statusIcon}
          </div>
          
          {/* Token 使用量 */}
          {node.status === 'completed' && node.tokenUsage && (
            <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 12, fontSize: 12 }}>
              <span style={{ color: colors.textSecondary }}>
                📊 {node.tokenUsage.totalTokens?.toLocaleString()} tokens
              </span>
              {node.duration && (
                <span style={{ color: colors.textSecondary }}>
                  ⏱️ {(node.duration / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          )}
          
          {/* 运行中动画 */}
          {node.status === 'running' && (
            <div style={{ marginTop: 4 }}>
              <div style={{
                height: 3,
                borderRadius: 2,
                background: 'rgba(99,102,241,0.2)',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: '30%',
                  background: `linear-gradient(90deg, ${colors.primary}, ${colors.primaryLight})`,
                  animation: 'pulse 1.5s ease-in-out infinite',
                }} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ==================== 节点连接线 ====================
interface ConnectionLineProps {
  fromStatus: NodeStatus;
  toStatus: NodeStatus;
}

const ConnectionLine: React.FC<ConnectionLineProps> = ({ fromStatus, toStatus }) => {
  const isActive = fromStatus === 'completed' && (toStatus === 'running' || toStatus === 'completed');
  const isRunning = toStatus === 'running';

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px 0' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* 连接线 */}
        <div
          style={{
            width: 2,
            height: 20,
            borderRadius: 1,
            transition: 'background 0.3s',
            background: isActive 
              ? `linear-gradient(180deg, ${colors.success}, ${isRunning ? colors.primary : colors.success})` 
              : colors.border,
          }}
        />
        {/* 箭头 */}
        <ArrowDownOutlined
          style={{
            fontSize: 10,
            transition: 'color 0.3s',
            color: isActive ? (isRunning ? colors.primary : colors.success) : colors.border,
          }}
        />
      </div>
    </div>
  );
};

// ==================== 主组件 ====================
interface WorkflowVisualizerProps {
  workflow: Workflow;
  selectedNodeId?: string;
  onNodeSelect: (nodeId: string | null) => void;
  streamingContent?: string;
}

const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  workflow,
  selectedNodeId,
  onNodeSelect,
}) => {
  const completedCount = workflow.nodes.filter(n => n.status === 'completed').length;
  const totalCount = workflow.nodes.length;

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部状态栏 */}
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${colors.border}`,
        background: 'rgba(30,41,59,0.5)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Text style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>
            执行流程
          </Text>
          
          {totalCount > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Text style={{ fontSize: 12, color: colors.textSecondary }}>
                {completedCount}/{totalCount}
              </Text>
              <Progress
                percent={totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0}
                size="small"
                style={{ width: 80, margin: 0 }}
                strokeColor={{ from: colors.primary, to: colors.primaryLight }}
                trailColor={colors.border}
                showInfo={false}
              />
            </div>
          )}
        </div>
      </div>

      {/* 节点流程图 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {workflow.nodes.length === 0 ? (
          <div style={{ 
            height: '100%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
          }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={<span style={{ color: colors.textSecondary }}>点击"开始执行"启动工作流</span>}
            />
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {workflow.nodes.map((node, index) => (
              <React.Fragment key={node.id}>
                <NodeCard
                  node={node}
                  isActive={workflow.currentNodeId === node.id}
                  isSelected={selectedNodeId === node.id}
                  onClick={() => onNodeSelect(selectedNodeId === node.id ? null : node.id)}
                />
                {index < workflow.nodes.length - 1 && (
                  <ConnectionLine
                    fromStatus={node.status}
                    toStatus={workflow.nodes[index + 1].status}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* 工作流整体进度 */}
      {workflow.status === 'running' && workflow.progress > 0 && (
        <div style={{
          padding: '8px 16px',
          borderTop: `1px solid ${colors.border}`,
          background: 'rgba(30,41,59,0.5)',
        }}>
          <Progress
            percent={workflow.progress}
            size="small"
            strokeColor={{ from: colors.primary, to: colors.success }}
            trailColor={colors.border}
          />
        </div>
      )}
    </div>
  );
};

export default WorkflowVisualizer;
