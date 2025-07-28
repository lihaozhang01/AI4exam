import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Spin, Alert, Button, Popconfirm, message, Input, Select, Modal } from 'antd';
import { DeleteOutlined, EyeOutlined, SearchOutlined } from '@ant-design/icons';
import './HistoryPage.css'; // 引入新的CSS文件

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const { Option } = Select;

const StatCard = ({ value, label }) => (
  <div className="stat">
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
  </div>
);

function HistoryPage() {
  // 为不同类型的数据创建独立的 state
  const [submissions, setSubmissions] = useState([]);
  const [papers, setPapers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('submissions'); // 'submissions' or 'papers'
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [order, setOrder] = useState('desc');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [deletingItemId, setDeletingItemId] = useState(null);
  const navigate = useNavigate();

  const fetchHistory = useCallback(async (forceRefresh = false) => {
    // 检查是否已有缓存
    if (!forceRefresh) {
      if (activeTab === 'submissions' && submissions.length > 0) {
        console.log('使用缓存的提交记录');
        return;
      }
      if (activeTab === 'papers' && papers.length > 0) {
        console.log('使用缓存的试卷库');
        return;
      }
    }

    setLoading(true);
    setError(null);
    const endpoint = activeTab === 'submissions' ? '/history/' : '/history_test_papers';
    const url = `${API_URL}${endpoint}`;

    const params = new URLSearchParams({
      search: searchTerm,
      sort_by: sortBy,
      order: order,
    });

    try {
      console.log(`正在从 ${url}?${params.toString()} 获取数据`);
      const response = await fetch(`${url}?${params.toString()}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`获取历史记录失败: ${response.status} ${response.statusText} - ${errorData.detail || JSON.stringify(errorData)}`);
      }
      const data = await response.json();
      // 根据当前 tab 更新对应的 state
      if (activeTab === 'submissions') {
        setSubmissions(data);
      } else {
        setPapers(data);
      }
    } catch (err) {
      console.error('获取历史记录时出错:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [activeTab, searchTerm, sortBy, order, submissions.length, papers.length]);

  // 切换 tab 或排序条件时触发数据获取
  useEffect(() => {
    fetchHistory();
  }, [activeTab, sortBy]);

  // 按下回车键时手动触发搜索（强制刷新）
  const handleSearch = () => {
    // 清空当前tab的缓存以强制重新获取
    if (activeTab === 'submissions') {
      setSubmissions([]);
    } else {
      setPapers([]);
    }
    fetchHistory(true);
  };

  const handleDelete = async (id, deletePaper = false) => {
    const url = activeTab === 'submissions'
      ? `${API_URL}/history/${id}?delete_paper=${deletePaper}`
      : `${API_URL}/history_test_papers/${id}`;

    try {
      const response = await fetch(url, { method: 'DELETE' });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`删除失败: ${response.status} - ${errorData.detail || '服务器内部错误'}`);
      }
      message.success('删除成功');
      // 删除成功后强制刷新数据
      fetchHistory(true);
    } catch (err) {
      setError(err.message);
      message.error(`删除失败: ${err.message}`);
    }
  };

  const handleAttemptDelete = (item) => {
    if (activeTab === 'submissions') {
      const submissionCount = submissions.filter(h => h.test_paper_id === item.test_paper_id).length;
      if (submissionCount === 1) {
        setDeletingItemId(item.id);
        setIsModalVisible(true);
      } else {
        Popconfirm.confirm({
          title: '确定要删除这份提交记录吗？',
          content: '此操作不可撤销。',
          onConfirm: () => handleDelete(item.id, false),
          okText: '确认删除',
          cancelText: '取消',
        });
      }
    } else { // 'papers' tab
      handleDelete(item.id);
    }
  };

  const handleModalOk = (deletePaper) => {
    handleDelete(deletingItemId, deletePaper);
    setIsModalVisible(false);
    setDeletingItemId(null);
  };



  return (
    <div className="history-container">
      <header className="history-header">
        <h1>学习历史</h1>
        <p>在这里回顾您所有的提交记录和试卷模板。</p>
      </header>

      <div className="tab-controls">
        <Button
          type={activeTab === 'submissions' ? 'primary' : 'default'}
          onClick={() => setActiveTab('submissions')}
        >
          提交历史
        </Button>
        <Button
          type={activeTab === 'papers' ? 'primary' : 'default'}
          onClick={() => setActiveTab('papers')}
        >
          试卷库
        </Button>
      </div>

      <div className="history-controls">
        <Input
          placeholder="按试卷名称搜索..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onPressEnter={handleSearch} // 修改为手动触发函数
          style={{ width: 240, marginRight: 8 }}
          prefix={<SearchOutlined />}
        />
        <Select value={sortBy} onChange={setSortBy} style={{ width: 120, marginRight: 8 }}>
          <Option value="created_at">按日期</Option>
          <Option value="name">按名称</Option>
        </Select>
        <Select value={order} onChange={setOrder} style={{ width: 120 }}>
          <Option value="desc">降序</Option>
          <Option value="asc">升序</Option>
        </Select>
      </div>

      {loading && <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}><Spin size="large" tip="加载中..." /></div>}
      {error && <Alert message="加载出错" description={error} type="error" showIcon />}

      {activeTab === 'papers' && !loading && !error && (
        papers.length > 0 ? (
          <div className="history-grid">
            {papers.map(paper => (
              <div key={paper.id} className="history-card paper-card">
                <div className="card-content">
                  <div className="card-header">
                    <h2>{paper.name}</h2>
                    <p className="card-date">创建于: {new Date(paper.created_at).toLocaleString()}</p>
                  </div>
                  <div className="card-stats">
                    <StatCard label="客观题" value={paper.total_objective_questions || 0} />
                    <StatCard label="主观题" value={paper.total_essay_questions || 0} />
                  </div>
                </div>
                <div className="card-actions">
                  <Button type="text" icon={<EyeOutlined />} onClick={() => navigate(`/testpaper/${paper.id}`)}>
                    查看详情
                  </Button>
                  <Popconfirm
                    title="确定要删除这份试卷吗？"
                    description="这将删除所有相关的提交记录，此操作不可撤销。"
                    onConfirm={() => handleDelete(paper.id)}
                    okText="确认删除"
                    cancelText="取消"
                  >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                      删除
                    </Button>
                  </Popconfirm>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state"><p>暂无试卷模板</p></div>
        )
      )}

      {activeTab === 'submissions' && !loading && !error && submissions.length > 0 ? (
        <div className="history-grid"> {/* 使用 grid 布局以保持一致性 */}
          {submissions.map(item => (
            <div key={item.id} className="history-card submission-card">
              <div className="card-content">
                <div className="card-header">
                  <h2 onClick={() => navigate(`/history/${item.id}`)}>
                    {item.test_paper?.name || `提交记录 #${item.id}`}
                  </h2>
                  <p className="card-date">提交于: {new Date(item.created_at).toLocaleString()}</p>
                </div>
                <div className="card-stats">
                  <StatCard
                    label="客观题正确率"
                    value={`${item.correct_objective_questions ?? 'N/A'} / ${item.test_paper?.total_objective_questions || 0}`}
                  />
                  <StatCard 
                    label="论述题总数" 
                    value={`${item.test_paper?.total_essay_questions ?? 'N/A'}`} 
                  />
                </div>
              </div>
              <div className="card-actions">
                <Button type="text" icon={<EyeOutlined />} onClick={() => navigate(`/history/${item.id}`)}>
                  查看
                </Button>
                <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleAttemptDelete(item)}>
                  删除
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : !loading && !error && (
        <div className="no-history-container">
          <h2>暂无历史记录</h2>
          <p>当您生成第一份试卷后，这里将记录您的学习旅程。</p>
          <Link to="/" className="go-to-generate-btn">
            去生成第一份试卷
          </Link>
        </div>
      )}

      <Modal
        title="删除确认"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="back" onClick={() => setIsModalVisible(false)}>
            取消
          </Button>,
          <Button key="submit" type="primary" danger onClick={() => handleModalOk(true)}>
            删除提交记录和试卷
          </Button>,
          <Button key="link" type="primary" onClick={() => handleModalOk(false)}>
            仅删除提交记录
          </Button>,
        ]}>
        <p>这是与该试卷关联的最后一份提交记录。</p>
        <p>您想同时删除试卷模板吗？</p>
      </Modal>

      <Link to="/" className="history-back-link">← 返回出题表单</Link>
    </div>
  );
}

export default HistoryPage;