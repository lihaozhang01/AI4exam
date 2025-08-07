# services/orchestration.py

from typing import List
from sqlalchemy.orm import Session

import models
import schemas
from . import database
from . import grading
from . import ai
def grade_and_save_test(db: Session, test_id: int, user_answers: List[schemas.UserAnswer]):
    """Grades a test submission, calculates statistics, and saves everything."""
    test_paper = get_test_paper_by_id(db, test_id)
    questions_map = {str(q.id): q for q in test_paper.questions}

    grading_results = []
    correct_objective_count = 0
    total_objective_count = 0
    total_essay_count = 0

    # Classify all questions first
    for question in test_paper.questions:
        if question.question_type in GRADING_STRATEGIES:
            total_objective_count += 1
        elif question.question_type == 'essay':
            total_essay_count += 1

    # Grade submitted answers
    for user_answer in user_answers:
        question = questions_map.get(str(user_answer.question_id))
        if not question:
            continue

        # 如果是论述题，直接提取参考答案，不进行评分
        if question.question_type == 'essay':
            explanation = ""
            # 参考答案存储在 correct_answer['reference_explanation'] 中
            if isinstance(question.correct_answer, dict):
                explanation = question.correct_answer.get('reference_explanation', '')
            elif isinstance(question.correct_answer, str):
                # 兼容旧数据或意外的字符串格式
                explanation = question.correct_answer
            else:
                explanation = ""
            
            grading_results.append(schemas.EssayGradeResult(
                question_id=user_answer.question_id,
                reference_explanation=explanation
            ))
            continue

        # 处理客观题
        if question.question_type not in GRADING_STRATEGIES:
            continue

        is_correct = grade_objective_question(question, user_answer)
        if is_correct:
            correct_objective_count += 1
        
        grading_results.append(schemas.ObjectiveGradeResult(
            question_id=user_answer.question_id, 
            is_correct=is_correct
        ))

    # Convert Pydantic models to dictionaries for JSON serialization
    user_answers_dicts = [ans.model_dump() for ans in user_answers]
    grading_results_dicts = [res.model_dump() for res in grading_results]

    # Create and save the result
    db_result = models.TestPaperResult(
        test_paper_id=test_id,
        user_answers=user_answers_dicts,
        grading_results=grading_results_dicts
    )

    db.add(db_result)
    db.commit()
    db.refresh(db_result)

    return db_result, grading_results
async def generate_and_save_overall_feedback(
    db: Session, 
    request: schemas.GenerateOverallFeedbackRequest,
    provider: str,
    api_key: str,
    evaluation_model: str = None,
    overall_feedback_prompt: str = None
) -> str:
    """Generates overall feedback, saves it to the specific result, and returns the feedback."""
    test_paper = database.get_test_paper_by_id(db, int(request.test_id))
    questions_map = {str(q.id): q for q in test_paper.questions}

    graded_info = []
    for user_answer in request.answers:
        question = questions_map.get(user_answer.question_id)
        if not question: continue

        graded_info.append({
            "stem": question.stem,
            "options": question.options,
            "user_answer": grading.get_formatted_user_answer(question, user_answer),
            "correct_answer": question.correct_answer,
            "is_correct": grading.grade_objective_question(question, user_answer),
            "explanation": (question.correct_answer or {}).get('explanation', '')
        })

    feedback = await ai.get_overall_feedback_from_ai(graded_info, provider, api_key, evaluation_model, overall_feedback_prompt)

    # Save the feedback to the database
    test_result = database.get_test_result_by_id(db, request.result_id)
    test_result.overall_feedback = feedback
    db.commit()

    return feedback


async def generate_and_save_single_question_feedback(
    db: Session, 
    request: schemas.GenerateSingleQuestionFeedbackRequest,
    provider: str,
    api_key: str,
    evaluation_model: str = None,
    single_question_feedback_prompt: str = None
) -> str:
    """Generates feedback for a single question, saves it, and returns it."""
    question = database.get_question_by_id(db, int(request.question_id))
    user_answer = request.user_answer or schemas.UserAnswer(question_id=request.question_id, question_type=question.question_type)

    feedback = await ai.get_single_question_feedback_from_ai(question, user_answer, provider, api_key, evaluation_model, single_question_feedback_prompt)

    # Save the feedback to the database
    test_result = database.get_test_result_by_id(db, request.result_id)
    if test_result.question_feedbacks is None:
        test_result.question_feedbacks = {}
    
    # Use mutable_json from sqlalchemy.dialects.postgresql import JSONB
    # For sqlite, we have to copy and reassign
    new_feedbacks = test_result.question_feedbacks.copy()
    new_feedbacks[request.question_id] = feedback
    test_result.question_feedbacks = new_feedbacks
    
    db.commit()

    return feedback