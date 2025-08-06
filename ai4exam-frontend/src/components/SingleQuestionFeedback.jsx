// src/components/SingleQuestionFeedback.jsx
import React from 'react';
import { Button, Alert } from 'antd';
import MarkdownRenderer from './MarkdownRenderer';
import './SingleQuestionFeedback.css';

const SingleQuestionFeedback = ({ questionId, feedback, onRequestFeedback, onClearFeedback }) => {
  return (
    <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderTop: '1px solid #eee' }}>
      <Button onClick={() => onRequestFeedback(questionId)}> 请求 AI 点评此题 </Button>
      {feedback && (
        <Alert
          message="AI 点评"
          description={<MarkdownRenderer>{feedback}</MarkdownRenderer>}
          type="info"
          showIcon
          style={{ marginTop: '16px' }}
          closable
          onClose={() => onClearFeedback(questionId)}
        />
      )}
    </div>
  );
};

export default SingleQuestionFeedback;