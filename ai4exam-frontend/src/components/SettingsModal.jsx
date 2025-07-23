import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, message, Select, Form, Spin, Tabs, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TabPane } = Tabs;

const SettingsModal = ({ isVisible, onOk, onCancel }) => {
  const [form] = Form.useForm();
  const [apiKey, setApiKey] = useState('');
  const [apiProvider, setApiProvider] = useState('google');
  const [isTesting, setIsTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown'); // unknown, success, error
  const [prompts, setPrompts] = useState({ generation: '', evaluation: '' });

  useEffect(() => {
    const storedApiKey = localStorage.getItem('api_key');
    const storedProvider = localStorage.getItem('api_provider');

    if (isVisible) {
      form.setFieldsValue({
        apiKey: storedApiKey || '',
        apiProvider: storedProvider || 'google',
        generationModel: localStorage.getItem('generation_model') || 'gemini-2.5-pro',
        evaluationModel: localStorage.getItem('evaluation_model') || 'gemini-2.5-pro',
      });
      setApiKey(storedApiKey || '');
      setApiProvider(storedProvider || 'google');
      setPrompts({
        generation: localStorage.getItem('generation_prompt') || '',
        evaluation: localStorage.getItem('evaluation_prompt') || '',
        overall_feedback: localStorage.getItem('overall_feedback_prompt') || '',
        single_question_feedback: localStorage.getItem('single_question_feedback_prompt') || ''
      });
      form.setFieldsValue({
        generationPrompt: localStorage.getItem('generation_prompt') || '',
        evaluationPrompt: localStorage.getItem('evaluation_prompt') || '',
        overallFeedbackPrompt: localStorage.getItem('overall_feedback_prompt') || '',
        singleQuestionFeedbackPrompt: localStorage.getItem('single_question_feedback_prompt') || ''
      });
    }
  }, [isVisible]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      localStorage.setItem('api_key', values.apiKey);
      localStorage.setItem('api_provider', values.apiProvider);
      localStorage.setItem('generation_model', values.generationModel);
      localStorage.setItem('evaluation_model', values.evaluationModel);
      localStorage.setItem('generation_prompt', values.generationPrompt);
      localStorage.setItem('evaluation_prompt', values.evaluationPrompt);
      localStorage.setItem('overall_feedback_prompt', values.overallFeedbackPrompt);
      localStorage.setItem('single_question_feedback_prompt', values.singleQuestionFeedbackPrompt);
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
      await axios.post('http://127.0.0.1:8000/test-api-key', {}, {
        headers: {
          'Content-Type': 'application/json',
          'X-Goog-Api-Key': values.apiKey,
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
      visible={isVisible}
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
              <Select onChange={setApiProvider}>
                <Option value="google">Google</Option>
                <Option value="siliconflow">硅基流动</Option>
                <Option value="volcengine">火山引擎</Option>
              </Select>
            </Form.Item>
            <Form.Item name="apiKey" label="API Key" rules={[{ required: true, message: '请输入API Key' }]}>
              <Input.Password placeholder="请输入您的API Key" />
            </Form.Item>
            <Form.Item name="generationModel" label="出题模型">
              {['google'].includes(apiProvider) ? (
                <Select placeholder="选择出题模型">
                  {apiProvider === 'google' && <Option value="gemini-1.5-pro">gemini-1.5-pro</Option>}
                  {apiProvider === 'google' && <Option value="gemini-1.5-flash">gemini-1.5-flash</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.0-flash">gemini-2.0-flash</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.5-pro">gemini-2.5-pro</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.5-flash">gemini-2.5-flash</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite</Option>}
                </Select>
              ) : (
                <Input placeholder="请输入模型ID，例如 Qwen/Qwen2-7B-Instruct" />
              )}
            </Form.Item>
            <Form.Item name="evaluationModel" label="点评模型">
              {['google'].includes(apiProvider) ? (
                <Select placeholder="选择点评模型">
                  {apiProvider === 'google' && <Option value="gemini-1.5-pro">gemini-1.5-pro</Option>}
                  {apiProvider === 'google' && <Option value="gemini-1.5-flash">gemini-1.5-flash</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.0-flash">gemini-2.0-flash</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.5-pro">gemini-2.5-pro</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.5-flash">gemini-2.5-flash</Option>}
                  {apiProvider === 'google' && <Option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite</Option>}
                </Select>
              ) : (
                <Input placeholder="请输入模型ID，例如 Qwen/Qwen2-7B-Instruct" />
              )}
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