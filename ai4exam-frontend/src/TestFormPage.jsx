import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { App, Spin, Button, Tooltip, message } from 'antd';
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
  const [messageApi, contextHolder] = message.useMessage();
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
    const storedApiKey = localStorage.getItem('api_key');
    if (storedApiKey) {
      setApiKey(storedApiKey);
    } else {
      setIsModalOpen(true);
    }
  }, []);

  const handleGenerate = async () => {
    // 增强的知识源验证
    if (!knowledgeSource.sourceText.trim() && knowledgeSource.fileList.length === 0) {
      messageApi.error('请提供知识源，可以是文本描述或上传文件！');
      return;
    }

    const testPaperStyle = localStorage.getItem('test_paper_style') || 'traditional';
    
    // 文件大小检查（限制10MB）
    if (knowledgeSource.fileList.length > 0) {
      const file = knowledgeSource.fileList[0].originFileObj;
      if (file.size > 10 * 1024 * 1024) {
        messageApi.error('文件大小不能超过10MB，请选择较小的文件！');
        return;
      }
    }

    setIsLoading(true);

    try {
      const question_config = Object.entries(testConfig.questionQuantities)
        .filter(([, count]) => count > 0)
        .map(([type, count]) => ({ type, count }));

      if (question_config.length === 0) {
        messageApi.error('请至少选择一种题型并设置数量大于0！');
        setIsLoading(false);
        return;
      }

      // 检查题目总数是否合理
      const totalQuestions = question_config.reduce((sum, item) => sum + item.count, 0);
      if (totalQuestions > 50) {
        messageApi.warning('题目总数建议不超过50道，当前设置可能生成时间过长！');
      }

      const config = {
        description: testConfig.description.trim(),
        question_config,
        difficulty: testConfig.difficulty,
      };

      const formData = new FormData();
      if (knowledgeSource.fileList.length > 0) {
        formData.append('source_file', knowledgeSource.fileList[0].originFileObj);
      }
      formData.append('source_text', knowledgeSource.sourceText.trim());
      formData.append('config_json', JSON.stringify(config));

      const storedApiKey = localStorage.getItem('api_key');
      if (!storedApiKey) {
        messageApi.error('请先在设置中填写您的API Key！');
        setIsModalOpen(true);
        setIsLoading(false);
        return;
      }

      // API Key格式验证
      if (storedApiKey.length < 10) {
        messageApi.error('API Key格式不正确，请检查您的API Key是否完整！');
        setIsModalOpen(true);
        setIsLoading(false);
        return;
      }

      const apiProvider = localStorage.getItem('api_provider') || 'google';
      const generationModel = localStorage.getItem('generation_model') || '';

      // 增强的模型验证逻辑
      const providersRequireModel = ['siliconflow', 'openai', 'anthropic', 'zhipuai', 'deepseek'];
      if (providersRequireModel.includes(apiProvider) && !generationModel.trim()) {
        messageApi.error(`当前选择的服务商 "${apiProvider}" 需要指定一个生成模型，请在设置中配置！`);
        setIsModalOpen(true);
        setIsLoading(false);
        return;
      }

      // 检查网络连接
      if (!navigator.onLine) {
        messageApi.error('网络连接已断开，请检查您的网络连接！');
        setIsLoading(false);
        return;
      }

      const generationPrompt = localStorage.getItem('generation_prompt') || '';

      const headers = {
        'Content-Type': 'multipart/form-data',
        'X-Api-Key': storedApiKey.trim(),
        'X-Provider': apiProvider,
        'X-Generation-Model': generationModel.trim(),
      };

      if (generationPrompt.trim()) {
        headers['X-Generation-Prompt'] = encodeURIComponent(generationPrompt.trim());
      }

      if (testPaperStyle === 'card') {
        // 卡片模式，先创建试卷条目，然后跳转到流式页面
        try {
          const response = await axios.post('http://127.0.0.1:8000/tests', formData, { headers });
          const test_id = response.data.test_id;
          messageApi.success('正在准备生成试卷...');
          navigate(`/test-streaming/${test_id}`);
        } catch (error) {
          console.error("API Error during test creation:", error);
          
          // 增强的错误提示
          let errorMessage = '创建试卷失败';
          if (error.response?.status === 401) {
            errorMessage = 'API Key无效或已过期，请检查您的API Key！';
          } else if (error.response?.status === 429) {
            errorMessage = '请求过于频繁，请稍后再试！';
          } else if (error.response?.status === 400) {
            errorMessage = error.response?.data?.detail || '请求参数有误，请检查输入内容！';
          } else if (error.code === 'ECONNREFUSED') {
            errorMessage = '无法连接到服务器，请检查服务器是否运行！';
          } else if (!navigator.onLine) {
            errorMessage = '网络连接已断开，请检查您的网络！';
          } else {
            errorMessage = error.response?.data?.detail || '服务器繁忙，请稍后再试！';
          }
          
          messageApi.error(errorMessage);
        }
      } else {
        // 传统模式，调用普通接口
        try {
          const response = await axios.post('http://127.0.0.1:8000/generate-test', formData, { headers });
          setTestData(response.data);
          messageApi.success('试卷生成成功！正在跳转...');
          navigate(`/testpaper/${response.data.test_id}`);
        } catch (error) {
          console.error("API Error:", error);
          
          // 增强的错误提示
          let errorMessage = '生成试卷失败';
          if (error.response?.status === 401) {
            errorMessage = 'API Key无效或已过期，请检查您的API Key！';
          } else if (error.response?.status === 429) {
            errorMessage = '请求过于频繁，请稍后再试！';
          } else if (error.response?.status === 400) {
            errorMessage = error.response?.data?.detail || '请求参数有误，请检查输入内容！';
          } else if (error.response?.status === 413) {
            errorMessage = '上传的文件过大，请选择较小的文件！';
          } else if (error.code === 'ECONNREFUSED') {
            errorMessage = '无法连接到服务器，请检查服务器是否运行！';
          } else if (!navigator.onLine) {
            errorMessage = '网络连接已断开，请检查您的网络！';
          } else if (error.response?.status >= 500) {
            errorMessage = '服务器内部错误，请稍后再试！';
          } else {
            errorMessage = error.response?.data?.detail || '生成试卷失败，请稍后再试！';
          }
          
          messageApi.error(errorMessage);
        }
      }
    } catch (error) {
      console.error("Unexpected Error:", error);
      messageApi.error('发生未知错误，请刷新页面后重试！');
    } finally {
      setIsLoading(false);
    }
  };

  const handleHistoryClick = () => {
    navigate('/history');
  };

  return (
    <div className="container">
      {contextHolder}
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