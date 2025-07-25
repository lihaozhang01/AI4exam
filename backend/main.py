import os
from typing import Optional, List
import uvicorn  # --- 新增的導入 ---

import google.generativeai as genai
from fastapi import Header, FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 清晰地从不同模块导入
import services
import schemas
from models import Base, engine, get_db, TestPaper, DBQuestion, TestPaperResult

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

import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_genai(x_goog_api_key: Optional[str] = Header(None, alias="X-Goog-Api-Key")):
    """Dependency to configure Google AI with API key from header or environment."""
    api_key = x_goog_api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("API Key is missing from 'X-Goog-Api-Key' header and environment.")
        raise HTTPException(400, "Google API Key is missing. Provide it in the 'X-Goog-Api-Key' header.")
    
    logger.info(f"Received API Key ending with '...{api_key[-4:]}'. Attempting to configure genai.")
    try:
        genai.configure(api_key=api_key)
        logger.info("Successfully configured Google AI.")
    except Exception as e:
        logger.error(f"Failed to configure Google AI: {e}")
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
    file_content = await source_file.read().decode('utf-8') if source_file else ""
    text_content = source_text if source_text else ""
    # Combine file content and text content
    knowledge_content = ""
    if file_content:
        knowledge_content += f"""以下是文件内容：
{file_content}
"""
    if text_content:
        knowledge_content += f"""以下是用户输入内容：
{text_content}
"""
    knowledge_content = knowledge_content.strip()
    config.knowledge_content = knowledge_content

    ai_response = await services.generate_test_from_ai(config)

    # 使用service函数创建试卷和问题
    db_test_paper = services.create_test_paper(db, knowledge_content, ai_response)

    # 从数据库记录构建响应模型
    questions_data = [
        schemas.QuestionModel(
            id=str(q.id),
            type=q.question_type,
            stem=q.stem,
            options=q.options,
            answer=q.correct_answer
        )
        for q in db_test_paper.questions
    ]

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
    # 调用新的服务函数，该函数会处理评分和保存的整个流程
    
    db_result, grading_results = services.grade_and_save_test(
        db=db,
        test_id=int(request.test_id),
        user_answers=request.answers
    )

    # API直接返回后端生成的评分结果
    return schemas.GradeQuestionsResponse(results=grading_results)


@app.post("/generate-overall-feedback", response_model=schemas.GenerateOverallFeedbackResponse)
async def generate_overall_feedback(request: schemas.GenerateOverallFeedbackRequest, db: Session = Depends(get_db), _: None = Depends(configure_genai)):
    feedback = await services.generate_and_save_overall_feedback(db, request)
    return schemas.GenerateOverallFeedbackResponse(feedback=feedback)


@app.post("/generate-single-question-feedback", response_model=schemas.GenerateSingleQuestionFeedbackResponse)
async def generate_single_question_feedback(request: schemas.GenerateSingleQuestionFeedbackRequest, db: Session = Depends(get_db), _: None = Depends(configure_genai)):
    feedback = await services.generate_and_save_single_question_feedback(db, request)
    return schemas.GenerateSingleQuestionFeedbackResponse(feedback=feedback)


@app.post("/evaluate-short-answer", response_model=schemas.EvaluateShortAnswerResponse)
async def evaluate_short_answer(request: schemas.EvaluateShortAnswerRequest, _: None = Depends(configure_genai)):
    response = await services.evaluate_essay_with_ai(request)
    return response
@app.post("/test-connectivity")
async def test_connectivity(_: None = Depends(configure_genai)):
    try:
        # The `configure_genai` dependency has already handled the key configuration.
        # We perform a lightweight API call here to further confirm the key's validity.
        genai.list_models()
        return {"message": "API Key is valid and connectivity is successful."}
    except Exception as e:
        logger.error(f"Connectivity test failed during model listing: {e}")
        raise HTTPException(status_code=400, detail=f"Connectivity test failed: {e}")

@app.get("/history", response_model=List[schemas.TestPaperResult])
def get_history(db: Session = Depends(get_db)):
    return services.get_all_test_results(db)


@app.get("/history/{result_id}", response_model=schemas.TestPaperResult)
def get_history_result(result_id: int, db: Session = Depends(get_db)):
    result = services.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@app.delete("/history/{result_id}", status_code=204)
def delete_history_result(result_id: int, db: Session = Depends(get_db)):
    success = services.delete_test_result(db, result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test result not found")
    return {"message": "Test result deleted successfully"}

# --- 新增：启动服务器的部分 ---
if __name__ == "__main__":
    # 使用 uvicorn 来运行 FastAPI 应用
    # host="0.0.0.0" 使其可以在局域网内被访问，对于Electron来说更稳定
    uvicorn.run(app, host="0.0.0.0", port=8000)