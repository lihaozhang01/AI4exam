import React from 'react';
import { Card, Radio, Space, Alert, Tag } from 'antd';
import useTestStore from '../store/useTestStore';

const SingleChoiceQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer } = useTestStore();

  return (
    <Card title={<div style={{ whiteSpace: 'pre-wrap' }}>{`${index + 1}. 单选题：${question.stem}`}</div>} style={{ marginBottom: '20px' }}>
      <Radio.Group
        onChange={(e) => updateUserAnswer(question.id, e.target.value)}
        value={userAnswers[question.id]}
        disabled={!!gradingResult} // 如果有结果，则禁用
      >
        <Space direction="vertical">
          {question.options.map((option, i) => <Radio key={i} value={i}>{String.fromCharCode(65 + i)}. {option}</Radio>)}
        </Space>
      </Radio.Group>
      {gradingResult && (
        <Alert
          style={{ marginTop: '15px' }}
          type={gradingResult.is_correct ? 'success' : 'error'}
          message={
            <>
              你的答案: {String.fromCharCode(65 + gradingResult.user_answer)} |
              正确答案: {String.fromCharCode(65 + gradingResult.correct_answer)}
              {gradingResult.is_correct ? '  回答正确！' : ''}
            </>
          }
          description={!gradingResult.is_correct ? `解析：${question.answer.explanation}` : null}
        />
      )}
    </Card>
  );
};
export default SingleChoiceQuestion;