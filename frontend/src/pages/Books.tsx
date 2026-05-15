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
  Table,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  BookOutlined,
  EditOutlined,
  ClockCircleOutlined,
  SearchOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import type { Book, GenreItem } from '@/types';
import { getBooks, createBook, deleteBook } from '@/services/api';

const { Search } = Input;

// Dify 风格颜色
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
};

const GENRE_LIST: GenreItem[] = [
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

const PLATFORM_OPTIONS = [
  { label: '起点', value: '起点' },
  { label: '番茄', value: '番茄' },
  { label: '晋江', value: '晋江' },
  { label: '通用', value: '通用' },
];

const genreGroupOptions = (() => {
  const groups: { label: string; options: { label: string; value: string }[] }[] = [];
  ['男频', '女频'].forEach((cat) => {
    groups.push({
      label: cat,
      options: GENRE_LIST.filter((g) => g.category === cat).map((g) => ({ label: g.name, value: g.key })),
    });
  });
  return groups;
})();

const getGenreGradient = (key: string): string => {
  const map: Record<string, string> = {
    xuanhuan: 'linear-gradient(135deg, #7c3aed, #8b5cf6)',
    xianxia: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    wuxia: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
    dushi: 'linear-gradient(135deg, #3b82f6, #60a5fa)',
    kehuan: 'linear-gradient(135deg, #06b6d4, #22d3ee)',
    gudai_yanqing: 'linear-gradient(135deg, #ec4899, #f472b6)',
    xiandai_yanqing: 'linear-gradient(135deg, #f472b6, #fb7185)',
  };
  return map[key] || 'linear-gradient(135deg, #7c3aed, #8b5cf6)';
};

const getGenreColors = (key: string): { bg: string; color: string; border: string } => {
  const map: Record<string, { bg: string; color: string; border: string }> = {
    xuanhuan: { bg: 'rgba(124,58,237,0.15)', color: '#a78bfa', border: 'rgba(124,58,237,0.3)' },
    xianxia: { bg: 'rgba(99,102,241,0.15)', color: '#818cf8', border: 'rgba(99,102,241,0.3)' },
    wuxia: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', border: 'rgba(245,158,11,0.3)' },
    dushi: { bg: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: 'rgba(59,130,246,0.3)' },
    kehuan: { bg: 'rgba(6,182,212,0.15)', color: '#22d3ee', border: 'rgba(6,182,212,0.3)' },
    gudai_yanqing: { bg: 'rgba(236,72,153,0.15)', color: '#f472b6', border: 'rgba(236,72,153,0.3)' },
  };
  return map[key] || { bg: 'rgba(124,58,237,0.15)', color: '#a78bfa', border: 'rgba(124,58,237,0.3)' };
};

const Books: React.FC = () => {
  const navigate = useNavigate();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [form] = Form.useForm();

  const fetchBooks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getBooks();
      const list: Book[] = Array.isArray(res) ? res : res?.data ?? [];
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

  const handleOpenCreate = () => {
    form.resetFields();
    form.setFieldsValue({ platform: '通用', chapter_words: 3000, target_chapters: 100 });
    setModalOpen(true);
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);
      await createBook(values);
      message.success('书籍创建成功');
      setModalOpen(false);
      fetchBooks();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('创建书籍失败');
      console.error(err);
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteBook(id);
      message.success('删除成功');
      fetchBooks();
    } catch (err) {
      message.error('删除失败');
    }
  };

  const getGenreName = (key: string) => GENRE_LIST.find((g) => g.key === key)?.name || key;
  const formatWordCount = (count: number) => count >= 10000 ? `${(count / 10000).toFixed(1)}万` : `${count.toLocaleString()}`;
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };

  // 搜索过滤
  const filteredBooks = books.filter((b) =>
    !searchText || b.title.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: '书名',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Book) => (
        <a onClick={() => navigate(`/book/${record.id}`)} style={{ color: colors.text, fontWeight: 500 }}>
          {text}
        </a>
      ),
    },
    {
      title: '题材',
      dataIndex: 'genre',
      key: 'genre',
      width: 120,
      render: (val: string) => {
        const gc = getGenreColors(val);
        return (
          <Tag style={{ background: gc.bg, color: gc.color, border: `1px solid ${gc.border}`, borderRadius: 6 }}>
            {getGenreName(val)}
          </Tag>
        );
      },
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 100,
      render: (val: string) => val || '-',
    },
    {
      title: '每章字数',
      dataIndex: 'chapter_words',
      key: 'chapter_words',
      width: 110,
      render: (val: number) => val ? val.toLocaleString() : '-',
    },
    {
      title: '目标章数',
      dataIndex: 'target_chapters',
      key: 'target_chapters',
      width: 110,
      render: (val: number) => val || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 130,
      render: (val: string) => formatDate(val),
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: unknown, record: Book) => (
        <Space size={8}>
          <Button type="link" size="small" style={{ color: colors.primaryLight }} onClick={() => navigate(`/book/${record.id}`)}>
            详情
          </Button>
          <Popconfirm title="确认删除" description={`确定删除《${record.title}》？`} onConfirm={() => handleDelete(record.id)} okText="删除" cancelText="取消" okButtonProps={{ danger: true }}>
            <Button type="text" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* 顶部操作栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <UnorderedListOutlined style={{ fontSize: 20, color: colors.primaryLight }} />
          <span style={{ fontSize: 16, fontWeight: 600, color: colors.text }}>全部书籍 ({filteredBooks.length})</span>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <Search
            placeholder="搜索书名..."
            allowClear
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 260, borderRadius: 10 }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleOpenCreate}
            style={{
              height: 40,
              borderRadius: 10,
              border: 'none',
              background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
              fontWeight: 500,
              boxShadow: `0 4px 14px ${colors.primary}40`,
            }}
          >
            创建新书
          </Button>
        </div>
      </div>

      {/* 书籍表格 */}
      <Card
        style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 16 }}
        styles={{ body: { padding: 0 } }}
      >
        <Table
          dataSource={filteredBooks.map((b) => ({ ...b, key: b.id }))}
          columns={columns}
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 本`, showSizeChanger: true }}
          style={{ borderRadius: 16 }}
        />
      </Card>

      {/* 创建弹窗 */}
      <Modal
        title={<div style={{ textAlign: 'center', fontSize: 20, fontWeight: 600, color: colors.text }}>创建新书</div>}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={600}
        centered
        styles={{
          content: { background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 16 },
          header: { borderBottom: `1px solid ${colors.border}` },
        }}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item label={<span style={{ color: colors.text, fontWeight: 500 }}>书名</span>} name="title" rules={[{ required: true, message: '请输入书名' }]}>
            <Input placeholder="请输入书籍名称" maxLength={50} showCount style={{ borderRadius: 10, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={<span style={{ color: colors.text, fontWeight: 500 }}>题材</span>} name="genre" rules={[{ required: true, message: '请选择题材' }]}>
                <Select placeholder="请选择题材" options={genreGroupOptions} showSearch optionFilterProp="label" dropdownStyle={{ background: colors.card, border: `1px solid ${colors.border}` }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={<span style={{ color: colors.text, fontWeight: 500 }}>平台</span>} name="platform">
                <Select placeholder="请选择发布平台" options={PLATFORM_OPTIONS} allowClear dropdownStyle={{ background: colors.card, border: `1px solid ${colors.border}` }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={<span style={{ color: colors.text, fontWeight: 500 }}>每章字数</span>} name="chapter_words" rules={[{ required: true }]}>
                <InputNumber min={500} max={20000} step={500} style={{ width: '100%', borderRadius: 10 }} placeholder="默认3000" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={<span style={{ color: colors.text, fontWeight: 500 }}>目标章数</span>} name="target_chapters" rules={[{ required: true }]}>
                <InputNumber min={1} max={10000} step={10} style={{ width: '100%', borderRadius: 10 }} placeholder="默认100" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label={<span style={{ color: colors.text, fontWeight: 500 }}>大纲</span>} name="outline">
            <Input.TextArea rows={4} placeholder="请输入书籍大纲（可选）" maxLength={5000} showCount style={{ borderRadius: 10, background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <Button onClick={() => setModalOpen(false)} style={{ borderRadius: 10, height: 44, padding: '0 24px', border: `1px solid ${colors.border}`, background: 'transparent', color: colors.text }}>取消</Button>
              <Button type="primary" loading={confirmLoading} onClick={handleCreate} style={{ height: 44, padding: '0 24px', borderRadius: 10, border: 'none', background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`, fontWeight: 500, boxShadow: `0 4px 14px ${colors.primary}40` }}>创建</Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Books;
