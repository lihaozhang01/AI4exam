// src/TestPaperPage.jsx (修复版)

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Button, Divider, message } from 'antd';
import axios from 'axios';
import useTestStore from './store/useTestStore';

import SingleChoiceQuestion from './components/SingleChoiceQuestion';
import MultipleChoiceQuestion from './components/MultipleChoiceQuestion';
import FillInTheBlankQuestion from './components/FillInTheBlankQuestion';
import EssayQuestion from './components/EssayQuestion';

const TestPaperPage = () => {
  const {
    testData,
    userAnswers,
    isLoading,
    setIsLoading,
    setGradingResults
  } = useTestStore();
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const objectiveAnswersPayload = [];
      const essayAnswersPayload = [];

      testData.questions.forEach(q => {
        const userAnswer = userAnswers[q.id];
        if (q.type === 'single_choice' || q.type === 'multiple_choice' || q.type === 'fill_in_the_blank') {
          objectiveAnswersPayload.push({
            question_id: q.id,
            user_response: userAnswer || (q.type === 'multiple_choice' ? [] : ''),
          });
        } else if (q.type === 'essay') {
          essayAnswersPayload.push({
            test_id: testData.test_id,
            question: {
              stem: q.stem,
              reference_explanation: q.answer.reference_explanation,
            },
            user_answer: userAnswer || '',
            question_id: q.id
          });
        }
      });

      const apiRequests = [];
      if (objectiveAnswersPayload.length > 0) {
        apiRequests.push(
          axios.post('http://127.0.0.1:8000/grade-objective-questions', {
            test_id: testData.test_id,
            answers: objectiveAnswersPayload,
            request_ai_feedback: true,
          })
        );
      }

      essayAnswersPayload.forEach(payload => {
        apiRequests.push(
          axios.post('http://127.0.0.1:8000/evaluate-short-answer', payload)
        );
      });

      if (apiRequests.length === 0) {
        message.info("没有需要提交的答案。");
        setIsLoading(false);
        return;
      }

      const responses = await Promise.all(apiRequests);

      // --- 关键修复：重构结果处理逻辑 ---
      const finalResults = {};
      let overallFeedback = null;
      let essayResponseIndex = 0; // 用于正确匹配论述题结果

      responses.forEach(res => {
        // 通过判断返回数据中是否包含 'results' 字段来识别是哪种API的返回
        if (res.data && res.data.results) {
          // 这是客观题的批改结果
          res.data.results.forEach(result => {
            finalResults[result.question_id] = result;
          });
          if (res.data.overall_feedback) {
            overallFeedback = res.data.overall_feedback;
          }
        } else if (res.data && res.data.score !== undefined) {
          // 这是论述题的批改结果
          const originalPayload = essayAnswersPayload[essayResponseIndex];
          if (originalPayload) {
            finalResults[originalPayload.question_id] = res.data;
          }
          essayResponseIndex++;
        }
      });
      // --- 修复结束 ---

      setGradingResults(finalResults);
      message.success('批改完成！');
      if (overallFeedback) {
        message.info(overallFeedback, 5);
      }

    } catch (error) {
      console.error("批改失败:", error);
      message.error('批改失败，请检查控制台获取详细错误。');
    } finally {
      setIsLoading(false);
    }
  };

  // ... (组件的其余部分保持不变)
  if (!testData || !testData.questions) {
    return (<Empty description="尚未生成试卷..."><Button onClick={() => navigate('/')}>返回出题</Button></Empty>);
  }

  return (
    <div>
      <h1 style={{ textAlign: 'center', marginBottom: '24px' }}>AI 智能模拟试卷</h1>
      {testData.questions.map((question, index) => {
        switch (question.type) {
          case 'single_choice': return <SingleChoiceQuestion key={question.id} question={question} index={index} />;
          case 'multiple_choice': return <MultipleChoiceQuestion key={question.id} question={question} index={index} />;
          case 'fill_in_the_blank': return <FillInTheBlankQuestion key={question.id} question={question} index={index} />;
          case 'essay': return <EssayQuestion key={question.id} question={question} index={index} />;
          default: return <p key={question.id}>未知题型</p>;
        }
      })}
      <Divider />
      <div style={{ textAlign: 'center' }}>
        <Button type="primary" size="large" onClick={handleSubmit} loading={isLoading} disabled={isLoading || !!useTestStore.getState().gradingResults}>
          {useTestStore.getState().gradingResults ? '批改已完成' : (isLoading ? '正在批改中...' : '完成作答，提交批改')}
        </Button>
      </div>
    </div>
  );
};

export default TestPaperPage;