import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Modal, Space, Typography } from 'antd';
import { BugOutlined, ClearOutlined, ReloadOutlined } from '@ant-design/icons';
import { apiLogger } from '../services/api';

const { Text, Paragraph } = Typography;

interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'request' | 'response' | 'error' | 'info';
  method?: string;
  url?: string;
  status?: number;
  data?: unknown;
  error?: string;
  duration?: number;
  requestId?: string;
}

interface LogPanelProps {
  visible?: boolean;
  onClose?: () => void;
}

const LogPanel: React.FC<LogPanelProps> = ({ visible = false, onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  useEffect(() => {
    // 订阅日志更新
    const unsubscribe = apiLogger.onUpdate((newLogs) => {
      setLogs(newLogs);
    });

    // 初始加载
    setLogs(apiLogger.getLogs());

    return () => {
      unsubscribe();
    };
  }, []);

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'request': return 'blue';
      case 'response': return 'green';
      case 'error': return 'red';
      default: return 'purple';
    }
  };

  const getTypeName = (type: string) => {
    switch (type) {
      case 'request': return '请求';
      case 'response': return '响应';
      case 'error': return '错误';
      default: return '信息';
    }
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 100,
      render: (time: Date) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {new Date(time).toLocaleTimeString()}
        </Text>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>{getTypeName(type)}</Tag>
      ),
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 70,
      render: (method?: string) => (
        method ? <Tag>{method}</Tag> : <Text type="secondary">-</Text>
      ),
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
      render: (url?: string) => (
        <Text code style={{ fontSize: 12 }}>{url || '-'}</Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status?: number) => {
        if (!status) return <Text type="secondary">-</Text>;
        const color = status >= 200 && status < 300 ? 'success' : 
                     status >= 400 && status < 500 ? 'warning' : 'danger';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      render: (duration?: number) => (
        duration ? (
          <Text type={duration > 5000 ? 'danger' : 'secondary'}>{duration}ms</Text>
        ) : <Text type="secondary">-</Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: LogEntry) => (
        <Button 
          type="link" 
          size="small"
          onClick={() => {
            setSelectedLog(record);
            setDetailVisible(true);
          }}
        >
          详情
        </Button>
      ),
    },
  ];

  const failedCount = logs.filter(l => l.type === 'error').length;

  return (
    <>
      <Card
        size="small"
        title={
          <Space>
            <BugOutlined />
            <span>API 日志</span>
            {failedCount > 0 && <Tag color="red">{failedCount} 个错误</Tag>}
          </Space>
        }
        extra={
          <Space>
            <Button 
              size="small" 
              icon={<ReloadOutlined />}
              onClick={() => setLogs(apiLogger.getLogs())}
            >
              刷新
            </Button>
            <Button 
              size="small" 
              danger
              icon={<ClearOutlined />}
              onClick={() => {
                apiLogger.clearLogs();
                setLogs([]);
              }}
            >
              清空
            </Button>
          </Space>
        }
        style={{ 
          marginTop: 16,
          background: '#1e293b',
          border: '1px solid #334155',
        }}
        styles={{ header: { background: '#1e293b', borderBottom: '1px solid #334155' } }}
      >
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          size="small"
          pagination={false}
          scroll={{ y: 300 }}
          rowClassName={(record) => record.type === 'error' ? 'error-row' : ''}
        />
      </Card>

      <Modal
        title="日志详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={700}
      >
        {selectedLog && (
          <div>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>基本信息</Text>
                <Card size="small" style={{ marginTop: 8 }}>
                  <Space direction="vertical">
                    <Text>时间：{new Date(selectedLog.timestamp).toLocaleString()}</Text>
                    <Text>类型：<Tag color={getTypeColor(selectedLog.type)}>{getTypeName(selectedLog.type)}</Tag></Text>
                    <Text>请求ID：{selectedLog.requestId || '-'}</Text>
                    {selectedLog.method && <Text>方法：{selectedLog.method}</Text>}
                    {selectedLog.url && <Text>URL：<Text code>{selectedLog.url}</Text></Text>}
                    {selectedLog.status && <Text>状态码：{selectedLog.status}</Text>}
                    {selectedLog.duration && <Text>耗时：{selectedLog.duration}ms</Text>}
                  </Space>
                </Card>
              </div>

              {selectedLog.data !== undefined && selectedLog.data !== null && (
                <div>
                  <Text strong>请求/响应数据</Text>
                  <Card size="small" style={{ marginTop: 8, background: '#0f172a' }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                      {typeof selectedLog.data === 'object' ? JSON.stringify(selectedLog.data, null, 2) : String(selectedLog.data)}
                    </pre>
                  </Card>
                </div>
              )}

              {selectedLog.error && (
                <div>
                  <Text strong>错误信息</Text>
                  <Card size="small" style={{ marginTop: 8, background: '#2d1f1f' }}>
                    <Paragraph type="danger" style={{ margin: 0 }}>
                      {selectedLog.error}
                    </Paragraph>
                  </Card>
                </div>
              )}
            </Space>
          </div>
        )}
      </Modal>
    </>
  );
};

export default LogPanel;
