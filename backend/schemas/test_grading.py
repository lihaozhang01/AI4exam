# schemas/test_grading.py

from typing import List, Optional, Union
from pydantic import BaseModel

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

class EssayGradeResult(BaseModel):
    question_id: str
    reference_explanation: str

class GradeQuestionsResponse(BaseModel):
    result_id: int
    results: List[Union[ObjectiveGradeResult, EssayGradeResult]]