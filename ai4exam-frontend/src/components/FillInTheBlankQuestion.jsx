// src/components/FillInTheBlankQuestion.jsx (修复版)

import React from 'react';
import { Card, Input, Alert } from 'antd';
import useTestStore from '../store/useTestStore';

const FillInTheBlankQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer } = useTestStore();

  // 关键修复：先判断数据类型，再决定如何显示


  // 修复：空的数量应该由答案数组的长度决定，而不是题干中的占位符数量
  // 使用 $blank$ 作为新的、更可靠的占位符
  const parts = question.stem.split('$blank$');
  const blanks = parts.length - 1;
  // 直接将答案作为数组处理，如果不存在则初始化为空数组
  const currentAnswers = userAnswers[question.id] || [];

  const handleInputChange = (e, i) => {
    const newAnswers = [...currentAnswers];
    newAnswers[i] = e.target.value;
    updateUserAnswer(question.id, newAnswers);
  };

  return (
    <Card title={`${index + 1}. 填空题`} style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center' }}>
        {parts.map((part, i) => (
          <React.Fragment key={i}>
            <span style={{ whiteSpace: 'pre-wrap' }}>{part}</span>
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
          message={`你的答案: ${currentAnswers.length > 0 && currentAnswers.some(ans => ans) ? currentAnswers.join(', ') : '未作答'} | 参考答案: ${question.answer.texts.join(' / ')}`}
          description={!gradingResult.is_correct ? `解析：${question.answer.explanation}` : null}
        />
      )}
    </Card>
  );
};

export default FillInTheBlankQuestion;