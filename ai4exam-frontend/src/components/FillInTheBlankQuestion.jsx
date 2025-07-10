// src/components/FillInTheBlankQuestion.jsx (修复版)

import React from 'react';
import { Card, Input, Alert } from 'antd';
import useTestStore from '../store/useTestStore';

const FillInTheBlankQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer } = useTestStore();

  // 关键修复：先判断数据类型，再决定如何显示
  const getCorrectAnswerText = (answer) => {
    if (Array.isArray(answer)) {
      return answer.join(' / '); // 如果是数组，用 join
    }
    return answer; // 如果不是数组（比如是字符串），直接返回
  };

  const blanks = question.stem.split('____').length - 1;
  const parts = question.stem.split('____');
  const currentAnswers = (userAnswers[question.id] || '').split('$$$');

  const handleInputChange = (e, i) => {
    const newAnswers = [...currentAnswers];
    // 确保数组长度足够
    while (newAnswers.length < blanks) {
      newAnswers.push('');
    }
    newAnswers[i] = e.target.value;
    updateUserAnswer(question.id, newAnswers.join('$$$'));
  };

  return (
    <Card title={`${index + 1}. 填空题`} style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center' }}>
        {parts.map((part, i) => (
          <React.Fragment key={i}>
            {part}
            {i < blanks && (
              <Input
                style={{ width: '150px', margin: '0 8px' }}
                onChange={(e) => handleInputChange(e, i)}
                value={currentAnswers[i] || ''}
                disabled={!!gradingResult}
              />
            )}
          </React.Fragment>
        ))}
      </div>
      {gradingResult && (
        <Alert
          style={{ marginTop: '15px' }}
          type={gradingResult.is_correct ? 'success' : 'error'}
          message={`你的答案: ${gradingResult.user_answer} | 参考答案: ${getCorrectAnswerText(gradingResult.correct_answer)}`}
        />
      )}
    </Card>
  );
};

export default FillInTheBlankQuestion;