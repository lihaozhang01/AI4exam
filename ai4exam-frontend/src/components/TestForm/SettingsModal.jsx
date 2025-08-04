import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, message, Select, Form, Spin, Tabs, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TabPane } = Tabs;

const SettingsModal = ({ isOpen, onOk, onCancel }) => {
  const [form] = Form.useForm();
  const [apiKey, setApiKey] = useState('');
  const [apiProvider, setApiProvider] = useState('google');

  const handleProviderChange = (value) => {
    setApiProvider(value);
    form.setFieldsValue({
      generation_model: '',
      evaluation_model: '',
    });
    // Also clear the values in localStorage immediately
    localStorage.setItem('generation_model', '');
    localStorage.setItem('evaluation_model', '');
  };
  const [isTesting, setIsTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown'); // unknown, success, error
  const [prompts, setPrompts] = useState({ generation: '', evaluation: '' });

  useEffect(() => {
    const storedApiKey = localStorage.getItem('api_key');
    const storedProvider = localStorage.getItem('api_provider');

    if (isOpen) {
      form.setFieldsValue({
        apiKey: storedApiKey || '',
        apiProvider: storedProvider || 'google',
        generation_model: localStorage.getItem('generation_model') || '',
        evaluation_model: localStorage.getItem('evaluation_model') || '',
        testPaperStyle: localStorage.getItem('test_paper_style') || 'classic',
      });
      setApiKey(storedApiKey || '');
      setApiProvider(storedProvider || 'google');
      form.setFieldsValue({
        generationPrompt: localStorage.getItem('generationPrompt') || '',
        evaluationPrompt: localStorage.getItem('evaluationPrompt') || '',
        overallFeedbackPrompt: localStorage.getItem('overallFeedbackPrompt') || '',
        singleQuestionFeedbackPrompt: localStorage.getItem('singleQuestionFeedbackPrompt') || ''
      });
    }
  }, [isOpen]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      localStorage.setItem('api_key', values.apiKey);
      localStorage.setItem('api_provider', values.apiProvider);
      localStorage.setItem('generation_model', values.generation_model);
      localStorage.setItem('evaluation_model', values.evaluation_model);
      localStorage.setItem('test_paper_style', values.testPaperStyle);
      localStorage.setItem('generationPrompt', values.generationPrompt);
      localStorage.setItem('evaluationPrompt', values.evaluationPrompt);
      localStorage.setItem('overallFeedbackPrompt', values.overallFeedbackPrompt);
      localStorage.setItem('singleQuestionFeedbackPrompt', values.singleQuestionFeedbackPrompt);

      message.success('设置已保存！');
      onOk();
    } catch (error) {
      console.log('Validate Failed:', error);
    }
  };

  const handleTestConnection = async () => {
    const values = await form.getFieldsValue();
    if (!values.apiKey) {
      message.error('请输入API Key');
      return;
    }
    setIsTesting(true);
    setConnectionStatus('unknown');
    try {
      // 发送 POST 请求到后端 /test-connectivity 端点
      // 请求体中包含 generationModel，用于测试连接
      // 请求头中包含 API Key 和提供商
      await axios.post('http://127.0.0.1:8000/test-connectivity',
        { model_name: values.generation_model }, // 在请求体中发送模型名称
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Api-Key': values.apiKey,
            'X-Provider': values.apiProvider
          }
        });
      message.success('API Key 有效！');
      setConnectionStatus('success');
    } catch (error) {
      message.error(error.response?.data?.detail || 'API Key 无效或网络错误');
      setConnectionStatus('error');
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <Modal
      title="设置"
      open={isOpen}
      onOk={handleOk}
      onCancel={onCancel}
      footer={[
        <Button key="back" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" onClick={handleOk}>
          保存
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical" name="settings_form">
        <Tabs defaultActiveKey="1">
          <TabPane tab="API 设置" key="1">
            <Form.Item name="apiProvider" label="API 提供商">
              <Select onChange={handleProviderChange}>
                <Option value="google">Google</Option>
                <Option value="siliconflow">硅基流动</Option>
                <Option value="deepseek">Deepseek</Option>
                <Option value="aliyun">阿里云</Option>
              </Select>
            </Form.Item>
            <Form.Item name="apiKey" label="API Key" rules={[{ required: true, message: '请输入API Key' }]}>
              <Input.Password placeholder="请输入您的API Key" />
            </Form.Item>
            <Form.Item name="generation_model" label="出题模型">
              {apiProvider === 'google' ? (
                <Select placeholder="选择出题模型">
                  <Option value="gemini-1.5-flash">gemini-1.5-flash</Option>
                  <Option value="gemini-1.5-pro">gemini-1.5-pro</Option>
                  <Option value="gemini-2.0-flash">gemini-2.0-flash</Option>
                  <Option value="gemini-2.0-pro">gemini-2.0-pro</Option>
                  <Option value="gemini-2.5-flash">gemini-2.5-flash</Option>
                  <Option value="gemini-2.5-pro">gemini-2.5-pro</Option>
                </Select>
              ) : apiProvider === 'deepseek' ? (
                <Select placeholder="选择Deepseek模型">
                  <Option value="deepseek-chat">Deepseek V3</Option>
                  <Option value="deepseek-reasoner">Deepseek R1</Option>
                </Select>
              ) : (
                <Input placeholder="请参考模型提供商要求输入模型ID" />
              )}
            </Form.Item>
            <Form.Item name="evaluation_model" label="点评模型">
              {apiProvider === 'google' ? (
                <Select placeholder="选择点评模型">
                  <Option value="gemini-1.5-flash">gemini-1.5-flash</Option>
                  <Option value="gemini-1.5-pro">gemini-1.5-pro</Option>
                  <Option value="gemini-2.0-flash">gemini-2.0-flash</Option>
                  <Option value="gemini-2.0-pro">gemini-2.0-pro</Option>
                  <Option value="gemini-2.5-flash">gemini-2.5-flash</Option>
                  <Option value="gemini-2.5-pro">gemini-2.5-pro</Option>
                </Select>
              ) : apiProvider === 'deepseek' ? (
                <Select placeholder="选择Deepseek模型">
                  <Option value="deepseek-chat">Deepseek V3</Option>
                  <Option value="deepseek-reasoner">Deepseek R1</Option>
                </Select>
              ) : (
                    <Input placeholder="请参考模型提供商要求输入模型ID" />
              )}

            </Form.Item>

            <Form.Item name="testPaperStyle" label="试卷样式">
              <Select placeholder="选择试卷样式">
                <Option value="classic">传统模式</Option>
                <Option value="card">卡片模式</Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Button onClick={handleTestConnection} loading={isTesting}>
                测试连通性
              </Button>
              {connectionStatus === 'success' && <Tag icon={<CheckCircleOutlined />} color="success">连接成功</Tag>}
              {connectionStatus === 'error' && <Tag icon={<CloseCircleOutlined />} color="error">连接失败</Tag>}
            </Form.Item>
          </TabPane>
          <TabPane tab="提示词设置" key="2">
            <Form.Item name="generationPrompt" label="出题提示词">
              <Input.TextArea rows={4} placeholder="留空则使用默认提示词" />
            </Form.Item>
            <Form.Item name="evaluationPrompt" label="简答题点评提示词">
              <Input.TextArea rows={4} placeholder="留空则使用默认提示词" />
            </Form.Item>
            <Form.Item name="overallFeedbackPrompt" label="整体反馈提示词">
              <Input.TextArea rows={4} placeholder="留空则使用默认提示词" />
            </Form.Item>
            <Form.Item name="singleQuestionFeedbackPrompt" label="单题反馈提示词">
              <Input.TextArea rows={4} placeholder="留空则使用默认提示词" />
            </Form.Item>
          </TabPane>
        </Tabs>
      </Form>
    </Modal>
  );
};

export default SettingsModal;