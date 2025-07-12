// src/HistoryPage.jsx

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { List, Typography, Spin, Alert } from 'antd';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_URL}/history`);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`获取历史记录失败: ${response.status} ${response.statusText} - ${errorData.detail || JSON.stringify(errorData)}`);
        }
        const data = await response.json();
        setHistory(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: '50px' }}><Spin size="large" /></div>;
  }

  if (error) {
    return <Alert message="错误" description={error} type="error" showIcon />;
  }

  return (
    <div>
      <h2>历史试卷</h2>
      <List
        itemLayout="horizontal"
        dataSource={history}
        renderItem={item => (
          <List.Item
            actions={[<Link to={`/testpaper/${item.id}`}>查看详情</Link>]}
          >
            <List.Item.Meta
              title={`试卷 #${item.test_paper_id}`}
              description={`完成于: ${new Date(item.created_at).toLocaleString()}`}
            />
          </List.Item>
        )}
      />
    </div>
  );
}

export default HistoryPage;