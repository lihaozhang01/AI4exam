# schemas/test_generation.py

from typing import List, Optional, Union
from pydantic import BaseModel

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
    name: str  # 试卷名称
    questions: List[QuestionModel]