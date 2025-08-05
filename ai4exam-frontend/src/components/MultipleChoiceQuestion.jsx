// ... imports ...
import React from 'react';
import { Card, Checkbox, Space, Alert } from 'antd';
import MarkdownRenderer from './MarkdownRenderer';
import './MultipleChoiceQuestion.css';
import useTestStore from '../store/useTestStore';

const MultipleChoiceQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer } = useTestStore();

  const handleChange = (i) => {
    const currentAnswers = userAnswers[question.id] || [];
    const newAnswers = currentAnswers.includes(i)
      ? currentAnswers.filter(ans => ans !== i)
      : [...currentAnswers, i];
    updateUserAnswer(question.id, newAnswers.sort((a, b) => a - b));
  };

  const formatAnswer = (indices) => indices.map(i => String.fromCharCode(65 + i)).join(', ');

  return (
    <Card title={`${index + 1}. 多选题`} style={{ marginBottom: '20px' }}>
      <MarkdownRenderer>{question.stem}</MarkdownRenderer>

      <Space direction="vertical" style={{ width: '100%', marginTop: '20px' }}>
        {question.options.map((option, i) => {
          const isSelected = (userAnswers[question.id] || []).includes(i);
          return (
            <div
              key={i}
              className={`choice-option ${isSelected ? 'selected' : ''}`}
              onClick={() => !gradingResult && handleChange(i)}
            >
              <Checkbox value={i} checked={isSelected} disabled={!!gradingResult} />
              <div className="choice-option-text"><MarkdownRenderer>{`${String.fromCharCode(65 + i)}. ${option}`}</MarkdownRenderer></div>
            </div>
          );
        })}
      </Space>

      {gradingResult && (
        <Alert
          style={{ marginTop: '15px' }}
          type={gradingResult.is_correct ? 'success' : 'error'}
          message={`你的答案: ${formatAnswer(userAnswers[question.id] || [])} | 正确答案: ${formatAnswer(question.answer.indexes || [])}`}
          description={question.answer.explanation ? <div>解析：<MarkdownRenderer>{question.answer.explanation}</MarkdownRenderer></div> : null}
        />
      )}
    </Card>
  );
};
export default MultipleChoiceQuestion;