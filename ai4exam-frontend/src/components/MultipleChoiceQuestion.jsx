// ... imports ...
import { Card, Checkbox, Space, Alert } from 'antd';
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
    <Card title={<div style={{ whiteSpace: 'pre-wrap' }}>{`${index + 1}. 多选题：${question.stem}`}</div>} style={{ marginBottom: '20px' }}>

      <Space direction="vertical" style={{ width: '100%' }}>
        {question.options.map((option, i) => {
          const isSelected = (userAnswers[question.id] || []).includes(i);
          return (
            <div
              key={i}
              className={`choice-option ${isSelected ? 'selected' : ''}`}
              onClick={() => !gradingResult && handleChange(i)}
            >
              <Checkbox value={i} checked={isSelected} disabled={!!gradingResult} />
              <div className="choice-option-text">{String.fromCharCode(65 + i)}. {option}</div>
            </div>
          );
        })}
      </Space>

      {gradingResult && (
        <Alert
          style={{ marginTop: '15px' }}
          type={gradingResult.is_correct ? 'success' : 'error'}
          message={`你的答案: ${formatAnswer(userAnswers[question.id] || [])} | 正确答案: ${formatAnswer(question.answer.indexes || [])}`}
          description={question.answer.explanation ? `解析：${question.answer.explanation}` : null}
        />
      )}
    </Card>
  );
};
export default MultipleChoiceQuestion;