import os
from typing import Optional, List

import google.generativeai as genai
from fastapi import Header, FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 清晰地从不同模块导入
from . import services
from . import schemas
from .models import Base, engine, get_db, TestPaper, DBQuestion, TestPaperResult

# --- App and Configuration Setup ---

# 在应用启动时创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI智能试卷助手 - 后端API",
    description="为AI智能试卷助手提供生成试卷、批改题目等功能的API服务。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def configure_genai(x_goog_api_key: Optional[str] = Header(None, alias="X-Goog-Api-Key")):
    """Dependency to configure Google AI with API key from header or environment."""
    api_key = x_goog_api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(400, "Google API Key is missing. Provide it in the 'X-Goog-Api-Key' header.")
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        raise HTTPException(500, f"Failed to configure Google AI: {e}")

# --- API Endpoints ---

@app.post("/generate-test", response_model=schemas.GenerateTestResponse)
async def generate_test(
    db: Session = Depends(get_db),
    source_file: Optional[UploadFile] = File(None),
    source_text: Optional[str] = Form(None),
    config_json: str = Form(...),
    _: None = Depends(configure_genai)
):
    if not source_file and not source_text:
        raise HTTPException(400, "Either source_file or source_text must be provided.")

    config = schemas.GenerateTestConfig.model_validate_json(config_json)
    knowledge_content = await source_file.read().decode('utf-8') if source_file else source_text

    ai_response = await services.generate_test_from_ai(knowledge_content, config)
    questions_data = [schemas.QuestionModel(**q) for q in ai_response.get('questions', [])]

    db_test_paper = TestPaper(source_type='file' if source_file else 'text', source_content=knowledge_content)
    db.add(db_test_paper)
    db.commit()
    db.refresh(db_test_paper)

    for q_model in questions_data:
        db.add(DBQuestion(
            test_paper_id=db_test_paper.id,
            question_type=q_model.type,
            stem=q_model.stem,
            options=q_model.options,
            correct_answer=q_model.answer.model_dump()
        ))
    db.commit()

    # 在返回前，为每个问题补充数据库生成的ID
    db.refresh(db_test_paper)
    for q_model, db_q in zip(questions_data, db_test_paper.questions):
        q_model.id = str(db_q.id)

    return schemas.GenerateTestResponse(test_id=str(db_test_paper.id), questions=questions_data)


@app.get("/test-papers/{test_id}", response_model=schemas.GenerateTestResponse)
async def get_test(test_id: int, db: Session = Depends(get_db)):
    test_paper = services.get_test_paper_by_id(db, test_id)
    questions_to_return = []
    for q in test_paper.questions:
        # 从DBQuestion构建QuestionModel
        question_data = {
            "id": str(q.id),
            "type": q.question_type, # 确保字段名称匹配
            "stem": q.stem,
            "options": q.options,
            "answer": q.correct_answer # 确保answer字段被填充
        }
        questions_to_return.append(schemas.QuestionModel(**question_data))

    return schemas.GenerateTestResponse(test_id=str(test_paper.id), questions=questions_to_return)


@app.post("/grade-questions", response_model=schemas.GradeQuestionsResponse)
async def grade_questions(request: schemas.GradeQuestionsRequest, db: Session = Depends(get_db)):
    test_paper = services.get_test_paper_by_id(db, int(request.test_id))
    questions_map = {str(q.id): q for q in test_paper.questions}
    
    results = [
        schemas.ObjectiveGradeResult(
            question_id=user_answer.question_id,
            is_correct=services.grade_objective_question(questions_map[user_answer.question_id], user_answer)
        )
        for user_answer in request.answers if user_answer.question_id in questions_map
    ]
    services.save_test_result(db, int(request.test_id), request.answers, results)

    return schemas.GradeQuestionsResponse(results=results)


@app.post("/generate-overall-feedback", response_model=schemas.GenerateOverallFeedbackResponse)
async def generate_overall_feedback(request: schemas.GenerateOverallFeedbackRequest, db: Session = Depends(get_db), _: None = Depends(configure_genai)):
    test_paper = services.get_test_paper_by_id(db, int(request.test_id))
    questions_map = {str(q.id): q for q in test_paper.questions}
    
    graded_info = []
    for user_answer in request.answers:
        question = questions_map.get(user_answer.question_id)
        if not question: continue
        
        graded_info.append({
            "stem": question.stem,
            "options": question.options,
            "user_answer": services.get_formatted_user_answer(question, user_answer),
            "correct_answer": question.correct_answer,
            "is_correct": services.grade_objective_question(question, user_answer),
            "explanation": (question.correct_answer or {}).get('explanation', '')
        })
    
    feedback = await services.get_overall_feedback_from_ai(graded_info)
    return schemas.GenerateOverallFeedbackResponse(feedback=feedback)


@app.post("/generate-single-question-feedback", response_model=schemas.GenerateSingleQuestionFeedbackResponse)
async def generate_single_question_feedback(request: schemas.GenerateSingleQuestionFeedbackRequest, db: Session = Depends(get_db), _: None = Depends(configure_genai)):
    question = services.get_question_by_id(db, int(request.question_id))
    user_answer = request.user_answer or schemas.UserAnswer(question_id=request.question_id)
    
    feedback = await services.get_single_question_feedback_from_ai(question, user_answer)
    return schemas.GenerateSingleQuestionFeedbackResponse(feedback=feedback)


@app.post("/evaluate-short-answer", response_model=schemas.EvaluateShortAnswerResponse)
async def evaluate_short_answer(request: schemas.EvaluateShortAnswerRequest, _: None = Depends(configure_genai)):
    response = await services.evaluate_essay_with_ai(request)
    return response


@app.get("/history", response_model=List[schemas.TestPaperResultSchema])
def get_history(db: Session = Depends(get_db)):
    return services.get_all_test_results(db)


@app.get("/history/{result_id}", response_model=schemas.TestPaperResultSchema)
def get_history_result(result_id: int, db: Session = Depends(get_db)):
    return services.get_test_result(db, result_id)