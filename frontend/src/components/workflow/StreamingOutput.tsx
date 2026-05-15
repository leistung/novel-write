/**
 * 实时输出组件
 * 
 * SSE 逐词打印效果，类似 ChatGPT
 */
import React, { useEffect, useRef, useState } from 'react';
import { Typography, Tag } from 'antd';

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
};

interface StreamingOutputProps {
  content: string;
  isStreaming: boolean;
  nodeName?: string;
}

const StreamingOutput: React.FC<StreamingOutputProps> = ({
  content,
  isStreaming,
  nodeName,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [content, autoScroll]);

  // 检测用户是否手动滚动
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 头部 */}
      <div style={{
        padding: '8px 16px',
        borderBottom: `1px solid ${colors.border}`,
        background: 'rgba(30,41,59,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Text style={{ fontSize: 13, color: colors.textSecondary }}>
            实时输出
          </Text>
          {nodeName && (
            <Tag style={{
              fontSize: 11,
              padding: '0 8px',
              borderRadius: 6,
              background: 'rgba(99,102,241,0.2)',
              color: colors.primary,
              border: 'none',
            }}>
              {nodeName}
            </Tag>
          )}
          {isStreaming && (
            <Tag style={{
              fontSize: 11,
              padding: '0 8px',
              borderRadius: 6,
              background: 'rgba(16,185,129,0.2)',
              color: colors.success,
              border: 'none',
              animation: 'pulse 1.5s infinite',
            }}>
              生成中
            </Tag>
          )}
        </div>
        <Text style={{ fontSize: 12, color: colors.textSecondary }}>
          {content.length.toLocaleString()} 字符
        </Text>
      </div>

      {/* 内容区 */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: 16,
          background: colors.bg,
        }}
      >
        {content ? (
          <div style={{ position: 'relative' }}>
            <pre style={{
              margin: 0,
              padding: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'inherit',
              fontSize: 14,
              lineHeight: 1.8,
              color: colors.text,
            }}>
              {content}
            </pre>
            {/* 光标动画 */}
            {isStreaming && (
              <span style={{
                display: 'inline-block',
                width: 8,
                height: 18,
                marginLeft: 2,
                background: colors.primary,
                borderRadius: 2,
                animation: 'blink 0.8s infinite',
                verticalAlign: 'text-bottom',
              }} />
            )}
          </div>
        ) : (
          <div style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Text style={{ color: colors.textSecondary }}>
              {isStreaming ? '等待输出...' : '暂无内容'}
            </Text>
          </div>
        )}
      </div>

      {/* 滚动提示 */}
      {!autoScroll && isStreaming && (
        <div style={{
          position: 'absolute',
          bottom: 60,
          right: 24,
        }}>
          <button
            onClick={() => {
              setAutoScroll(true);
              if (containerRef.current) {
                containerRef.current.scrollTop = containerRef.current.scrollHeight;
              }
            }}
            style={{
              padding: '6px 12px',
              background: colors.primary,
              color: '#fff',
              fontSize: 12,
              borderRadius: 20,
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(99,102,241,0.4)',
              transition: 'background 0.2s',
            }}
          >
            ↓ 最新内容
          </button>
        </div>
      )}

      {/* CSS 动画 */}
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default StreamingOutput;
