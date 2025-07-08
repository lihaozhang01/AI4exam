#### 4\. 简化的API接口设计 (Simplified API Design)


1.  **支持文件上传**: `generate-test`接口将改为`multipart/form-data`格式，以同时支持文本粘贴和文件上传（.pdf, .epub）。
2.  **配置更灵活**: 用户可以为**每种题型**分别设置数量，并加入了一段描述性文字，以更好地指导AI。
3.  **新增多选题**: 响应体中加入了对“多选题”的支持。
4.  **新增客观题批改接口**: 创建了一个全新的接口，用于批量批改选择题和填空题，并能根据用户意愿提供AI反馈。

-----

### **接口1：生成试卷 (已更新)**

  * **Endpoint**: `/generate-test`
  * **Method**: `POST`
  * **Content-Type**: `multipart/form-data`
  * **描述**: 用户上传文件或粘贴文本，并提供详细配置，AI据此生成试卷。

#### **请求体 (Request Body - `multipart/form-data`)**

请求由多个部分(part)组成：

1.  **`source_file`** (File, 可选): 用户上传的源文件（.pdf, .epub等）。`source_file` 和 `source_text` 至少需要提供一个。
2.  **`source_text`** (String, 可选): 用户粘贴的源文本。
3.  **`config_json`** (String, 必填): 一个包含所有配置的JSON字符串。前端需要将配置对象`JSON.stringify()`后放入此部分。
    ```json
    // 这是 config_json 字符串解析后的对象结构
    {
      "description": "string", // (新增, 可选) 用户对本次出题的额外描述或要求，例如“请侧重于概念理解”或“请围绕第三章内容出题”。
      "question_config": [ // (更新) 一个描述题型和数量的数组
        {
          "type": "single_choice", // 题型: 单选题
          "count": 5 // 该题型的数量
        },
        {
          "type": "multiple_choice", // 题型: 多选题
          "count": 3
        },
        {
          "type": "fill_in_the_blank", // 题型: 填空题
          "count": 4
        },
        {
          "type": "essay", // 题型: 论述题
          "count": 1
        }
      ],
      "difficulty": "string" // (保留) 整体难度: "easy", "medium", "hard"
    }
    ```

#### **响应体 (Response Body - JSON)**

```json
{
  "test_id": "string", // 试卷的唯一标识符。
  "questions": [
    // ... 其他题目 ...
    {
      "id": "q_mc_1",
      "type": "multiple_choice", // (新增) 多选题类型
      "stem": "以下哪些属于哺乳动物的特征？",
      "options": [
        "胎生",
        "卵生",
        "恒温",
        "用肺呼吸"
      ],
      "answer": {
        "correct_option_indices": [0, 2, 3], // (更新) 正确答案变为索引数组，支持多个正确选项。
        "explanation": "哺乳动物的核心特征包括胎生（多数）、恒温、以及用肺呼吸。卵生是鸟类和部分爬行动物的特征。"
      }
    }
    // ... 其他类型的题目结构保持不变 ...
  ]
}
```

-----

### **接口2：批量批改客观题 (全新)**

  * **Endpoint**: `/grade-objective-questions`
  * **Method**: `POST`
  * **Content-Type**: `application/json`
  * **描述**: 接收用户对单选题、多选题、填空题的全部作答，进行批量批改。用户可选择是否需要AI对本次作答情况生成一段总结性反馈。

#### **请求体 (Request Body - JSON)**

```json
{
  "test_id": "string", // (必填) 正在批改的试卷ID。
  "answers": [ // (必填) 用户的答案数组。
    {
      "question_id": "q_sc_1", // 对应题目的ID
      "user_response": 1 // 单选题：用户选择的选项索引 (0, 1, 2...)
    },
    {
      "question_id": "q_mc_1",
      "user_response": [0, 2] // 多选题：用户选择的选项索引数组
    },
    {
      "question_id": "q_fb_1",
      "user_response": "叶绿体" // 填空题：用户填写的字符串
    }
  ],
  "request_ai_feedback": "boolean" // (必填) 用户是否需要AI对整体表现生成反馈。true 或 false。
}
```

#### **响应体 (Response Body - JSON)**

```json
{
  "results": [ // 每个题目对应的批改结果数组。
    {
      "question_id": "q_sc_1",
      "is_correct": false, // 该题是否完全正确
      "user_answer": 1,
      "correct_answer": 0 // 后端返回正确答案，便于前端展示
    },
    {
      "question_id": "q_mc_1",
      "is_correct": false, // 多选题，少选、多选、错选均为false
      "user_answer": [0, 2],
      "correct_answer": [0, 2, 3]
    },
    {
      "question_id": "q_fb_1",
      "is_correct": true,
      "user_answer": "叶绿体",
      "correct_answer": ["叶绿体", "chloroplast"] // 正确答案可以是数组，兼容多种说法
    }
  ],
  "overall_feedback": "string" // (条件返回) 如果请求中 request_ai_feedback 为 true，则返回AI生成的总结性反馈。否则此字段不存在或为null。
                                // 例如："本次作答在概念理解上表现不错，但在细节记忆上还有提升空间，尤其要注意区分A和B这两个易混淆的知识点。"
}
```

-----

### **接口3：批改简答/论述题**

当用户完成一道非客观题的作答后，前端调用此接口以获取AI的智能评分和反馈。

  * **Endpoint**: `/evaluate-short-answer`
  * **Method**: `POST`
  * **描述**: 接收用户对某道简答题的回答，由AI进行分析和批改，返回结构化的反馈。

#### **请求体 (Request Body)**

```json
{
  "test_id": "string", // (可选，但推荐) 对应之前生成的试卷ID，帮助后端追溯上下文。
  "question": { // (必填) 被批改的原始题目信息。
    "stem": "string", // 原始题干。
    "reference_explanation": "string" // 生成题目时附带的参考答案/解析。
  },
  "user_answer": "string" // (必填) 用户输入的回答文本。
}
```

#### **响应体 (Response Body)**

```json
{
  "score": "integer", // AI给出的分数 (例如，0-100)。
  "feedback": "string", // 一段对用户回答的总体评价。
  "strengths": [ // (推荐) 识别出的优点，以数组形式提供，便于前端展示。
    "string" // 例如: "准确地指出了光反应的场所。"
  ],
  "areas_for_improvement": [ // (推荐) 识别出的待改进点，以数组形式提供。
    "string" // 例如: "可以更详细地描述暗反应中的碳固定过程。"
  ]
}
```