// src/TestFormPage.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Upload, message, Tabs, Divider, Space, InputNumber, Tag } from 'antd';
import { UploadOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import useTestStore from './store/useTestStore'; // 引入Zustand store

const { TextArea } = Input;
const { Dragger } = Upload;

const ALL_QUESTION_TYPES = {
  single_choice: '单选题',
  multiple_choice: '多选题',
  fill_in_the_blank: '填空题',
  essay: '论述题',
};

const TestFormPage = () => {
  const [form] = Form.useForm();
  const [selectedTypes, setSelectedTypes] = useState({});

  // 从Zustand store获取函数和状态
  const { setIsLoading, setTestData, isLoading } = useTestStore();
  const navigate = useNavigate(); // 获取跳转函数

  const addQuestionType = (type) => {
    if (selectedTypes[type] !== undefined) {
      message.info('该题型已添加！'); return;
    }
    setSelectedTypes(prev => ({ ...prev, [type]: 5 }));
  };

  const removeQuestionType = (typeToRemove) => {
    setSelectedTypes(prev => {
      const newTypes = { ...prev };
      delete newTypes[typeToRemove];
      return newTypes;
    });
  };

  const handleQuantityChange = (type, value) => {
    setSelectedTypes(prev => ({ ...prev, [type]: value }));
  };

  // 核心：处理表单提交的函数
  const onFinish = async (values) => {
    if (Object.keys(selectedTypes).length === 0) {
      message.error('请至少选择一种题型！');
      return;
    }

    setIsLoading(true);

    try {
      // 1. 准备API需要的数据
      const question_config = Object.entries(selectedTypes).map(([type, count]) => ({ type, count }));
      const config = {
        description: "由AI智能试卷助手生成", // 可以增加一个描述输入框
        question_config,
        difficulty: "medium" // 难度可以后续添加一个选项
      };

      const formData = new FormData();
      // 根据用户输入，添加 source_text 或 source_file
      if (values.source_file && values.source_file.length > 0) {
        formData.append('source_file', values.source_file[0].originFileObj);
      } else if (values.source_text) {
        formData.append('source_text', values.source_text);
      } else {
        message.error('请提供知识源，可以是文本或文件。');
        setIsLoading(false);
        return;
      }

      formData.append('config_json', JSON.stringify(config));

      // 2. 调用API
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        message.error('请先在右上角设置中填写您的API Key！');
        setIsLoading(false);
        return;
      }

      const response = await axios.post('http://127.0.0.1:8000/generate-test', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Goog-Api-Key': apiKey,
        }
      });

      // 3. 将返回的数据存入全局状态
      setTestData(response.data);
      message.success('试卷生成成功！正在跳转...');

      // 4. 跳转到试卷页面
      navigate('/test');

    } catch (error) {
      console.error("API Error:", error);
      message.error('生成试卷失败，请检查API Key或联系管理员。');
    } finally {
      setIsLoading(false);
    }
  };

  // ... (组件的其余部分保持不变, 为了简洁省略)
  // ... (确保你复制的是下面的完整返回部分)
  return (
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Divider orientation="left">1. 提供知识源</Divider>
      <Tabs defaultActiveKey="1">
        <Tabs.TabPane tab="粘贴文本" key="1">
          <Form.Item name="source_text">
            <TextArea rows={10} placeholder="请在此处粘贴你需要出题的文本内容..." />
          </Form.Item>
        </Tabs.TabPane>
        <Tabs.TabPane tab="上传文件" key="2">
          <Form.Item name="source_file" valuePropName="fileList" getValueFromEvent={(e) => e && e.fileList}>
            <Dragger beforeUpload={() => false} maxCount={1}>
              <p className="ant-upload-drag-icon"><UploadOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持 .pdf, .txt, .md 等文件格式。</p>
            </Dragger>
          </Form.Item>
        </Tabs.TabPane>
      </Tabs>

      <Divider orientation="left">2. 选择并配置题型</Divider>
      <Form.Item label="点击添加你需要的题型:">
        <Space wrap>
          {Object.keys(ALL_QUESTION_TYPES).map(typeKey => (
            <Button key={typeKey} onClick={() => addQuestionType(typeKey)}>
              {ALL_QUESTION_TYPES[typeKey]}
            </Button>
          ))}
        </Space>
      </Form.Item>

      {Object.keys(selectedTypes).length > 0 && (
        <Form.Item label="设置题目数量:">
          <Space direction="vertical" style={{ width: '100%' }}>
            {Object.entries(selectedTypes).map(([type, count]) => (
              <Space key={type}>
                <Tag color="blue" style={{ width: '80px', textAlign: 'center' }}>{ALL_QUESTION_TYPES[type]}</Tag>
                <InputNumber min={1} max={20} value={count} onChange={(value) => handleQuantityChange(type, value)} />
                <span>道</span>
                <Button type="text" icon={<CloseCircleOutlined />} onClick={() => removeQuestionType(type)} danger />
              </Space>
            ))}
          </Space>
        </Form.Item>
      )}

      <Divider />

      <Form.Item>
        <Button type="primary" htmlType="submit" size="large" loading={isLoading}>
          {isLoading ? '正在生成中...' : '开始智能生成试卷'}
        </Button>
      </Form.Item>
    </Form>
  );
};

export default TestFormPage;