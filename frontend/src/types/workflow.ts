/**
 * 工作流可视化类型定义
 */

// 节点状态
export type NodeStatus = 'pending' | 'running' | 'completed' | 'error' | 'skipped';

// 节点类型
export type NodeType = 'agent' | 'llm' | 'tool' | 'condition' | 'start' | 'end';

// 单个节点
export interface WorkflowNode {
  id: string;
  name: string;
  type: NodeType;
  status: NodeStatus;
  description?: string;
  
  // 输入输出
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  
  // LLM 相关
  systemPrompt?: string;
  userPrompt?: string;
  generatedContent?: string;
  
  // 统计
  tokenUsage?: {
    promptTokens?: number;
    completionTokens?: number;
    totalTokens?: number;
  };
  duration?: number; // 毫秒
  
  // 错误信息
  error?: string;
  
  // 时间戳
  startedAt?: string;
  completedAt?: string;
}

// 节点连接
export interface NodeConnection {
  from: string;
  to: string;
  label?: string;
}

// 工作流状态
export type WorkflowStatus = 'idle' | 'running' | 'paused' | 'completed' | 'error';

// 工作流定义
export interface Workflow {
  id: string;
  name: string;
  type: 'generate-outline' | 'continue-chapters' | 'rewrite-chapter';
  status: WorkflowStatus;
  nodes: WorkflowNode[];
  connections: NodeConnection[];
  
  // 当前进度
  currentNodeId?: string;
  progress: number; // 0-100
  
  // 时间
  startedAt?: string;
  completedAt?: string;
  
  // 流式输出缓冲
  streamingContent: string;
}

// SSE 事件类型
export interface WorkflowSSEEvent {
  type: 'workflow_start' | 'node_start' | 'node_token' | 'node_end' | 'node_error' | 'workflow_end' | 'progress' | 'error';
  
  // workflow_start / workflow_end
  workflowId?: string;
  workflowName?: string;
  
  // node_* 事件
  nodeId?: string;
  nodeName?: string;
  nodeType?: NodeType;
  
  // node_token
  token?: string;
  
  // node_end
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  systemPrompt?: string;
  userPrompt?: string;
  tokenUsage?: { promptTokens?: number; completionTokens?: number; totalTokens?: number };
  duration?: number;
  
  // node_error
  error?: string;
  
  // progress
  progress?: number;
}
