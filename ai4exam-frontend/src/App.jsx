// src/App.jsx

import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Modal, Input, Button, message, Space } from 'antd';
import { SettingOutlined } from '@ant-design/icons'; // 引入图标
import 'antd/dist/reset.css';
import TestPaperPage from './TestPaperPage';
// 引入我们将要创建的真实表单页面
import TestFormPage from './TestFormPage';
import HistoryPage from './HistoryPage'; // 引入历史页面

// 试卷页的占位符

const { Header, Content, Footer } = Layout;

function App() {
  const [isModalVisible, setIsModalVisible] = useState(false);
  // 尝试从localStorage读取已有的key，用于在模态框中显示
  const [apiKey, setApiKey] = useState(localStorage.getItem('api_key') || '');
  const location = useLocation();

  const showSettingsModal = () => {
    setApiKey(localStorage.getItem('api_key') || ''); // 每次打开都重新读取
    setIsModalVisible(true);
  };

  const handleOk = () => {
    if (apiKey.trim() === '') {
      message.error('API Key 不能为空！');
      return;
    }
    localStorage.setItem('api_key', apiKey);
    message.success('API Key 已更新！');
    setIsModalVisible(false);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  return (
    <Layout style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo" style={{ color: 'white', marginRight: '20px', fontSize: '18px' }}>
            AI 智能试卷助手
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={[location.pathname]}
            style={{ lineHeight: '64px' }}
            items={[
              { key: '/', label: <Link to="/">出题表单</Link> },
              { key: '/history', label: <Link to="/history">历史试卷</Link> },
            ]}
          />
        </div>
        <Button type="text" icon={<SettingOutlined style={{ color: 'white', fontSize: '20px' }} />} onClick={showSettingsModal} />
      </Header>

      {/* 内容区现在会填满剩余空间 */}
      <Content style={{ padding: '24px 50px', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ background: '#fff', padding: 24, flex: 1 }}>
          <Routes>
            <Route path="/" element={<TestFormPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/testpaper/:testId" element={<TestPaperPage />} />
            <Route path="/history/:resultId" element={<TestPaperPage />} />
          </Routes>
        </div>
      </Content>

      <Footer style={{ textAlign: 'center' }}>
        AI Exam Assistant ©{new Date().getFullYear()} Created with Ant Design
      </Footer>

      <Modal
        title="API Key 设置"
        open={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
        okText="保存"
        cancelText="取消"
      >
        <p>您的AI API Key将仅保存在您的浏览器中。</p>
        <Input.Password
          placeholder="请输入您的API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </Modal>
    </Layout>
  );
}

export default App;