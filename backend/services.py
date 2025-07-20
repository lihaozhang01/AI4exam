import json
import re
from typing import Dict, Any, Callable, List

import google.generativeai as genai
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

# 从 schemas 导入 Pydantic 模型，从 models 导入 SQLAlchemy 模型
from . import schemas
from . import models
from .prompts import (
    GENERATE_TEST_PROMPT, EVALUATE_ESSAY_PROMPT, 
    OVERALL_FEEDBACK_PROMPT, SINGLE_QUESTION_FEEDBACK_PROMPT
)


# --- Reusable Utilities ---

def _extract_json_from_ai_response(ai_text: str) -> Dict[str, Any]:
    """安全地从AI的文本响应中提取和解析JSON。"""
    match = re.search(r"```json\n(.*?)\n```", ai_text, re.DOTALL)
    json_str = match.group(1).strip() if match else ai_text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed. String was: {json_str[:500]}...")
        raise HTTPException(status_code=500, detail=f"AI returned malformed JSON: {e}")


# --- Database Interaction Services ---

def get_test_paper_by_id(db: Session, test_id: int) -> models.TestPaper:
    """通过ID从数据库获取试卷，如果找不到则抛出404异常。"""
    test_paper = db.query(models.TestPaper).filter(models.TestPaper.id == test_id).first()
    if not test_paper:
        raise HTTPException(status_code=404, detail=f"Test with ID {test_id} not found.")
    return test_paper

def create_test_paper(db: Session, source_type: str, source_content: str, ai_response: Dict[str, Any]) -> models.TestPaper:
    """Creates a test paper record in the database, including a generated name."""
    # 优先从AI响应中获取标题，否则生成默认标题
    paper_name = ai_response.get('title', f"基于{source_type}的试卷 - {source_content[:20]}...")

    db_test_paper = models.TestPaper(
        name=paper_name,
        source_type=source_type,
        source_content=source_content
    )
    db.add(db_test_paper)

    # 将AI生成的问题添加到数据库
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
    """通过ID从数据库获取问题，如果找不到则抛出404异常。"""
    question = db.query(models.DBQuestion).filter(models.DBQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found.")
    return question


# --- Objective Question Grading Logic (Strategy Pattern) ---

def _grade_single_choice(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    print(f"--- Grading Single Choice Question ID: {user_answer.question_id} ---")
    print(f"Received UserAnswer object: {user_answer}")
    print(f"Correct answer: {correct_answer}")
    
    return user_answer.answer_index is not None and user_answer.answer_index == correct_answer.get('index')

def _grade_multiple_choice(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    return set(user_answer.answer_indices or []) == set(correct_answer.get('indexes', []))

def _grade_fill_in_blank(user_answer: schemas.UserAnswer, correct_answer: Any) -> bool:
    """Grades a fill-in-the-blank question.
    
    Handles cases where correct_answer could be a dict {'texts': [...]} or a direct list [...].
    """
    user_texts = user_answer.answer_texts or []
    
    
    # Standardize correct_texts from various possible formats
    if isinstance(correct_answer, dict):
        correct_texts = correct_answer.get('texts', [])
    elif isinstance(correct_answer, list):
        correct_texts = correct_answer
    else:
        correct_texts = []

    # If there are no correct answers defined, the user's answer is correct only if they submitted nothing.
    if not correct_texts:
        return not any(user_texts)

    # Pad the user's answers with empty strings to match the length of correct answers
    standardized_user_texts = (user_texts + [''] * len(correct_texts))[:len(correct_texts)]

    # Compare each blank
    for user_text, correct_text in zip(standardized_user_texts, correct_texts):
        if user_text.strip() != str(correct_text).strip():
            return False

    return True
    # 使用列表比较，确保

GRADING_STRATEGIES: Dict[str, Callable[[schemas.UserAnswer, Dict], bool]] = {
    'single_choice': _grade_single_choice,
    'multiple_choice': _grade_multiple_choice,
    'fill_in_the_blank': _grade_fill_in_blank,
}

def grade_and_save_test(db: Session, test_id: int, user_answers: List[schemas.UserAnswer]):
    """Grades a test submission and saves the results to the database."""
    test_paper = get_test_paper_by_id(db, test_id)
    if not test_paper:
        return None, []  # Or raise an exception
    questions_map = {str(q.id): q for q in test_paper.questions}

    grading_results = []
    for user_answer in user_answers:
        question = questions_map.get(user_answer.question_id)
        if not question:
            continue  # Skip if the question ID is invalid
        
        is_correct = grade_objective_question(question, user_answer)
        grading_results.append(schemas.ObjectiveGradeResult(
            question_id=user_answer.question_id,
            is_correct=is_correct
        ))

    # Convert Pydantic models to dictionaries for JSON serialization
    user_answers_dicts = [ans.model_dump() for ans in user_answers]
    grading_results_dicts = [res.model_dump() for res in grading_results]

    db_result = models.TestPaperResult(
        test_paper_id=test_id,
        user_answers=user_answers_dicts,
        grading_results=grading_results_dicts
    )

    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    return db_result, grading_results

def get_all_test_results(db: Session):
    """Fetches all test paper results, including the test paper name."""
    return (
        db.query(models.TestPaperResult)
        .options(joinedload(models.TestPaperResult.test_paper))
        .order_by(models.TestPaperResult.created_at.desc())
        .all()
    )

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


def grade_objective_question(question: models.DBQuestion, user_answer: schemas.UserAnswer) -> bool:
    """根据题型分发并批改单个客观题。"""


    grading_func = GRADING_STRATEGIES.get(question.question_type)
    if not grading_func:
        return False
    return grading_func(user_answer, question.correct_answer or {})

def get_formatted_user_answer(question: models.DBQuestion, user_answer: schemas.UserAnswer) -> Any:
    """获取用于AI prompt或展示的用户答案的原始格式。"""
    q_type = question.question_type
    if q_type == 'single_choice': return user_answer.answer_index
    if q_type == 'multiple_choice': return user_answer.answer_indices
    if q_type == 'fill_in_blank': return user_answer.answer_texts
    if q_type == 'essay': return user_answer.answer_text
    return None


# --- AI Interaction Services ---

async def generate_test_from_ai(knowledge_content: str, config: schemas.GenerateTestConfig) -> Dict[str, Any]:
    prompt = GENERATE_TEST_PROMPT.format(
        knowledge_content=knowledge_content,
        config_json=config.model_dump_json(indent=2)
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        response = await model.generate_content_async(prompt)
        return _extract_json_from_ai_response(response.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI test generation failed: {e}")

async def get_overall_feedback_from_ai(graded_info: List[Dict]) -> str:
    prompt = OVERALL_FEEDBACK_PROMPT.format(
        graded_info=json.dumps(graded_info, ensure_ascii=False, indent=2)
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI feedback generation failed: {e}")

async def get_single_question_feedback_from_ai(question: models.DBQuestion, user_answer: schemas.UserAnswer) -> str:
    q_type = question.question_type
    options = question.options or []
    user_answer_str = "未作答"

    if q_type == 'single_choice' and user_answer.answer_index is not None and 0 <= user_answer.answer_index < len(options):
        user_answer_str = options[user_answer.answer_index]
    elif q_type == 'multiple_choice' and user_answer.answer_indices:
        user_answer_str = ", ".join([options[i] for i in user_answer.answer_indices if 0 <= i < len(options)])
    elif q_type == 'fill_in_blank' and user_answer.answer_texts:
        user_answer_str = ", ".join(user_answer.answer_texts)
    elif q_type == 'essay' and user_answer.answer_text:
        user_answer_str = user_answer.answer_text
    
    prompt = SINGLE_QUESTION_FEEDBACK_PROMPT.format(
        question_content=question.stem,
        options=options,
        user_answer=user_answer_str,
        correct_answer=question.correct_answer or {},
        explanation=(question.correct_answer or {}).get('explanation', '')
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI feedback generation failed: {e}")

async def evaluate_essay_with_ai(request: schemas.EvaluateShortAnswerRequest) -> schemas.EvaluateShortAnswerResponse:
    prompt = EVALUATE_ESSAY_PROMPT.format(
        question_stem=request.question.stem,
        reference_explanation=request.question.reference_explanation,
        user_answer=request.user_answer
    )
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        response = await model.generate_content_async(prompt)
        ai_response_data = _extract_json_from_ai_response(response.text)
        
        # 将AI结果和原始参考答案合并到响应模型中
        return schemas.EvaluateShortAnswerResponse(
            **ai_response_data,
            reference_explanation=request.question.reference_explanation
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI evaluation failed: {e}")