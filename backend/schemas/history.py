# schemas/history.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import datetime

class TestPaper(BaseModel):
    id: int
    name: str
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
    test_paper: TestPaper # 嵌套的TestPaper信息

    # 新增的统计字段
    correct_objective_questions: int = 0
    total_objective_questions: int = 0
    total_essay_questions: int = 0

    class Config:
        from_attributes = True