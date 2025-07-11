from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, sessionmaker
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class TestPaper(Base):
    __tablename__ = 'test_papers'
    id = Column(Integer, primary_key=True)
    source_type = Column(String(50)) # 'text' or 'file'
    source_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    questions = relationship('Question', back_populates='test_paper')

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    test_paper_id = Column(Integer, ForeignKey('test_papers.id'))
    question_type = Column(String(50)) # e.g., 'single_choice', 'essay'
    stem = Column(Text)
    options = Column(JSON) # For multiple choice
    correct_answer = Column(JSON)
    test_paper = relationship('TestPaper', back_populates='questions')

# 数据库连接设置
DATABASE_URL = "sqlite:///f:/ai4exam/backend/test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from typing import List, Optional, Union, Dict, Any


class QuestionConfig(BaseModel):
    type: str
    count: int


class GenerateTestConfig(BaseModel):
    description: str
    question_config: List[QuestionConfig]
    difficulty: str


class SingleChoiceAnswer(BaseModel):
    correct_option_index: int
    explanation: str

class MultipleChoiceAnswer(BaseModel):
    correct_option_indices: List[int]
    explanation: str

class FillInTheBlankAnswer(BaseModel):
    correct_answers: List[str]

class EssayAnswer(BaseModel):
    reference_explanation: str

class QuestionModel(BaseModel):
    id: str
    type: str
    stem: str
    options: Optional[List[str]] = None
    answer: Union[SingleChoiceAnswer, MultipleChoiceAnswer, FillInTheBlankAnswer, EssayAnswer, str]

class GenerateTestResponse(BaseModel):
    test_id: str
    questions: List[QuestionModel]

class UserSingleChoiceAnswer(BaseModel):
    question_id: str
    question_type: str = "single_choice"
    answer_index: int

class UserMultipleChoiceAnswer(BaseModel):
    question_id: str
    question_type: str = "multiple_choice"
    answer_indices: List[int]

class UserFillInTheBlankAnswer(BaseModel):
    question_id: str
    question_type: str = "fill_in_the_blank"
    answer_texts: List[str]

class UserEssayAnswer(BaseModel):
    question_id: str
    question_type: str = "essay"
    answer_text: str

class GradeQuestionsRequest(BaseModel):
    test_id: str
    answers: List[Union[UserSingleChoiceAnswer, UserMultipleChoiceAnswer, UserFillInTheBlankAnswer, UserEssayAnswer]]

class ObjectiveGradeResult(BaseModel):
    question_id: str
    is_correct: bool
    user_answer: Any
    correct_answer: Any

class EssayGradeResult(BaseModel):
    question_id: str
    user_answer: str
    reference_explanation: str

class GradeQuestionsResponse(BaseModel):
    results: List[Union[ObjectiveGradeResult, EssayGradeResult]]


class GenerateOverallFeedbackRequest(BaseModel):
    test_id: str
    answers: List[Union[UserSingleChoiceAnswer, UserMultipleChoiceAnswer, UserFillInTheBlankAnswer, UserEssayAnswer]]


class GenerateOverallFeedbackResponse(BaseModel):
    feedback: str


class GenerateSingleQuestionFeedbackRequest(BaseModel):
    test_id: str
    question_id: str
    user_answer: Any # Can be int, List[int], or List[str]


class GenerateSingleQuestionFeedbackResponse(BaseModel):
    feedback: str


class QuestionInfo(BaseModel):
    stem: str
    reference_explanation: str


class EvaluateShortAnswerRequest(BaseModel):
    test_id: Optional[str] = None
    question: QuestionInfo
    user_answer: str


class EvaluateShortAnswerResponse(BaseModel):
    score: int
    feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    reference_explanation: str