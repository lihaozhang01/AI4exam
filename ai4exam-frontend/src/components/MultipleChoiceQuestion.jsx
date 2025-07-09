// ... imports ...
import { Card, Checkbox, Space, Alert } from 'antd';
import useTestStore from '../store/useTestStore';

const MultipleChoiceQuestion = ({ question, index }) => {
  const { userAnswers, updateUserAnswer, gradingResults } = useTestStore();
  const result = gradingResults ? gradingResults[question.id] : null;

  const formatAnswer = (indices) => indices.map(i => String.fromCharCode(65 + i)).join(', ');

  return (
    <Card title={`${index + 1}. 多选题：${question.stem}`} style={{ marginBottom: '20px' }}>
      <Checkbox.Group
        onChange={(values) => updateUserAnswer(question.id, values)}
        value={userAnswers[question.id] || []}
        disabled={!!result}
      >
        <Space direction="vertical">
          {question.options.map((option, i) => <Checkbox key={i} value={i}>{String.fromCharCode(65 + i)}. {option}</Checkbox>)}
        </Space>
      </Checkbox.Group>
      {result && (
        <Alert
          style={{ marginTop: '15px' }}
          type={result.is_correct ? 'success' : 'error'}
          message={`你的答案: ${formatAnswer(result.user_answer)} | 正确答案: ${formatAnswer(result.correct_answer)}`}
          description={!result.is_correct ? `解析：${question.answer.explanation}` : null}
        />
      )}
    </Card>
  );
};
export default MultipleChoiceQuestion;