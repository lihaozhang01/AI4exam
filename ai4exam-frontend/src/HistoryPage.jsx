import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Spin, Alert, Button, Popconfirm, message } from 'antd';
import { DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import './HistoryPage.css'; // 引入新的CSS文件

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const StatCard = ({ value, label }) => (
  <div className="stat">
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
  </div>
);

function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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
        // 根据创建时间降序排序
        data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setHistory(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`${API_URL}/history/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`删除失败: ${response.status} - ${errorData.detail || '服务器内部错误'}`);
      }
      setHistory(history.filter(item => item.id !== id));
      message.success('历史记录删除成功');
    } catch (err) {
      setError(err.message);
      message.error(`删除失败: ${err.message}`);
    }
  };



  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><Spin size="large" tip="加载历史中..." /></div>;
  }

  if (error) {
    return <div className="history-container"><Alert message="加载出错" description={error} type="error" showIcon /></div>;
  }

  return (
    <div className="history-container">
      <header className="history-header">
        <h1>历史试卷</h1>
        <p>温故而知新</p>
      </header>

      {history.length > 0 ? (
        <div className="history-grid">
          {history.map(item => {
            return (
              <div key={item.id} className="history-card">
                <div className="card-content">
                  <div className="card-header">
                    <h2 onClick={() => navigate(`/history/${item.id}`)}>
                      {item.test_paper ? item.test_paper.name : `试卷 #${item.test_paper_id}`}
                    </h2>
                    <p className="card-date">{new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <div className="card-stats">
                    <StatCard
                      label="客观题正确率"
                      value={`${item.correct_objective_questions}/${item.total_objective_questions}`}
                    />
                    <StatCard value={item.total_essay_questions} label="论述题" />
                  </div>
                </div>
                <div className="card-actions">
                  <Button
                    type="text"
                    icon={<EyeOutlined />}
                    onClick={() => navigate(`/history/${item.id}`)}
                  >
                    查看
                  </Button>
                  <Popconfirm
                    title="确定要删除这份试卷吗？此操作不可撤销。"
                    onConfirm={() => handleDelete(item.id)}
                    okText="确认删除"
                    cancelText="取消"
                  >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                      删除
                    </Button>
                  </Popconfirm>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="no-history-container">
          <h2>暂无历史记录</h2>
          <p>当您生成第一份试卷后，这里将记录您的学习旅程。</p>
          <Link to="/" className="go-to-generate-btn">
            去生成第一份试卷
          </Link>
        </div>
      )}
      <Link to="/" className="history-back-link">← 返回出题表单</Link>
    </div>
  );
}

export default HistoryPage;