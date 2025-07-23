import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Input, Button, Upload, message, InputNumber, Spin } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import axios from 'axios';
import useTestStore from './store/useTestStore';
import SettingsModal from './components/SettingsModal';
import './TestFormPage.css'; // 引入新的CSS文件

const { TextArea } = Input;

// 题型配置
const QUESTION_TYPES_CONFIG = {
  single_choice: { label: '单选题', default: 5 },
  multiple_choice: { label: '多选题', default: 3 },
  fill_in_the_blank: { label: '填空题', default: 5 },
  essay: { label: '简答题', default: 2 },
};

const TestFormPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [fileList, setFileList] = useState([]);
  const [questionQuantities, setQuestionQuantities] = useState({
    single_choice: 5,
    multiple_choice: 3,
    fill_in_the_blank: 5,
    essay: 2,
  });

  const { setIsLoading, setTestData, isLoading } = useTestStore();
  const navigate = useNavigate();

  useEffect(() => {
    const storedApiKey = localStorage.getItem('api_key');
    if (storedApiKey) {
      setApiKey(storedApiKey);
    } else {
      setIsModalOpen(true); // 如果没有key，则自动弹出
    }
  }, []);

  const handleQuantityChange = (type, value) => {
    setQuestionQuantities(prev => ({ ...prev, [type]: value }));
  };

  const onFinish = async () => {
    if (!sourceText && fileList.length === 0) {
      message.error('请提供知识源，可以是文本或文件。');
      return;
    }

    setIsLoading(true);

    try {
      const question_config = Object.entries(questionQuantities)
        .filter(([, count]) => count > 0) // 过滤掉数量为0的题型
        .map(([type, count]) => ({ type, count }));

      if (question_config.length === 0) {
        message.error('请至少选择一种题型并设置数量大于0！');
        setIsLoading(false);
        return;
      }

      const config = {
        description: "由AI智能试卷助手生成",
        question_config,
        difficulty: "medium"
      };

      const formData = new FormData();
      if (fileList.length > 0) {
        formData.append('source_file', fileList[0].originFileObj);
      } else {
        formData.append('source_text', sourceText);
      }
      formData.append('config_json', JSON.stringify(config));

      if (!apiKey) {
        message.error('请先在设置中填写您的API Key！');
        setIsModalOpen(true);
        setIsLoading(false);
        return;
      }

      const apiProvider = localStorage.getItem('api_provider') || 'google';
      const generationModel = localStorage.getItem('generation_model') || (apiProvider === 'google' ? 'gemini-pro' : 'gpt-3.5-turbo');
      const generationPrompt = localStorage.getItem('generation_prompt') || '';

      const headers = {
        'Content-Type': 'multipart/form-data',
        'X-Api-Key': apiKey,
        'X-Provider': apiProvider,
        'X-Generation-Model': generationModel
      };

      if (generationPrompt) {
        headers['X-Generation-Prompt'] = generationPrompt;
      }

      const response = await axios.post('http://127.0.0.1:8000/generate-test', formData, { headers });

      setTestData(response.data);
      message.success('试卷生成成功！正在跳转...');

      navigate(`/testpaper/${response.data.test_id}`);

    } catch (error) {
      console.error("API Error:", error);
      message.error(error.response?.data?.detail || '生成试卷失败，请检查API Key或联系管理员。');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = ({ fileList: newFileList }) => {
    setFileList(newFileList);
    if (newFileList.length > 0) {
      setSourceText(''); // 如果上传了文件，清空文本输入
    }
  };

  const handleTextChange = (e) => {
    setSourceText(e.target.value);
    if (e.target.value) {
      setFileList([]); // 如果输入了文本，清空文件列表
    }
  }

  return (
    <div className="container" style={{ margin: '0 auto' }}>
      <header>
        <h1>AI 试卷助手</h1>
        <p>输入知识，静待佳题</p>
      </header>

      <main className="main-card">
        <Spin spinning={isLoading} tip="正在生成中，请稍候..." size="large">
          {/* 知识源 */}
          <section className="section">
            <h2 className="section-title">知识源</h2>
            <div className="knowledge-source">
              <TextArea
                value={sourceText}
                onChange={handleTextChange}
                placeholder="在此处粘贴文本、教学大纲或相关知识点..."
                rows={6}
              />
              <div className="upload-section">
                <span>或</span>
                <Upload
                  fileList={fileList}
                  onChange={handleFileChange}
                  beforeUpload={() => false} // 不自动上传
                  maxCount={1}
                  showUploadList={false}
                >
                  <a href="#" style={{ color: 'var(--accent-color)', textDecoration: 'none' }}> 上传文件 </a>
                </Upload>
                <span>(PDF, DOCX, TXT)</span>
              </div>
              {fileList.length > 0 && (
                <div>已选择文件：{fileList[0].name}</div>
              )}
            </div>
          </section>

          {/* 题型设置 */}
          <section className="section">
            <h2 className="section-title">题型设置</h2>
            <div className="question-selection">
              {Object.entries(QUESTION_TYPES_CONFIG).map(([type, { label }]) => (
                <div className="question-type" key={type}>
                  <label htmlFor={type}>{label}</label>
                  <InputNumber
                    id={type}
                    className="quantity-input"
                    min={0}
                    value={questionQuantities[type]}
                    onChange={(value) => handleQuantityChange(type, value)}
                    aria-label={`${label}数量`}
                  />
                </div>
              ))}
            </div>
          </section>

          {/* 生成按钮 */}
          <section className="action-bar">
            <Button className="generate-btn" onClick={onFinish} disabled={isLoading}>
              一键生成
            </Button>
          </section>
        </Spin>
      </main>

      <Link to="/history" className="history-link">查看历史试卷 →</Link>

      <SettingsModal
        isVisible={isModalOpen}
        onOk={() => setIsModalOpen(false)}
        onCancel={() => setIsModalOpen(false)}
      />

      <Button
        className="settings-btn"
        icon={<SettingOutlined />}
        onClick={() => setIsModalOpen(true)}
      />

    </div>
  );
};

export default TestFormPage;