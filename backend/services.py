import json
import re
from typing import Dict, Any, Callable, List

import google.generativeai as genai
from fastapi import HTTPException
from sqlalchemy.orm import Session

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

def get_question_by_id(db: Session, question_id: int) -> models.DBQuestion:
    """通过ID从数据库获取问题，如果找不到则抛出404异常。"""
    question = db.query(models.DBQuestion).filter(models.DBQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found.")
    return question


# --- Objective Question Grading Logic (Strategy Pattern) ---

def _grade_single_choice(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    return user_answer.answer_index is not None and user_answer.answer_index == correct_answer.get('index')

def _grade_multiple_choice(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    return set(user_answer.answer_indices or []) == set(correct_answer.get('indexes', []))

def _grade_fill_in_blank(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    # The frontend joins answers with '$$$', so we need to split them here.
    user_texts = user_answer.answer.split('$$$') if isinstance(user_answer.answer, str) else []
    correct_texts = correct_answer.get('texts', [])
    
    # Strip whitespace from both user's answers and correct answers.
    user_texts_stripped = [text.strip() for text in user_texts]
    correct_texts_stripped = [text.strip() for text in correct_texts]
    
    return user_texts_stripped == correct_texts_stripped
    # 使用列表比较，确保

GRADING_STRATEGIES: Dict[str, Callable[[schemas.UserAnswer, Dict], bool]] = {
    'single_choice': _grade_single_choice,
    'multiple_choice': _grade_multiple_choice,
    'fill_in_blank': _grade_fill_in_blank,
}

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