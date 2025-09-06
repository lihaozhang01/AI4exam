// src/TestPaperPage.jsx

import React, { useEffect, useState, useRef } from 'react'; // 1. 引入 useRef
import { useNavigate, useParams, useSearchParams, Link, useLocation } from 'react-router-dom';
import { Empty, Button, Divider, message, Alert, Spin, Space, Switch } from 'antd';
import { UpOutlined, ExportOutlined } from '@ant-design/icons';
import axios from 'axios';
import useTestStore from './store/useTestStore';

import SingleChoiceQuestion from './components/SingleChoiceQuestion';
import MultipleChoiceQuestion from './components/MultipleChoiceQuestion';
import FillInTheBlankQuestion from './components/FillInTheBlankQuestion';
import EssayQuestion from './components/EssayQuestion';
import MarkdownRenderer from './components/MarkdownRenderer';
import OverallFeedback from './components/OverallFeedback';
import SingleQuestionFeedback from './components/SingleQuestionFeedback';
import './TestPaperPage.css';

// Helper function to build the payload for API calls
const buildAnswersPayload = (userAnswers, questions) => {
  if (!questions || !Array.isArray(questions)) {
    return [];
  }
  return Object.keys(userAnswers).map(questionId => {
    const question = questions.find(q => String(q.id) === questionId); // Robust comparison
    if (!question) {
      console.warn(`Question with id ${questionId} not found. Skipping.`);
      return null;
    }
    const answer = userAnswers[questionId];
    const basePayload = { question_id: questionId, question_type: question.type };

    switch (question.type) {
      case 'single_choice':
        return { ...basePayload, answer_index: answer };
      case 'multiple_choice':
        return { ...basePayload, answer_indices: answer || [] };
      case 'fill_in_the_blank':
        const answers = typeof answer === 'string' ? answer.split('$$$') : (answer || []);
        return { ...basePayload, answer_texts: answers };
      case 'essay':
        return { ...basePayload, answer_text: answer || "" };
      default:
        return null;
    }
  }).filter(Boolean);
};

const TestPaperPage = () => {
  const [messageApi, contextHolder] = message.useMessage(); // 1. 使用 antd 的 message hook
  const { testId, resultId } = useParams();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const {
    testData,
    setTestData,
    setTestForHistory,
    userAnswers,
    setUserAnswers,
    isLoading,
    setIsLoading,
    setGradingResults,
    resultId: storeResultId,
    gradingResults,
    overallFeedback,
    setOverallFeedback,
    submissionStatus,
    setSubmissionStatus,
    singleQuestionFeedbacks,
    setSingleQuestionFeedback,
    reset,
  } = useTestStore();

  const [originalTestId, setOriginalTestId] = useState(null);
  const [showOnlyIncorrect, setShowOnlyIncorrect] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const scrollableContentRef = useRef(null);
  const effectRan = useRef(false);

  useEffect(() => {
    if (effectRan.current === true && process.env.NODE_ENV === 'development') {
      return;
    }
    const fetchTestPaper = async (id) => {
      setIsLoading(true);
      try {
        const fromStreaming = searchParams.get('from') === 'streaming';

        const response = await axios.get(`http://127.0.0.1:8000/test-papers/${id}`);

        if (!fromStreaming) {
          reset();
        }

        const newQuestions = response.data.questions || [];
        const answersToKeep = {};

        if (fromStreaming) {
          // 从 store 获取流式答题的答案和题目
          const { userAnswers: streamAnswers, streamQuestions } = useTestStore.getState();

          // ✅ 最终解决方案：基于顺序进行答案合并
          // 遍历从API获取的新题目
          newQuestions.forEach((newQuestion, index) => {
            // 找到流式题目中对应顺序的题目
            const correspondingStreamQuestion = streamQuestions[index];
            if (correspondingStreamQuestion) {
              // 获取这个流式题目的ID (例如 'q1')
              const streamQuestionId = correspondingStreamQuestion.id;
              // 在流式答案中用这个ID查找对应的答案
              const answerForThisQuestion = streamAnswers[streamQuestionId];
              // 如果找到了答案，就把它赋给新题目的ID (例如 '123')
              if (answerForThisQuestion !== undefined) {
                answersToKeep[newQuestion.id] = answerForThisQuestion;
              }
            }
          });
        }

        // 更新状态
        setTestData(response.data);
        setUserAnswers(answersToKeep);

        // 设置其他状态
        setSubmissionStatus('in_progress');
        setGradingResults(null);
        setOverallFeedback(null);
        setSingleQuestionFeedback({});
        setOriginalTestId(id);

      } catch (error) {
        console.error("获取新试卷失败:", error.response ? error.response.data : error.message);
        messageApi.error("获取新试卷失败，请返回首页重试。" + (error.response ? `(${error.response.status})` : ''));
        navigate('/');
      } finally {
        setIsLoading(false);
      }
    };

    const fetchTestResult = async (id) => {
      // This function remains unchanged.
      setIsLoading(true);
      try {
        const response = await axios.get(`http://127.0.0.1:8000/history/${id}`);
        const result = response.data;
        const testPaperResponse = await axios.get(`http://127.0.0.1:8000/test-papers/${result.test_paper_id}`);
        setTestForHistory(testPaperResponse.data);
        const answers = result.user_answers || [];
        const formattedAnswers = {};
        answers.forEach(ans => {
          let finalAnswer;
          if (ans.answer_index !== null && ans.answer_index !== undefined) finalAnswer = ans.answer_index;
          else if (ans.answer_indices) finalAnswer = ans.answer_indices;
          else if (ans.answer_texts) finalAnswer = ans.answer_texts;
          else if (ans.answer_text) finalAnswer = ans.answer_text;
          else finalAnswer = null;
          if (finalAnswer !== null) formattedAnswers[ans.question_id] = finalAnswer;
        });
        setUserAnswers(formattedAnswers);
        setGradingResults(result.grading_results || [], id);
        if (result.overall_feedback) setOverallFeedback(result.overall_feedback);
        if (result.question_feedbacks) {
          Object.entries(result.question_feedbacks).forEach(([qId, feedback]) => {
            setSingleQuestionFeedback(qId, feedback);
          });
        }
        setSubmissionStatus('submitted_and_showing_answers');
        setOriginalTestId(result.test_paper_id);
      } catch (error) {
        console.error("获取历史试卷失败:", error.response ? error.response.data : error.message);
        messageApi.error("获取历史试卷失败，请稍后重试。" + (error.response ? `(${error.response.status})` : ''));
        navigate('/history');
      } finally {
        setIsLoading(false);
      }
    };

    if (resultId) {
      fetchTestResult(resultId);
    } else if (testId) {
      fetchTestPaper(testId);
    } else if (!testData) {
      navigate('/');
    }
    // 4. 在 effect 的末尾标记它已经运行过一次
    return () => {
      effectRan.current = true;
    }
  }, [resultId, testId, navigate, searchParams, setTestData, setTestForHistory, setUserAnswers, setIsLoading, setGradingResults, setOverallFeedback, setSubmissionStatus, setSingleQuestionFeedback, reset, location.key]);

  useEffect(() => {
    const handleScroll = () => {
      // 监听整个页面的滚动
      if (window.scrollY > 300) {
        setShowBackToTop(true);
      } else {
        setShowBackToTop(false);
      }
    };

    window.addEventListener('scroll', handleScroll);

    // 清理函数
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []); // 空依赖数组意味着这个 effect 只在组件挂载和卸载时运行一次

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth' // 平滑滚动
    });
  };

  const handleSubmitAndShowAnswers = async () => {
    // This function remains unchanged.
    setIsLoading(true);
    try {
      if (!testData || !testData.test_id) { messageApi.error("试卷信息不完整，无法提交。请返回首页重试。"); return; }
      if (!testData || !testData.questions) { messageApi.error('试卷数据加载失败，请刷新页面重试'); setIsLoading(false); return; }
      const allAnswers = buildAnswersPayload(userAnswers, testData.questions);
      const apiKey = localStorage.getItem('api_key');
      const apiProvider = localStorage.getItem('api_provider');
      const evaluationModel = localStorage.getItem('evaluation_model');
      const evaluationPrompt = localStorage.getItem('evaluationPrompt');
      if (!apiKey) { messageApi.error('请先在右上角设置中填写您的API Key！'); setIsLoading(false); return; }
      const response = await axios.post('http://127.0.0.1:8000/grade-questions', { test_id: testData.test_id, answers: allAnswers }, {
        headers: {
          'X-Api-Key': apiKey,
          'X-Provider': apiProvider,
          'X-Evaluation-Model': evaluationModel,
          'X-Evaluation-Prompt': evaluationPrompt ? encodeURIComponent(evaluationPrompt) : ''
        }
      });
      setGradingResults(response.data.results, response.data.result_id);
      setSubmissionStatus('submitted_and_showing_answers');
      navigate(`/history/${response.data.result_id}`, { replace: true });
      messageApi.success('Objective questions have been auto-graded! You can now request detailed AI feedback.');
    } catch (error) {
      console.error("Error submitting answers:", error.response ? error.response.data : error.message);
      messageApi.error("提交答案失败，请检查网络连接或稍后再试。" + (error.response ? `(${error.response.status})` : ''));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetakeTest = () => {
    if (originalTestId) {
      reset();
      navigate(`/testpaper/${originalTestId}`, { state: { key: Date.now() } });
    }
  };

  const handleExportHtml = () => {
    if (testData && testData.test_id) {
      // 打开新窗口导出HTML
      window.open(`http://127.0.0.1:8000/export/test-paper/${testData.test_id}/html`, '_blank');
      messageApi.success('试卷已导出为HTML格式');
    } else {
      messageApi.error('试卷信息不完整，无法导出');
    }
  };

  const handleRequestAiFeedback = async () => {
    // This function remains unchanged.
    setIsLoading(true);
    messageApi.info('正在请求AI对整卷进行分析，请稍候...');
    try {
      if (!testData || !testData.test_id) { messageApi.error("试卷信息不完整，无法请求分析。"); return; }
      if (!testData || !testData.questions) { messageApi.error('试卷数据加载失败，请刷新页面重试'); setIsLoading(false); return; }
      const answersToSend = buildAnswersPayload(userAnswers, testData.questions);
      const apiKey = localStorage.getItem('api_key');
      const apiProvider = localStorage.getItem('api_provider');
      const evaluationModel = localStorage.getItem('evaluation_model');
      const overallFeedbackPrompt = localStorage.getItem('overallFeedbackPrompt');
      if (!apiKey) { messageApi.error('请先在右上角设置中填写您的API Key！'); setIsLoading(false); return; }
      const currentResultId = storeResultId || resultId;
      if (!currentResultId) { messageApi.error("无法获取到试卷结果ID，请先提交答案。"); setIsLoading(false); return; }
      const response = await axios.post('http://127.0.0.1:8000/generate-overall-feedback', { result_id: parseInt(currentResultId, 10), test_id: testData.test_id, answers: answersToSend }, {
        headers: {
          'X-Api-Key': apiKey,
          'X-Provider': apiProvider,
          'X-Evaluation-Model': evaluationModel,
          'X-Overall-Feedback-Prompt': overallFeedbackPrompt ? encodeURIComponent(overallFeedbackPrompt) : ''
        }
      });
      setOverallFeedback(response.data.feedback);
      messageApi.success('AI分析完成！');
    } catch (error) {
      console.error("Error requesting AI feedback:", error.response ? error.response.data : error.message);
      messageApi.error("请求AI反馈失败，请稍后再试。" + (error.response ? `(${error.response.status})` : ''));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestSingleQuestionFeedback = async (questionId) => {
    // This function remains unchanged.
    messageApi.info(`正在为题目请求AI点评...`);
    try {
      if (!testData || !testData.questions) { messageApi.error('试卷数据加载失败，请刷新页面重试'); return; }
      const question = testData.questions.find(q => q.id === questionId);
      if (!question) { messageApi.error('题目不存在'); return; }
      let userAnswer = userAnswers[questionId];
      if (question.type === 'fill_in_the_blank' && typeof userAnswer === 'string') userAnswer = userAnswer.split('$$$');
      const apiKey = localStorage.getItem('api_key');
      const evaluationModel = localStorage.getItem('evaluation_model');
      const singleQuestionFeedbackPrompt = localStorage.getItem('singleQuestionFeedbackPrompt');
      const apiProvider = localStorage.getItem('api_provider');
      if (!apiKey) { messageApi.error('请先在新建页面的右下角设置中填写您的API Key！'); return; }
      let userAnswerPayload;
      switch (question.type) {
        case 'single_choice': userAnswerPayload = { question_type: 'single_choice', answer_index: userAnswer }; break;
        case 'multiple_choice': userAnswerPayload = { question_type: 'multiple_choice', answer_indices: userAnswer || [] }; break;
        case 'fill_in_the_blank': userAnswerPayload = { question_type: 'fill_in_the_blank', answer_texts: userAnswer || [] }; break;
        case 'essay': userAnswerPayload = { question_type: 'essay', answer_text: userAnswer || "" }; break;
        default: messageApi.error(`Unsupported question type: ${question.type}`); return;
      }
      const currentResultId = storeResultId || resultId;
      if (!currentResultId) { messageApi.error("无法获取到试卷结果ID，请先提交答案。"); return; }
      const response = await axios.post('http://127.0.0.1:8000/generate-single-question-feedback', { result_id: parseInt(currentResultId, 10), question_id: question.id, user_answer: userAnswerPayload }, {
        headers: {
          'X-Api-Key': apiKey,
          'X-Provider': apiProvider,
          'X-Evaluation-Model': evaluationModel,
          'X-Single-Question-Feedback-Prompt': singleQuestionFeedbackPrompt ? encodeURIComponent(singleQuestionFeedbackPrompt) : ''
        }
      });
      setSingleQuestionFeedback(questionId, response.data.feedback);
      messageApi.success(`该题的AI点评已生成！`);
    } catch (error) {
      console.error('Error requesting single question feedback:', error.response ? error.response.data : error.message);
      messageApi.error('请求该题反馈失败，请稍后再试。' + (error.response ? `(${error.response.status})` : ''));
    }
  };

  const renderContent = () => (
    !testData || !testData.questions ? null :
      <>
        <OverallFeedback feedback={overallFeedback} onClose={() => setOverallFeedback(null)} />
        {testData.questions
          .filter(question => {
            if (!showOnlyIncorrect || submissionStatus !== 'submitted_and_showing_answers') {
              return true; // 如果不要求只看错题，或者还没提交，则显示所有题目
            }
            const result = gradingResults?.find(r => r.question_id === question.id);
            return result && result.is_correct === false; // 只显示被标记为错误并且有批改结果的题目
          })
          .map((question, index) => (
            <div key={question.id}>
              {(() => {
                const result = gradingResults?.find(r => r.question_id === question.id);
                switch (question.type) {
                  case 'single_choice': return <SingleChoiceQuestion question={question} index={index} gradingResult={result} />;
                  case 'multiple_choice': return <MultipleChoiceQuestion question={question} index={index} gradingResult={result} />;
                  case 'fill_in_the_blank': return <FillInTheBlankQuestion question={question} index={index} gradingResult={result} />;
                  case 'essay': return <EssayQuestion question={question} index={index} gradingResult={result} />;
                  default: return <p>未知题型</p>;
                }
              })()}
              {submissionStatus === 'submitted_and_showing_answers' && (
                <SingleQuestionFeedback
                  questionId={question.id}
                  feedback={singleQuestionFeedbacks[question.id]}
                  onRequestFeedback={handleRequestSingleQuestionFeedback}
                  onClearFeedback={() => setSingleQuestionFeedback(question.id, null)}
                />
              )}
            </div>
          ))}
        <Divider />
      </>
  );

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  const { name, description } = testData || {};
  return (
    <div className="test-paper-container">
      {contextHolder}
      <div className="test-paper-header">
        <div></div>
        <div style={{ textAlign: 'center' }}>
          <h1>{name}</h1>
          <p>{description}</p>
        </div>
        <div className="test-paper-header-nav-side">
          <Link to="/" className="paper-to-generator">←返回出题表单</Link>
          <Link to="/history" className="paper-to-history">查看历史试卷→</Link>
        </div>
      </div>
      <div className="scrollable-content" ref={scrollableContentRef}>
        {submissionStatus === 'submitted_and_showing_answers' && (
          <div style={{ textAlign: 'center', margin: '20px 0' }}>
            <Switch 
              checked={showOnlyIncorrect} 
              onChange={setShowOnlyIncorrect} 
            />
            <span style={{ marginLeft: '8px' }}>只看错题</span>
          </div>
        )}
        {renderContent()}
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          {submissionStatus === 'in_progress' && (
            <Space direction="horizontal" style={{ justifyContent: 'center', width: '100%' }}>
              <Button type="primary" size="large" onClick={handleSubmitAndShowAnswers} loading={isLoading} className="submit-and-show-answers-btn"> 提交并查看答案 </Button>
              <Button 
                icon={<ExportOutlined />} 
                size="large" 
                onClick={handleExportHtml}
                type="primary"
                style={{ backgroundColor: '#C4E9E4', borderColor: '#C4E9E4' }}
              >
                导出HTML
              </Button>
            </Space>
          )}
          {submissionStatus === 'submitted_and_showing_answers' && (
            <Space direction="horizontal" style={{ justifyContent: 'center', width: '100%' }}>
              <Button type="primary" size="large" onClick={handleRequestAiFeedback} loading={isLoading}> {isLoading ? '正在请求AI分析...' : '请求AI进行分析'} </Button>
              <Button size="large" onClick={handleRetakeTest}> 重新作答 </Button>
              <Button 
                icon={<ExportOutlined />} 
                size="large" 
                onClick={handleExportHtml}
                type="primary"
                style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
              >
                导出HTML
              </Button>
            </Space>
          )}
          {submissionStatus === 'submitted_and_showing_answers' && gradingResults && (
            <p style={{ marginTop: '16px', color: '#888' }}>分析完成后，你还可以针对单个题目请求AI进行更详细的点评。</p>
          )}
        </div>
      </div>
      <button 
        className={`back-to-top-button ${showBackToTop ? 'visible' : ''}`}
        onClick={scrollToTop}
      >
        <UpOutlined />
      </button>
    </div>
  );
};

export default TestPaperPage;