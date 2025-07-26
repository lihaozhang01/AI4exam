# services/database.py

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from .grading import GRADING_STRATEGIES

# --- Database Interaction Services ---

def get_test_paper_by_id(db: Session, test_id: int) -> models.TestPaper:
    """通過ID從資料庫獲取試卷，如果找不到則拋出404異常。"""
    test_paper = db.query(models.TestPaper).filter(models.TestPaper.id == test_id).first()
    if not test_paper:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found.")
    return test_paper

def create_test_paper(db: Session, source_content: str, ai_response: dict) -> models.TestPaper:
    """Creates a test paper record in the database, including a generated name."""
    # 優先從AI響應中獲取標題，否則生成預設標題
    paper_name = ai_response.get('title', f"AI生成的試卷 - {source_content[:20]}...")

    db_test_paper = models.TestPaper(
        name=paper_name,
        source_content=source_content
    )
    db.add(db_test_paper)

    # 將AI生成的問題添加到資料庫
    questions_data = ai_response.get('questions', [])
    for q_data in questions_data:
        db_question = models.DBQuestion(
            test_paper=db_test_paper, # Link back to the paper
            question_type=q_data.get('type'),
            stem=q_data.get('stem'),
            options=q_data.get('options'),
            correct_answer=q_data.get('answer')
        )
        db.add(db_question)

    db.commit()
    db.refresh(db_test_paper)
    return db_test_paper

def get_question_by_id(db: Session, question_id: int) -> models.DBQuestion:
    """通過ID從資料庫獲取問題，如果找不到則拋出404異常。"""
    question = db.query(models.DBQuestion).filter(models.DBQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found.")
    return question

def get_test_result_by_id(db: Session, result_id: int) -> models.TestPaperResult:
    """Fetches a single test result by its ID."""
    result = db.query(models.TestPaperResult).filter(models.TestPaperResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"Test result with ID {result_id} not found.")
    return result

def get_all_test_results(db: Session):
    """Fetches all test paper results and calculates statistics on the fly."""
    results = (
        db.query(models.TestPaperResult)
        .options(joinedload(models.TestPaperResult.test_paper).subqueryload(models.TestPaper.questions))
        .order_by(models.TestPaperResult.created_at.desc())
        .all()
    )

    # 為每条結果動態計算統計數據
    for result in results:
        test_paper = result.test_paper
        if not test_paper or not test_paper.questions:
            result.total_objective_questions = 0
            result.total_essay_questions = 0
            result.correct_objective_questions = 0
            continue

        # 統計題目類型數量
        total_objective = sum(1 for q in test_paper.questions if q.question_type in GRADING_STRATEGIES)
        total_essay = sum(1 for q in test_paper.questions if q.question_type == 'essay')

        # 統計客觀題正確數
        correct_objective = sum(1 for grade in result.grading_results if isinstance(grade, dict) and grade.get('is_correct'))
        
        # 將統計結果附加到 result 物件上，這樣 Pydantic 可以使用它們
        result.total_objective_questions = total_objective
        result.total_essay_questions = total_essay
        result.correct_objective_questions = correct_objective

    return results

def get_test_result(db: Session, result_id: int) -> models.TestPaperResult:
    """Fetches a single test paper result by its ID, eagerly loading the test paper data."""
    result = (
        db.query(models.TestPaperResult)
        .options(joinedload(models.TestPaperResult.test_paper))
        .filter(models.TestPaperResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Test result with ID {result_id} not found.")
    return result

def delete_test_result(db: Session, result_id: int) -> bool:
    """Deletes a test result, and the test paper if it's the last result."""
    result = db.query(models.TestPaperResult).filter(models.TestPaperResult.id == result_id).first()
    if not result:
        return False

    test_paper_id = result.test_paper_id
    db.delete(result)
    db.commit()

    # Check if there are any remaining results for this test paper
    remaining_results_count = db.query(models.TestPaperResult).filter(models.TestPaperResult.test_paper_id == test_paper_id).count()

    if remaining_results_count == 0:
        # If no results are left, delete the test paper itself
        test_paper = db.query(models.TestPaper).filter(models.TestPaper.id == test_paper_id).first()
        if test_paper:
            db.delete(test_paper)
            db.commit()
            
    return True