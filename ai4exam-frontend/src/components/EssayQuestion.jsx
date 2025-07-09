import React from 'react';
import { Card, Input, Tag, Divider, List } from 'antd';
import useTestStore from '../store/useTestStore';

const { TextArea } = Input;

const EssayQuestion = ({ question, index }) => {
  const { userAnswers, updateUserAnswer, gradingResults } = useTestStore();
  const result = gradingResults ? gradingResults[question.id] : null;

  return (
    <Card title={`${index + 1}. 论述题：${question.stem}`} style={{ marginBottom: '20px' }}>
      <TextArea
        rows={6}
        onChange={(e) => updateUserAnswer(question.id, e.target.value)}
        value={userAnswers[question.id]}
        disabled={!!result} // 如果有结果，则禁用
      />
      {result && (
        <div style={{ marginTop: '15px' }}>
          <Divider>AI 批改反馈</Divider>
          <p><strong>得分: </strong> <Tag color="blue" style={{ fontSize: '16px' }}>{result.score} / 100</Tag></p>
          <p><strong>总评: </strong> {result.feedback}</p>
          <List
            size="small"
            header={<strong>优点:</strong>}
            dataSource={result.strengths}
            renderItem={(item) => <List.Item>✅ {item}</List.Item>}
            bordered
            style={{ marginBottom: '10px' }}
          />
          <List
            size="small"
            header={<strong>待改进:</strong>}
            dataSource={result.areas_for_improvement}
            renderItem={(item) => <List.Item>❌ {item}</List.Item>}
            bordered
          />
        </div>
      )}
    </Card>
  );
};

export default EssayQuestion;