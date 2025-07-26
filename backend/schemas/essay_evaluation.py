# schemas/essay_evaluation.py

from typing import List, Optional
from pydantic import BaseModel

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