from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel

# 所有 Pydantic 模型都移到这里
class QuestionConfig(BaseModel):
    type: str
    count: int

class GenerateTestConfig(BaseModel):
    description: str
    question_config: List[QuestionConfig]
    difficulty: str

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
    question_id: str
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
    test_id: str
    answers: List[UserAnswer]

class GenerateOverallFeedbackResponse(BaseModel):
    feedback: str

class GenerateSingleQuestionFeedbackRequest(BaseModel):
    question_id: str
    user_answer: Optional[UserAnswer] = None

class GenerateSingleQuestionFeedbackResponse(BaseModel):
    feedback: str

# --- Essay Evaluation Models ---
class QuestionInfo(BaseModel):
    stem: str
    reference_explanation: str

class EvaluateShortAnswerRequest(BaseModel):
    question: QuestionInfo
    user_answer: str

class EvaluateShortAnswerResponse(BaseModel):
    score: int
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    reference_explanation: str