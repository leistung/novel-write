import React from 'react';
import { Result } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';

const Help: React.FC = () => (
  <div style={{ padding: 40 }}>
    <Result
      icon={<QuestionCircleOutlined style={{ color: '#7c3aed' }} />}
      title="帮助中心"
      subTitle="使用文档和常见问题正在建设中，敬请期待..."
      style={{ color: '#f1f5f9' }}
    />
  </div>
);

export default Help;
