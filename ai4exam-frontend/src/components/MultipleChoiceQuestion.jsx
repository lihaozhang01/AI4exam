// ... imports ...
import { Card, Checkbox, Space, Alert } from 'antd';
import useTestStore from '../store/useTestStore';

const MultipleChoiceQuestion = ({ question, index, gradingResult }) => {
  const { userAnswers, updateUserAnswer } = useTestStore();

  const formatAnswer = (indices) => indices.map(i => String.fromCharCode(65 + i)).join(', ');

  return (
    <Card title={<div style={{ whiteSpace: 'pre-wrap' }}>{`${index + 1}. 多选题：${question.stem}`}</div>} style={{ marginBottom: '20px' }}>
      <Checkbox.Group
        onChange={(values) => updateUserAnswer(question.id, values)}
        value={userAnswers[question.id] || []}
        disabled={!!gradingResult}
      >
        <Space direction="vertical">
          {question.options.map((option, i) => <Checkbox key={i} value={i}>{String.fromCharCode(65 + i)}. {option}</Checkbox>)}
        </Space>
      </Checkbox.Group>
      {gradingResult && (
        <Alert
          style={{ marginTop: '15px' }}
          type={gradingResult.is_correct ? 'success' : 'error'}
          message={`你的答案: ${formatAnswer(gradingResult.user_answer || [])} | 正确答案: ${formatAnswer(gradingResult.correct_answer || [])}`} 
          description={!gradingResult.is_correct ? `解析：${question.answer.explanation}` : null}
        />
      )}
    </Card>
  );
};
export default MultipleChoiceQuestion;