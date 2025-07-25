// src/TestPaperPage.jsx

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import { Empty, Button, Divider, message, Checkbox, Alert, Spin, Space } from 'antd';
import axios from 'axios';
import useTestStore from './store/useTestStore';

import SingleChoiceQuestion from './components/SingleChoiceQuestion';
import MultipleChoiceQuestion from './components/MultipleChoiceQuestion';
import FillInTheBlankQuestion from './components/FillInTheBlankQuestion';
import EssayQuestion from './components/EssayQuestion';
import MarkdownRenderer from './components/MarkdownRenderer';
import './TestPaperPage.css';

// Helper function to build the payload for API calls
const buildAnswersPayload = (userAnswers, questions) => {
  return Object.keys(userAnswers).map(questionId => {
    const question = questions.find(q => q.id === questionId);
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
        // 如果答案是单个字符串（由$$$拼接），则拆分为数组
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
  const { testId, resultId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    testData,
    setTestData,
    setTestForHistory, // 使用新的 action
    userAnswers,
    setUserAnswers,
    isLoading,
    setIsLoading,
    setGradingResults,
    resultId: storeResultId, // Rename to avoid conflict with useParams resultId
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

  useEffect(() => {
    const fetchTestPaper = async (id) => {
      setIsLoading(true);
      try {
        const response = await axios.get(`http://127.0.0.1:8000/test-papers/${id}`);
        reset();
        setTestData(response.data);
        setSubmissionStatus('in_progress');
        setOriginalTestId(id);
      } catch (error) {
        console.error("获取新试卷失败:", error.response ? error.response.data : error.message);
        message.error("获取新试卷失败，请返回首页重试。" + (error.response ? `(${error.response.status})` : ''));
        navigate('/');
      } finally {
        setIsLoading(false);
      }
    };

    const fetchTestResult = async (id) => {
      setIsLoading(true);
      try {
        const response = await axios.get(`http://127.0.0.1:8000/history/${id}`);
        const result = response.data;

        const testPaperResponse = await axios.get(`http://127.0.0.1:8000/test-papers/${result.test_paper_id}`);
        setTestForHistory(testPaperResponse.data); // 改为调用 setTestForHistory
        const answers = result.user_answers;
        const formattedAnswers = {};
        answers.forEach(ans => {
          let finalAnswer;
          if (ans.answer_index !== null && ans.answer_index !== undefined) {
            finalAnswer = ans.answer_index;
          } else if (ans.answer_indices) {
            finalAnswer = ans.answer_indices;
          } else if (ans.answer_texts) {
            finalAnswer = ans.answer_texts;
          } else if (ans.answer_text) {
            finalAnswer = ans.answer_text;
          } else {
            finalAnswer = null;
          }

          if (finalAnswer !== null) {
            formattedAnswers[ans.question_id] = finalAnswer;
          }
        });
        setUserAnswers(formattedAnswers);
        setGradingResults(result.grading_results, id); // Also set resultId in store

        // Restore AI feedback if available
        if (result.overall_feedback) {
          setOverallFeedback(result.overall_feedback);
        }
        if (result.question_feedbacks) {
          Object.entries(result.question_feedbacks).forEach(([qId, feedback]) => {
            setSingleQuestionFeedback(qId, feedback);
          });
        }

        setSubmissionStatus('submitted_and_showing_answers');
        setOriginalTestId(result.test_paper_id);

      } catch (error) {
        console.error("获取历史试卷失败:", error.response ? error.response.data : error.message);
        message.error("获取历史试卷失败，请稍后重试。" + (error.response ? `(${error.response.status})` : ''));
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
    // Using location.key forces a re-fetch when navigating to the same route
  }, [resultId, testId, navigate, location.key]);

  const handleSubmitAndShowAnswers = async () => {
    setIsLoading(true);
    try {
      if (!testData || !testData.test_id) {
        message.error("试卷信息不完整，无法提交。请返回首页重试。");
        return;
      }

      const allAnswers = buildAnswersPayload(userAnswers, testData.questions);
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        message.error('请先在右上角设置中填写您的API Key！');
        setIsLoading(false);
        return;
      }

      const response = await axios.post('http://127.0.0.1:8000/grade-questions', {
        test_id: testData.test_id,
        answers: allAnswers,
      }, {
        headers: {
          'X-Goog-Api-Key': apiKey,
        }
      });

      setGradingResults(response.data.results, response.data.result_id);

      setSubmissionStatus('submitted_and_showing_answers');
      // After submission, navigate to the result page to reflect the URL change
      // This makes the resultId from useParams available and consistent
      navigate(`/history/${response.data.result_id}`, { replace: true });
      message.success('Objective questions have been auto-graded! You can now request detailed AI feedback.');
    } catch (error) {
      console.error("Error submitting answers:", error.response ? error.response.data : error.message);
      message.error("提交答案失败，请检查网络连接或稍后再试。" + (error.response ? `(${error.response.status})` : ''));
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

  const handleRequestAiFeedback = async () => {
    setIsLoading(true);
    message.info('正在请求AI对整卷进行分析，请稍候...');
    try {
      if (!testData || !testData.test_id) {
        message.error("试卷信息不完整，无法请求分析。");
        return;
      }

      const answersToSend = buildAnswersPayload(userAnswers, testData.questions);
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        message.error('请先在右上角设置中填写您的API Key！');
        setIsLoading(false);
        return;
      }

      const currentResultId = storeResultId || resultId;
      if (!currentResultId) {
        message.error("无法获取到试卷结果ID，请先提交答案。");
        setIsLoading(false);
        return;
      }

      const response = await axios.post('http://127.0.0.1:8000/generate-overall-feedback', {
        result_id: parseInt(currentResultId, 10),
        test_id: testData.test_id,
        answers: answersToSend,
      }, {
        headers: {
          'X-Goog-Api-Key': apiKey,
        }
      });
      setOverallFeedback(response.data.feedback);
      message.success('AI分析完成！');
    } catch (error) {
      console.error("Error requesting AI feedback:", error.response ? error.response.data : error.message);
      message.error("请求AI反馈失败，请稍后再试。" + (error.response ? `(${error.response.status})` : ''));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestSingleQuestionFeedback = async (questionId) => {
    message.info(`正在为题目 ${questionId} 请求AI点评...`);
    try {
      const question = testData.questions.find(q => q.id === questionId);
      let userAnswer = userAnswers[questionId];

      // 确保填空题答案是数组格式
      if (question.type === 'fill_in_the_blank' && typeof userAnswer === 'string') {
        userAnswer = userAnswer.split('$$$');
      }

      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        message.error('请先在右上角设置中填写您的API Key！');
        return; // No loading state change needed here as it's per-question
      }

      let userAnswerPayload;
      switch (question.type) {
        case 'single_choice':
          userAnswerPayload = { question_type: 'single_choice', answer_index: userAnswer };
          break;
        case 'multiple_choice':
          userAnswerPayload = { question_type: 'multiple_choice', answer_indices: userAnswer || [] };
          break;
        case 'fill_in_the_blank':
          userAnswerPayload = { question_type: 'fill_in_the_blank', answer_texts: userAnswer || [] };
          break;
        case 'essay':
          userAnswerPayload = { question_type: 'essay', answer_text: userAnswer || "" };
          break;
        default:
          message.error(`Unsupported question type: ${question.type}`);
          return;
      }

      const currentResultId = storeResultId || resultId;
      if (!currentResultId) {
        message.error("无法获取到试卷结果ID，请先提交答案。");
        return; // No loading state to change here, it's a quick action
      }

      const response = await axios.post('http://127.0.0.1:8000/generate-single-question-feedback', {
        result_id: parseInt(currentResultId, 10),
        question_id: question.id,
        user_answer: userAnswerPayload,
      }, {
        headers: {
          'X-Goog-Api-Key': apiKey,
        }
      });
      setSingleQuestionFeedback(questionId, response.data.feedback);
      message.success(`题目 ${questionId} 的AI点评已生成！`);
    } catch (error) {
      console.error('Error requesting single question feedback:', error.response ? error.response.data : error.message);
      message.error('请求该题反馈失败，请稍后再试。' + (error.response ? `(${error.response.status})` : ''));
    }
  };

  const renderContent = () => (
    !testData || !testData.questions ? null :
      <>
        {overallFeedback && (
          <Alert
            message="AI 总结与点评"
            description={<MarkdownRenderer content={overallFeedback} />}
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
            closable
            onClose={() => setOverallFeedback(null)} // 允许用户关闭
          />
        )}
        {testData.questions.map((question, index) => (
          <div key={question.id}>
            {(() => {
              const result = gradingResults?.find(r => r.question_id === question.id);
              switch (question.type) {
                case 'single_choice': return <SingleChoiceQuestion question={question} index={index} gradingResult={result} />;
                case 'multiple_choice': return <MultipleChoiceQuestion question={question} index={index} gradingResult={result} />;
                case 'fill_in_the_blank': return <FillInTheBlankQuestion question={question} index={index} gradingResult={result} />;
                case 'essay': return <EssayQuestion question={question} index={index} gradingResult={result} />; // 确保传递了 gradingResult
                default: return <p>未知题型</p>;
              }
            })()}
            {submissionStatus === 'submitted_and_showing_answers' && (
              <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderTop: '1px solid #eee' }}>
                <Button onClick={() => handleRequestSingleQuestionFeedback(question.id)}>
                  请求 AI 点评此题
                </Button>
                {singleQuestionFeedbacks[question.id] && (
                  <Alert
                    message="AI 点评"
                    description={<MarkdownRenderer content={singleQuestionFeedbacks[question.id]} />}
                    type="info"
                    showIcon
                    style={{ marginTop: '16px' }}
                    closable
                    onClose={() => setSingleQuestionFeedback(question.id, null)}
                  />
                )}
              </div>
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



  // 在确认 testData 存在后再解构
  const { name, description, questions } = testData || {};

  return (
    <div className="test-paper-container">
      <div className="test-paper-header">
        <div> {/* 左侧空 div，用于对齐 */} </div>
        <div style={{ textAlign: 'center' }}>
          <h1>{name}</h1>
          <p>{description}</p>
        </div>
        <div className="test-paper-header-nav-side">
          <Link to="/" className="paper-to-generator">新建试卷</Link>
          <Link to="/history" className="paper-to-history">历史试卷</Link>
        </div>
      </div>
      <div className="scrollable-content">
        <Divider />
        {renderContent()}
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          {submissionStatus === 'in_progress' && (
            <Button type="primary" size="large" onClick={handleSubmitAndShowAnswers} loading={isLoading}>
              提交并查看答案
            </Button>
          )}
          {submissionStatus === 'submitted_and_showing_answers' && (
            <Space direction="horizontal" style={{ justifyContent: 'center', width: '100%' }}>
              <Button type="primary" size="large" onClick={handleRequestAiFeedback} loading={isLoading}>
                {isLoading ? '正在请求AI分析...' : '请求AI进行分析'}
              </Button>
              <Button size="large" onClick={handleRetakeTest}>
                重新作答
              </Button>
            </Space>
          )}
          {submissionStatus === 'submitted_and_showing_answers' && gradingResults && (
            <p style={{ marginTop: '16px', color: '#888' }}>分析完成后，你还可以针对单个题目请求AI进行更详细的点评。</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestPaperPage;