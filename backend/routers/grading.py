# routers/grading.py

import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import services
import schemas
from database import get_db
from dependencies import configure_genai

router = APIRouter(
    tags=["Grading & Feedback"]
)

@router.post("/grade-questions", response_model=schemas.GradeQuestionsResponse)
async def grade_questions(
    request: schemas.GradeQuestionsRequest, 
    db: Session = Depends(get_db),
    provider: str = Header(..., alias="X-Provider"),
    api_key: str = Header(..., alias="X-Api-Key"),
    evaluation_model: Optional[str] = Header(None, alias="X-Evaluation-Model"),
    evaluation_prompt: Optional[str] = Header(None, alias="X-Evaluation-Prompt")
):
    decoded_prompt = urllib.parse.unquote(evaluation_prompt) if evaluation_prompt else None
    db_result, grading_results = await services.grade_and_save_test(
        db=db,
        request=request,
        provider=provider,
        api_key=api_key,
        evaluation_model=evaluation_model,
        evaluation_prompt=decoded_prompt
    )
    return schemas.GradeQuestionsResponse(result_id=db_result.id, results=grading_results)


@router.post("/generate-overall-feedback", response_model=schemas.GenerateOverallFeedbackResponse)
async def generate_overall_feedback(
    request: schemas.GenerateOverallFeedbackRequest, 
    db: Session = Depends(get_db), 
    provider: str = Header(..., alias="X-Provider"),
    api_key: str = Header(..., alias="X-Api-Key"),
    evaluation_model: Optional[str] = Header(None, alias="X-Evaluation-Model"),
    overall_feedback_prompt: Optional[str] = Header(None, alias="X-Overall-Feedback-Prompt")
):
    decoded_prompt = urllib.parse.unquote(overall_feedback_prompt) if overall_feedback_prompt else None
    feedback = await services.generate_and_save_overall_feedback(db, request, provider, api_key, evaluation_model, decoded_prompt)
    return schemas.GenerateOverallFeedbackResponse(feedback=feedback)


@router.post("/generate-single-question-feedback", response_model=schemas.GenerateSingleQuestionFeedbackResponse)
async def generate_single_question_feedback(
    request: schemas.GenerateSingleQuestionFeedbackRequest, 
    db: Session = Depends(get_db), 
    provider: str = Header(..., alias="X-Provider"),
    api_key: str = Header(..., alias="X-Api-Key"),
    evaluation_model: Optional[str] = Header(None, alias="X-Evaluation-Model"),
    single_question_feedback_prompt: Optional[str] = Header(None, alias="X-Single-Question-Feedback-Prompt")
):
    decoded_prompt = urllib.parse.unquote(single_question_feedback_prompt) if single_question_feedback_prompt else None
    feedback = await services.generate_and_save_single_question_feedback(db, request, provider, api_key, evaluation_model, decoded_prompt)
    return schemas.GenerateSingleQuestionFeedbackResponse(feedback=feedback)


@router.post("/evaluate-short-answer", response_model=schemas.EvaluateShortAnswerResponse)
async def evaluate_short_answer(
    request: schemas.EvaluateShortAnswerRequest, 
    provider: str = Header(..., alias="X-Provider"),
    api_key: str = Header(..., alias="X-Api-Key"),
    evaluation_model: Optional[str] = Header(None, alias="X-Evaluation-Model"),
    evaluation_prompt: Optional[str] = Header(None, alias="X-Evaluation-Prompt")
):
    decoded_prompt = urllib.parse.unquote(evaluation_prompt) if evaluation_prompt else None
    response = await services.evaluate_essay_with_ai(request, provider, api_key, evaluation_model, decoded_prompt)
    return response