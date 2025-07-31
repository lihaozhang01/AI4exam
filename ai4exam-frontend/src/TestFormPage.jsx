import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Button, Tooltip } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import axios from 'axios';
import useTestStore from './store/useTestStore';
import SettingsModal from './components/TestForm/SettingsModal';
import PageHeader from './components/TestForm/PageHeader';
import KnowledgeSourceForm from './components/TestForm/KnowledgeSourceForm';
import TestConfigForm from './components/TestForm/TestConfigForm';
import ActionButtons from './components/TestForm/ActionButtons';
import './TestFormPage.css';
import snowLeopardIcon from './assets/knowledge_bao.png'; // 导入图片

const TestFormPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [knowledgeSource, setKnowledgeSource] = useState({
    sourceText: '',
    fileList: [],
  });
  const [testConfig, setTestConfig] = useState({
    description: '',
    difficulty: 'medium',
    questionQuantities: {
      single_choice: 5,
      multiple_choice: 0,
      fill_in_the_blank: 0,
      essay: 0,
    },
  });

  const { setIsLoading, setTestData, isLoading } = useTestStore();
  const navigate = useNavigate();

  useEffect(() => {
    const storedApiKey = localStorage.getItem('apiKey');
    if (storedApiKey) {
      setApiKey(storedApiKey);
    } else {
      setIsModalOpen(true);
    }
  }, []);

  const handleGenerate = async () => {
    const testPaperStyle = localStorage.getItem('test_paper_style') || 'traditional';
    if (!knowledgeSource.sourceText && knowledgeSource.fileList.length === 0) {
      message.error('请提供知识源，可以是文本或文件。');
      return;
    }

    setIsLoading(true);

    try {
      const question_config = Object.entries(testConfig.questionQuantities)
        .filter(([, count]) => count > 0)
        .map(([type, count]) => ({ type, count }));

      if (question_config.length === 0) {
        message.error('请至少选择一种题型并设置数量大于0！');
        setIsLoading(false);
        return;
      }

      const config = {
        description: testConfig.description,
        question_config,
        difficulty: testConfig.difficulty,
      };

      const formData = new FormData();
      if (knowledgeSource.fileList.length > 0) {
        formData.append('source_file', knowledgeSource.fileList[0].originFileObj);
      }
      // Always append source_text, even if it's an empty string, to match backend logic
      formData.append('source_text', knowledgeSource.sourceText);
      formData.append('config_json', JSON.stringify(config));

      const storedApiKey = localStorage.getItem('apiKey');
      if (!storedApiKey) {
        message.error('请先在设置中填写您的API Key！');
        setIsModalOpen(true);
        setIsLoading(false);
        return;
      }

      const apiProvider = localStorage.getItem('api_provider') || 'google';
      const generationModel = localStorage.getItem('generation_model');
      const generationPrompt = localStorage.getItem('generation_prompt') || '';

      const headers = {
        'Content-Type': 'multipart/form-data',
        'X-Api-Key': storedApiKey,
        'X-Provider': apiProvider,
        'X-Generation-Model': generationModel,
      };

      if (generationPrompt) {
        headers['X-Generation-Prompt'] = encodeURIComponent(generationPrompt);
      }

      if (testPaperStyle === 'card') {
        // 卡片模式，先创建试卷条目，然后跳转到流式页面
        try {
          const response = await axios.post('http://127.0.0.1:8000/tests', formData, { headers });
          const test_id = response.data.test_id;
          message.success('正在准备生成试卷...');
          navigate(`/test-streaming/${test_id}`);
        } catch (error) {
          console.error("API Error during test creation:", error);
          message.error(error.response?.data?.detail || '创建试卷失败，请检查网络或联系管理员。');
        }
      } else {
        // 传统模式，调用普通接口
        const response = await axios.post('http://127.0.0.1:8000/generate-test', formData, { headers });
        setTestData(response.data);
        message.success('试卷生成成功！正在跳转...');
        navigate(`/testpaper/${response.data.test_id}`);
      }
    } catch (error) {
      console.error("API Error:", error);
      message.error(error.response?.data?.detail || '生成试卷失败，请检查API Key或联系管理员。');
    } finally {
      setIsLoading(false);
    }
  };

  const handleHistoryClick = () => {
    navigate('/history');
  };

  return (
    <div className="container">
      <a className="history-link" onClick={handleHistoryClick}>
        查看历史试卷→
      </a>

      <main className="main-card">
        {/* 将 PageHeader 移入 main-card 内部 */}
        <PageHeader />
        <Spin spinning={isLoading} tip="正在生成中，请稍候..." size="large">
          <div className="form-container">
            <KnowledgeSourceForm
              source={knowledgeSource}
              onSourceChange={setKnowledgeSource}
            />
            <TestConfigForm
              config={testConfig}
              onConfigChange={setTestConfig}
            />
          </div>
        </Spin>
        <ActionButtons
          onGenerate={handleGenerate}
          loading={isLoading}
        />
      </main>

      <Tooltip title="设置">
        <Button
          icon={<SettingOutlined />}
          className="settings-page-button"
          onClick={() => setIsModalOpen(true)}
        />
      </Tooltip>

      <SettingsModal
        isOpen={isModalOpen}
        onOk={() => setIsModalOpen(false)}
        onCancel={() => setIsModalOpen(false)}
      />

      {/* 彩蛋：知识雪豹 */}
      <div className="easter-egg-container">
        <div className="snow-leopard-icon">
          <img src={snowLeopardIcon} alt="知识学爆" style={{ width: '100px', height: '100px' }} />
        </div>
        <span className="easter-egg-text">知识学爆</span>
      </div>
    </div>
  );
};

export default TestFormPage;