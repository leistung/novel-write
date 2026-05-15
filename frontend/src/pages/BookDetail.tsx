import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Tabs,
  Table,
  Button,
  Modal,
  Input,
  Switch,
  Tag,
  message,
  Space,
  Spin,
  Empty,
  Descriptions,
  Card,
  Tooltip,
  Popconfirm,
} from 'antd';
import {
  ArrowLeftOutlined,
  BookOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  EditOutlined,
  DeleteOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  BarChartOutlined,
  EyeOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getBook,
  getChapters,
  startGenerateOutline,
  startContinueChapters,
  startRewriteChapter,
  deleteBook,
} from '../services/api';
import type { Book, Chapter } from '../types';
import StreamGenerator from '../components/StreamGenerator';
import { WorkflowExecution } from '../components/workflow';

const { TextArea } = Input;

// ==================== 设计令牌（深色主题，与 Home/AppLayout 一致） ====================
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

/** 审核评分颜色 */
function auditScoreColor(score: number): string {
  if (score >= 80) return colors.success;
  if (score >= 60) return colors.warning;
  return colors.error;
}

/** 题材名称映射 */
const GENRE_NAME_MAP: Record<string, string> = {
  xuanhuan: '玄幻',
  qihuan: '奇幻',
  wuxia: '武侠',
  xianxia: '仙侠',
  dushi: '都市',
  xianshi: '现实',
  lishi: '历史',
  junshi: '军事',
  youxi: '游戏',
  tiyu: '体育',
  kehuan: '科幻',
  xuanyi_linghuan: '悬疑灵幻',
  xiaoshuo_m: '轻小说',
  duanpian_m: '短篇',
  zhutian_wuxian: '诸天无限',
  gudai_yanqing: '古代言情',
  xiandai_yanqing: '现代言情',
  xuanhuan_yanqing: '玄幻言情',
  xuanyi_tuili: '悬疑推理',
  langman_qingchun: '浪漫青春',
  xianxia_qiyuan: '仙侠奇缘',
  kehuan_kongjian: '科幻空间',
  youxi_jingji: '游戏竞技',
  xiaoshuo_f: '轻小说',
  duanpian_f: '短篇',
  xianshi_shenghuo: '现实生活',
};

const BookDetail: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const numericBookId = Number(bookId);

  // ========== 数据状态 ==========
  const [book, setBook] = useState<Book | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);

  // ========== UI 状态 ==========
  const [activeTab, setActiveTab] = useState('overview');
  const [bookLoading, setBookLoading] = useState(false);
  const [chaptersLoading, setChaptersLoading] = useState(false);

  // 生成大纲
  const [generatingOutline, setGeneratingOutline] = useState(false);

  // 续写 Modal
  const [continueModalOpen, setContinueModalOpen] = useState(false);
  const [continueForm, setContinueForm] = useState({
    startChapter: 1,
    count: 1,
    externalContext: '',
  });
  const [continueSubmitting, setContinueSubmitting] = useState(false);

  // 重写 Modal
  const [rewriteModalOpen, setRewriteModalOpen] = useState(false);
  const [rewriteForm, setRewriteForm] = useState({
    chapterNum: 1,
    rewriteRequirements: '',
    keepPlot: true,
  });
  const [rewriteSubmitting, setRewriteSubmitting] = useState(false);

  // 工作流可视化
  const [workflowType, setWorkflowType] = useState<'generate-outline' | 'continue-chapters' | 'rewrite-chapter' | null>(null);
  const [workflowParams, setWorkflowParams] = useState<{
    startChapter?: number;
    count?: number;
    chapterNum?: number;
    rewriteRequirements?: string;
    keepPlot?: boolean;
  }>({});

  // ========== 数据加载 ==========

  const loadBook = useCallback(async () => {
    try {
      setBookLoading(true);
      const data = await getBook(numericBookId);
      setBook(data);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载书籍详情失败';
      message.error(errorMsg);
    } finally {
      setBookLoading(false);
    }
  }, [numericBookId]);

  const loadChapters = useCallback(async () => {
    try {
      setChaptersLoading(true);
      const data = await getChapters(numericBookId);
      setChapters(Array.isArray(data) ? data : data.chapters || []);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '加载章节列表失败';
      message.error(errorMsg);
    } finally {
      setChaptersLoading(false);
    }
  }, [numericBookId]);

  useEffect(() => {
    if (!numericBookId) return;
    loadBook();
    loadChapters();
  }, [numericBookId, loadBook, loadChapters]);

  // ========== 操作处理 ==========

  /** 删除书籍 */
  const handleDeleteBook = async () => {
    try {
      await deleteBook(numericBookId);
      message.success('书籍已删除');
      navigate('/');
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '删除书籍失败';
      message.error(errorMsg);
    }
  };

  /** 生成大纲 */
  const handleGenerateOutline = async () => {
    Modal.confirm({
      title: '生成大纲',
      icon: <ExclamationCircleOutlined />,
      content: '确定要为本书生成完整大纲吗？这将启动一个工作流，可能需要较长时间。',
      okText: '开始生成',
      cancelText: '取消',
      onOk: async () => {
        try {
          setGeneratingOutline(true);
          await startGenerateOutline(numericBookId);
          message.success('大纲生成工作流已启动');
        } catch (err: unknown) {
          const errorMsg = err instanceof Error ? err.message : '启动大纲生成失败';
          message.error(errorMsg);
        } finally {
          setGeneratingOutline(false);
        }
      },
    });
  };

  /** 续写章节 */
  const handleContinueChapters = async () => {
    if (!continueForm.startChapter || continueForm.startChapter < 1) {
      message.warning('请输入有效的起始章节号');
      return;
    }
    try {
      setContinueSubmitting(true);
      await startContinueChapters({
        book_id: numericBookId,
        start_chapter: continueForm.startChapter,
        count: continueForm.count,
        external_context: continueForm.externalContext || undefined,
      });
      message.success(`续写任务已启动，共 ${continueForm.count} 章`);
      setContinueModalOpen(false);
      setTimeout(() => loadChapters(), 2000);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '启动续写失败';
      message.error(errorMsg);
    } finally {
      setContinueSubmitting(false);
    }
  };

  /** 重写章节 */
  const handleRewriteChapter = async () => {
    if (!rewriteForm.chapterNum || rewriteForm.chapterNum < 1) {
      message.warning('请输入有效的章节号');
      return;
    }
    if (!rewriteForm.rewriteRequirements.trim()) {
      message.warning('请输入改写要求');
      return;
    }
    try {
      setRewriteSubmitting(true);
      await startRewriteChapter({
        book_id: numericBookId,
        chapter_num: rewriteForm.chapterNum,
        rewrite_requirements: rewriteForm.rewriteRequirements,
        keep_plot: rewriteForm.keepPlot,
      });
      message.success(`第 ${rewriteForm.chapterNum} 章重写任务已启动`);
      setRewriteModalOpen(false);
      setTimeout(() => loadChapters(), 2000);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '启动重写失败';
      message.error(errorMsg);
    } finally {
      setRewriteSubmitting(false);
    }
  };

  // ========== 章节表格列定义 ==========
  const chapterColumns: ColumnsType<Chapter> = [
    {
      title: '章节号',
      dataIndex: 'chapter_number',
      key: 'chapter_number',
      width: 100,
      sorter: (a, b) => a.chapter_number - b.chapter_number,
      defaultSortOrder: 'ascend',
      render: (val: number) => (
        <span style={{ color: colors.text, fontWeight: 500 }}>第 {val} 章</span>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (val: string) => (
        <span style={{ color: colors.text }}>{val || '--'}</span>
      ),
    },
    {
      title: '字数',
      dataIndex: 'word_count',
      key: 'word_count',
      width: 110,
      sorter: (a, b) => a.word_count - b.word_count,
      render: (val: number) => (
        <span style={{ color: colors.textSecondary }}>{val?.toLocaleString() || 0}</span>
      ),
    },
    {
      title: '审核分数',
      dataIndex: 'audit_score',
      key: 'audit_score',
      width: 110,
      sorter: (a, b) => (a.audit_score || 0) - (b.audit_score || 0),
      render: (val: number) => {
        if (val == null) {
          return <span style={{ color: colors.textSecondary }}>--</span>;
        }
        return (
          <Tag
            style={{
              background: auditScoreColor(val),
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 12,
              fontWeight: 500,
              padding: '2px 12px',
            }}
          >
            {val}
          </Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: Chapter) => (
        <Tooltip title="查看章节详情">
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            style={{ color: colors.primaryLight }}
            onClick={() => navigate(`/book/${numericBookId}/chapter/${record.chapter_number}`)}
          />
        </Tooltip>
      ),
    },
  ];

  // ========== 渲染：概览 Tab ==========
  const renderOverview = () => {
    if (bookLoading) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      );
    }
    if (!book) {
      return <Empty description="暂无书籍信息" />;
    }

    const genreName = GENRE_NAME_MAP[book.genre] || book.genre;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* 书籍基本信息卡片 */}
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
              <BookOutlined style={{ marginRight: 8, color: colors.primaryLight }} />
              基本信息
            </h3>
          </div>
          <Descriptions
            column={{ xs: 1, sm: 2, md: 3 }}
            colon={false}
            labelStyle={{ color: colors.textSecondary, fontSize: 14 }}
            contentStyle={{ color: colors.text, fontSize: 14, fontWeight: 500 }}
          >
            <Descriptions.Item label="书名">{book.title}</Descriptions.Item>
            <Descriptions.Item label="题材">
              <Tag
                style={{
                  background: 'rgba(124,58,237,0.15)',
                  color: colors.primaryLight,
                  border: `1px solid rgba(124,58,237,0.3)`,
                  borderRadius: 6,
                  fontSize: 12,
                  padding: '2px 10px',
                }}
              >
                {genreName}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="平台">
              {book.platform ? (
                <Tag
                  style={{
                    background: 'rgba(148,163,184,0.1)',
                    color: colors.textSecondary,
                    border: `1px solid ${colors.border}`,
                    borderRadius: 6,
                    fontSize: 12,
                    padding: '2px 10px',
                  }}
                >
                  {book.platform}
                </Tag>
              ) : (
                <span style={{ color: colors.textSecondary }}>--</span>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="每章字数">
              {book.chapter_words?.toLocaleString() || '--'}
            </Descriptions.Item>
            <Descriptions.Item label="目标章数">
              {book.target_chapters || '--'}
            </Descriptions.Item>
            <Descriptions.Item label="写作风格">
              {book.writing_style || '--'}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 大纲卡片 */}
        <Card
          style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
          }}
          styles={{ body: { padding: 24 } }}
        >
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: 0 }}>
              <FileTextOutlined style={{ marginRight: 8, color: colors.primaryLight }} />
              大纲
            </h3>
            <Button
              type="link"
              size="small"
              icon={<ApartmentOutlined />}
              onClick={() => navigate(`/book/${numericBookId}/outline`)}
              style={{ color: colors.primaryLight, padding: 0, fontSize: 13 }}
            >
              查看完整大纲
            </Button>
          </div>
          {book.outline || book.story_bible || book.volume_outline ? (
            <div
              style={{
                background: colors.bg,
                borderRadius: 8,
                padding: 16,
                maxHeight: 400,
                overflow: 'auto',
                color: colors.textSecondary,
                fontSize: 14,
                lineHeight: 1.8,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}
            >
              {book.story_bible ? (
                <>
                  <div style={{ color: colors.primaryLight, fontWeight: 600, marginBottom: 8, fontSize: 15 }}>
                    📖 世界观设定（Story Bible）
                  </div>
                  <div style={{ marginBottom: 16 }}>{book.story_bible}</div>
                </>
              ) : null}
              {book.character_matrix ? (
                <>
                  <div style={{ color: colors.primaryLight, fontWeight: 600, marginBottom: 8, fontSize: 15 }}>
                    👥 角色设定
                  </div>
                  <div style={{ marginBottom: 16 }}>{book.character_matrix}</div>
                </>
              ) : null}
              {book.volume_outline ? (
                <>
                  <div style={{ color: colors.primaryLight, fontWeight: 600, marginBottom: 8, fontSize: 15 }}>
                    📋 卷纲大纲
                  </div>
                  <div style={{ marginBottom: 16 }}>{book.volume_outline}</div>
                </>
              ) : null}
              {!book.story_bible && !book.character_matrix && !book.volume_outline && book.outline && (
                <>{book.outline}</>
              )}
            </div>
          ) : (
            <Empty
              description={
                <span style={{ color: colors.textSecondary }}>暂无大纲，请在"操作"选项卡中生成</span>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>

        {/* 时间信息 */}
        <Card
          style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
          }}
          styles={{ body: { padding: 24 } }}
        >
          <Descriptions
            column={{ xs: 1, sm: 2 }}
            colon={false}
            labelStyle={{ color: colors.textSecondary, fontSize: 14 }}
            contentStyle={{ color: colors.text, fontSize: 14 }}
          >
            <Descriptions.Item label="创建时间">
              {book.created_at ? new Date(book.created_at).toLocaleString('zh-CN') : '--'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    );
  };

  // ========== 渲染：章节 Tab ==========
  const renderChapters = () => (
    <div>
      <div style={{
        marginBottom: 20,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ fontSize: 14, color: colors.textSecondary }}>
          共 <span style={{ color: colors.text, fontWeight: 600 }}>{chapters.length}</span> 章
        </span>
        <Button
          size="small"
          icon={<SyncOutlined />}
          onClick={loadChapters}
          loading={chaptersLoading}
          style={{
            borderRadius: 8,
            border: `1px solid ${colors.border}`,
            background: 'transparent',
            color: colors.textSecondary,
          }}
        >
          刷新
        </Button>
      </div>

      {chaptersLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      ) : chapters.length === 0 ? (
        <Card
          style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
          }}
          styles={{ body: { padding: '80px 0' } }}
        >
          <Empty
            description={
              <span style={{ color: colors.textSecondary }}>暂无章节，请在"操作"选项卡中开始续写</span>
            }
          />
        </Card>
      ) : (
        <Card
          style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 12,
          }}
          styles={{ body: { padding: 4 } }}
        >
          <Table
            dataSource={chapters.map((c) => ({ ...c, key: c.id }))}
            columns={chapterColumns}
            pagination={{
              pageSize: 15,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 章`,
              pageSizeOptions: ['10', '15', '20', '50'],
            }}
            scroll={{ x: 600 }}
            size="middle"
          />
        </Card>
      )}
    </div>
  );

  // ========== 渲染：操作 Tab ==========
  const renderOperations = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* 工作流可视化入口 */}
      {workflowType && (
        <div style={{ marginBottom: 16 }}>
          <WorkflowExecution
            bookId={numericBookId}
            type={workflowType}
            startChapter={workflowParams.startChapter}
            count={workflowParams.count}
            chapterNum={workflowParams.chapterNum}
            rewriteRequirements={workflowParams.rewriteRequirements}
            keepPlot={workflowParams.keepPlot}
            onComplete={() => {
              message.success('工作流执行完成');
              loadBook();
              loadChapters();
              // 不再自动关闭工作流组件，让用户可以查看执行结果
            }}
            onError={(error) => {
              message.error(error);
            }}
            onClose={() => setWorkflowType(null)}
          />
        </div>
      )}

      {/* 生成大纲 */}
      <Card
        style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 8px 0' }}>
              <ThunderboltOutlined style={{ marginRight: 8, color: colors.warning }} />
              生成大纲
            </h3>
            <p style={{ color: colors.textSecondary, fontSize: 14, margin: 0 }}>
              使用 AI 为本书生成完整的创作大纲，包括世界观、角色设定、主线剧情等
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <Button
              type="primary"
              icon={<ApartmentOutlined />}
              onClick={() => {
                setWorkflowType('generate-outline');
                setWorkflowParams({});
              }}
              style={{
                height: 44,
                padding: '0 20px',
                borderRadius: 10,
                border: 'none',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                color: '#fff',
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              可视化执行
            </Button>
            <Button
              icon={<ThunderboltOutlined />}
              loading={generatingOutline}
              onClick={handleGenerateOutline}
              style={{
                height: 44,
                padding: '0 20px',
                borderRadius: 10,
                border: `1px solid ${colors.border}`,
                background: 'transparent',
                color: colors.warning,
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              快速生成
            </Button>
          </div>
        </div>
      </Card>

      {/* 续写章节 */}
      <Card
        style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 8px 0' }}>
              <EditOutlined style={{ marginRight: 8, color: colors.success }} />
              续写章节
            </h3>
            <p style={{ color: colors.textSecondary, fontSize: 14, margin: 0 }}>
              从指定章节开始续写，可自定义续写章数和额外指令
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <Button
              type="primary"
              icon={<ApartmentOutlined />}
              onClick={() => {
                const maxChapter = chapters.length > 0
                  ? Math.max(...chapters.map((c) => c.chapter_number))
                  : 0;
                setWorkflowType('continue-chapters');
                setWorkflowParams({ startChapter: maxChapter + 1, count: 1 });
              }}
              style={{
                height: 44,
                padding: '0 20px',
                borderRadius: 10,
                border: 'none',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                color: '#fff',
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              可视化执行
            </Button>
            <Button
              icon={<EditOutlined />}
              onClick={() => {
                const maxChapter = chapters.length > 0
                  ? Math.max(...chapters.map((c) => c.chapter_number))
                  : 0;
                setContinueForm({
                  startChapter: maxChapter + 1,
                  count: 1,
                  externalContext: '',
                });
                setContinueModalOpen(true);
              }}
              style={{
                height: 44,
                padding: '0 20px',
                borderRadius: 10,
                border: `1px solid ${colors.border}`,
                background: 'transparent',
                color: colors.success,
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              快速续写
            </Button>
          </div>
        </div>
      </Card>

      {/* 重写章节 */}
      <Card
        style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 8px 0' }}>
              <SyncOutlined style={{ marginRight: 8, color: colors.primaryLight }} />
              重写章节
            </h3>
            <p style={{ color: colors.textSecondary, fontSize: 14, margin: 0 }}>
              对指定章节进行重写，可设置改写要求和是否保持剧情连贯
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <Button
              type="primary"
              icon={<ApartmentOutlined />}
              onClick={() => {
                setWorkflowType('rewrite-chapter');
                setWorkflowParams({ chapterNum: 1, rewriteRequirements: '', keepPlot: true });
              }}
              style={{
                height: 44,
                padding: '0 20px',
                borderRadius: 10,
                border: 'none',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                color: '#fff',
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              可视化执行
            </Button>
            <Button
              icon={<SyncOutlined />}
              onClick={() => {
                setRewriteForm({
                  chapterNum: 1,
                  rewriteRequirements: '',
                  keepPlot: true,
                });
                setRewriteModalOpen(true);
              }}
              style={{
                height: 44,
                padding: '0 20px',
                borderRadius: 10,
                border: `1px solid ${colors.border}`,
                background: 'transparent',
                color: colors.primaryLight,
                fontWeight: 500,
                fontSize: 14,
              }}
            >
              快速重写
            </Button>
          </div>
        </div>
      </Card>

      {/* 删除书籍 */}
      <Card
        style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
        }}
        styles={{ body: { padding: 24 } }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 8px 0' }}>
              <DeleteOutlined style={{ marginRight: 8, color: colors.error }} />
              删除书籍
            </h3>
            <p style={{ color: colors.textSecondary, fontSize: 14, margin: 0 }}>
              永久删除本书及其所有章节数据，此操作不可恢复
            </p>
          </div>
          <Popconfirm
            title="确认删除"
            description={`确定要删除《${book?.title || ''}》吗？此操作不可恢复。`}
            onConfirm={handleDeleteBook}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              style={{
                height: 44,
                padding: '0 28px',
                borderRadius: 10,
                border: `1px solid ${colors.error}`,
                background: 'transparent',
                color: colors.error,
                fontWeight: 500,
                fontSize: 15,
                flexShrink: 0,
              }}
            >
              删除书籍
            </Button>
          </Popconfirm>
        </div>
      </Card>

      {/* 续写 Modal */}
      <Modal
        title={
          <span style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>续写章节</span>
        }
        open={continueModalOpen}
        onOk={handleContinueChapters}
        onCancel={() => setContinueModalOpen(false)}
        confirmLoading={continueSubmitting}
        okText="开始续写"
        cancelText="取消"
        width={520}
        centered
        okButtonProps={{
          style: {
            background: `linear-gradient(135deg, ${colors.success}, #34d399)`,
            border: 'none',
            fontWeight: 500,
            borderRadius: 8,
          },
        }}
        cancelButtonProps={{
          style: {
            borderRadius: 8,
            border: `1px solid ${colors.border}`,
            color: colors.textSecondary,
          },
        }}
        styles={{
          content: {
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 16,
          },
          header: {
            borderBottom: `1px solid ${colors.border}`,
            background: colors.card,
          },
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, marginTop: 16 }}>
          <div>
            <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
              起始章节号
            </label>
            <Input
              type="number"
              min={1}
              value={continueForm.startChapter}
              onChange={(e) =>
                setContinueForm((prev) => ({
                  ...prev,
                  startChapter: Number(e.target.value),
                }))
              }
              style={{
                borderRadius: 8,
                height: 40,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
              placeholder="从第几章开始续写"
            />
          </div>
          <div>
            <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
              续写数量
            </label>
            <Input
              type="number"
              min={1}
              max={10}
              value={continueForm.count}
              onChange={(e) =>
                setContinueForm((prev) => ({
                  ...prev,
                  count: Math.min(10, Math.max(1, Number(e.target.value))),
                }))
              }
              style={{
                borderRadius: 8,
                height: 40,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
              placeholder="1-10章"
            />
          </div>
          <div>
            <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
              额外指令（可选）
            </label>
            <TextArea
              rows={4}
              value={continueForm.externalContext}
              onChange={(e) =>
                setContinueForm((prev) => ({
                  ...prev,
                  externalContext: e.target.value,
                }))
              }
              placeholder="例如：下一章需要加入角色之间的对话，推进感情线..."
              style={{
                borderRadius: 8,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
            />
          </div>
        </div>
      </Modal>

      {/* 重写 Modal */}
      <Modal
        title={
          <span style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>重写章节</span>
        }
        open={rewriteModalOpen}
        onOk={handleRewriteChapter}
        onCancel={() => setRewriteModalOpen(false)}
        confirmLoading={rewriteSubmitting}
        okText="开始重写"
        cancelText="取消"
        width={520}
        centered
        okButtonProps={{
          style: {
            background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
            border: 'none',
            fontWeight: 500,
            borderRadius: 8,
          },
        }}
        cancelButtonProps={{
          style: {
            borderRadius: 8,
            border: `1px solid ${colors.border}`,
            color: colors.textSecondary,
          },
        }}
        styles={{
          content: {
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 16,
          },
          header: {
            borderBottom: `1px solid ${colors.border}`,
            background: colors.card,
          },
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, marginTop: 16 }}>
          <div>
            <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
              章节号
            </label>
            <Input
              type="number"
              min={1}
              value={rewriteForm.chapterNum}
              onChange={(e) =>
                setRewriteForm((prev) => ({
                  ...prev,
                  chapterNum: Number(e.target.value),
                }))
              }
              style={{
                borderRadius: 8,
                height: 40,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
              placeholder="要重写的章节号"
            />
          </div>
          <div>
            <label style={{ fontSize: 14, fontWeight: 500, color: colors.text, display: 'block', marginBottom: 8 }}>
              改写要求
            </label>
            <TextArea
              rows={4}
              value={rewriteForm.rewriteRequirements}
              onChange={(e) =>
                setRewriteForm((prev) => ({
                  ...prev,
                  rewriteRequirements: e.target.value,
                }))
              }
              placeholder="描述需要改写的内容和方向..."
              style={{
                borderRadius: 8,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>保持剧情连贯</label>
            <Switch
              checked={rewriteForm.keepPlot}
              onChange={(checked) =>
                setRewriteForm((prev) => ({
                  ...prev,
                  keepPlot: checked,
                }))
              }
            />
          </div>
        </div>
      </Modal>
    </div>
  );

  // ========== 主渲染 ==========
  return (
    <div style={{ background: colors.bg, minHeight: '100vh', padding: '0 32px 24px' }}>
      {/* 页面顶部 */}
      <div style={{
        padding: '20px 0',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
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
        <span style={{
          fontSize: 22,
          fontWeight: 700,
          color: colors.text,
        }}>
          {book?.title || `书籍 #${bookId}`}
        </span>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key)}
        items={[
          {
            key: 'overview',
            label: (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <BarChartOutlined />
                概览
              </span>
            ),
            children: (
              <div style={{ paddingTop: 24 }}>
                {renderOverview()}
              </div>
            ),
          },
          {
            key: 'chapters',
            label: (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <FileTextOutlined />
                章节
              </span>
            ),
            children: (
              <div style={{ paddingTop: 24 }}>
                {renderChapters()}
              </div>
            ),
          },
          {
            key: 'operations',
            label: (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ThunderboltOutlined />
                操作
              </span>
            ),
            children: (
              <div style={{ paddingTop: 24 }}>
                {renderOperations()}
              </div>
            ),
          },
        ]}
        style={{
          '.ant-tabs-nav': {
            marginBottom: 0,
            '&::before': {
              display: 'none',
            },
          },
          '.ant-tabs-tab': {
            fontSize: 14,
            fontWeight: 500,
            color: colors.textSecondary,
            padding: '12px 0',
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
    </div>
  );
};

export default BookDetail;
