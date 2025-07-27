import React from 'react';
import { Button } from 'antd';
import './ActionButtons.css';

const ActionButtons = ({ onGenerate, loading }) => {
  return (
    <div className="action-buttons-container">
      <Button
        type="primary"
        onClick={onGenerate}
        loading={loading}
        className="generate-button"
      >
        {loading ? '正在生成...' : '生成试卷'}
      </Button>
    </div>
  );
};

export default ActionButtons;