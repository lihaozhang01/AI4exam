import os
import json
import uuid
import re
import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional

from models import (
    GenerateTestConfig,
    GenerateTestResponse,
    GradeQuestionsRequest,
    GradeQuestionsResponse,
    EvaluateShortAnswerRequest,
    EvaluateShortAnswerResponse,
    Question,
    ObjectiveGradeResult,
    EssayGradeResult,
    GenerateOverallFeedbackRequest,
    GenerateOverallFeedbackResponse,
    GenerateSingleQuestionFeedbackRequest,
    GenerateSingleQuestionFeedbackResponse
)
from prompts import GENERATE_TEST_PROMPT, EVALUATE_ESSAY_PROMPT, OVERALL_FEEDBACK_PROMPT, SINGLE_QUESTION_FEEDBACK_PROMPT

# 加载环境变量
load_dotenv()

# 配置Google Gemini API
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
genai.configure(api_key=GEMINI_API_KEY)

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

# 全局的内存存储，用于保存生成的试卷数据以供后续批改使用
# key: test_id, value: { "questions": List[Question], "answers": Dict[str, Any] }
mock_test_data: dict = {}


@app.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test(
    source_file: Optional[UploadFile] = File(None),
    source_text: Optional[str] = Form(None),
    config_json: str = Form(...)
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
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await model.generate_content_async(prompt)

        # 异步迭代，拼接完整的AI响应文本
        full_response_text = ""
        async for chunk in response:
            try:
                full_response_text += chunk.text
            except Exception as e:
                # 处理可能出现的无text属性的chunk
                pass
        
        # 使用正则表达式从响应中提取JSON代码块
        match = re.search(r"```json\n(.*?)\n```", full_response_text, re.DOTALL)
        if not match:
            # 如果没有找到代码块，尝试直接解析整个文本，以防AI直接返回纯JSON
            try:
                ai_response = json.loads(full_response_text)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON.")
        else:
            json_response_str = match.group(1).strip()
            ai_response = json.loads(json_response_str)
        
        questions = [Question(**q) for q in ai_response['questions']]

    except Exception as e:
        # 这里可以添加更详细的日志记录
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    # 4. 存储生成的试卷和答案以备后续批改
    test_id = str(uuid.uuid4())
    answers_for_grading = {}
    for q in questions:
        # 根据API.md的定义，为不同题型提取正确答案
        if q.type == 'single_choice' and hasattr(q.answer, 'correct_option_index'):
            answers_for_grading[q.id] = q.answer.correct_option_index
        elif q.type == 'multiple_choice' and hasattr(q.answer, 'correct_option_indices'):
            answers_for_grading[q.id] = q.answer.correct_option_indices
        elif q.type == 'fill_in_the_blank' and hasattr(q.answer, 'correct_answers'):
            answers_for_grading[q.id] = q.answer.correct_answers
        elif q.type == 'essay' and hasattr(q.answer, 'reference_explanation'):
            # 论述题没有标准答案，但可以把参考答案存起来，以便后续查看或给AI评估用
            answers_for_grading[q.id] = q.answer.reference_explanation

    mock_test_data[test_id] = {
        "questions": questions,
        "answers": answers_for_grading
    }

    # 5. 返回结果
    return GenerateTestResponse(test_id=test_id, questions=questions)

@app.post("/grade-questions", response_model=GradeQuestionsResponse)
async def grade_questions(request: GradeQuestionsRequest):
    """
    批量批改客观题接口（仅返回对错，不进行AI分析）。
    """
    test_data = mock_test_data.get(request.test_id)
    if not test_data:
        raise HTTPException(status_code=404, detail="Test ID not found")

    correct_answers_map = test_data["answers"]
    questions_map = {q.id: q for q in test_data["questions"]}
    results = []

    for user_answer_obj in request.answers:
        question_id = user_answer_obj.question_id
        user_response = None
        if hasattr(user_answer_obj, 'answer_index'):
            user_response = user_answer_obj.answer_index
        elif hasattr(user_answer_obj, 'answer_indices'):
            user_response = user_answer_obj.answer_indices
        elif hasattr(user_answer_obj, 'answer_texts'):
            user_response = user_answer_obj.answer_texts

        correct_answer = correct_answers_map.get(question_id)
        question = questions_map.get(question_id)

        if question is None:
            continue

        # 根据题目类型分别处理
        if user_answer_obj.question_type == 'essay':
            # 确保我们正在处理一个包含 'answer_text' 的对象
            if hasattr(user_answer_obj, 'answer_text'):
                results.append(EssayGradeResult(
                    question_id=question_id,
                    user_answer=user_answer_obj.answer_text,
                    reference_explanation=correct_answers_map.get(question_id, "")
                ))
        else: # 处理所有客观题
            user_response = None
            correct_answer = correct_answers_map.get(question_id)

            if correct_answer is None:
                continue
            
            is_correct = False
            if user_answer_obj.question_type == 'single_choice':
                user_response = user_answer_obj.answer_index
                is_correct = (user_response == correct_answer)
            elif user_answer_obj.question_type == 'multiple_choice':
                user_response = user_answer_obj.answer_indices
                # 对列表进行排序，确保顺序不影响判断
                is_correct = (sorted(user_response) == sorted(correct_answer))
            elif user_answer_obj.question_type == 'fill_in_the_blank':
                user_response = user_answer_obj.answer_texts
                # 同样转换为集合来判断，忽略顺序和重复
                is_correct = (set(map(str, user_response)) == set(map(str, correct_answer)))

            results.append(ObjectiveGradeResult(
                question_id=question_id,
                is_correct=is_correct,
                user_answer=user_response,
                correct_answer=correct_answer
            ))

    return GradeQuestionsResponse(results=results)


@app.post("/generate-overall-feedback", response_model=GenerateOverallFeedbackResponse)
async def generate_overall_feedback(request: GenerateOverallFeedbackRequest):
    """
    为整个试卷生成AI反馈和点评。
    """
    test_data = mock_test_data.get(request.test_id)
    if not test_data:
        raise HTTPException(status_code=404, detail="Test ID not found")

    correct_answers_map = test_data["answers"]
    questions_map = {q.id: q for q in test_data["questions"]}
    graded_info_for_ai = []

    for user_answer_obj in request.answers:
        question_id = user_answer_obj.question_id
        user_response = None
        if hasattr(user_answer_obj, 'answer_index'):
            user_response = user_answer_obj.answer_index
        elif hasattr(user_answer_obj, 'answer_indices'):
            user_response = user_answer_obj.answer_indices
        elif hasattr(user_answer_obj, 'answer_texts'):
            user_response = user_answer_obj.answer_texts

        correct_answer = correct_answers_map.get(question_id)
        question = questions_map.get(question_id)

        if correct_answer is None or question is None:
            continue

        is_correct = False
        if question.type == 'single_choice':
            is_correct = (user_response == correct_answer)
        elif question.type == 'multiple_choice':
            is_correct = (sorted(user_response) == sorted(correct_answer))
        elif question.type == 'fill_in_the_blank':
            is_correct = (set(map(str, user_response)) == set(map(str, correct_answer)))

        graded_info_for_ai.append({
            "stem": question.stem,
            "options": question.options,
            "user_answer": user_response,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": getattr(question.answer, 'explanation', '')
        })

    try:
        prompt = OVERALL_FEEDBACK_PROMPT.format(
            graded_info=json.dumps(graded_info_for_ai, ensure_ascii=False, indent=2)
        )
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        return GenerateOverallFeedbackResponse(feedback=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI feedback generation failed: {e}")

@app.post("/generate-single-question-feedback", response_model=GenerateSingleQuestionFeedbackResponse)
async def generate_single_question_feedback(request: GenerateSingleQuestionFeedbackRequest):
    """
    为单个问题生成AI反馈。
    """
    test_data = mock_test_data.get(request.test_id)
    if not test_data:
        raise HTTPException(status_code=404, detail="Test ID not found")

    question = next((q for q in test_data["questions"] if q.id == request.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question ID not found")

    correct_answer = test_data["answers"].get(request.question_id)
    user_answer_obj = request.user_answers.get(request.question_id)
    user_answer_str = ""
    if user_answer_obj is None:
        user_answer_str = "未作答"
    else:
        question_type = question.type
        if question_type == 'single_choice':
            answer_index = user_answer_obj.answer_index
            if answer_index is not None and 0 <= answer_index < len(question.options):
                user_answer_str = question.options[answer_index]
            else:
                user_answer_str = "无效答案"
        elif question_type == 'multiple_choice':
            answer_indices = user_answer_obj.answer_indices
            options = question.options
            user_answers = [options[i] for i in answer_indices if 0 <= i < len(options)]
            user_answer_str = ", ".join(user_answers) if user_answers else "未作答"
        elif question_type == 'fill_in_the_blank':
            answer_texts = user_answer_obj.answer_texts
            user_answer_str = ", ".join(answer_texts) if answer_texts else "未作答"
        else:
            user_answer_str = "暂不支持该题型"

    try:
        prompt = SINGLE_QUESTION_FEEDBACK_PROMPT.format(
            question_content=question.stem,
            options=question.options,
            user_answer=user_answer_str,
            correct_answer=correct_answer,
            explanation=getattr(question.answer, 'explanation', '')
        )
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        return GenerateSingleQuestionFeedbackResponse(feedback=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI feedback generation failed: {e}")

@app.post("/evaluate-short-answer", response_model=EvaluateShortAnswerResponse)
async def evaluate_short_answer(request: EvaluateShortAnswerRequest):
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
        model = genai.GenerativeModel('gemini-pro')
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