// src/TestPaperPage.jsx (修复版)

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Button, Divider, message, Checkbox, Alert } from 'antd';
import axios from 'axios';
import useTestStore from './store/useTestStore';

import SingleChoiceQuestion from './components/SingleChoiceQuestion';
import MultipleChoiceQuestion from './components/MultipleChoiceQuestion';
import FillInTheBlankQuestion from './components/FillInTheBlankQuestion';
import EssayQuestion from './components/EssayQuestion';

const TestPaperPage = () => {
  const navigate = useNavigate();
  const {
    testData,
    userAnswers,
    isLoading,
    setIsLoading,
    setGradingResults,
    gradingResults,
    overallFeedback,
    setOverallFeedback,
    submissionStatus,
    setSubmissionStatus,
    singleQuestionFeedbacks,
    setSingleQuestionFeedback,
  } = useTestStore();

  const handleSubmitAndShowAnswers = async () => {
    setIsLoading(true);
    try {
      const answersToSend = Object.keys(userAnswers).map(questionId => {
        const question = testData.questions.find(q => q.id === questionId);
        const answer = userAnswers[questionId];

        switch (question.type) {
          case 'single_choice':
            return { question_id: questionId, question_type: 'single_choice', answer_index: answer };
          case 'multiple_choice':
            return { question_id: questionId, question_type: 'multiple_choice', answer_indices: answer };
          case 'fill_in_the_blank':
            // Assuming the answer is an array of strings
            return { question_id: questionId, question_type: 'fill_in_the_blank', answer_texts: answer };
          default:
            return null; // Or handle other types appropriately
        }
      }).filter(Boolean); // Filter out any null entries

      const response = await axios.post('/api/grade-objective-questions', {
        test_id: testData.test_id,
        answers: answersToSend,
      });
      
      setGradingResults(response.data.results);
      setSubmissionStatus('submitted_and_showing_answers');
      message.success('答案已揭晓！现在可以请求AI进行详细点评。');
    } catch (error) {
      console.error("Error submitting answers:", error);
      message.error("提交答案失败，请稍后再试。");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestAiFeedback = async () => {
    setIsLoading(true);
    message.info('正在请求AI对整卷进行分析，请稍候...');
    try {
      const answersToSend = Object.keys(userAnswers).map(questionId => {
        const question = testData.questions.find(q => q.id === questionId);
        const answer = userAnswers[questionId];

        switch (question.type) {
          case 'single_choice':
            return { question_id: questionId, question_type: 'single_choice', answer_index: answer };
          case 'multiple_choice':
            return { question_id: questionId, question_type: 'multiple_choice', answer_indices: answer };
          case 'fill_in_the_blank':
            return { question_id: questionId, question_type: 'fill_in_the_blank', answer_texts: answer };
          default:
            return null;
        }
      }).filter(Boolean);

      const response = await axios.post('/api/generate-overall-feedback', {
        test_id: testData.test_id,
        answers: answersToSend,
      });
      setOverallFeedback(response.data.feedback);
      message.success('AI分析完成！');
    } catch (error) {
      console.error("Error requesting AI feedback:", error);
      message.error("请求AI反馈失败，请稍后再试。");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestSingleQuestionFeedback = async (questionId) => {
    message.info(`正在为题目 ${questionId} 请求AI点评...`);
    try {
      const question = testData.questions.find(q => q.id === questionId);
      const userAnswer = userAnswers[questionId];

      const response = await axios.post('/api/generate-single-question-feedback', {
        test_id: testData.test_id,
        question_id: question.id,
        user_answer: userAnswer,
      });
      setSingleQuestionFeedback(questionId, response.data.feedback);
      message.success(`题目 ${questionId} 的AI点评已生成！`);
    } catch (error) {
      console.error('Error requesting single question feedback:', error);
      message.error('请求该题反馈失败，请稍后再试。');
    } 
  };


  // ... (组件的其余部分保持不变)
  if (!testData || !testData.questions) {
    return (<Empty description="尚未生成试卷..."><Button onClick={() => navigate('/')}>返回出题</Button></Empty>);
  }

  return (
    <div>
      <h1 style={{ textAlign: 'center', marginBottom: '24px' }}>AI 智能模拟试卷</h1>
      {overallFeedback && (
        <Alert
          message="AI 总结与点评"
          description={overallFeedback}
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
              case 'essay': return <EssayQuestion question={question} index={index} gradingResult={result} />;
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
                  description={singleQuestionFeedbacks[question.id]}
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
      <div style={{ textAlign: 'center', marginTop: '24px' }}>
        {submissionStatus === 'not_submitted' && (
          <Button type="primary" size="large" onClick={handleSubmitAndShowAnswers} loading={isLoading}>
            提交并查看答案
          </Button>
        )}
        {submissionStatus === 'submitted_and_showing_answers' && (
          <Button type="primary" size="large" onClick={handleRequestAiFeedback} loading={isLoading}>
            {isLoading ? '正在请求AI分析...' : '请求AI进行分析'}
          </Button>
        )}
        {submissionStatus !== 'not_submitted' && gradingResults && (
           <p style={{marginTop: '16px', color: '#888'}}>分析完成后，你还可以针对单个题目请求AI进行更详细的点评。</p>
        )}
      </div>
    </div>
  );
};

export default TestPaperPage;