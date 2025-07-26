# schemas/feedback.py

from typing import List, Optional
from pydantic import BaseModel
from .test_grading import UserAnswer

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