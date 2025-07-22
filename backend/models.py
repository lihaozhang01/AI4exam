import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

Base = declarative_base()

class TestPaper(Base):
    __tablename__ = 'test_papers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)  # 试卷名称
    source_type = Column(String(50))
    source_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    questions = relationship('DBQuestion', back_populates='test_paper', cascade="all, delete-orphan")
    results = relationship('TestPaperResult', back_populates='test_paper', cascade="all, delete-orphan")

class TestPaperResult(Base):
    __tablename__ = 'test_paper_results'
    id = Column(Integer, primary_key=True, index=True)
    test_paper_id = Column(Integer, ForeignKey('test_papers.id'))
    user_answers = Column(JSON) # Store user's answers
    grading_results = Column(JSON) # Store grading results
    overall_feedback = Column(Text, nullable=True) # Store overall AI feedback
    question_feedbacks = Column(JSON, nullable=True) # Store individual question AI feedbacks
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
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

# 数据库连接可以保留在这里，或者移动到单独的 database.py 文件
DATABASE_URL = "sqlite:///./test.db" # 使用相对路径更具可移植性
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()