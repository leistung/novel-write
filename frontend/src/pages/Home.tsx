import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Button,
  Tag,
  Space,
  Modal,
  Input,
  Select,
  InputNumber,
  Form,
  Popconfirm,
  message,
  Spin,
  Card,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  BookOutlined,
  EditOutlined,
  FileTextOutlined,
  RocketOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { Book, GenreItem } from '@/types';
import { getBooks, createBook, deleteBook } from '@/services/api';

const { TextArea } = Input;

// Dify 风格颜色
const colors = {
  bg: '#0f172a',
  sidebar: '#1e293b',
  card: '#1e293b',
  cardHover: '#252f47',
  primary: '#7c3aed',
  primaryLight: '#8b5cf6',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  border: '#334155',
  success: '#10b981',
  warning: '#f59e0b',
};

/** 题材列表 */
const GENRE_LIST: GenreItem[] = [
  // 男频
  { key: 'xuanhuan', name: '玄幻', category: '男频' },
  { key: 'qihuan', name: '奇幻', category: '男频' },
  { key: 'wuxia', name: '武侠', category: '男频' },
  { key: 'xianxia', name: '仙侠', category: '男频' },
  { key: 'dushi', name: '都市', category: '男频' },
  { key: 'xianshi', name: '现实', category: '男频' },
  { key: 'lishi', name: '历史', category: '男频' },
  { key: 'junshi', name: '军事', category: '男频' },
  { key: 'youxi', name: '游戏', category: '男频' },
  { key: 'tiyu', name: '体育', category: '男频' },
  { key: 'kehuan', name: '科幻', category: '男频' },
  { key: 'xuanyi_linghuan', name: '悬疑灵幻', category: '男频' },
  { key: 'xiaoshuo_m', name: '轻小说', category: '男频' },
  { key: 'duanpian_m', name: '短篇', category: '男频' },
  { key: 'zhutian_wuxian', name: '诸天无限', category: '男频' },
  // 女频
  { key: 'gudai_yanqing', name: '古代言情', category: '女频' },
  { key: 'xiandai_yanqing', name: '现代言情', category: '女频' },
  { key: 'xuanhuan_yanqing', name: '玄幻言情', category: '女频' },
  { key: 'xuanyi_tuili', name: '悬疑推理', category: '女频' },
  { key: 'langman_qingchun', name: '浪漫青春', category: '女频' },
  { key: 'xianxia_qiyuan', name: '仙侠奇缘', category: '女频' },
  { key: 'kehuan_kongjian', name: '科幻空间', category: '女频' },
  { key: 'youxi_jingji', name: '游戏竞技', category: '女频' },
  { key: 'xiaoshuo_f', name: '轻小说', category: '女频' },
  { key: 'duanpian_f', name: '短篇', category: '女频' },
  { key: 'xianshi_shenghuo', name: '现实生活', category: '女频' },
];

/** 平台选项 */
const PLATFORM_OPTIONS = [
  { label: '起点', value: '起点' },
  { label: '番茄', value: '番茄' },
  { label: '晋江', value: '晋江' },
  { label: '通用', value: '通用' },
];

/** 题材 Select 分组选项 */
const genreGroupOptions = (() => {
  const groups: { label: string; options: { label: string; value: string }[] }[] = [];
  const categories = ['男频', '女频'];
  categories.forEach((cat) => {
    const items = GENRE_LIST.filter((g) => g.category === cat);
    groups.push({
      label: cat,
      options: items.map((g) => ({ label: g.name, value: g.key })),
    });
  });
  return groups;
})();

/** 题材渐变色映射 */
const getGenreGradient = (key: string): string => {
  const map: Record<string, string> = {
    xuanhuan: 'linear-gradient(135deg, #7c3aed, #8b5cf6)',
    xianxia: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    qihuan: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
    wuxia: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
    lishi: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
    dushi: 'linear-gradient(135deg, #3b82f6, #60a5fa)',
    xianshi: 'linear-gradient(135deg, #64748b, #94a3b8)',
    junshi: 'linear-gradient(135deg, #ef4444, #f87171)',
    youxi: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
    tiyu: 'linear-gradient(135deg, #22c55e, #4ade80)',
    kehuan: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
    gudai_yanqing: 'linear-gradient(135deg, #ec4899, #f472b6)',
    xiandai_yanqing: 'linear-gradient(135deg, #f472b6, #fb7185)',
    xuanhuan_yanqing: 'linear-gradient(135deg, #ec4899, #f472b6)',
    langman_qingchun: 'linear-gradient(135deg, #f472b6, #fb7185)',
    xianxia_qiyuan: 'linear-gradient(135deg, #a78bfa, #c4b5fd)',
    kehuan_kongjian: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
  };
  return map[key] || 'linear-gradient(135deg, #7c3aed, #8b5cf6)';
};

/** 题材Tag颜色映射 */
const getGenreColors = (key: string): { bg: string; color: string; border: string } => {
  const map: Record<string, { bg: string; color: string; border: string }> = {
    xuanhuan: { bg: 'rgba(124,58,237,0.15)', color: '#a78bfa', border: 'rgba(124,58,237,0.3)' },
    xianxia: { bg: 'rgba(99,102,241,0.15)', color: '#818cf8', border: 'rgba(99,102,241,0.3)' },
    qihuan: { bg: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: 'rgba(139,92,246,0.3)' },
    wuxia: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', border: 'rgba(245,158,11,0.3)' },
    dushi: { bg: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: 'rgba(59,130,246,0.3)' },
    kehuan: { bg: 'rgba(6,182,212,0.15)', color: '#22d3ee', border: 'rgba(6,182,212,0.3)' },
    gudai_yanqing: { bg: 'rgba(236,72,153,0.15)', color: '#f472b6', border: 'rgba(236,72,153,0.3)' },
    xiandai_yanqing: { bg: 'rgba(244,114,182,0.15)', color: '#f9a8d4', border: 'rgba(244,114,182,0.3)' },
  };
  return map[key] || { bg: 'rgba(124,58,237,0.15)', color: '#a78bfa', border: 'rgba(124,58,237,0.3)' };
};

/** 扩展书籍类型 */
interface BookWithStats extends Book {
  completed_chapters?: number;
  total_words?: number;
  avg_audit_score?: number;
}

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [books, setBooks] = useState<BookWithStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [form] = Form.useForm();

  /** 加载书籍列表 */
  const fetchBooks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getBooks();
      const list: BookWithStats[] = Array.isArray(res) ? res : res?.data ?? [];
      setBooks(list);
    } catch (err) {
      message.error('获取书籍列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  /** 打开创建弹窗 */
  const handleOpenCreate = () => {
    form.resetFields();
    form.setFieldsValue({
      platform: '通用',
      chapter_words: 3000,
      target_chapters: 100,
    });
    setModalOpen(true);
  };

  /** 提交创建 */
  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);
      await createBook(values);
      message.success('书籍创建成功');
      setModalOpen(false);
      fetchBooks();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return;
      }
      message.error('创建书籍失败');
      console.error(err);
    } finally {
      setConfirmLoading(false);
    }
  };

  /** 删除书籍 */
  const handleDelete = async (id: number) => {
    try {
      await deleteBook(id);
      message.success('删除成功');
      fetchBooks();
    } catch (err) {
      message.error('删除失败');
      console.error(err);
    }
  };

  /** 查看详情 */
  const handleViewDetail = (bookId: number) => {
    navigate(`/book/${bookId}`);
  };

  /** 格式化字数 */
  const formatWordCount = (count: number): string => {
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)}万`;
    }
    return `${count.toLocaleString()}`;
  };

  /** 格式化日期 */
  const formatDate = (dateStr: string): string => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  /** 获取题材名称 */
  const getGenreName = (key: string): string => {
    const found = GENRE_LIST.find((g) => g.key === key);
    return found ? found.name : key;
  };

  /** 计算进度百分比 */
  const getProgressPercent = (book: BookWithStats): number => {
    const completed = book.completed_chapters ?? 0;
    const target = book.target_chapters || 1;
    return Math.min(Math.round((completed / target) * 100), 100);
  };

  // 统计信息
  const totalBooks = books.length;
  const totalWords = books.reduce((sum, b) => sum + (b.total_words ?? 0), 0);
  const completedBooks = books.filter((b) => getProgressPercent(b) === 100).length;

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* 统计卡片区域 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={8}>
          <Card
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
            }}
            styles={{ body: { padding: 24 } }}
          >
            <Statistic
              title={<span style={{ color: colors.textSecondary }}>书籍总数</span>}
              value={totalBooks}
              prefix={<BookOutlined style={{ color: colors.primaryLight }} />}
              valueStyle={{ color: colors.text, fontSize: 32, fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
            }}
            styles={{ body: { padding: 24 } }}
          >
            <Statistic
              title={<span style={{ color: colors.textSecondary }}>总字数</span>}
              value={formatWordCount(totalWords)}
              prefix={<FileTextOutlined style={{ color: colors.success }} />}
              valueStyle={{ color: colors.text, fontSize: 32, fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
            }}
            styles={{ body: { padding: 24 } }}
          >
            <Statistic
              title={<span style={{ color: colors.textSecondary }}>已完成</span>}
              value={completedBooks}
              prefix={<RocketOutlined style={{ color: colors.warning }} />}
              valueStyle={{ color: colors.text, fontSize: 32, fontWeight: 600 }}
            />
          </Card>
        </Col>
      </Row>

      {/* 内容区域 */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '120px 0' }}>
          <Spin size="large" />
        </div>
      ) : books.length === 0 ? (
        /* 空状态 */
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            paddingTop: 80,
          }}
        >
          <div
            style={{
              width: 160,
              height: 160,
              borderRadius: 24,
              background: `linear-gradient(135deg, ${colors.primary}20, ${colors.primaryLight}20)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 24,
              border: `1px solid ${colors.primary}30`,
            }}
          >
            <BookOutlined style={{ fontSize: 64, color: colors.primaryLight, opacity: 0.8 }} />
          </div>
          <div style={{ fontSize: 20, fontWeight: 600, color: colors.text, marginBottom: 8 }}>
            开始你的创作之旅
          </div>
          <div style={{ fontSize: 14, color: colors.textSecondary, marginBottom: 32 }}>
            创建你的第一部AI辅助小说，让创作更高效
          </div>
          <Button
            type="primary"
            size="large"
            icon={<PlusOutlined />}
            onClick={handleOpenCreate}
            style={{
              height: 48,
              padding: '0 32px',
              borderRadius: 10,
              border: 'none',
              background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
              fontWeight: 500,
              fontSize: 15,
              boxShadow: `0 4px 14px ${colors.primary}40`,
            }}
          >
            创建第一本书
          </Button>
        </div>
      ) : (
        /* 书籍卡片网格 */
        <Row gutter={[24, 24]}>
          {books.map((book) => {
            const percent = getProgressPercent(book);
            const completed = book.completed_chapters ?? 0;
            const target = book.target_chapters || 100;
            const totalWords = book.total_words ?? 0;
            const genreColors = getGenreColors(book.genre);
            const gradient = getGenreGradient(book.genre);

            return (
              <Col xs={24} sm={12} lg={8} xl={6} key={book.id}>
                <div
                  style={{
                    background: colors.card,
                    borderRadius: 16,
                    border: `1px solid ${colors.border}`,
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                    overflow: 'hidden',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                  onMouseEnter={(e) => {
                    const el = e.currentTarget;
                    el.style.borderColor = colors.primary;
                    el.style.boxShadow = `0 0 20px ${colors.primary}20`;
                    el.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    const el = e.currentTarget;
                    el.style.borderColor = colors.border;
                    el.style.boxShadow = 'none';
                    el.style.transform = 'translateY(0)';
                  }}
                  onClick={() => handleViewDetail(book.id)}
                >
                  {/* 顶部彩色渐变条 */}
                  <div
                    style={{
                      height: 4,
                      background: gradient,
                    }}
                  />

                  {/* 主体内容 */}
                  <div
                    style={{
                      padding: 24,
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    {/* 书名 */}
                    <div
                      style={{
                        fontSize: 18,
                        fontWeight: 600,
                        color: colors.text,
                        marginBottom: 12,
                        lineHeight: 1.4,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {book.title}
                    </div>

                    {/* 题材 + 平台标签 */}
                    <div style={{ marginBottom: 20 }}>
                      <Space size={8} wrap>
                        <Tag
                          style={{
                            background: genreColors.bg,
                            color: genreColors.color,
                            border: `1px solid ${genreColors.border}`,
                            borderRadius: 6,
                            fontSize: 12,
                            padding: '4px 10px',
                            margin: 0,
                          }}
                        >
                          {getGenreName(book.genre)}
                        </Tag>
                        {book.platform && (
                          <Tag
                            style={{
                              background: 'rgba(148,163,184,0.1)',
                              color: colors.textSecondary,
                              border: `1px solid ${colors.border}`,
                              borderRadius: 6,
                              fontSize: 12,
                              padding: '4px 10px',
                              margin: 0,
                            }}
                          >
                            {book.platform}
                          </Tag>
                        )}
                      </Space>
                    </div>

                    {/* 进度区域 */}
                    <div style={{ marginBottom: 20 }}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginBottom: 8,
                        }}
                      >
                        <span style={{ fontSize: 13, color: colors.textSecondary }}>
                          写作进度
                        </span>
                        <span style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>
                          {completed} / {target} 章
                        </span>
                      </div>
                      <div
                        style={{
                          height: 8,
                          borderRadius: 4,
                          background: 'rgba(255,255,255,0.05)',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${percent}%`,
                            borderRadius: 4,
                            background: gradient,
                            transition: 'width 0.6s ease',
                          }}
                        />
                      </div>
                    </div>

                    {/* 统计行 */}
                    <div style={{ marginBottom: 20, flex: 1 }}>
                      <Row gutter={16}>
                        <Col span={12}>
                          <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 4 }}>
                            总字数
                          </div>
                          <div style={{ fontSize: 18, fontWeight: 600, color: colors.text }}>
                            {formatWordCount(totalWords)}
                          </div>
                        </Col>
                        <Col span={12}>
                          <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 4 }}>
                            完成度
                          </div>
                          <div style={{ fontSize: 18, fontWeight: 600, color: colors.primaryLight }}>
                            {percent}%
                          </div>
                        </Col>
                      </Row>
                    </div>

                    {/* 底部分隔线 */}
                    <div
                      style={{
                        borderTop: `1px solid ${colors.border}`,
                        paddingTop: 16,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ fontSize: 12, color: colors.textSecondary }}>
                        <ClockCircleOutlined style={{ marginRight: 4 }} />
                        {formatDate(book.created_at)}
                      </span>
                      <Space size={8}>
                        <Button
                          type="text"
                          size="small"
                          icon={<EditOutlined />}
                          style={{ color: colors.textSecondary }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewDetail(book.id);
                          }}
                        >
                          编辑
                        </Button>
                        <Popconfirm
                          title="确认删除"
                          description={`确定要删除《${book.title}》吗？`}
                          onConfirm={(e) => {
                            e?.stopPropagation();
                            handleDelete(book.id);
                          }}
                          okText="删除"
                          cancelText="取消"
                          okButtonProps={{ danger: true }}
                        >
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={(e) => e.stopPropagation()}
                          >
                            删除
                          </Button>
                        </Popconfirm>
                      </Space>
                    </div>
                  </div>
                </div>
              </Col>
            );
          })}
        </Row>
      )}

      {/* 创建新书弹窗 */}
      <Modal
        title={
          <div style={{ textAlign: 'center', fontSize: 20, fontWeight: 600, color: colors.text }}>
            创建新书
          </div>
        }
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={600}
        centered
        styles={{
          content: {
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 16,
          },
          header: {
            borderBottom: `1px solid ${colors.border}`,
          },
        }}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            label={<span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>书名</span>}
            name="title"
            rules={[{ required: true, message: '请输入书名' }]}
          >
            <Input
              placeholder="请输入书籍名称"
              maxLength={50}
              showCount
              style={{
                borderRadius: 10,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>题材</span>}
            name="genre"
            rules={[{ required: true, message: '请选择题材' }]}
          >
            <Select
              placeholder="请选择题材"
              options={genreGroupOptions}
              showSearch
              optionFilterProp="label"
              style={{
                borderRadius: 10,
              }}
              dropdownStyle={{
                background: colors.card,
                border: `1px solid ${colors.border}`,
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>平台</span>}
            name="platform"
          >
            <Select
              placeholder="请选择发布平台"
              options={PLATFORM_OPTIONS}
              allowClear
              style={{ borderRadius: 10 }}
              dropdownStyle={{
                background: colors.card,
                border: `1px solid ${colors.border}`,
              }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>每章字数</span>
                }
                name="chapter_words"
                rules={[{ required: true, message: '请输入每章字数' }]}
              >
                <InputNumber
                  min={500}
                  max={20000}
                  step={500}
                  style={{ width: '100%', borderRadius: 10 }}
                  placeholder="默认3000"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>目标章数</span>
                }
                name="target_chapters"
                rules={[{ required: true, message: '请输入目标章数' }]}
              >
                <InputNumber
                  min={1}
                  max={10000}
                  step={10}
                  style={{ width: '100%', borderRadius: 10 }}
                  placeholder="默认100"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label={<span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>大纲</span>}
            name="outline"
          >
            <TextArea
              rows={4}
              placeholder="请输入书籍大纲（可选）"
              maxLength={5000}
              showCount
              style={{
                borderRadius: 10,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
            />
          </Form.Item>

          {/* 底部按钮 */}
          <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <Button
                onClick={() => setModalOpen(false)}
                style={{
                  borderRadius: 10,
                  height: 44,
                  padding: '0 24px',
                  border: `1px solid ${colors.border}`,
                  background: 'transparent',
                  color: colors.text,
                }}
              >
                取消
              </Button>
              <Button
                type="primary"
                loading={confirmLoading}
                onClick={handleCreate}
                style={{
                  height: 44,
                  padding: '0 24px',
                  borderRadius: 10,
                  border: 'none',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                  color: '#fff',
                  fontWeight: 500,
                  boxShadow: `0 4px 14px ${colors.primary}40`,
                }}
              >
                创建
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Home;
