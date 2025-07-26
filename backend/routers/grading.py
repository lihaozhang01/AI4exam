# routers/grading.py

import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import services
import schemas
from models import get_db
from dependencies import configure_genai

router = APIRouter(
    tags=["Grading & Feedback"]
)

@router.post("/grade-questions", response_model=schemas.GradeQuestionsResponse)
async def grade_questions(request: schemas.GradeQuestionsRequest, db: Session = Depends(get_db)):
    db_result, grading_results = services.grade_and_save_test(
        db=db,
        test_id=int(request.test_id),
        user_answers=request.answers
    )
    return schemas.GradeQuestionsResponse(result_id=db_result.id, results=grading_results)


@router.post("/generate-overall-feedback", response_model=schemas.GenerateOverallFeedbackResponse)
async def generate_overall_feedback(
    request: schemas.GenerateOverallFeedbackRequest, 
    db: Session = Depends(get_db), 
    generation_model: Optional[str] = Header(None, alias="X-Generation-Model"),
    generation_prompt: Optional[str] = Header(None, alias="X-Generation-Prompt"),
    _: None = Depends(configure_genai)
):
    decoded_prompt = urllib.parse.unquote(generation_prompt) if generation_prompt else None
    feedback = await services.generate_and_save_overall_feedback(db, request, generation_model, decoded_prompt)
    return schemas.GenerateOverallFeedbackResponse(feedback=feedback)


@router.post("/generate-single-question-feedback", response_model=schemas.GenerateSingleQuestionFeedbackResponse)
async def generate_single_question_feedback(
    request: schemas.GenerateSingleQuestionFeedbackRequest, 
    db: Session = Depends(get_db), 
    generation_model: Optional[str] = Header(None, alias="X-Generation-Model"),
    generation_prompt: Optional[str] = Header(None, alias="X-Generation-Prompt"),
    _: None = Depends(configure_genai)
):
    decoded_prompt = urllib.parse.unquote(generation_prompt) if generation_prompt else None
    feedback = await services.generate_and_save_single_question_feedback(db, request, generation_model, decoded_prompt)
    return schemas.GenerateSingleQuestionFeedbackResponse(feedback=feedback)


@router.post("/evaluate-short-answer", response_model=schemas.EvaluateShortAnswerResponse)
async def evaluate_short_answer(
    request: schemas.EvaluateShortAnswerRequest, 
    generation_model: Optional[str] = Header(None, alias="X-Generation-Model"),
    generation_prompt: Optional[str] = Header(None, alias="X-Generation-Prompt"),
    _: None = Depends(configure_genai)
):
    decoded_prompt = urllib.parse.unquote(generation_prompt) if generation_prompt else None
    response = await services.evaluate_essay_with_ai(request, generation_model, decoded_prompt)
    return response