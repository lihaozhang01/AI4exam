// TestStreamingPage.jsx
import React from 'react'; // 移除了 useEffect
import { Spin, Alert, Button, Typography, message, Card, Row, Col } from 'antd';
import { useNavigate } from 'react-router-dom';
import { shallow } from 'zustand/shallow';
import useTestStore from './store/useTestStore';
import MultipleChoiceQuestion from './components/MultipleChoiceQuestion';
import FillInTheBlankQuestion from './components/FillInTheBlankQuestion';
import EssayQuestion from './components/EssayQuestion';
import SingleChoiceQuestion from './components/SingleChoiceQuestion';
import './TestStreamingPage.css';

const { Title, Paragraph } = Typography;

const TestStreamingPage = () => {
  const navigate = useNavigate();

  // ✅ 从 store 中订阅所有需要展示的状态
  // 不再需要获取 processStreamResponse action
  const {
    streamMetadata,
    streamQuestions,
    isStreamLoading,
    isStreamCompleted,
    streamError,
  } = useTestStore(
    (state) => ({
      streamMetadata: state.streamMetadata,
      streamQuestions: state.streamQuestions,
      isStreamLoading: state.isStreamLoading,
      isStreamCompleted: state.isStreamCompleted,
      streamError: state.streamError,
    }),
    shallow
  );

  // 🔴 关键修复：整个 useEffect 已被移除。
  // 组件不再负责启动数据处理流程。

  const handleSavePaper = async () => {
    if (!isStreamCompleted) {
      message.warning('试卷尚未生成完毕，请稍后');
      return;
    }

    if (!streamMetadata || streamQuestions.length === 0) {
      message.error('没有可保存的试卷内容');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/tests/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Api-Key': 'your_api_key_here', // 请替换为实际的 API Key 获取方式
        },
        body: JSON.stringify({
          title: streamMetadata.title,
          description: streamMetadata.description,
          questions: streamQuestions,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP 错误！状态: ${response.status}`);
      }

      const result = await response.json();
      message.success('试卷保存成功！');
      navigate(`/testpaper/${result.id}`);
    } catch (err) {
      message.error(`保存失败: ${err.message}`);
    }
  };

  const renderQuestionComponent = (question, index) => {
    if (!question) return null;
    const commonProps = { question, index };
    switch (question.question_type) {
      case 'multiple_choice':
        return <MultipleChoiceQuestion {...commonProps} />;
      case 'fill_in_the_blank':
        return <FillInTheBlankQuestion {...commonProps} />;
      case 'essay':
        return <EssayQuestion {...commonProps} />;
      case 'single_choice':
        return <SingleChoiceQuestion {...commonProps} />;
      default:
        return <p>未知题型: {question.question_type}</p>;
    }
  };

  return (
    <div className="test-streaming-page">
      {isStreamLoading && <Spin tip="正在生成试卷..." size="large" fullscreen />}
      {streamError && <Alert message="错误" description={streamError} type="error" showIcon closable />}

      {streamMetadata && (
        <header className="test-header">
          <Title level={2}>{streamMetadata.title}</Title>
          <Paragraph>{streamMetadata.description}</Paragraph>
        </header>
      )}

      <div className="questions-container">
        <Row gutter={[16, 16]}>
          {streamQuestions.map((q, index) => (
            <Col span={24} key={index}>
              <Card title={`第 ${index + 1} 题`} bordered={false}>
                {renderQuestionComponent(q, index)}
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {isStreamCompleted && (
        <div className="actions-footer">
          <Button type="primary" size="large" onClick={handleSavePaper} disabled={!isStreamCompleted || streamQuestions.length === 0}>
            保存试卷
          </Button>
        </div>
      )}
    </div>
  );
};

export default TestStreamingPage;