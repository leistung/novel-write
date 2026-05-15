/**
 * 流式生成组件
 * 
 * 使用 SSE 接收后端 LLM 实时输出
 */
import React, { useState, useRef, useCallback } from 'react';
import { Button, Card, Progress, Space, Typography, Alert, Spin } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { SSEClient, SSEEvent, streamGenerateOutline, streamContinueChapters, streamRewriteChapter } from '../services/sse';

const { Text, Title } = Typography;

interface StreamGeneratorProps {
  bookId: number;
  type: 'outline' | 'continue' | 'rewrite';
  startChapter?: number;
  count?: number;
  chapterNum?: number;
  rewriteRequirements?: string;
  keepPlot?: boolean;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface NodeOutput {
  name: string;
  content: string;
  status: 'running' | 'completed' | 'error';
}

const StreamGenerator: React.FC<StreamGeneratorProps> = ({
  bookId,
  type,
  startChapter = 1,
  count = 1,
  chapterNum = 1,
  rewriteRequirements = '',
  keepPlot = true,
  onComplete,
  onError,
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentNode, setCurrentNode] = useState<string>('');
  const [nodes, setNodes] = useState<Record<string, NodeOutput>>({});
  const [error, setError] = useState<string>('');
  const sseClientRef = useRef<SSEClient | null>(null);

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'start':
        if (event.node) {
          setCurrentNode(event.node);
          setNodes((prev) => ({
            ...prev,
            [event.node!]: { name: event.node!, content: '', status: 'running' },
          }));
        }
        break;

      case 'token':
        if (event.node && event.text) {
          setNodes((prev) => ({
            ...prev,
            [event.node!]: {
              ...prev[event.node!],
              content: (prev[event.node!]?.content || '') + event.text,
            },
          }));
        }
        break;

      case 'node_end':
        if (event.node) {
          setNodes((prev) => ({
            ...prev,
            [event.node!]: {
              ...prev[event.node!],
              status: event.ok ? 'completed' : 'error',
            },
          }));
        }
        break;

      case 'progress':
        if (event.value !== undefined) {
          setProgress(event.value);
        }
        break;

      case 'done':
        setIsRunning(false);
        setProgress(100);
        onComplete?.();
        break;

      case 'error':
        setIsRunning(false);
        const errorMsg = event.error || '未知错误';
        setError(errorMsg);
        onError?.(errorMsg);
        break;
    }
  }, [onComplete, onError]);

  const handleSSEError = useCallback((err: Error) => {
    setIsRunning(false);
    setError(err.message);
    onError?.(err.message);
  }, [onError]);

  const handleSSEClose = useCallback(() => {
    // 连接关闭时的处理
  }, []);

  const start = () => {
    setIsRunning(true);
    setError('');
    setProgress(0);
    setNodes({});

    let client: SSEClient;

    switch (type) {
      case 'outline':
        client = streamGenerateOutline(bookId, handleEvent, handleSSEError, handleSSEClose);
        break;
      case 'continue':
        client = streamContinueChapters(
          bookId, startChapter, count,
          handleEvent, handleSSEError, handleSSEClose
        );
        break;
      case 'rewrite':
        client = streamRewriteChapter(
          bookId, chapterNum, rewriteRequirements, keepPlot,
          handleEvent, handleSSEError, handleSSEClose
        );
        break;
      default:
        return;
    }

    sseClientRef.current = client;
  };

  const stop = () => {
    if (sseClientRef.current) {
      sseClientRef.current.disconnect();
      sseClientRef.current = null;
    }
    setIsRunning(false);
  };

  const getButtonText = () => {
    switch (type) {
      case 'outline':
        return isRunning ? '生成中...' : '生成大纲';
      case 'continue':
        return isRunning ? `续写第${startChapter}章中...` : `续写${count}章`;
      case 'rewrite':
        return isRunning ? `重写第${chapterNum}章中...` : `重写第${chapterNum}章`;
      default:
        return '开始';
    }
  };

  return (
    <Card
      title={
        <Space>
          <Title level={5} style={{ margin: 0, color: '#e2e8f0' }}>
            {type === 'outline' ? '大纲生成' : type === 'continue' ? '续写章节' : '重写章节'}
          </Title>
          {isRunning && <Spin size="small" />}
        </Space>
      }
      style={{
        background: '#1e293b',
        border: '1px solid #334155',
      }}
      headStyle={{
        background: '#1e293b',
        borderBottom: '1px solid #334155',
      }}
      bodyStyle={{
        background: '#1e293b',
      }}
    >
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError('')}
          style={{ marginBottom: 16 }}
        />
      )}

      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          onClick={isRunning ? stop : start}
          disabled={isRunning && type === 'outline'}
          loading={isRunning && type === 'outline'}
        >
          {getButtonText()}
        </Button>
        {isRunning && (
          <Button icon={<CloseCircleOutlined />} onClick={stop} danger>
            停止
          </Button>
        )}
      </Space>

      {isRunning && progress > 0 && (
        <Progress
          percent={progress}
          status={isRunning ? 'active' : 'normal'}
          strokeColor={{ from: '#6366f1', to: '#8b5cf6' }}
          style={{ marginBottom: 16 }}
        />
      )}

      {currentNode && (
        <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
          当前节点: {currentNode}
        </Text>
      )}

      {/* 节点输出列表 */}
      <div style={{ maxHeight: 400, overflow: 'auto' }}>
        {Object.values(nodes).map((node) => (
          <Card
            key={node.name}
            size="small"
            title={
              <Space>
                <Text strong style={{ color: '#e2e8f0' }}>{node.name}</Text>
                {node.status === 'running' && <Spin size="small" />}
                {node.status === 'completed' && (
                  <Text type="success">✓ 完成</Text>
                )}
                {node.status === 'error' && (
                  <Text type="danger">✗ 失败</Text>
                )}
              </Space>
            }
            style={{
              marginBottom: 8,
              background: '#0f172a',
              border: '1px solid #334155',
            }}
            bodyStyle={{
              background: '#0f172a',
            }}
          >
            <pre
              style={{
                margin: 0,
                padding: 8,
                background: '#0f172a',
                color: '#a5b4fc',
                fontSize: 13,
                lineHeight: 1.6,
                maxHeight: 200,
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
                fontFamily: '"JetBrains Mono", "Fira Code", monospace',
              }}
            >
              {node.content || '等待输出...'}
            </pre>
          </Card>
        ))}
      </div>
    </Card>
  );
};

export default StreamGenerator;
