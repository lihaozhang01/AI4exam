// src/HistoryPage.jsx

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { List, Typography, Spin, Alert, Button, Popconfirm, message } from 'antd';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`${API_URL}/history/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        // Even if the status is 204, response.ok is true.
        // This will catch 404, 500, etc.
        const errorData = await response.json().catch(() => ({})); // Avoid JSON parse error on empty body
        throw new Error(`删除失败: ${response.status} - ${errorData.detail || '服务器内部错误'}`);
      }
      setHistory(history.filter(item => item.id !== id));
      message.success('历史记录删除成功');
    } catch (err) {
      setError(err.message);
      message.error(`删除失败: ${err.message}`);
    }
  };

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
            actions={[
              <Link to={`/history/${item.id}`}>查看详情</Link>,
              <Popconfirm
                title="确定删除这条历史记录吗？"
                onConfirm={() => handleDelete(item.id)}
                okText="是"
                cancelText="否"
              >
                <Button type="link" danger>删除</Button>
              </Popconfirm>
            ]}
          >
            <List.Item.Meta
              title={item.test_paper ? item.test_paper.name : `试卷 #${item.test_paper_id}`}
              description={`完成于: ${new Date(item.created_at).toLocaleString()}`}
            />
          </List.Item>
        )}
      />
    </div>
  );
}

export default HistoryPage;