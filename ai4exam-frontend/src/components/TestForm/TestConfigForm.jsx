import React from 'react';
import { Input, Segmented, Slider } from 'antd';
import './Forms.css';

const { TextArea } = Input;

// 题型配置
const QUESTION_TYPES_CONFIG = {
    single_choice: { label: '单选题', color: 'var(--single-choice-color)' },
    multiple_choice: { label: '多选题', color: 'var(--multiple-choice-color)' },
    fill_in_the_blank: { label: '填空题', color: 'var(--fill-in-the-blank-color)' },
    essay: { label: '简答题', color: 'var(--essay-color)' },
};

const TestConfigForm = ({ config, onConfigChange }) => {
  const { description, difficulty, questionQuantities } = config;

  const handleDescriptionChange = (e) => {
    onConfigChange({ ...config, description: e.target.value });
  };

  const handleDifficultyChange = (value) => {
    onConfigChange({ ...config, difficulty: value });
  };

  const handleQuantityChange = (type, value) => {
    onConfigChange({
      ...config,
      questionQuantities: { ...questionQuantities, [type]: value },
    });
  };

  const difficultyOptions = [
    { label: '简单', value: 'easy' },
    { label: '中等', value: 'medium' },
    { label: '困难', value: 'hard' },
  ];

  return (
    <section className="test-config-section">
      <h3 className="section-title"><span className="title-decorator"></span>试卷配置</h3>
      <p className="section-subtitle">定制试卷的描述、难度和题型数量。</p>

      <div className="config-item">
        <label htmlFor="description"><span className="title-decorator"></span>试卷描述</label>
        <TextArea
          id="description"
          rows={3}
          value={description}
          onChange={handleDescriptionChange}
          placeholder="对于题目内容更详细的描述"
          className="config-textarea"
        />
      </div>

      <div className="config-item">
        <label htmlFor="difficulty"><span className="title-decorator"></span>试卷难度</label>
        <Segmented
          id="difficulty"
          options={difficultyOptions}
          value={difficulty}
          onChange={handleDifficultyChange}
          className={`config-segmented difficulty-${difficulty}`}
        />
      </div>

      <div className="config-item">
        <label><span className="title-decorator"></span>各题型数量</label>
        <div className="question-sliders">
          {Object.entries(QUESTION_TYPES_CONFIG).map(([type, config]) => (
            <div key={type} className="slider-item">
              <span className="slider-label">{config.label}</span>
              <Slider
                min={0}
                max={20} // 将最大值改为10
                value={questionQuantities[type]}
                onChange={(value) => handleQuantityChange(type, value)}
                className="config-slider"
                step={1}
                handleStyle={{ 
                  borderColor: 'var(--accent-hover)',
                  backgroundColor: 'var(--accent-hover)' // 将圆形按钮填充色也改为青绿色
                }} 
                trackStyle={{ backgroundColor: 'var(--accent-hover)' }} // 使用主题悬停色
              />
              <span className="slider-value" style={{ color: 'var(--accent-hover)' }}>
                {questionQuantities[type]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TestConfigForm;