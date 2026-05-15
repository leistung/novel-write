import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Spin,
  Drawer,
  Descriptions,
  Tag,
  message,
  Tooltip,
  Empty,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  LeftOutlined,
  RightOutlined,
  InfoCircleOutlined,
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { getChapter, updateChapter } from '@/services/api';
import type { Chapter } from '@/types';

// ==================== 工具函数 ====================

/** 审核评分颜色 */
function scoreColor(score: number): string {
  if (score >= 80) return 'green';
  if (score >= 60) return 'orange';
  return 'red';
}

/** 章节类型中文映射 */
function chapterTypeLabel(type: string): string {
  const map: Record<string, string> = {
    opening: '开篇',
    development: '发展',
    climax: '高潮',
    transition: '过渡',
    ending: '结尾',
    foreshadowing: '伏笔',
    exposition: '说明',
  };
  return map[type] || type;
}

/** 章节类型颜色映射 */
function chapterTypeColor(type: string): string {
  const map: Record<string, string> = {
    opening: 'blue',
    development: 'cyan',
    climax: 'red',
    transition: 'orange',
    ending: 'purple',
    foreshadowing: 'geekblue',
    exposition: 'magenta',
  };
  return map[type] || 'default';
}

/** 状态中文映射 */
function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    completed: '已完成',
    reviewed: '已审核',
    published: '已发布',
  };
  return map[status] || status;
}

/** 状态颜色映射 */
function statusColor(status: string): string {
  const map: Record<string, string> = {
    draft: 'default',
    completed: 'green',
    reviewed: 'blue',
    published: 'purple',
  };
  return map[status] || 'default';
}

// ==================== 样式常量 ====================

const styles = {
  page: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    background: '#0f172a',
  },
  navbar: {
    height: 56,
    minHeight: 56,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    borderBottom: '1px solid #334155',
    background: '#1e293b',
    flexShrink: 0,
  },
  iconBtn: {
    width: 40,
    height: 40,
    minWidth: 40,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    border: 'none',
    background: '#334155',
    cursor: 'pointer',
    transition: 'background 0.2s',
    padding: 0,
    outline: 'none',
  } as React.CSSProperties,
  iconBtnHover: '#475569',
  navbarTitle: {
    fontSize: 16,
    fontWeight: 600,
    color: '#f1f5f9',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
    textAlign: 'center' as const,
    flex: 1,
    padding: '0 16px',
  },
  readerArea: {
    flex: 1,
    overflow: 'auto',
    padding: '40px 0',
    background: '#0f172a',
  },
  contentWrapper: {
    maxWidth: 720,
    margin: '0 auto',
    padding: '0 24px',
  },
  paragraph: {
    fontSize: 16,
    lineHeight: 1.9,
    color: '#e2e8f0',
    textIndent: '2em',
    marginBottom: '1.2em',
    letterSpacing: 0.5,
  },
  editTextArea: {
    fontSize: 16,
    lineHeight: 1.9,
    border: '2px solid #6366f1',
    borderRadius: 8,
    padding: '20px 24px',
    resize: 'none' as const,
    outline: 'none',
  },
  editToolbar: {
    position: 'fixed' as const,
    bottom: 0,
    left: 0,
    right: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    background: '#1e293b',
    boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.3)',
    zIndex: 100,
  },
  wordCount: {
    fontSize: 13,
    color: '#94a3b8',
  },
  cancelBtn: {
    border: '1px solid #334155',
    borderRadius: 6,
    color: '#94a3b8',
    background: '#1e293b',
    cursor: 'pointer',
    padding: '6px 16px',
    fontSize: 14,
  },
  saveBtn: {
    border: 'none',
    borderRadius: 6,
    color: '#ffffff',
    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    cursor: 'pointer',
    padding: '6px 20px',
    fontSize: 14,
    fontWeight: 500,
  },
  drawerLabel: {
    color: '#94a3b8',
    fontSize: 13,
  },
  drawerValue: {
    color: '#1e293b',
    fontSize: 13,
  },
  codeBlock: {
    background: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    fontSize: 12,
    lineHeight: 1.6,
    maxHeight: 300,
    overflow: 'auto' as const,
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-all' as const,
    color: '#334155',
    margin: 0,
  },
  codeBlockTitle: {
    fontWeight: 600,
    marginBottom: 8,
    color: '#1e293b',
    fontSize: 13,
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '60vh',
  },
};

// ==================== 组件 ====================

const ChapterReader: React.FC = () => {
  const { bookId, chapterNum } = useParams<{ bookId: string; chapterNum: string }>();
  const navigate = useNavigate();
  const numericBookId = Number(bookId);
  const numericChapterNum = Number(chapterNum);

  // ========== 数据状态 ==========
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // ========== UI 状态 ==========
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);

  // ========== 数据加载 ==========
  const loadChapter = useCallback(async () => {
    if (!numericBookId || !numericChapterNum) return;
    try {
      setLoading(true);
      const data = await getChapter(numericBookId, numericChapterNum);
      setChapter(data);
      setEditContent(data.content || '');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载章节失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [numericBookId, numericChapterNum]);

  useEffect(() => {
    loadChapter();
  }, [loadChapter]);

  // ========== 操作处理 ==========

  /** 进入编辑模式 */
  const handleEnterEdit = () => {
    setEditContent(chapter?.content || '');
    setEditMode(true);
  };

  /** 取消编辑 */
  const handleCancelEdit = () => {
    setEditContent(chapter?.content || '');
    setEditMode(false);
  };

  /** 保存编辑 */
  const handleSaveEdit = async () => {
    try {
      setSaving(true);
      await updateChapter(numericBookId, numericChapterNum, {
        content: editContent,
      });
      message.success('章节保存成功');
      setEditMode(false);
      loadChapter();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '保存章节失败';
      message.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  /** 导航到上一章 */
  const goToPrevChapter = () => {
    if (numericChapterNum > 1) {
      navigate(`/book/${numericBookId}/chapter/${numericChapterNum - 1}`);
    }
  };

  /** 导航到下一章 */
  const goToNextChapter = () => {
    navigate(`/book/${numericBookId}/chapter/${numericChapterNum + 1}`);
  };

  // ========== 渲染函数 ==========

  /** 将正文按 \n\n 分段 */
  const renderParagraphs = (content: string) => {
    if (!content) {
      return <Empty description="暂无内容" />;
    }
    const paragraphs = content.split('\n\n').filter((p) => p.trim());
    return paragraphs.map((paragraph, index) => (
      <p key={index} style={styles.paragraph}>
        {paragraph.split('\n').map((line, lineIdx) => (
          <React.Fragment key={lineIdx}>
            {lineIdx > 0 && <br />}
            {line}
          </React.Fragment>
        ))}
      </p>
    ));
  };

  /** 渲染 JSON 详情（代码块样式） */
  const renderJsonDetails = (
    data: Record<string, unknown> | undefined,
    title: string,
  ) => {
    if (!data || Object.keys(data).length === 0) return null;
    return (
      <div style={{ marginTop: 16 }}>
        <div style={styles.codeBlockTitle}>{title}</div>
        <pre style={styles.codeBlock}>
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  };

  /** 圆形图标按钮组件 */
  const CircleButton: React.FC<{
    icon: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    title?: string;
    danger?: boolean;
  }> = ({ icon, onClick, disabled, title, danger }) => (
    <Tooltip title={title}>
      <button
        style={{
          ...styles.iconBtn,
          opacity: disabled ? 0.3 : 1,
          cursor: disabled ? 'not-allowed' : 'pointer',
          color: danger ? '#ef4444' : '#64748b',
        }}
        onClick={disabled ? undefined : onClick}
        disabled={disabled}
        onMouseEnter={(e) => {
          if (!disabled) {
            (e.currentTarget as HTMLButtonElement).style.background = styles.iconBtnHover;
          }
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLButtonElement).style.background = '#f8fafc';
        }}
      >
        {icon}
      </button>
    </Tooltip>
  );

  // ========== 主渲染 ==========

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <Spin size="large">
          <div style={{ padding: 50 }} />
        </Spin>
      </div>
    );
  }

  if (!chapter) {
    return (
      <div style={styles.loadingContainer}>
        <Empty description="章节不存在" />
      </div>
    );
  }

  return (
    <div style={styles.page}>
      {/* ========== 顶部导航栏 ========== */}
      <div style={styles.navbar}>
        {/* 左侧：返回按钮 */}
        <CircleButton
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
          title="返回"
        />

        {/* 中间：章节标题 */}
        <span style={styles.navbarTitle}>
          第{chapter.chapter_number}章 {chapter.title}
        </span>

        {/* 右侧：操作按钮组 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CircleButton
            icon={<LeftOutlined />}
            onClick={goToPrevChapter}
            disabled={numericChapterNum <= 1}
            title="上一章"
          />
          <CircleButton
            icon={<RightOutlined />}
            onClick={goToNextChapter}
            title="下一章"
          />
          <CircleButton
            icon={<InfoCircleOutlined />}
            onClick={() => setDrawerOpen(true)}
            title="章节信息"
          />
          <CircleButton
            icon={<EditOutlined />}
            onClick={() => {
              if (editMode) {
                handleCancelEdit();
              } else {
                handleEnterEdit();
              }
            }}
            title={editMode ? '退出编辑' : '编辑章节'}
            danger={editMode}
          />
        </div>
      </div>

      {/* ========== 阅读区域 ========== */}
      <div style={styles.readerArea}>
        <div style={styles.contentWrapper}>
          {/* 阅读模式 */}
          {!editMode && (
            <div>{renderParagraphs(chapter.content)}</div>
          )}

          {/* 编辑模式 */}
          {editMode && (
            <div>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                style={{
                  ...styles.editTextArea,
                  width: '100%',
                  minHeight: 'calc(100vh - 56px - 120px)',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
                placeholder="在此编辑章节内容..."
              />
            </div>
          )}
        </div>
      </div>

      {/* ========== 编辑模式底部工具栏 ========== */}
      {editMode && (
        <div style={styles.editToolbar}>
          <span style={styles.wordCount}>
            {editContent.length.toLocaleString()} 字
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              style={styles.cancelBtn}
              onClick={handleCancelEdit}
            >
              <CloseOutlined style={{ marginRight: 4 }} />
              取消
            </button>
            <button
              style={{
                ...styles.saveBtn,
                opacity: saving ? 0.7 : 1,
              }}
              onClick={handleSaveEdit}
              disabled={saving}
            >
              <SaveOutlined style={{ marginRight: 4 }} />
              保存
            </button>
          </div>
        </div>
      )}

      {/* ========== 信息面板（Drawer） ========== */}
      <Drawer
        title="章节信息"
        placement="right"
        width={380}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        styles={{
          header: {
            borderBottom: '1px solid #f1f5f9',
            padding: '16px 24px',
          },
          body: {
            padding: '20px 24px',
          },
        }}
      >
        <Descriptions
          column={1}
          size="small"
          colon={false}
          labelStyle={styles.drawerLabel}
          contentStyle={styles.drawerValue}
        >
          <Descriptions.Item label="字数">
            {chapter.word_count?.toLocaleString() || '--'}
          </Descriptions.Item>
          <Descriptions.Item label="审核评分">
            {chapter.audit_score != null ? (
              <Tag color={scoreColor(chapter.audit_score)}>
                {chapter.audit_score}
              </Tag>
            ) : (
              <span style={{ color: '#94a3b8' }}>--</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="连续性评分">
            {chapter.continuity_score != null ? (
              <Tag color={scoreColor(chapter.continuity_score)}>
                {chapter.continuity_score}
              </Tag>
            ) : (
              <span style={{ color: '#94a3b8' }}>--</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="章节类型">
            <Tag color={chapterTypeColor(chapter.chapter_type)}>
              {chapterTypeLabel(chapter.chapter_type)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColor(chapter.status)}>
              {statusLabel(chapter.status)}
            </Tag>
          </Descriptions.Item>
        </Descriptions>

        {/* 审核详情 */}
        {renderJsonDetails(chapter.audit_details, '审核详情')}

        {/* 连续性检查详情 */}
        {renderJsonDetails(chapter.continuity_details, '连续性检查详情')}
      </Drawer>
    </div>
  );
};

export default ChapterReader;
