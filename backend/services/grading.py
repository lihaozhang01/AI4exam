# services/grading.py

from typing import Dict, Any, Callable, List
import schemas
import models

# --- Objective Question Grading Logic (Strategy Pattern) ---

def _grade_single_choice(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    """評分單選題"""
    return user_answer.answer_index is not None and user_answer.answer_index == correct_answer.get('index')

def _grade_multiple_choice(user_answer: schemas.UserAnswer, correct_answer: Dict) -> bool:
    """評分多選題"""
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

GRADING_STRATEGIES: Dict[str, Callable[[schemas.UserAnswer, Dict], bool]] = {
    'single_choice': _grade_single_choice,
    'multiple_choice': _grade_multiple_choice,
    'fill_in_the_blank': _grade_fill_in_blank,
}

def grade_objective_question(question: models.DBQuestion, user_answer: schemas.UserAnswer) -> bool:
    """根據題型分發並批改单个客觀題。"""
    grading_func = GRADING_STRATEGIES.get(question.question_type)
    if not grading_func:
        return False
    return grading_func(user_answer, question.correct_answer or {})

def get_formatted_user_answer(question: models.DBQuestion, user_answer: schemas.UserAnswer) -> Any:
    """獲取用於AI prompt或展示的用戶答案的原始格式。"""
    q_type = question.question_type
    if q_type == 'single_choice': return user_answer.answer_index
    if q_type == 'multiple_choice': return user_answer.answer_indices
    if q_type == 'fill_in_blank': return user_answer.answer_texts
    if q_type == 'essay': return user_answer.answer_text
    return None