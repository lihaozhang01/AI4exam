from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel
import datetime

# 所有 Pydantic 模型都移到这里
class QuestionConfig(BaseModel):
    type: str
    count: int

class GenerateTestConfig(BaseModel):
    description: str
    question_config: List[QuestionConfig]
    difficulty: str
    generation_prompt: Optional[str] = None

# --- Answer Models for AI Generation ---
class SingleChoiceAnswer(BaseModel):
    index: int
    explanation: str

class MultipleChoiceAnswer(BaseModel):
    indexes: List[int]
    explanation: str

class FillInTheBlankAnswer(BaseModel):
    texts: List[str]
    explanation: str

class EssayAnswer(BaseModel):
    reference_explanation: str

class QuestionModel(BaseModel):
    id: Optional[str] = None # ID在返回给前端时才有
    type: str
    stem: str
    options: Optional[List[str]] = None
    answer: Union[SingleChoiceAnswer, MultipleChoiceAnswer, FillInTheBlankAnswer, EssayAnswer]

class GenerateTestResponse(BaseModel):
    test_id: str
    questions: List[QuestionModel]

# --- User Answer Models for Grading ---
# 注意：我们将所有UserAnswer合并到一个模型中，以便在services.py中进行类型提示
class UserAnswer(BaseModel):
    question_id: Optional[str] = None # 在单个问题反馈中，此ID在请求体顶层，因此设为可选
    question_type: str 
    answer_index: Optional[int] = None
    answer_indices: Optional[List[int]] = None
    answer_texts: Optional[List[str]] = None
    answer_text: Optional[str] = None


class GradeQuestionsRequest(BaseModel):
    test_id: str
    answers: List[UserAnswer]

class ObjectiveGradeResult(BaseModel):
    question_id: str
    is_correct: bool

class GradeQuestionsResponse(BaseModel):
    results: List[ObjectiveGradeResult]

# --- Feedback Models ---
class GenerateOverallFeedbackRequest(BaseModel):
    result_id: int
    test_id: str
    answers: List[UserAnswer]
    overall_feedback_prompt: Optional[str] = None

class GenerateOverallFeedbackResponse(BaseModel):
    feedback: str

class GenerateSingleQuestionFeedbackRequest(BaseModel):
    result_id: int
    question_id: str
    user_answer: Optional[UserAnswer] = None
    single_question_feedback_prompt: Optional[str] = None

class GenerateSingleQuestionFeedbackResponse(BaseModel):
    feedback: str

# --- Essay Evaluation Models ---
class QuestionInfo(BaseModel):
    stem: str
    reference_explanation: str

class EvaluateShortAnswerRequest(BaseModel):
    question: QuestionInfo
    user_answer: str
    evaluation_prompt: Optional[str] = None

class EvaluateShortAnswerResponse(BaseModel):
    score: int
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    reference_explanation: str

# --- Test Paper History --- 
class TestPaper(BaseModel):
    id: int
    name: str
    source_type: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TestPaperResult(BaseModel):
    id: int
    test_paper_id: int
    user_answers: List[Any]
    grading_results: List[Any]
    overall_feedback: Optional[str] = None
    question_feedbacks: Optional[Dict[str, str]] = None
    created_at: datetime.datetime
    test_paper: TestPaper# 嵌套的TestPaper信息

    # 新增的统计字段
    correct_objective_questions: int = 0
    total_objective_questions: int = 0
    total_essay_questions: int = 0

    class Config:
        from_attributes = True