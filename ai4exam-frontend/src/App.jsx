// src/App.jsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { App as AntApp } from 'antd'; // 引入 Ant Design 的 App 组件
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

// Main App component wrapped with AntApp
function App() {
  return (
    <AntApp>
      <AppRoot />
    </AntApp>
  );
}

export default App;