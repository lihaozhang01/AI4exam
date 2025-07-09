import time
import uuid
from fastapi import FastAPI, Form, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# -----------------------------------------------------------------------------
# 初始化FastAPI应用
# -----------------------------------------------------------------------------
app = FastAPI(
    title="AI智能试卷助手 (模拟后端)",
    description="这是一个用于前端开发的模拟API服务器。它严格遵循API.md中的契约，返回固定的、写死的JSON数据，无需连接真实AI。",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# 配置跨域资源共享 (CORS)
# 允许所有来源的请求，这在开发阶段非常方便。
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# -----------------------------------------------------------------------------
# Mock Data: `/generate-test` 的模拟响应体
# 这份数据是根据你的 API.md 精心编写的，包含了所有题型。
# -----------------------------------------------------------------------------
mock_test_paper = {
    "test_id": f"test_{uuid.uuid4()}",
    "questions": [
        {
            "id": "q_sc_1",
            "type": "single_choice",
            "stem": "在Python中，以下哪个关键字用于定义一个函数？",
            "options": ["func", "def", "function", "define"],
            "answer": {
                "correct_option_index": 1,
                "explanation": "在Python中，`def` 是用来定义函数的关键字，是 'define' 的缩写。"
            }
        },
        {
            "id": "q_sc_2",
            "type": "single_choice",
            "stem": "以下哪个数据类型是不可变的？",
            "options": ["list", "dict", "set", "tuple"],
            "answer": {
                "correct_option_index": 3,
                "explanation": "元组（tuple）是不可变序列，一旦创建就不能修改。列表（list）、字典（dict）和集合（set）都是可变的。"
            }
        },
        {
            "id": "q_mc_1",
            "type": "multiple_choice",
            "stem": "以下哪些是面向对象编程（OOP）的核心概念？",
            "options": [
                "封装 (Encapsulation)",
                "继承 (Inheritance)",
                "过程 (Procedure)",
                "多态 (Polymorphism)"
            ],
            "answer": {
                "correct_option_indices": [0, 1, 3],
                "explanation": "面向对象编程的三大核心特征是封装、继承和多态。过程是过程式编程的核心概念。"
            }
        },
        {
            "id": "q_fb_1",
            "type": "fill_in_the_blank",
            "stem": "光合作用主要在植物细胞的______中进行。",
            "answer": {
                "correct_answers": ["叶绿体", "chloroplast"],
                "explanation": "叶绿体是进行光合作用的细胞器，它包含了吸收光能的叶绿素。"
            }
        },
        {
            "id": "q_fb_2",
            "type": "fill_in_the_blank",
            "stem": "HTTP协议的默认端口号是____，而HTTPS协议的默认端口号是____。",
            "answer": {
                "correct_answers": ["80, 443"],
                "explanation": "HTTP使用80端口进行通信，而加密的HTTPS使用443端口。"
            }
        },
        {
            "id": "q_es_1",
            "type": "essay",
            "stem": "请简述什么是RESTful API，并列举其至少三个主要特点。",
            "answer": {
                "reference_explanation": "RESTful API是一种遵循REST（Representational State Transfer）架构风格的网络服务设计模式。主要特点包括：1. 客户端-服务器架构：清晰分离关注点。2. 无状态（Stateless）：服务器不存储客户端会话信息。3. 统一接口（Uniform Interface）：使用标准的HTTP方法（GET, POST, PUT, DELETE）对资源进行操作。4. 资源导向：通过URL（统一资源标识符）来定位资源。"
            }
        }
    ]
}


# -----------------------------------------------------------------------------
# API Endpoint 1: /generate-test (已更新)
# -----------------------------------------------------------------------------
@app.post(
    "/generate-test",
    summary="生成试卷 (模拟)",
    description="接收出题配置，但无论输入是什么，始终返回一个固定的、包含多种题型的模拟试卷JSON。",
)
async def generate_test(
    source_file: Optional[UploadFile] = File(None, description="用户上传的源文件（模拟接口中未使用）。"),
    source_text: Optional[str] = Form(None, description="用户粘贴的源文本（模拟接口中未使用）。"),
    config_json: str = Form(..., description="包含所有配置的JSON字符串。"),
):
    """
    这是一个模拟接口。它会打印接收到的配置，但总是返回预先定义好的试卷数据。
    这使得前端可以立即开始UI开发和数据绑定工作。
    """
    print("接收到 '/generate-test' 请求:")
    print(f"  - Source File: {source_file.filename if source_file else '无'}")
    print(f"  - Source Text: {'有' if source_text else '无'}")
    print(f"  - Config JSON: {config_json}")
    
    # 无论输入如何，都返回固定的mock数据
    return mock_test_paper


# -----------------------------------------------------------------------------
# API Endpoint 2: /grade-objective-questions (全新)
# -----------------------------------------------------------------------------
class UserAnswer(BaseModel):
    question_id: str
    user_response: Union[int, List[int], str]

class GradeRequest(BaseModel):
    test_id: str = Field(..., description="正在批改的试卷ID。")
    answers: List[UserAnswer] = Field(..., description="用户的答案数组。")
    request_ai_feedback: bool = Field(..., description="用户是否需要AI对整体表现生成反馈。")


@app.post(
    "/grade-objective-questions",
    summary="批量批改客观题 (模拟)",
    description="接收用户的作答，返回一个固定的、模拟的批改结果。",
)
async def grade_objective_questions(request: GradeRequest):
    """
    模拟客观题的批量批改。
    它会根据预设的正确答案来判断用户提交答案的对错，并组装响应。
    """
    print("接收到 '/grade-objective-questions' 请求:")
    print(request.model_dump_json(indent=2))

    # 预设的正确答案，用于模拟批改
    correct_answers_map = {
        "q_sc_1": 1,
        "q_mc_1": [0, 1, 3],
        "q_fb_1": ["叶绿体", "chloroplast"],
        "q_fb_2": "80, 443"
    }

    results = []
    for ans in request.answers:
        is_correct = False
        # 简单模拟批改逻辑
        if ans.question_id in correct_answers_map:
            correct_answer = correct_answers_map[ans.question_id]
            if isinstance(correct_answer, list):
                # 多选题或多答案填空题
                if isinstance(ans.user_response, list): # 多选题
                     is_correct = sorted(ans.user_response) == sorted(correct_answer)
                else: # 填空题
                     is_correct = ans.user_response in correct_answer
            else:
                is_correct = ans.user_response == correct_answer

        results.append({
            "question_id": ans.question_id,
            "is_correct": is_correct,
            "user_answer": ans.user_response,
            "correct_answer": correct_answers_map.get(ans.question_id, "未知题目的答案")
        })
    
    response_body = {"results": results}

    if request.request_ai_feedback:
        response_body["overall_feedback"] = "本次作答模拟反馈：整体表现不错，但在面向对象概念的掌握上似乎有遗漏，请重点复习“多态”相关的知识点。继续努力！"

    return response_body


# -----------------------------------------------------------------------------
# API Endpoint 3: /evaluate-short-answer (模拟)
# 在精简版方案中叫做 /api/evaluate-essay
# -----------------------------------------------------------------------------
class QuestionInfo(BaseModel):
    stem: str
    reference_explanation: str

class EvaluateRequest(BaseModel):
    test_id: Optional[str] = None
    question: QuestionInfo
    user_answer: str

@app.post(
    "/evaluate-short-answer",
    summary="批改简答/论述题 (模拟)",
    description="接收用户的论述题作答，返回一个固定的、模拟的AI评分和反馈。",
)
async def evaluate_short_answer(request: EvaluateRequest):
    """
    模拟AI对论述题的批改。它会返回一个结构化的、预先写好的评价。
    """
    print("接收到 '/evaluate-short-answer' 请求:")
    print(request.model_dump_json(indent=2))

    # 模拟AI处理延时
    time.sleep(2) 

    return {
        "score": 85,
        "feedback": "回答基本正确，准确地指出了RESTful API的核心概念。如果能结合具体例子（如一个博客文章的API）来说明资源和HTTP方法如何对应，会更加完美。",
        "strengths": [
            "准确地指出了RESTful是一种架构风格，而非具体技术。",
            "成功列举了无状态、客户端-服务器分离等关键特点。"
        ],
        "areas_for_improvement": [
            "可以更详细地描述“统一接口”的含义。",
            "缺少实际的例子来支撑论述，略显抽象。"
        ]
    }


# -----------------------------------------------------------------------------
# 启动服务器的指令
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("启动模拟API服务器，请访问 http://127.0.0.1:8000")
    print("API文档地址: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)