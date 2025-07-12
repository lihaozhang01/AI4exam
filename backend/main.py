import os
import json
import uuid
import re
from typing import Optional, Dict, Any
from fastapi import Header
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .models import (
    SessionLocal, TestPaper, Question as DBQuestion, get_db,
    GenerateTestConfig,
    GenerateTestResponse,
    GradeQuestionsRequest,
    GradeQuestionsResponse,
    EvaluateShortAnswerRequest,
    EvaluateShortAnswerResponse,
    QuestionModel,
    ObjectiveGradeResult,
    EssayGradeResult,
    GenerateOverallFeedbackRequest,
    GenerateOverallFeedbackResponse,
    GenerateSingleQuestionFeedbackRequest,
    GenerateSingleQuestionFeedbackResponse
)
from .prompts import GENERATE_TEST_PROMPT, EVALUATE_ESSAY_PROMPT, OVERALL_FEEDBACK_PROMPT, SINGLE_QUESTION_FEEDBACK_PROMPT

def configure_genai(x_goog_api_key: Optional[str] = Header(None, alias="X-Goog-Api-Key")):
    """
    Dependency function to configure Google AI with the API key from the request header.
    """
    api_key = x_goog_api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Google API Key is missing. Please provide it in the 'X-Goog-Api-Key' header."
        )
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure Google AI: {e}")

# Create database tables on startup
from .models import Base, engine
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI智能试卷助手 - 后端API",
    description="为AI智能试卷助手提供生成试卷、批改题目等功能的API服务。",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # 明确指定前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test(
    source_file: Optional[UploadFile] = File(None),
    source_text: Optional[str] = Form(None),
    config_json: str = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(configure_genai)
):
    """
    生成试卷接口。
    """
    if not source_file and not source_text:
        raise HTTPException(status_code=400, detail="Either source_file or source_text must be provided.")

    try:
        config = GenerateTestConfig.parse_raw(config_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid config_json: {e}")

    # 1. 读取知识源内容
    knowledge_content = ""
    if source_text:
        knowledge_content = source_text
    elif source_file:
        try:
            contents = await source_file.read()
            knowledge_content = contents.decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    # 2. 构建Prompt
    prompt = GENERATE_TEST_PROMPT.format(
        knowledge_content=knowledge_content,
        config_json=config.model_dump_json(indent=2)
    )

    # 3. 调用AI模型
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("Sending request to Google AI...")
        # Set stream=False to get the full response at once
        response = await model.generate_content_async(prompt, stream=False)
        print("Received full response from Google AI.")

        # Since stream=False, response.text should contain the full response
        if not response.text:
            raise HTTPException(status_code=500, detail="AI response was empty.")

        full_response_text = response.text

        # 使用正则表达式从响应中提取JSON代码块
        match = re.search(r"```json\n(.*?)\n```", full_response_text, re.DOTALL)
        if not match:
            try:
                ai_response = json.loads(full_response_text)
            except json.JSONDecodeError:
                print(f"Raw AI Response causing JSON error: {full_response_text}")
                raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON and no JSON block was found.")
        else:
            json_response_str = match.group(1).strip()
            try:
                ai_response = json.loads(json_response_str)
            except json.JSONDecodeError:
                print(f"Extracted JSON string causing error: {json_response_str}")
                raise HTTPException(status_code=500, detail="Failed to parse extracted JSON from AI response.")

        questions = [QuestionModel(**q) for q in ai_response['questions']]

    except Exception as e:
        print(f"An unexpected error occurred during AI generation: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    # 4. 将生成的试卷数据存入数据库
    db_test_paper = TestPaper(
        source_type='text' if source_text else 'file',
        source_content=knowledge_content
    )
    db.add(db_test_paper)
    db.commit()
    db.refresh(db_test_paper)

    for q_model in questions:
        db_question = DBQuestion(
            test_paper_id=db_test_paper.id,
            question_type=q_model.type,
            stem=q_model.stem,
            options=q_model.options,  # options is likely a list of strings, directly savable to JSON field
            correct_answer=q_model.answer.model_dump() if hasattr(q_model.answer, 'model_dump') else q_model.answer,
        )
        db.add(db_question)
    db.commit()

    # 5. 返回结果
    return GenerateTestResponse(test_id=str(db_test_paper.id), questions=questions)

@app.get("/get-test/{test_id}")
async def get_test(test_id: int, db: Session = Depends(get_db)):
    test_paper = db.query(TestPaper).filter(TestPaper.id == test_id).first()
    if not test_paper:
        raise HTTPException(status_code=404, detail="Test not found")
    
    questions = []
    for q in test_paper.questions:
        question_data = {
            "id": str(q.id),
            "type": q.question_type,
            "stem": q.stem,
            "options": q.options,
            "answer": q.correct_answer
        }
        questions.append(QuestionModel(**question_data))
        
    return GenerateTestResponse(test_id=str(test_paper.id), questions=questions)

@app.post("/grade-questions", response_model=GradeQuestionsResponse)
async def grade_questions(request: GradeQuestionsRequest, db: Session = Depends(get_db)):
    """
    批量批改客观题接口（仅返回对错，不进行AI分析）。
    """
    test_paper = db.query(TestPaper).filter(TestPaper.id == int(request.test_id)).first()
    if not test_paper:
        raise HTTPException(status_code=404, detail="Test ID not found")

    questions_map = {str(q.id): q for q in test_paper.questions}
    results = []

    for user_answer_obj in request.answers:
        question_id = user_answer_obj.question_id
        question = questions_map.get(question_id)
        if not question:
            continue

        correct_answer_json = question.correct_answer

        # 根据题目类型分别处理
        if user_answer_obj.question_type == 'essay':
            if hasattr(user_answer_obj, 'answer_text'):
                results.append(EssayGradeResult(
                    question_id=question_id,
                    user_answer=user_answer_obj.answer_text,
                    reference_explanation=correct_answer_json.get('reference_explanation', '')
                ))
        else:  # 处理所有客观题
            is_correct = False
            user_response = None
            if user_answer_obj.question_type == 'single_choice' and hasattr(user_answer_obj, 'answer_index'):
                user_response = user_answer_obj.answer_index
                is_correct = (user_response == correct_answer_json.get('correct_option_index'))
            elif user_answer_obj.question_type == 'multiple_choice' and hasattr(user_answer_obj, 'answer_indices'):
                user_response = user_answer_obj.answer_indices
                is_correct = (sorted(user_response) == sorted(correct_answer_json.get('correct_option_indices', [])))
            elif user_answer_obj.question_type == 'fill_in_the_blank' and hasattr(user_answer_obj, 'answer_texts'):
                user_response = user_answer_obj.answer_texts
                # 同样转换为集合来判断，忽略顺序和重复
                is_correct = (set(map(str.strip, user_response)) == set(map(str.strip, correct_answer_json.get('correct_answers', []))))

            # 添加评分结果
            results.append(ObjectiveGradeResult(
                question_id=question_id,
                is_correct=is_correct,
                user_answer=user_response,
                correct_answer=correct_answer_json
            ))

    return GradeQuestionsResponse(results=results)


@app.post("/generate-overall-feedback", response_model=GenerateOverallFeedbackResponse)
async def generate_overall_feedback(request: GenerateOverallFeedbackRequest, db: Session = Depends(get_db), _: None = Depends(configure_genai)):
    """
    为整个试卷生成AI反馈和点评。
    """
    test_paper = db.query(TestPaper).filter(TestPaper.id == int(request.test_id)).first()
    if not test_paper:
        raise HTTPException(status_code=404, detail="Test ID not found")

    questions_map = {str(q.id): q for q in test_paper.questions}
    graded_info_for_ai = []

    for user_answer_obj in request.answers:
        question_id = user_answer_obj.question_id
        question = questions_map.get(question_id)
        if not question:
            continue

        correct_answer_json = question.correct_answer
        user_response: Any = None
        is_correct = False

        if user_answer_obj.question_type == 'single_choice' and hasattr(user_answer_obj, 'answer_index'):
            user_response = user_answer_obj.answer_index
            is_correct = (user_response == correct_answer_json.get('correct_option_index'))
        elif user_answer_obj.question_type == 'multiple_choice' and hasattr(user_answer_obj, 'answer_indices'):
            user_response = user_answer_obj.answer_indices
            is_correct = (sorted(user_response) == sorted(correct_answer_json.get('correct_option_indices', [])))
        elif user_answer_obj.question_type == 'fill_in_the_blank' and hasattr(user_answer_obj, 'answer_texts'):
            user_response = user_answer_obj.answer_texts
            is_correct = (set(map(str.strip, user_response)) == set(map(str.strip, correct_answer_json.get('correct_answers', []))))
        elif user_answer_obj.question_type == 'essay' and hasattr(user_answer_obj, 'answer_text'):
             user_response = user_answer_obj.answer_text
             is_correct = False # Essay questions are not bool-correct

        graded_info_for_ai.append({
            "stem": question.stem,
            "options": question.options,
            "user_answer": user_response,
            "correct_answer": correct_answer_json,
            "is_correct": is_correct,
            "explanation": correct_answer_json.get('explanation', '') if correct_answer_json else ''
        })

    try:
        prompt = OVERALL_FEEDBACK_PROMPT.format(
            graded_info=json.dumps(graded_info_for_ai, ensure_ascii=False, indent=2)
        )
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await model.generate_content_async(prompt)
        return GenerateOverallFeedbackResponse(feedback=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI feedback generation failed: {e}")

@app.post("/generate-single-question-feedback", response_model=GenerateSingleQuestionFeedbackResponse)
async def generate_single_question_feedback(request: GenerateSingleQuestionFeedbackRequest, db: Session = Depends(get_db), _: None = Depends(configure_genai)):
    """
    为单个问题生成AI反馈。
    """
    question = db.query(DBQuestion).filter(DBQuestion.id == int(request.question_id)).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question ID not found")

    user_answer_str = ""
    user_answer_data = request.user_answer

    if user_answer_data is None:
        user_answer_str = "未作答"
    else:
        question_type = question.question_type
        if question_type == 'single_choice' and user_answer_data.answer_index is not None:
            if question.options and 0 <= user_answer_data.answer_index < len(question.options):
                user_answer_str = question.options[user_answer_data.answer_index]
            else:
                user_answer_str = "无效答案索引"
        elif question_type == 'multiple_choice' and user_answer_data.answer_indices is not None:
            options = question.options or []
            user_answers = [options[i] for i in user_answer_data.answer_indices if 0 <= i < len(options)]
            user_answer_str = ", ".join(user_answers) if user_answers else "未作答"
        elif question_type == 'fill_in_the_blank' and user_answer_data.answer_texts is not None:
            user_answer_str = ", ".join(user_answer_data.answer_texts) if user_answer_data.answer_texts else "未作答"
        elif question_type == 'essay' and user_answer_data.answer_text is not None:
            user_answer_str = user_answer_data.answer_text
        else:
            user_answer_str = "未提供有效答案"

    correct_answer = question.correct_answer
    explanation = correct_answer.get('explanation', '') if correct_answer else ''

    try:
        prompt = SINGLE_QUESTION_FEEDBACK_PROMPT.format(
            question_content=question.stem,
            options=question.options,
            user_answer=user_answer_str,
            correct_answer=correct_answer,
            explanation=explanation
        )
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await model.generate_content_async(prompt)
        return GenerateSingleQuestionFeedbackResponse(feedback=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI feedback generation failed: {e}")

@app.post("/evaluate-short-answer", response_model=EvaluateShortAnswerResponse)
async def evaluate_short_answer(request: EvaluateShortAnswerRequest, _: None = Depends(configure_genai)):
    """
    批改简答/论述题接口。
    """
    # 1. 构建Prompt
    prompt = EVALUATE_ESSAY_PROMPT.format(
        question_stem=request.question.stem,
        reference_explanation=request.question.reference_explanation,
        user_answer=request.user_answer
    )

    # 2. 调用AI模型
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await model.generate_content_async(prompt)
        
        # 使用正则表达式从响应中提取JSON代码块
        match = re.search(r"```json\n(.*?)\n```", response.text, re.DOTALL)
        if not match:
            # 如果没有找到代码块，尝试直接解析整个文本
            try:
                ai_response = json.loads(response.text)
            except json.JSONDecodeError:
                 raise HTTPException(status_code=500, detail="Failed to parse AI response for evaluation.")
        else:
            json_response_str = match.group(1).strip()
            ai_response = json.loads(json_response_str)
        
        # 将AI返回的评估结果和原始的参考答案合并
        response_data = ai_response
        response_data['reference_explanation'] = request.question.reference_explanation

        return EvaluateShortAnswerResponse(**response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)