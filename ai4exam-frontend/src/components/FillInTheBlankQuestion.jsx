// src/components/FillInTheBlankQuestion.jsx (修复版)

import React from 'react';
import { Card, Input, Alert } from 'antd';
import useTestStore from '../store/useTestStore';

const FillInTheBlankQuestion = ({ question, index }) => {
  const { userAnswers, updateUserAnswer, gradingResults } = useTestStore();
  const result = gradingResults ? gradingResults[question.id] : null;

  // 关键修复：先判断数据类型，再决定如何显示
  const getCorrectAnswerText = (answer) => {
    if (Array.isArray(answer)) {
      return answer.join(' / '); // 如果是数组，用 join
    }
    return answer; // 如果不是数组（比如是字符串），直接返回
  };

  return (
    <Card title={`${index + 1}. 填空题：${question.stem.replace('____', '')}`} style={{ marginBottom: '20px' }}>
      <Input
        onChange={(e) => updateUserAnswer(question.id, e.target.value)}
        value={userAnswers[question.id]}
        disabled={!!result}
      />
      {result && (
        <Alert
          style={{ marginTop: '15px' }}
          type={result.is_correct ? 'success' : 'error'}
          message={`你的答案: ${result.user_answer} | 参考答案: ${getCorrectAnswerText(result.correct_answer)}`}
        />
      )}
    </Card>
  );
};

export default FillInTheBlankQuestion;