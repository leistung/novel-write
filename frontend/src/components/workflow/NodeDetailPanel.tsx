/**
 * 节点详情面板
 * 
 * 展示节点的输入、输出、提示词、生成内容
 */
import React, { useState } from 'react';
import { Tabs, Typography, Tag, Empty, Descriptions, Button } from 'antd';
import { CopyOutlined, CheckOutlined, RobotOutlined, BulbOutlined, ToolOutlined } from '@ant-design/icons';
import type { WorkflowNode } from '../../types/workflow';

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

interface NodeDetailPanelProps {
  node: WorkflowNode | null;
}

const NodeDetailPanel: React.FC<NodeDetailPanelProps> = ({ node }) => {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  // 代码块渲染
  const CodeBlock: React.FC<{ content: string; title?: string; copyKey?: string }> = ({
    content,
    title,
    copyKey,
  }) => (
    <div style={{ position: 'relative' }}>
      {title && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <Text style={{ fontSize: 12, color: colors.textSecondary }}>
            {title}
          </Text>
          {copyKey && (
            <Button
              type="text"
              size="small"
              icon={copied === copyKey ? <CheckOutlined /> : <CopyOutlined />}
              onClick={() => copyToClipboard(content, copyKey)}
              style={{ color: colors.textSecondary, fontSize: 12 }}
            />
          )}
        </div>
      )}
      <pre style={{
        background: colors.bg,
        borderRadius: 8,
        padding: 16,
        overflow: 'auto',
        maxHeight: 200,
        fontSize: 13,
        color: colors.text,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
        lineHeight: 1.6,
        border: `1px solid ${colors.border}`,
        margin: 0,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
      }}>
        {content || '(空)'}
      </pre>
    </div>
  );

  if (!node) {
    return (
      <div style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: colors.card,
        borderRadius: 12,
        border: `1px solid ${colors.border}`,
      }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={<span style={{ color: colors.textSecondary }}>点击节点查看详情</span>}
        />
      </div>
    );
  }

  // 节点图标
  const NodeIconComponent = node.type === 'agent' ? RobotOutlined : 
                            node.type === 'llm' ? BulbOutlined : ToolOutlined;

  // 状态颜色
  const statusColor = node.status === 'completed' ? colors.success : 
                      node.status === 'running' ? colors.primary : 
                      node.status === 'error' ? colors.error : colors.textSecondary;

  const tabItems = [
    // 输入
    {
      key: 'input',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          📥 输入
          {node.input && Object.keys(node.input).length > 0 && (
            <Tag style={{ marginLeft: 4, fontSize: 10, padding: '0 6px', borderRadius: 6, background: 'rgba(99,102,241,0.2)', color: colors.primary, border: 'none' }}>
              {Object.keys(node.input).length}
            </Tag>
          )}
        </span>
      ),
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {node.input && Object.keys(node.input).length > 0 ? (
            Object.entries(node.input).map(([key, value]) => (
              <div key={key}>
                <Text style={{ fontSize: 12, color: colors.textSecondary, display: 'block', marginBottom: 6 }}>
                  {key}
                </Text>
                <CodeBlock
                  content={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  copyKey={`input-${key}`}
                />
              </div>
            ))
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span style={{ color: colors.textSecondary }}>无输入数据</span>} />
          )}
        </div>
      ),
    },
    // 提示词
    {
      key: 'prompts',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          💬 提示词
          {(node.systemPrompt || node.userPrompt) && (
            <Tag style={{ marginLeft: 4, fontSize: 10, padding: '0 6px', borderRadius: 6, background: 'rgba(168,85,247,0.2)', color: '#a855f7', border: 'none' }}>
              {(node.systemPrompt ? 1 : 0) + (node.userPrompt ? 1 : 0)}
            </Tag>
          )}
        </span>
      ),
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {node.systemPrompt && (
            <div>
              <Text style={{ fontSize: 12, color: colors.textSecondary, display: 'block', marginBottom: 6 }}>
                System Prompt
              </Text>
              <CodeBlock content={node.systemPrompt} copyKey="system-prompt" />
            </div>
          )}
          {node.userPrompt && (
            <div>
              <Text style={{ fontSize: 12, color: colors.textSecondary, display: 'block', marginBottom: 6 }}>
                User Prompt
              </Text>
              <CodeBlock content={node.userPrompt} copyKey="user-prompt" />
            </div>
          )}
          {!node.systemPrompt && !node.userPrompt && (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span style={{ color: colors.textSecondary }}>无提示词</span>} />
          )}
        </div>
      ),
    },
    // 输出
    {
      key: 'output',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          📤 输出
          {node.generatedContent && (
            <Tag style={{ marginLeft: 4, fontSize: 10, padding: '0 6px', borderRadius: 6, background: 'rgba(16,185,129,0.2)', color: colors.success, border: 'none' }}>
              {node.generatedContent.length}字
            </Tag>
          )}
        </span>
      ),
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {node.generatedContent ? (
            <CodeBlock
              content={node.generatedContent}
              title="生成内容"
              copyKey="generated-content"
            />
          ) : node.output && Object.keys(node.output).length > 0 ? (
            Object.entries(node.output).map(([key, value]) => (
              <div key={key}>
                <Text style={{ fontSize: 12, color: colors.textSecondary, display: 'block', marginBottom: 6 }}>
                  {key}
                </Text>
                <CodeBlock
                  content={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  copyKey={`output-${key}`}
                />
              </div>
            ))
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span style={{ color: colors.textSecondary }}>无输出数据</span>} />
          )}
        </div>
      ),
    },
    // 统计
    {
      key: 'stats',
      label: '📊 统计',
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Descriptions
            column={2}
            size="small"
            labelStyle={{ color: colors.textSecondary, fontSize: 13 }}
            contentStyle={{ color: colors.text, fontSize: 13 }}
          >
            <Descriptions.Item label="状态">
              <Tag style={{
                background: `${statusColor}20`,
                color: statusColor,
                border: 'none',
                borderRadius: 6,
              }}>
                {node.status === 'completed' ? '已完成' : node.status === 'running' ? '执行中' : node.status === 'error' ? '出错' : node.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag style={{ background: 'rgba(51,65,85,0.5)', color: colors.text, border: 'none', borderRadius: 6 }}>
                {node.type}
              </Tag>
            </Descriptions.Item>
            {node.tokenUsage && (
              <>
                <Descriptions.Item label="Prompt Tokens">
                  {node.tokenUsage.promptTokens?.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Completion Tokens">
                  {node.tokenUsage.completionTokens?.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Total Tokens">
                  <Text strong style={{ color: colors.primary }}>
                    {node.tokenUsage.totalTokens?.toLocaleString()}
                  </Text>
                </Descriptions.Item>
              </>
            )}
            {node.duration && (
              <Descriptions.Item label="耗时">
                {(node.duration / 1000).toFixed(2)}s
              </Descriptions.Item>
            )}
            {node.startedAt && (
              <Descriptions.Item label="开始时间">
                {new Date(node.startedAt).toLocaleTimeString('zh-CN')}
              </Descriptions.Item>
            )}
            {node.completedAt && (
              <Descriptions.Item label="完成时间">
                {new Date(node.completedAt).toLocaleTimeString('zh-CN')}
              </Descriptions.Item>
            )}
          </Descriptions>

          {node.error && (
            <div>
              <Text style={{ fontSize: 12, color: colors.error, display: 'block', marginBottom: 6 }}>
                错误信息
              </Text>
              <pre style={{
                background: 'rgba(239,68,68,0.1)',
                borderRadius: 8,
                padding: 12,
                fontSize: 13,
                color: colors.error,
                border: `1px solid rgba(239,68,68,0.3)`,
                margin: 0,
                whiteSpace: 'pre-wrap',
              }}>
                {node.error}
              </pre>
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: colors.card,
      borderRadius: 12,
      border: `1px solid ${colors.border}`,
      overflow: 'hidden',
    }}>
      {/* 头部 */}
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${colors.border}`,
        background: 'rgba(30,41,59,0.5)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(99,102,241,0.15)',
          }}>
            <NodeIconComponent style={{ fontSize: 20, color: colors.primary }} />
          </div>
          <div>
            <Text strong style={{ fontSize: 15, color: colors.text }}>
              {node.name}
            </Text>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
              <Tag style={{
                background: `${statusColor}20`,
                color: statusColor,
                border: 'none',
                borderRadius: 6,
                fontSize: 11,
                padding: '0 8px',
              }}>
                {node.status === 'completed' ? '已完成' : node.status === 'running' ? '执行中' : node.status === 'error' ? '出错' : '待执行'}
              </Tag>
              {node.duration && (
                <Text style={{ fontSize: 12, color: colors.textSecondary }}>
                  ⏱️ {(node.duration / 1000).toFixed(1)}s
                </Text>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 内容 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        <Tabs
          defaultActiveKey="output"
          items={tabItems}
          style={{ marginBottom: 0 }}
        />
      </div>
    </div>
  );
};

export default NodeDetailPanel;
