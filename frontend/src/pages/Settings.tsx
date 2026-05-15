import React from 'react';
import { Result } from 'antd';
import { SettingOutlined } from '@ant-design/icons';

const Settings: React.FC = () => (
  <div style={{ padding: 40 }}>
    <Result
      icon={<SettingOutlined style={{ color: '#7c3aed' }} />}
      title="设置"
      subTitle="应用偏好设置正在建设中，敬请期待..."
      style={{ color: '#f1f5f9' }}
    />
  </div>
);

export default Settings;
