# services/ai.py

import json
import re
from typing import Dict, Any, List

import google.generativeai as genai
from openai import AsyncOpenAI
from fastapi import HTTPException

import schemas
import models
from prompts import (
    GENERATE_TEST_PROMPT, EVALUATE_ESSAY_PROMPT, 
    OVERALL_FEEDBACK_PROMPT, SINGLE_QUESTION_FEEDBACK_PROMPT, GENERATE_STREAMABLE_TEST_PROMPT
)

# --- LLM Client Factory ---

def get_llm_client(provider: str, api_key: str, generation_model: str = None):
    """根据提供商获取相应的LLM客户端。"""
    if provider == 'google':
        genai.configure(api_key=api_key)
        return genai
    elif provider == 'siliconflow':
        # Special handling for SiliconFlow to inject model into the base_url if needed
        # This is a placeholder for any such logic. As of now, it uses a generic client.
        return AsyncOpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
    elif provider == 'volcengine':
        return AsyncOpenAI(api_key=api_key, base_url="https://api.volcengineapi.com/v1") 
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider: {provider}")

# --- Reusable Utilities ---

def _extract_json_from_ai_response(ai_text: str) -> Dict[str, Any]:
    """安全地從AI的文本響應中提取和解析JSON。"""
    match = re.search(r"```json\n(.*?)\n```", ai_text, re.DOTALL)
    json_str = match.group(1).strip() if match else ai_text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed. String was: {json_str[:500]}...")
        raise HTTPException(status_code=500, detail=f"AI returned malformed JSON: {e}")

# --- Streaming AI Service ---
async def generate_test_stream_from_ai(
    knowledge_content: str, 
    config: schemas.GenerateTestConfig, 
    provider: str,
    api_key: str,
    generation_model: str = None,
    generation_prompt: str = None
):
    """
    使用流式响应逐步生成试卷，并通过智能解析器实时处理数据。
    """
    # 选择模型和prompt
    model_name = generation_model 
    system_prompt = generation_prompt or GENERATE_STREAMABLE_TEST_PROMPT['system_prompt']
    
    # 构建完整的prompt
    prompt = f"{system_prompt}\n\n{GENERATE_STREAMABLE_TEST_PROMPT['format_instructions']}".format(
        knowledge_content=knowledge_content,
        config_json=config.model_dump_json(indent=2)
    )
    # 初始化模型并开始流式生成
    try:
        if provider == 'google':
            get_llm_client(provider, api_key)  # Configure API key
            model = genai.GenerativeModel(model_name)
            stream = await model.generate_content_async(prompt, stream=True)
        else: # OpenAI compatible
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": GENERATE_STREAMABLE_TEST_PROMPT['format_instructions'].format(
                    knowledge_content=knowledge_content,
                    config_json=config.model_dump_json(indent=2)
                )}
            ]

            try:
                client = get_llm_client(provider, api_key)
                stream = await client.chat.completions.create(
                    model=generation_model, 
                    messages=messages,
                    stream=True
                )
            except Exception as e:
                print(f"---[AI_SERVICE_ERROR]---")
                print(f"Error calling SiliconFlow API: {e}")
                print("-------------------------")
                raise e

    except Exception as e:
        # 如果模型初始化或API调用失败，立即停止并报告错误
        error_message = f"Error initializing or calling AI model: {e}"
        print(error_message)
        yield f"data: {json.dumps({'error': error_message})}\n\n" 
        return
    # --- 智能解析器 ---
    buffer = ""
    meta_yielded = False
    chunk_count = 0
    async for chunk in stream:
        chunk_count += 1
        if provider == 'google':
            buffer += chunk.text
        else: # OpenAI compatible
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                 buffer += chunk.choices[0].delta.content

        # --- 实时解析和产生事件 ---
        # 尝试解析元数据
        if not meta_yielded:
            meta_end_marker = "%%END_OF_META%%"
            if meta_end_marker in buffer:
                meta_part, buffer = buffer.split(meta_end_marker, 1)
                meta_json_str = meta_part.strip().replace("```json", "").replace("```", "").strip()
                try:
                    meta_data = json.loads(meta_json_str)
                    yield f"data: {json.dumps({'type': 'metadata', 'content': meta_data})}\n\n"
                    meta_yielded = True
                except json.JSONDecodeError:
                    error_msg = f"Metadata JSON decode error for chunk: {meta_json_str[:200]}"
                    print(f"---[AI_SERVICE_DEBUG]---: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                    # Do not put the chunk back, just discard it and continue.

        # 尝试解析问题
        question_end_marker = "%%END_OF_QUESTION%%"
        while question_end_marker in buffer:
            question_part, buffer = buffer.split(question_end_marker, 1)
            
            # Use regex to safely extract JSON from the part
            match = re.search(r"```json\n(.*?)\n```", question_part, re.DOTALL)
            if match:
                question_json_str = match.group(1).strip()
            else:
                # If no ```json``` block, assume the whole part is a JSON string
                question_json_str = question_part.strip()

            if not question_json_str:
                continue

            try:
                question_data = json.loads(question_json_str)
                yield f"data: {json.dumps({'type': 'question', 'content': question_data})}\n\n"
            except json.JSONDecodeError:
                error_msg = f"Question JSON decode error for chunk: {question_json_str[:200]}"
                print(f"---[AI_SERVICE_DEBUG]---: {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                # If a block is corrupted, we skip it and move to the next one.
                pass

# --- AI Interaction Services ---

async def generate_test_from_ai(
    knowledge_content: str, 
    config: schemas.GenerateTestConfig, 
    provider: str,
    api_key: str,
    generation_model: str = None,
    generation_prompt: str = None
) -> Dict[str, Any]:
    # 優先使用用戶指定的模型，否則使用預設模型
    model_name = generation_model 
    # 優先使用用戶指定的prompt，否則使用預設prompt
    system_prompt = generation_prompt or GENERATE_TEST_PROMPT['system_prompt']
    
    prompt = f"{system_prompt}\n\n{GENERATE_TEST_PROMPT['format_instructions']}".format(
        knowledge_content=knowledge_content,
        config_json=config.model_dump_json(indent=2)
    )
    try:
        if provider == 'google':
            get_llm_client(provider, api_key) # Configure API key
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            response_text = response.text
        else: # OpenAI compatible
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt} # Re-using the fully formatted prompt for simplicity
            ]
            client = get_llm_client(provider, api_key)
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=False
            )
            response_text = response.choices[0].message.content

        return _extract_json_from_ai_response(response_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI test generation failed: {e}")

async def get_overall_feedback_from_ai(graded_info: List[Dict], provider: str, api_key: str, evaluation_model: str = None, overall_feedback_prompt: str = None) -> str:
    model_name = evaluation_model
    system_prompt = overall_feedback_prompt or OVERALL_FEEDBACK_PROMPT['system_prompt']
    prompt = f"{system_prompt}\n\n{OVERALL_FEEDBACK_PROMPT['format_instructions']}".format(
        graded_info=json.dumps(graded_info, ensure_ascii=False, indent=2)
    )
    try:
        client = get_llm_client(provider, api_key)
        if provider == 'google':
            model = client.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            return response.text
        else: # OpenAI compatible
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            response = await client.chat.completions.create(model=model_name, messages=messages, stream=False)
            return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI feedback generation failed: {e}")

async def get_single_question_feedback_from_ai(question: models.DBQuestion, user_answer: schemas.UserAnswer, provider: str, api_key: str, evaluation_model: str = None, single_question_feedback_prompt: str = None) -> str:
    # Use the question_type from the user_answer payload
    q_type = user_answer.question_type
    options = question.options or []
    user_answer_str = "未作答"

    if q_type == 'single_choice' and user_answer.answer_index is not None and 0 <= user_answer.answer_index < len(options):
        user_answer_str = options[user_answer.answer_index]
    elif q_type == 'multiple_choice' and user_answer.answer_indices:
        user_answer_str = ", ".join([options[i] for i in user_answer.answer_indices if 0 <= i < len(options)])
    elif q_type == 'fill_in_the_blank' and user_answer.answer_texts:
        user_answer_str = ", ".join(user_answer.answer_texts)
    elif q_type == 'essay' and user_answer.answer_text:
        user_answer_str = user_answer.answer_text

    question_content = {
        "type": question.question_type,
        "stem": question.stem,
        "options": question.options,
        "correct_answer": question.correct_answer,
        "explanation": (question.correct_answer or {}).get('explanation', '')
    }
    
    model_name = evaluation_model
    system_prompt = single_question_feedback_prompt or SINGLE_QUESTION_FEEDBACK_PROMPT['system_prompt']
    prompt = f"{system_prompt}\n\n{SINGLE_QUESTION_FEEDBACK_PROMPT['format_instructions']}".format(
        question_content=json.dumps(question_content, ensure_ascii=False, indent=4),
        user_answer=user_answer_str
    )
    try:
        client = get_llm_client(provider, api_key)
        if provider == 'google':
            model = client.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            return response.text
        else: # OpenAI compatible
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            response = await client.chat.completions.create(model=model_name, messages=messages, stream=False)
            return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI feedback generation failed: {e}")

async def evaluate_essay_with_ai(request: schemas.EvaluateShortAnswerRequest, provider: str, api_key: str, evaluation_model: str = None, evaluation_prompt: str = None) -> schemas.EvaluateShortAnswerResponse:
    model_name = evaluation_model
    system_prompt = evaluation_prompt or EVALUATE_ESSAY_PROMPT['system_prompt']
    prompt = f"{system_prompt}\n\n{EVALUATE_ESSAY_PROMPT['format_instructions']}".format(
        question_stem=request.question.stem,
        reference_explanation=request.question.reference_explanation,
        user_answer=request.user_answer
    )
    try:
        client = get_llm_client(provider, api_key)
        if provider == 'google':
            model = client.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            response_text = response.text
        else: # OpenAI compatible
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            response = await client.chat.completions.create(model=model_name, messages=messages, stream=False)
            response_text = response.choices[0].message.content
        
        ai_response_data = _extract_json_from_ai_response(response_text)
        
        # 將AI結果和原始參考答案合併到響應模型中
        return schemas.EvaluateShortAnswerResponse(
            **ai_response_data,
            reference_explanation=request.question.reference_explanation
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI evaluation failed: {e}")