import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Tabs,
  Button,
  Spin,
  Empty,
  Tag,
  message,
  Input,
} from 'antd';
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  UserOutlined,
  BranchesOutlined,
  HeartOutlined,
  AimOutlined,
  AppstoreOutlined,
  ThunderboltOutlined,
  ReadOutlined,
  FormatPainterOutlined,
} from '@ant-design/icons';
import {
  getBook,
  getOutlineFiles,
  getOutlineContent,
  updateOutlineFile,
  getBookState,
} from '../services/api';
import type { OutlineFile, BookState } from '../types';

const { TextArea } = Input;

// ==================== 设计令牌（深色主题，与 BookDetail 一致） ====================
const colors = {
  bg: '#0f172a',
  card: '#1e293b',
  primary: '#7c3aed',
  primaryLight: '#8b5cf6',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  border: '#334155',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
};

// ==================== 大纲文件定义 ====================
const OUTLINE_FILES: Array<{ key: string; label: string; icon: React.ReactNode }> = [
  { key: 'worldview', label: '世界观设定', icon: <GlobalOutlined /> },
  { key: 'characters', label: '角色设定', icon: <UserOutlined /> },
  { key: 'plot', label: '主线剧情', icon: <BranchesOutlined /> },
  { key: 'arcs', label: '情感弧线', icon: <HeartOutlined /> },
  { key: 'hooks', label: '伏笔设计', icon: <AimOutlined /> },
  { key: 'settings', label: '场景设定', icon: <AppstoreOutlined /> },
  { key: 'power_system', label: '力量体系', icon: <ThunderboltOutlined /> },
  { key: 'outline', label: '卷纲大纲', icon: <ReadOutlined /> },
  { key: 'rules', label: '创作规则', icon: <FormatPainterOutlined /> },
];

// ==================== 组件 ====================
const OutlineView: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const numericBookId = Number(bookId);

  // ========== 数据状态 ==========
  const [bookTitle, setBookTitle] = useState<string>('');
  const [bookOutline, setBookOutline] = useState<string>('');
  const [outlineFiles, setOutlineFiles] = useState<OutlineFile[]>([]);
  const [bookState, setBookState] = useState<BookState | null>(null);

  // ========== UI 状态 ==========
  const [loading, setLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [stateLoading, setStateLoading] = useState(false);

  // 当前选中的大纲文件
  const [activeFileKey, setActiveFileKey] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [fileContentLoading, setFileContentLoading] = useState(false);

  // 编辑模式
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState<string>('');
  const [saving, setSaving] = useState(false);

  // 状态 Tab
  const [stateTab, setStateTab] = useState<string>('current_state');

  // ========== 数据加载 ==========

  const loadBookInfo = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getBook(numericBookId);
      setBookTitle(data.title || '');
      setBookOutline(data.outline || '');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载书籍信息失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [numericBookId]);

  const loadOutlineFiles = useCallback(async () => {
    try {
      setFilesLoading(true);
      const data = await getOutlineFiles(numericBookId);
      setOutlineFiles(Array.isArray(data.files) ? data.files : []);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载大纲文件列表失败';
      message.error(errorMsg);
    } finally {
      setFilesLoading(false);
    }
  }, [numericBookId]);

  const loadBookState = useCallback(async () => {
    try {
      setStateLoading(true);
      const data = await getBookState(numericBookId);
      setBookState(data);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载书籍状态失败';
      message.error(errorMsg);
    } finally {
      setStateLoading(false);
    }
  }, [numericBookId]);

  const loadFileContent = useCallback(async (key: string) => {
    try {
      setFileContentLoading(true);
      const data = await getOutlineContent(numericBookId, key);
      setFileContent(data.content || '');
      setEditContent(data.content || '');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载文件内容失败';
      message.error(errorMsg);
      setFileContent('');
      setEditContent('');
    } finally {
      setFileContentLoading(false);
    }
  }, [numericBookId]);

  useEffect(() => {
    if (!numericBookId) return;
    loadBookInfo();
    loadOutlineFiles();
    loadBookState();
  }, [numericBookId, loadBookInfo, loadOutlineFiles, loadBookState]);

  // ========== 操作处理 ==========

  const handleSelectFile = (key: string) => {
    setActiveFileKey(key);
    setEditing(false);
    loadFileContent(key);
  };

  const handleStartEdit = () => {
    setEditContent(fileContent);
    setEditing(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
    setEditContent(fileContent);
  };

  const handleSaveEdit = async () => {
    if (!activeFileKey) return;
    try {
      setSaving(true);
      await updateOutlineFile(numericBookId, activeFileKey, editContent);
      setFileContent(editContent);
      setEditing(false);
      message.success('保存成功');
      // 刷新文件列表以更新 exists 状态
      loadOutlineFiles();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '保存失败';
      message.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  // ========== 辅助方法 ==========

  /** 获取文件 exists 状态 */
  const getFileExists = (key: string): boolean => {
    const file = outlineFiles.find((f) => f.key === key);
    return file?.exists ?? false;
  };

  /** 获取当前选中文件的 label */
  const getActiveFileLabel = (): string => {
    const def = OUTLINE_FILES.find((f) => f.key === activeFileKey);
    return def?.label || activeFileKey || '';
  };

  /** 渲染状态文本块 */
  const renderStateBlock = (text: string | undefined | null) => {
    if (!text) {
      return (
        <Empty
          description={<span style={{ color: colors.textSecondary }}>暂无数据</span>}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      );
    }
    return (
      <div
        style={{
          background: colors.bg,
          borderRadius: 8,
          padding: 20,
          color: colors.textSecondary,
          fontSize: 14,
          lineHeight: 1.8,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          maxHeight: 600,
          overflow: 'auto',
        }}
      >
        {text}
      </div>
    );
  };

  // ========== 渲染：原始大纲区域 ==========
  const renderOriginalOutline = () => {
    if (!bookOutline) return null;
    return (
      <Card
        style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: 0 }}>
            <FileTextOutlined style={{ marginRight: 8, color: colors.primaryLight }} />
            原始大纲
          </h3>
          <p style={{ color: colors.textSecondary, fontSize: 13, margin: '6px 0 0 0' }}>
            创建书籍时输入的大纲概要
          </p>
        </div>
        <div
          style={{
            background: colors.bg,
            borderRadius: 8,
            padding: 16,
            maxHeight: 200,
            overflow: 'auto',
            color: colors.textSecondary,
            fontSize: 14,
            lineHeight: 1.8,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {bookOutline}
        </div>
      </Card>
    );
  };

  // ========== 渲染：大纲文件浏览区 ==========
  const renderOutlineBrowser = () => (
    <Card
      style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
      }}
      styles={{ body: { padding: 24 } }}
    >
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: 0 }}>
          <FileTextOutlined style={{ marginRight: 8, color: colors.primaryLight }} />
          大纲文件
        </h3>
        <p style={{ color: colors.textSecondary, fontSize: 13, margin: '6px 0 0 0' }}>
          点击左侧文件查看详细内容，支持在线编辑
        </p>
      </div>

      <div style={{ display: 'flex', gap: 20, minHeight: 500 }}>
        {/* 左侧文件列表 */}
        <div
          style={{
            width: 240,
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {filesLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
              <Spin />
            </div>
          ) : (
            OUTLINE_FILES.map((fileDef) => {
              const exists = getFileExists(fileDef.key);
              const isActive = activeFileKey === fileDef.key;
              return (
                <div
                  key={fileDef.key}
                  onClick={() => handleSelectFile(fileDef.key)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 10,
                    cursor: 'pointer',
                    background: isActive
                      ? 'rgba(124,58,237,0.15)'
                      : 'transparent',
                    border: isActive
                      ? `1px solid rgba(124,58,237,0.4)`
                      : `1px solid transparent`,
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      (e.currentTarget as HTMLDivElement).style.background = 'rgba(148,163,184,0.08)';
                      (e.currentTarget as HTMLDivElement).style.borderColor = colors.border;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      (e.currentTarget as HTMLDivElement).style.background = 'transparent';
                      (e.currentTarget as HTMLDivElement).style.borderColor = 'transparent';
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span
                      style={{
                        fontSize: 15,
                        color: isActive ? colors.primaryLight : colors.textSecondary,
                      }}
                    >
                      {fileDef.icon}
                    </span>
                    <span
                      style={{
                        fontSize: 14,
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? colors.text : colors.textSecondary,
                      }}
                    >
                      {fileDef.label}
                    </span>
                  </div>
                  <Tag
                    style={{
                      margin: 0,
                      padding: '1px 8px',
                      fontSize: 11,
                      borderRadius: 6,
                      background: exists
                        ? 'rgba(16,185,129,0.12)'
                        : 'rgba(148,163,184,0.08)',
                      color: exists ? colors.success : colors.textSecondary,
                      border: exists
                        ? '1px solid rgba(16,185,129,0.25)'
                        : `1px solid ${colors.border}`,
                    }}
                  >
                    {exists ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <CheckCircleOutlined style={{ fontSize: 10 }} />
                        已生成
                      </span>
                    ) : (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <ClockCircleOutlined style={{ fontSize: 10 }} />
                        未生成
                      </span>
                    )}
                  </Tag>
                </div>
              );
            })
          )}
        </div>

        {/* 右侧内容区 */}
        <div
          style={{
            flex: 1,
            background: colors.bg,
            borderRadius: 10,
            border: `1px solid ${colors.border}`,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* 内容区头部 */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 20px',
              borderBottom: `1px solid ${colors.border}`,
              flexShrink: 0,
            }}
          >
            <span style={{ fontSize: 15, fontWeight: 600, color: colors.text }}>
              {activeFileKey ? getActiveFileLabel() : '请选择文件'}
            </span>
            {activeFileKey && getFileExists(activeFileKey) && !editing && (
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={handleStartEdit}
                style={{
                  color: colors.primaryLight,
                  borderRadius: 6,
                  fontSize: 13,
                }}
              >
                编辑
              </Button>
            )}
            {editing && (
              <div style={{ display: 'flex', gap: 8 }}>
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={handleCancelEdit}
                  style={{
                    color: colors.textSecondary,
                    borderRadius: 6,
                    fontSize: 13,
                  }}
                >
                  取消
                </Button>
                <Button
                  type="primary"
                  size="small"
                  icon={<SaveOutlined />}
                  loading={saving}
                  onClick={handleSaveEdit}
                  style={{
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                    border: 'none',
                    borderRadius: 6,
                    fontSize: 13,
                  }}
                >
                  保存
                </Button>
              </div>
            )}
          </div>

          {/* 内容区主体 */}
          <div style={{ flex: 1, padding: 20, overflow: 'auto' }}>
            {fileContentLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
                <Spin size="large" />
              </div>
            ) : !activeFileKey ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  minHeight: 300,
                }}
              >
                <FileTextOutlined
                  style={{ fontSize: 48, color: colors.border, marginBottom: 16 }}
                />
                <span style={{ color: colors.textSecondary, fontSize: 14 }}>
                  从左侧选择一个大纲文件查看
                </span>
              </div>
            ) : editing ? (
              <TextArea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                autoSize={{ minRows: 20 }}
                style={{
                  borderRadius: 8,
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  color: colors.text,
                  fontSize: 14,
                  lineHeight: 1.8,
                  resize: 'none',
                }}
              />
            ) : fileContent ? (
              <div
                style={{
                  color: colors.textSecondary,
                  fontSize: 14,
                  lineHeight: 1.8,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {fileContent}
              </div>
            ) : (
              <Empty
                description={<span style={{ color: colors.textSecondary }}>该文件尚未生成内容</span>}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </div>
        </div>
      </div>
    </Card>
  );

  // ========== 渲染：书籍动态状态区 ==========
  const renderBookState = () => (
    <Card
      style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
      }}
      styles={{ body: { padding: 24 } }}
    >
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: 0 }}>
          <BranchesOutlined style={{ marginRight: 8, color: colors.warning }} />
          书籍动态状态
        </h3>
        <p style={{ color: colors.textSecondary, fontSize: 13, margin: '6px 0 0 0' }}>
          AI 在创作过程中维护的实时状态信息
        </p>
      </div>

      {stateLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      ) : !bookState ? (
        <Empty
          description={<span style={{ color: colors.textSecondary }}>暂无状态数据</span>}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Tabs
          activeKey={stateTab}
          onChange={(key) => setStateTab(key)}
          items={[
            {
              key: 'current_state',
              label: '当前状态',
              children: renderStateBlock(bookState.current_state),
            },
            {
              key: 'pending_hooks',
              label: '待处理伏笔',
              children: renderStateBlock(bookState.pending_hooks),
            },
            {
              key: 'character_matrix',
              label: '角色矩阵',
              children: renderStateBlock(bookState.character_matrix),
            },
            {
              key: 'emotional_arcs',
              label: '情感弧线',
              children: renderStateBlock(bookState.emotional_arcs),
            },
          ]}
          style={{
            '.ant-tabs-nav': {
              marginBottom: 16,
              '&::before': {
                display: 'none',
              },
            },
            '.ant-tabs-tab': {
              fontSize: 14,
              fontWeight: 500,
              color: colors.textSecondary,
              padding: '10px 0',
              margin: '0 12px',
            },
            '.ant-tabs-tab:hover': {
              color: colors.primaryLight,
            },
            '.ant-tabs-tab-active .ant-tabs-tab-btn': {
              color: colors.primaryLight,
              fontWeight: 600,
            },
            '.ant-tabs-ink-bar': {
              height: 2,
              background: colors.primary,
              borderRadius: 1,
            },
          } as React.CSSProperties}
        />
      )}
    </Card>
  );

  // ========== 主渲染 ==========
  return (
    <div style={{ background: colors.bg, minHeight: '100vh', padding: '0 32px 24px' }}>
      {/* 页面顶部导航栏 */}
      <div
        style={{
          padding: '20px 0',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/book/${bookId}`)}
          style={{
            color: colors.textSecondary,
            fontSize: 16,
            width: 36,
            height: 36,
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        />
        <span
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: colors.text,
          }}
        >
          {bookTitle || `书籍 #${bookId}`}
        </span>
        <Tag
          style={{
            marginLeft: 8,
            background: 'rgba(124,58,237,0.15)',
            color: colors.primaryLight,
            border: `1px solid rgba(124,58,237,0.3)`,
            borderRadius: 6,
            fontSize: 12,
            padding: '2px 10px',
          }}
        >
          大纲总览
        </Tag>
      </div>

      {/* 页面内容 */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 120 }}>
          <Spin size="large" />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 原始大纲 */}
          {renderOriginalOutline()}

          {/* 大纲文件浏览区 */}
          {renderOutlineBrowser()}

          {/* 书籍动态状态区 */}
          {renderBookState()}
        </div>
      )}
    </div>
  );
};

export default OutlineView;
