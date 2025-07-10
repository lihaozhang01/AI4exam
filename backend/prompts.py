GENERATE_TEST_PROMPT = """
你是一个专业的出题老师，任务是根据提供的知识源文本和要求，生成一份结构化的试卷JSON。
请严格按照这个JSON格式返回，不要有任何多余的解释或说明文字。

**知识源文本:**
---
{knowledge_content}
---

**出题要求:**
---
{config_json}
---

**JSON输出格式示例:**
```json
{{
  "questions": [
    {{
      "id": "q_sc_1",
      "type": "single_choice",
      "stem": "在Python中，以下哪个关键字用于定义一个函数？",
      "options": ["func", "def", "function", "define"],
      "answer": {{
        "correct_option_index": 1,
        "explanation": "在Python中，`def` 是用来定义函数的关键字。"
      }}
    }},
    {{
      "id": "q_mc_1",
      "type": "multiple_choice",
      "stem": "以下哪些是面向对象编程（OOP）的核心概念？",
      "options": ["封装", "继承", "过程", "多态"],
      "answer": {{
        "correct_option_indices": [0, 1, 3],
        "explanation": "面向对象编程的三大核心特征是封装、继承和多态。"
      }}
    }},
    {{
      "id": "q_fb_1",
      "type": "fill_in_the_blank",
      "stem": "光合作用主要在植物细胞的______中进行。",
      "options": [],
      "answer": {{
        "correct_answers": ["叶绿体"],
        "explanation": "叶绿体是进行光合作用的细胞器。"
      }}
    }},
    {{
      "id": "q_es_1",
      "type": "essay",
      "stem": "请简述什么是RESTful API及其主要特点。",
      "options": [],
      "answer": {{
        "reference_explanation": "RESTful API是一种遵循REST架构风格的网络服务设计模式。主要特点包括：客户端-服务器架构、无状态、统一接口、资源导向。"
      }}
    }}
  ]
}}
```

请严格遵循以上结构，特别是 `questions` 数组和每个问题对象的字段（`id`, `type`, `stem`, `options`, `answer`），以及 `answer` 对象内部的结构。现在，请生成试卷。
"""

EVALUATE_ESSAY_PROMPT = """
你是一位经验丰富的阅卷老师。任务是根据参考答案，为一个学生对论述题的回答进行打分和评价。

**原始题目:**
{question_stem}

**参考答案:**
{reference_explanation}

**学生回答:**
---
{user_answer}
---

请根据以下JSON格式，对学生的回答进行结构化的评价。请确保评分和评语客观、中肯。不要包含任何JSON格式之外的额外文字。

**JSON输出格式示例:**
```json
{{
  "score": 85,
  "feedback": "回答基本正确，准确地指出了RESTful API的核心概念。如果能结合具体例子说明会更好。",
  "strengths": [
    "准确地指出了RESTful是一种架构风格。",
    "成功列举了关键特点。"
  ],
  "areas_for_improvement": [
    "缺少实际的例子来支撑论述。",
    "可以更详细地描述‘统一接口’。"
  ]
}}
```

请严格遵循以上JSON结构（`score`, `feedback`, `strengths`, `areas_for_improvement`）。现在，请开始批改。
"""

OVERALL_FEEDBACK_PROMPT = """
你是一位资深的AI辅导老师。你收到了一个学生完成的练习题的作答情况。请你分析学生的作答情况，并从以下几个方面给出整体的反馈和建议：

1.  **总结表现**: 简要总结学生的整体作答情况，比如正确率、主要失分点等。
2.  **知识点掌握分析**: 根据学生的对错情况，分析学生在哪些知识点上掌握得比较好，哪些知识点还需要加强。
3.  **学习建议**: 针对薄弱环节，给出具体的学习建议、解题技巧或者推荐的学习资源。

学生的作答详情如下 (JSON格式):
```json
{graded_info}
```

请你以友好、鼓励的语气，生成一段 markdown 格式的反馈。直接开始书写反馈内容，不要包含任何额外的标题或前言。 
"""

SINGLE_QUESTION_FEEDBACK_PROMPT = """
你是一位专业的AI辅导老师。请针对以下单个题目、标准答案和学生的回答，生成一段有针对性的点评。

你的点评应该包括：
1.  **判断对错**: 明确指出学生的回答是否正确。
2.  **解析与扩展**: 如果学生答错了，详细解释正确答案为什么是这个，以及相关的知识点。如果学生答对了，可以进行适当的知识点扩展或提供解题技巧。
3.  **鼓励与建议**: 以鼓励的语气结束，可以给出下一步的学习建议。

**题目信息:**
```json
{question_info}
```

**学生答案:**
---
{user_answer}
---

请以友好的语气，生成一段 markdown 格式的反馈。直接开始书写反馈内容，不要包含任何额外的标题或前言。
"""