# routers/export.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import services
import schemas
from database import get_db

router = APIRouter(
    prefix="/export",
    tags=["Export"]
)

@router.get("/test-paper/{test_id}/html", response_class=HTMLResponse)
async def export_test_paper_to_html(test_id: int, db: Session = Depends(get_db)):
    """导出试卷为静态HTML格式"""
    test_paper = services.get_test_paper_by_id(db, test_id)
    if not test_paper:
        raise HTTPException(status_code=404, detail="Test paper not found")
    
    questions = [
        schemas.QuestionModel(
            id=str(q.id),
            type=q.question_type,
            stem=q.stem,
            options=q.options,
            answer=q.correct_answer
        )
        for q in test_paper.questions
    ]
    
    # 生成HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{test_paper.name}</title>
        <style>
            body {{
                font-family: 'Arial', 'Microsoft YaHei', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .question {{
                margin-bottom: 30px;
                padding: 15px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f9f9f9;
            }}
            .question-stem {{
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .options {{
                margin-left: 20px;
            }}
            .option {{
                margin-bottom: 5px;
                cursor: pointer;
            }}
            .option:hover {{
                background-color: #f0f0f0;
            }}
            .answer {{
                margin-top: 15px;
                padding: 10px;
                border-top: 1px dashed #ccc;
                display: none;
            }}
            .show-answer {{
                margin-top: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                cursor: pointer;
                border-radius: 4px;
            }}
            .show-answer:hover {{
                background-color: #45a049;
            }}
            .explanation {{
                margin-top: 10px;
                font-style: italic;
            }}
            .correct {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .fill-blank-input {{
                border: none;
                border-bottom: 1px solid #999;
                outline: none;
                padding: 5px;
                margin: 0 5px;
                width: 150px;
            }}
            textarea {{
                width: 100%;
                min-height: 100px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                resize: vertical;
            }}
        </style>
    </head>
    <body>
        <h1>{test_paper.name}</h1>
        <div id="test-paper">
    """
    
    # 为每种题型生成HTML
    for i, question in enumerate(questions):
        question_number = i + 1
        question_html = f"""
        <div class="question" id="question-{question.id}">
            <div class="question-stem">{question_number}. {question.stem}</div>
        """
        
        if question.type == "single_choice":
            question_html += '<div class="options">'
            for j, option in enumerate(question.options):
                option_letter = chr(65 + j)  # A, B, C, D...
                question_html += f"""
                <div class="option" onclick="selectSingleOption('{question.id}', {j})">
                    <input type="radio" id="q{question.id}-option{j}" name="q{question.id}" value="{j}">
                    <label for="q{question.id}-option{j}">{option_letter}. {option}</label>
                </div>
                """
            question_html += '</div>'
            
            # 答案部分
            correct_index = question.answer.index
            correct_letter = chr(65 + correct_index)
            explanation = question.answer.explanation
            
            question_html += f"""
            <div class="answer" id="answer-{question.id}">
                <div class="correct">正确答案: {correct_letter}</div>
                <div class="explanation">{explanation}</div>
            </div>
            """
            
        elif question.type == "multiple_choice":
            question_html += '<div class="options">'
            for j, option in enumerate(question.options):
                option_letter = chr(65 + j)
                question_html += f"""
                <div class="option" onclick="toggleMultipleOption('{question.id}', {j})">
                    <input type="checkbox" id="q{question.id}-option{j}" name="q{question.id}" value="{j}">
                    <label for="q{question.id}-option{j}">{option_letter}. {option}</label>
                </div>
                """
            question_html += '</div>'
            
            # 答案部分
            correct_indices = question.answer.indexes
            correct_letters = [chr(65 + idx) for idx in correct_indices]
            explanation = question.answer.explanation
            
            question_html += f"""
            <div class="answer" id="answer-{question.id}">
                <div class="correct">正确答案: {', '.join(correct_letters)}</div>
                <div class="explanation">{explanation}</div>
            </div>
            """
            
        elif question.type == "fill_in_the_blank":
            blanks_count = len(question.answer.texts)
            question_html += '<div class="fill-in-blank">'
            for j in range(blanks_count):
                question_html += f"""
                <div style="margin-bottom: 10px;">
                    <label>空白 {j+1}:</label>
                    <input type="text" class="fill-blank-input" id="q{question.id}-blank{j}">
                </div>
                """
            question_html += '</div>'
            
            # 答案部分
            correct_answers = question.answer.texts
            explanation = question.answer.explanation
            
            answer_html = '<div class="correct">正确答案:</div><ul>'
            for j, ans in enumerate(correct_answers):
                if isinstance(ans, list):
                    answer_html += f"<li>空白 {j+1}: {', '.join(ans)}</li>"
                else:
                    answer_html += f"<li>空白 {j+1}: {ans}</li>"
            answer_html += '</ul>'
            
            question_html += f"""
            <div class="answer" id="answer-{question.id}">
                {answer_html}
                <div class="explanation">{explanation}</div>
            </div>
            """
            
        elif question.type == "essay":
            question_html += f"""
            <div>
                <textarea id="q{question.id}-essay" placeholder="请在此输入您的答案..."></textarea>
            </div>
            """
            
            # 答案部分
            reference_answer = question.answer.reference_explanation
            explanation = ""  # 问答题没有单独的explanation字段
            
            question_html += f"""
            <div class="answer" id="answer-{question.id}">
                <div class="correct">参考答案:</div>
                <div>{reference_answer}</div>
                <div class="explanation">{explanation}</div>
            </div>
            """
        
        # 添加显示答案按钮
        question_html += f"""
            <button class="show-answer" onclick="toggleAnswer('{question.id}')">显示答案</button>
        </div>
        """
        
        html_content += question_html
    
    # 添加JavaScript
    html_content += """
        </div>
        
        <script>
            // 单选题选择
            function selectSingleOption(questionId, optionIndex) {
                const options = document.querySelectorAll(`input[name="q${questionId}"]`);
                options.forEach((option, index) => {
                    option.checked = index === optionIndex;
                });
            }
            
            // 多选题选择
            function toggleMultipleOption(questionId, optionIndex) {
                const option = document.getElementById(`q${questionId}-option${optionIndex}`);
                option.checked = !option.checked;
            }
            
            // 显示/隐藏答案
            function toggleAnswer(questionId) {
                const answerDiv = document.getElementById(`answer-${questionId}`);
                const button = document.querySelector(`#question-${questionId} .show-answer`);
                
                if (answerDiv.style.display === 'block') {
                    answerDiv.style.display = 'none';
                    button.textContent = '显示答案';
                } else {
                    answerDiv.style.display = 'block';
                    button.textContent = '隐藏答案';
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html_content