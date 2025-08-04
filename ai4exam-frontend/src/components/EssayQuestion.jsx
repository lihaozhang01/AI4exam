import React from 'react';
import { Card, Input, Tag, Divider, List } from 'antd';
import MarkdownRenderer from './MarkdownRenderer';
import useTestStore from '../store/useTestStore';

const { TextArea } = Input;

const EssayQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer, submissionStatus } = useTestStore();
  const userAnswer = userAnswers[question.id] || '';
  const isSubmitted = submissionStatus === 'submitted_and_showing_answers';

  return (
    <Card title={`${index + 1}. 论述题`} style={{ marginBottom: '20px' }}>
      <MarkdownRenderer>{question.stem}</MarkdownRenderer>
      <p>你的回答:</p>
      <TextArea
        rows={6}
        onChange={(e) => {
          updateUserAnswer(question.id, e.target.value);
        }}
        value={userAnswer}
        disabled={isSubmitted}
        style={{ marginBottom: '16px' }}
      />

      {isSubmitted && (
        <div>
          {question.reference_explanation && (
            <>
              <Divider>参考答案</Divider>
              <div style={{ background: '#f6ffed', border: '1px solid #b7eb8f', padding: '12px', borderRadius: '4px' }}>
                <MarkdownRenderer>{question.reference_explanation}</MarkdownRenderer>
              </div>
            </>
          )}
          {gradingResult && gradingResult.feedback && (
            <div style={{ marginTop: '16px' }}>
              <Divider>AI 详细点评</Divider>
              <p><strong>总评: </strong><MarkdownRenderer>{gradingResult.feedback}</MarkdownRenderer></p>
              <List
                size="small"
                header={<strong>优点:</strong>}
                dataSource={gradingResult.strengths || []}
                renderItem={(item) => <List.Item>✅ <MarkdownRenderer>{item}</MarkdownRenderer></List.Item>}
                bordered
                style={{ marginBottom: '10px' }}
              />
              <List
                size="small"
                header={<strong>待改进:</strong>}
                dataSource={gradingResult.areas_for_improvement || []}
                renderItem={(item) => <List.Item>❌ <MarkdownRenderer>{item}</MarkdownRenderer></List.Item>}
                bordered
              />
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default EssayQuestion;