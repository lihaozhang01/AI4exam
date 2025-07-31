// TestStreamingPage.jsx
import React, { useState, useEffect, useRef } from 'react'; // 重新引入 useRef
import { Spin, Alert, Button, Typography, message, Card } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import useTestStore from './store/useTestStore';
import MultipleChoiceQuestion from './components/MultipleChoiceQuestion';
import FillInTheBlankQuestion from './components/FillInTheBlankQuestion';
import EssayQuestion from './components/EssayQuestion';
import SingleChoiceQuestion from './components/SingleChoiceQuestion';
import './TestStreamingPage.css';

const { Title, Paragraph } = Typography;

const TestStreamingPage = () => {
  const navigate = useNavigate();
  const { test_id } = useParams();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // ✅ 最终修复：使用 useRef 来确保 Effect 只在开发环境的严格模式下运行一次
  const effectRan = useRef(false);

  // State selection and derived variables are correct.
  const streamQuestions = useTestStore((state) => state.streamQuestions);
  const isStreamLoading = useTestStore((state) => state.isStreamLoading);
  const isStreamCompleted = useTestStore((state) => state.isStreamCompleted);
  const streamError = useTestStore((state) => state.streamError);
  const streamMetadata = useTestStore((state) => state.streamMetadata);
  const processStreamResponse = useTestStore((state) => state.processStreamResponse);
  const reset = useTestStore((state) => state.reset);
  const questionCount = streamQuestions.length;
  const currentQuestion = streamQuestions[currentQuestionIndex];

  // Effect #1: Data Fetching
  useEffect(() => {
    // 在开发环境中，这个判断会阻止 effect 运行第二次
    // 在生产环境中，这个判断永远是 false，effect 会正常运行一次
    if (effectRan.current === true && process.env.NODE_ENV === 'development') {
      return;
    }

    const streamTest = async () => {
      try {
        const apiKey = localStorage.getItem('apiKey');
        const headers = { 'Content-Type': 'application/json' };
        if (apiKey) headers['X-Api-Key'] = apiKey;

        const response = await fetch(`http://127.0.0.1:8000/generate-stream-test/${test_id}`, {
          method: 'GET',
          headers,
        });

        await processStreamResponse(response);
      } catch (error) {
        console.error('Fetch initiation failed:', error);
        message.error(`发起试卷请求失败: ${error.message}`);
      }
    };

    if (test_id) {
      streamTest();
    }

    // 在 effect 第一次成功执行后，立即标记
    effectRan.current = true;

  }, [test_id, processStreamResponse]); // 依赖项保持不变

  // Effect #2: Cleanup on unmount - this is correct.
  useEffect(() => {
    return () => {
      reset();
    }
  }, [reset]);

  // Keyboard navigation effect - this is correct.
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (questionCount === 0) return;
      if (event.key === 'ArrowRight') {
        setCurrentQuestionIndex((prevIndex) => Math.min(prevIndex + 1, questionCount - 1));
      } else if (event.key === 'ArrowLeft') {
        setCurrentQuestionIndex((prevIndex) => Math.max(prevIndex - 1, 0));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [questionCount]);

  const handleViewPaper = () => navigate(`/testpaper/${test_id}`);

  const renderQuestionComponent = (question, index) => {
    if (!question) return null;
    const commonProps = { question, index };
    switch (question.type) { //  <-- 修改这里
      case 'multiple_choice': return <MultipleChoiceQuestion {...commonProps} />;
      case 'fill_in_the_blank': return <FillInTheBlankQuestion {...commonProps} />;
      case 'essay': return <EssayQuestion {...commonProps} />;
      case 'single_choice': return <SingleChoiceQuestion {...commonProps} />;
      default: return <p>未知题型: {question.type}</p>; //  <-- 顺便修改这里，以便未来调试
    }
  };

  return (
    <div className="test-streaming-page">
      {isStreamLoading && !currentQuestion && <Spin tip="正在生成首道题目..." size="large" fullscreen />}
      {streamError && <Alert message="错误" description={streamError} type="error" showIcon closable />}

      {streamMetadata && (
        <header className="test-header">
          <Title level={2}>{streamMetadata.title}</Title>
          <Paragraph>{streamMetadata.description}</Paragraph>
        </header>
      )}

      <div className="question-display-area">
        {/* ✅ 调试信息：在渲染时打印出判断条件 */}
        {(() => {
          console.log('%c[RENDER LOGIC] Evaluating... currentQuestion exists:', 'color: purple', !!currentQuestion, 'isStreamCompleted:', isStreamCompleted);
        })()}

        {currentQuestion ? (
          <Card
            title={`第 ${currentQuestionIndex + 1} 题`}
            bordered={false}
            key={currentQuestionIndex}
          >
            {renderQuestionComponent(currentQuestion, currentQuestionIndex)}
          </Card>
        ) : (
          isStreamCompleted ? (
            <Alert message={`错误：无法加载第 ${currentQuestionIndex + 1} 题。`} type="error" />
          ) : (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
              <p style={{ marginTop: '16px' }}>正在加载第 {currentQuestionIndex + 1} 题...</p>
            </div>
          )
        )}
      </div>

      <div className="navigation-footer">
        <div className="nav-buttons">
          <Button onClick={() => setCurrentQuestionIndex(p => Math.max(p - 1, 0))} disabled={currentQuestionIndex === 0}>
            上一题
          </Button>
          <span className="nav-text">
            第 {currentQuestionIndex + 1} / {questionCount} 题
            {isStreamLoading && !isStreamCompleted && ' (加载中...)'}
          </span>
          <Button onClick={() => setCurrentQuestionIndex(p => Math.min(p + 1, questionCount - 1))} disabled={currentQuestionIndex >= questionCount - 1 || questionCount === 0}>
            下一题
          </Button>
        </div>

        {isStreamCompleted && (
          <Button type="primary" size="large" onClick={handleViewPaper}>
            查看完整试卷
          </Button>
        )}
      </div>
    </div>
  );
};

export default TestStreamingPage;