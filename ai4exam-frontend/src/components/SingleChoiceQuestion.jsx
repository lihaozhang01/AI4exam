import React from 'react';
import { Card, Radio, Space, Alert, Tag } from 'antd';
import useTestStore from '../store/useTestStore';

const SingleChoiceQuestion = ({ question, index }) => {
  const { userAnswers, updateUserAnswer, gradingResults } = useTestStore();
  const result = gradingResults ? gradingResults[question.id] : null;

  return (
    <Card title={`${index + 1}. 单选题：${question.stem}`} style={{ marginBottom: '20px' }}>
      <Radio.Group
        onChange={(e) => updateUserAnswer(question.id, e.target.value)}
        value={userAnswers[question.id]}
        disabled={!!result} // 如果有结果，则禁用
      >
        <Space direction="vertical">
          {question.options.map((option, i) => <Radio key={i} value={i}>{String.fromCharCode(65 + i)}. {option}</Radio>)}
        </Space>
      </Radio.Group>
      {result && (
        <Alert
          style={{ marginTop: '15px' }}
          type={result.is_correct ? 'success' : 'error'}
          message={
            <>
              你的答案: {String.fromCharCode(65 + result.user_answer)} |
              正确答案: {String.fromCharCode(65 + result.correct_answer)}
              {result.is_correct ? '  回答正确！' : ''}
            </>
          }
          description={!result.is_correct ? `解析：${question.answer.explanation}` : null}
        />
      )}
    </Card>
  );
};
export default SingleChoiceQuestion;