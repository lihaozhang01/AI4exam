from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
import json
import uuid

from models import (
    GenerateTestConfig,
    QuestionConfig,
    GenerateTestResponse,
    Question,
    MultipleChoiceAnswer,
    GradeObjectiveQuestionsRequest,
    GradeObjectiveQuestionsResponse,
    GradeResult,
    EvaluateShortAnswerRequest,
    EvaluateShortAnswerResponse,
    QuestionInfo
)

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for mock test data (for test_id lookup)
mock_test_data = {}

@app.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test(
    knowledge_content: str = Form(...),
    test_config: str = Form(...)
):
    """
    生成试卷接口。
    """
    try:
        config_data = json.loads(test_config)
        config = GenerateTestConfig(
            description=knowledge_content,
            question_config=[
                QuestionConfig(type='single_choice', count=config_data['questionCounts']['single_choice']),
                QuestionConfig(type='multiple_choice', count=config_data['questionCounts']['multiple_choice']),
                QuestionConfig(type='fill_in_the_blank', count=config_data['questionCounts']['fill_in_the_blank']),
                QuestionConfig(type='essay', count=config_data['questionCounts']['essay']),
            ],
            difficulty=config_data['difficulty']
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid test_config JSON: {e}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key in test_config: {e}")

    test_id = str(uuid.uuid4())

    # Mock response based on API.md
    mock_questions = []
    mock_answers = {}

    question_id_counter = 1

    for q_config in config.question_config:
        q_type = q_config.type
        q_count = q_config.count

        for _ in range(q_count):
            q_id = f"q_{q_type}_{question_id_counter}"
            question_id_counter += 1

            if q_type == "single_choice":
                mock_questions.append(Question(
                    id=q_id,
                    type="single_choice",
                    stem=f"{q_id}：以下哪项是正确的？",
                    options=["选项A", "选项B", "选项C", "选项D"],
                    answer=MultipleChoiceAnswer(correct_option_indices=[0], explanation="这是模拟单选题的答案解释。")
                ))
                mock_answers[q_id] = 0
            elif q_type == "multiple_choice":
                mock_questions.append(Question(
                    id=q_id,
                    type="multiple_choice",
                    stem=f"{q_id}：以下哪些是正确的？",
                    options=["选项A", "选项B", "选项C", "选项D"],
                    answer=MultipleChoiceAnswer(correct_option_indices=[0, 1], explanation="这是模拟多选题的答案解释。")
                ))
                mock_answers[q_id] = [0, 1]
            elif q_type == "fill_in_the_blank":
                mock_questions.append(Question(
                    id=q_id,
                    type="fill_in_the_blank",
                    stem=f"{q_id}：请填写______。",
                    answer=["模拟答案"]
                ))
                mock_answers[q_id] = "模拟答案"
            elif q_type == "essay":
                mock_questions.append(Question(
                    id=q_id,
                    type="essay",
                    stem=f"{q_id}：请简述______。",
                    answer="这是模拟论述题的答案。"
                ))

    mock_test_data[test_id] = {
        "questions": mock_questions,
        "answers": mock_answers
    }

    return GenerateTestResponse(test_id=test_id, questions=mock_questions)

@app.post("/grade-objective-questions", response_model=GradeObjectiveQuestionsResponse)
async def grade_objective_questions(request: GradeObjectiveQuestionsRequest):
    """
    批量批改客观题接口。
    """
    if request.test_id not in mock_test_data:
        raise HTTPException(status_code=404, detail="Test ID not found")

    correct_answers = mock_test_data[request.test_id]["answers"]
    results = []

    for user_answer_obj in request.answers:
        question_id = user_answer_obj.question_id
        user_response = user_answer_obj.user_response
        correct_ans = correct_answers.get(question_id)

        is_correct = False
        if correct_ans is not None:
            if isinstance(correct_ans, list):
                # For multiple choice or fill-in-the-blank with multiple correct options
                if isinstance(user_response, list):
                    is_correct = sorted(user_response) == sorted(correct_ans)
                elif isinstance(user_response, str):
                    is_correct = user_response in correct_ans
            else:
                # For single choice or single fill-in-the-blank
                is_correct = user_response == correct_ans

        results.append(GradeResult(
            question_id=question_id,
            is_correct=is_correct,
            user_answer=user_response,
            correct_answer=correct_ans # Return correct answer for frontend display
        ))

    overall_feedback = None
    if request.request_ai_feedback:
        overall_feedback = "本次作答在概念理解上表现不错，但在细节记忆上还有提升空间，尤其要注意区分A和B这两个易混淆的知识点。"

    return GradeObjectiveQuestionsResponse(results=results, overall_feedback=overall_feedback)

@app.post("/evaluate-short-answer", response_model=EvaluateShortAnswerResponse)
async def evaluate_short_answer(request: EvaluateShortAnswerRequest):
    """
    批改简答/论述题接口。
    """
    # Mock response based on API.md
    return EvaluateShortAnswerResponse(
        score=85,
        feedback="您的回答基本准确地阐述了细胞呼吸的过程和意义，结构清晰。",
        strengths=["准确地指出了有氧呼吸和无氧呼吸的区别。", "强调了能量供应和物质转化两方面的意义。"],
        areas_for_improvement=["可以更详细地描述有氧呼吸的三个阶段的具体反应。", "在无氧呼吸的产物描述上可以更全面，例如植物和动物的不同产物。"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)