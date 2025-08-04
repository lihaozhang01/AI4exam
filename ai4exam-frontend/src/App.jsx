// src/App.jsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { App as AntApp, ConfigProvider } from 'antd'; // 导入 ConfigProvider
import 'antd/dist/reset.css';
import TestPaperPage from './TestPaperPage';
import TestFormPage from './TestFormPage';
import HistoryPage from './HistoryPage';
import TestStreamingPage from './TestStreamingPage';

// Root component that includes AntApp for context
const AppRoot = () => (
  <div style={{ minHeight: '100vh', width: '100vw' }}>
    <Routes>
      <Route path="/" element={<TestFormPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/testpaper/:testId" element={<TestPaperPage />} />
      <Route path="/history/:resultId" element={<TestPaperPage />} />
      <Route path="/test-streaming/:test_id" element={<TestStreamingPage />} />
    </Routes>
  </div>
);

// Main App component wrapped with ConfigProvider and AntApp
function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#709a94', // 设定你的灰绿色主色调
          colorSuccess: '#88c0b7', // 成功色也用灰绿色
          // 其他 token 变量可以按需修改
        },
      }}
    >
      <AntApp>
        <AppRoot />
      </AntApp>
    </ConfigProvider>
  );
}

export default App;