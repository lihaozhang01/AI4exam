import React from 'react';
import { Card, Radio, Space, Alert, Tag } from 'antd';
import MarkdownRenderer from './MarkdownRenderer';
import './SingleChoiceQuestion.css'; // 引入样式文件
import useTestStore from '../store/useTestStore';

const SingleChoiceQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer } = useTestStore();

  return (
    <Card title={`${index + 1}. 单选题`} style={{ marginBottom: '20px' }}>
      <MarkdownRenderer>{question.stem}</MarkdownRenderer>

      <Space direction="vertical" style={{ width: '100%' }}>
        {question.options.map((option, i) => (
          <div
            key={i}
            className={`choice-option ${userAnswers[question.id] === i ? 'selected' : ''}`}
            onClick={() => {
              if (!gradingResult) {
                updateUserAnswer(question.id, i);
              }
            }}
          >
            <Radio value={i} checked={userAnswers[question.id] === i} disabled={!!gradingResult} />
            <div className="choice-option-text"><MarkdownRenderer>{`${String.fromCharCode(65 + i)}. ${option}`}</MarkdownRenderer></div>
          </div>
        ))}
      </Space>

      {gradingResult && (
        <Alert
          style={{ marginTop: '15px' }}
          type={gradingResult.is_correct ? 'success' : 'error'}
          message={`你的答案: ${String.fromCharCode(65 + userAnswers[question.id])} | 正确答案: ${String.fromCharCode(65 + question.answer.index)}`}
          description={
            <div>
              {gradingResult.is_correct ? (
                <Tag color="success">回答正确</Tag>
              ) : (
                <Tag color="error">回答错误</Tag>
              )}
              {question.answer.explanation && <div>解析：<MarkdownRenderer>{question.answer.explanation}</MarkdownRenderer></div>}
            </div>
          }
        />
      )}
    </Card>
  );
};
export default SingleChoiceQuestion;