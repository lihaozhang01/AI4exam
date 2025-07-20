// src/App.jsx

import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import 'antd/dist/reset.css';
import TestPaperPage from './TestPaperPage';
// 引入我们将要创建的真实表单页面
import TestFormPage from './TestFormPage';
import HistoryPage from './HistoryPage'; // 引入历史页面

// 试卷页的占位符

function App() {
  return (
    <div style={{ minHeight: '100vh', width: '100vw' }}>
      <Routes>
        <Route path="/" element={<TestFormPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/testpaper/:testId" element={<TestPaperPage />} />
        <Route path="/history/:resultId" element={<TestPaperPage />} />
      </Routes>
    </div>
  );
}

export default App;