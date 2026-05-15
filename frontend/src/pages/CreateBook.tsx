import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Row,
  Col,
  message,
  Steps,
  Typography,
} from 'antd';
import { BookOutlined, EditOutlined, CheckCircleOutlined, ArrowLeftOutlined, BugOutlined } from '@ant-design/icons';
import { createBook } from '@/services/api';
import { apiLogger } from '@/services/api';
import LogPanel from '@/components/LogPanel';

const { TextArea } = Input;
const { Title, Text } = Typography;

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
  error: '#ef4444',
};

const GENRE_LIST = [
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

const PLATFORM_OPTIONS = [
  { label: '起点', value: '起点' },
  { label: '番茄', value: '番茄' },
  { label: '晋江', value: '晋江' },
  { label: '通用', value: '通用' },
];

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

const CreateBook: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [recentError, setRecentError] = useState<string | null>(null);
  
  // 保存第一步的数据
  const [step1Data, setStep1Data] = useState<{title?: string; genre?: string; platform?: string}>({});

  // 监听API错误
  useEffect(() => {
    const unsubscribe = apiLogger.onUpdate((logs) => {
      const lastError = logs.find(l => l.type === 'error');
      if (lastError && lastError.url?.includes('/books')) {
        setRecentError(lastError.error || '创建书籍失败');
      }
    });
    return () => unsubscribe();
  }, []);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      setRecentError(null);
      
      console.log('[CreateBook] 提交数据:', values);
      
      const result = await createBook(values);
      console.log('[CreateBook] 创建成功:', result);
      
      message.success('书籍创建成功！');
      navigate('/books');
    } catch (err: unknown) {
      console.error('[CreateBook] 创建失败:', err);
      
      // 检查是否是表单验证错误
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return;
      }
      
      // 提取错误信息
      let errorMsg = '创建书籍失败';
      if (err && typeof err === 'object') {
        const error = err as { response?: { data?: { detail?: string } }; message?: string };
        if (error.response?.data?.detail) {
          errorMsg = error.response.data.detail;
        } else if (error.message) {
          errorMsg = error.message;
        }
      }
      
      setRecentError(errorMsg);
      message.error(errorMsg);
      
      // 显示日志面板
      setShowLogs(true);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    {
      title: '基本信息',
      icon: <BookOutlined />,
    },
    {
      title: '详细设置',
      icon: <EditOutlined />,
    },
    {
      title: '完成',
      icon: <CheckCircleOutlined />,
    },
  ];

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* 返回按钮 */}
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/')}
        style={{
          color: colors.textSecondary,
          marginBottom: 24,
          padding: '8px 16px',
          borderRadius: 8,
        }}
      >
        返回工作台
      </Button>

      {/* 标题 */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2} style={{ color: colors.text, marginBottom: 8 }}>
          创建新书
        </Title>
        <Text style={{ color: colors.textSecondary }}>
          填写以下信息，开始你的AI辅助创作之旅
        </Text>
      </div>

      {/* 错误提示 */}
      {recentError && (
        <Card
          style={{
            background: '#2d1f1f',
            border: `1px solid ${colors.error}`,
            borderRadius: 12,
            marginBottom: 24,
          }}
        >
          <Row align="middle">
            <Col flex="auto">
              <Text type="danger">
                <strong>创建失败:</strong> {recentError}
              </Text>
            </Col>
            <Col>
              <Button
                size="small"
                icon={<BugOutlined />}
                onClick={() => setShowLogs(!showLogs)}
              >
                {showLogs ? '隐藏日志' : '查看日志'}
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {/* 日志面板 */}
      {showLogs && (
        <LogPanel />
      )}

      {/* 步骤条 */}
      <Card
        style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 16,
          marginBottom: 24,
        }}
        styles={{ body: { padding: 24 } }}
      >
        <Steps
          current={currentStep}
          items={steps}
          style={{
            marginBottom: 32,
          }}
        />

        <Form
          form={form}
          layout="vertical"
          initialValues={{
            platform: '通用',
            chapter_words: 3000,
            target_chapters: 100,
          }}
          preserve={true}
        >
          <div style={{ display: currentStep === 0 ? 'block' : 'none' }}>
            <Form.Item
              label={
                <span style={{ color: colors.text, fontWeight: 500 }}>书名</span>
              }
              name="title"
              rules={[{ required: true, message: '请输入书名' }]}
            >
                <Input
                  placeholder="给你的小说起个响亮的名字"
                  maxLength={50}
                  showCount
                  style={{
                    background: colors.bg,
                    border: `1px solid ${colors.border}`,
                    color: colors.text,
                    borderRadius: 10,
                    height: 48,
                  }}
                />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label={
                      <span style={{ color: colors.text, fontWeight: 500 }}>题材</span>
                    }
                    name="genre"
                    rules={[{ required: true, message: '请选择题材' }]}
                  >
                    <Select
                      placeholder="选择题材类型"
                      options={genreGroupOptions}
                      showSearch
                      optionFilterProp="label"
                      style={{ borderRadius: 10 }}
                      dropdownStyle={{
                        background: colors.card,
                        border: `1px solid ${colors.border}`,
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label={
                      <span style={{ color: colors.text, fontWeight: 500 }}>平台</span>
                    }
                    name="platform"
                  >
                    <Select
                      placeholder="选择发布平台"
                      options={PLATFORM_OPTIONS}
                      allowClear
                      style={{ borderRadius: 10 }}
                      dropdownStyle={{
                        background: colors.card,
                        border: `1px solid ${colors.border}`,
                      }}
                    />
                  </Form.Item>
                </Col>
              </Row>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24 }}>
              <Button
                type="primary"
                onClick={async () => {
                  try {
                    // 验证第一步的字段
                    await form.validateFields(['title', 'genre']);
                    setCurrentStep(1);
                  } catch (e) {
                    // 验证失败，不切换步骤
                  }
                }}
                style={{
                  height: 44,
                  padding: '0 32px',
                  borderRadius: 10,
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                  border: 'none',
                  fontWeight: 500,
                }}
              >
                下一步
              </Button>
            </div>
          </div>

          <div style={{ display: currentStep === 1 ? 'block' : 'none' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label={
                      <span style={{ color: colors.text, fontWeight: 500 }}>每章字数</span>
                    }
                    name="chapter_words"
                    rules={[{ required: true, message: '请输入每章字数' }]}
                  >
                    <InputNumber
                      min={500}
                      max={20000}
                      step={500}
                      style={{ width: '100%', borderRadius: 10, height: 48 }}
                      placeholder="建议 2000-5000 字"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label={
                      <span style={{ color: colors.text, fontWeight: 500 }}>目标章数</span>
                    }
                    name="target_chapters"
                    rules={[{ required: true, message: '请输入目标章数' }]}
                  >
                    <InputNumber
                      min={1}
                      max={10000}
                      step={10}
                      style={{ width: '100%', borderRadius: 10, height: 48 }}
                      placeholder="建议 50-500 章"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label={
                  <span style={{ color: colors.text, fontWeight: 500 }}>大纲（可选）</span>
                }
                name="outline"
              >
                <TextArea
                  rows={6}
                  placeholder="简要描述故事主线、主要角色和剧情发展..."
                  maxLength={5000}
                  showCount
                  style={{
                    background: colors.bg,
                    border: `1px solid ${colors.border}`,
                    color: colors.text,
                    borderRadius: 10,
                  }}
                />
              </Form.Item>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginTop: 24,
                }}
              >
                <Button
                  onClick={() => setCurrentStep(0)}
                  style={{
                    height: 44,
                    padding: '0 32px',
                    borderRadius: 10,
                    border: `1px solid ${colors.border}`,
                    background: 'transparent',
                    color: colors.text,
                  }}
                >
                  上一步
                </Button>
                <Button
                  type="primary"
                  loading={loading}
                  onClick={handleSubmit}
                  style={{
                    height: 44,
                    padding: '0 32px',
                    borderRadius: 10,
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                    border: 'none',
                    fontWeight: 500,
                    boxShadow: `0 4px 14px ${colors.primary}40`,
                  }}
                >
                  创建书籍
                </Button>
              </div>
            </div>
          </Form>
      </Card>
    </div>
  );
};

export default CreateBook;
