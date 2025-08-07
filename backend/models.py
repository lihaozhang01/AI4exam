import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

Base = declarative_base()

class TestPaper(Base):
    __tablename__ = 'test_papers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True, index=True)  # 试卷名称
    total_objective_questions = Column(Integer, default=0)  # 客观题总数
    total_essay_questions = Column(Integer, default=0)  # 主观题总数

    source_content = Column(Text)
    config = Column(JSON) # 保存生成配置
    generation_prompt = Column(Text, nullable=True) # 保存生成提示
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    questions = relationship('DBQuestion', back_populates='test_paper', cascade="all, delete-orphan")
    results = relationship('TestPaperResult', back_populates='test_paper', cascade="all, delete-orphan")

class TestPaperResult(Base):
    __tablename__ = 'test_paper_results'
    id = Column(Integer, primary_key=True, index=True)
    test_paper_id = Column(Integer, ForeignKey('test_papers.id'))
    user_answers = Column(JSON) # Store user's answers
    grading_results = Column(JSON) # Store grading results
    correct_objective_questions = Column(Integer, nullable=False, default=0)  # 客观题正确数
    overall_feedback = Column(Text, nullable=True) # Store overall AI feedback
    question_feedbacks = Column(JSON, nullable=True) # Store individual question AI feedbacks
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    test_paper = relationship('TestPaper', back_populates='results')


class DBQuestion(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    test_paper_id = Column(Integer, ForeignKey('test_papers.id'))
    question_type = Column(String(50))
    stem = Column(Text)
    options = Column(JSON)
    correct_answer = Column(JSON)
    test_paper = relationship('TestPaper', back_populates='questions')