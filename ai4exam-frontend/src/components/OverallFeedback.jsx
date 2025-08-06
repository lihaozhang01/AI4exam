// src/components/OverallFeedback.jsx
import React from 'react';
import { Alert } from 'antd';
import MarkdownRenderer from './MarkdownRenderer';
import './OverallFeedback.css';

const OverallFeedback = ({ feedback, onClose }) => {
  if (!feedback) {
    return null;
  }

  return (
    <Alert
      message="AI 总结与点评"
      description={<MarkdownRenderer>{feedback}</MarkdownRenderer>}
      type="info"
      showIcon
      style={{ marginBottom: '24px' }}
      closable
      onClose={onClose}
    />
  );
};

export default OverallFeedback;