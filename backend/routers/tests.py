# routers/tests.py

import urllib.parse
from typing import Optional
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Header
import json
from sqlalchemy.orm import Session

import services
import schemas
from database import get_db
from dependencies import configure_genai

router = APIRouter(
    tags=["Test Generation & Retrieval"]
)

@router.post("/tests", status_code=201)
async def create_test_entry(
    db: Session = Depends(get_db),
    source_file: Optional[UploadFile] = File(None),
    source_text: Optional[str] = Form(None),
    config_json: str = Form(...),
    name: Optional[str] = Form(None), # 试卷名称
    generation_model: Optional[str] = Header(None, alias="X-Generation-Model"),
    generation_prompt: Optional[str] = Header(None, alias="X-Generation-Prompt"),
):
    if not source_file and not source_text:
        raise HTTPException(status_code=400, detail="Either source_file or source_text must be provided.")

    config = schemas.GenerateTestConfig.model_validate_json(config_json)
    file_content = (await source_file.read()).decode('utf-8') if source_file else ""
    text_content = source_text if source_text else ""
    
    knowledge_content = ""
    if file_content:
        knowledge_content += f"以下是文件内容：\n{file_content}\n"
    if text_content:
        knowledge_content += f"以下是用户输入内容：\n{text_content}\n"
    knowledge_content = knowledge_content.strip()

    # 在数据库中创建试卷记录，但不生成具体问题
    db_test_paper = services.create_test_paper(
        db=db, 
        name=name,
        source_content=knowledge_content, 
        config=config, 
        generation_prompt=generation_prompt,
        ai_response=None  # We are not generating questions here
    )

    return {"test_id": db_test_paper.id}


@router.post("/generate-test", response_model=schemas.GenerateTestResponse)
async def generate_test(
    db: Session = Depends(get_db),
    source_file: Optional[UploadFile] = File(None),
    source_text: Optional[str] = Form(None),
    config_json: str = Form(...),
    name: Optional[str] = Form(None),
    provider: str = Header(..., alias="X-Provider"),
    api_key: str = Header(..., alias="X-Api-Key"),
    generation_model: Optional[str] = Header(None, alias="X-Generation-Model"),
    generation_prompt: Optional[str] = Header(None, alias="X-Generation-Prompt")
):
    decoded_prompt = urllib.parse.unquote(generation_prompt) if generation_prompt else None
    if not source_file and not source_text:
        raise HTTPException(status_code=400, detail="Either source_file or source_text must be provided.")

    config = schemas.GenerateTestConfig.model_validate_json(config_json)
    file_content = (await source_file.read()).decode('utf-8') if source_file else ""
    text_content = source_text if source_text else ""
    
    knowledge_content = ""
    if file_content:
        knowledge_content += f"以下是文件内容：\n{file_content}\n"
    if text_content:
        knowledge_content += f"以下是用户输入内容：\n{text_content}\n"
    knowledge_content = knowledge_content.strip()

    ai_response = await services.generate_test_from_ai(
        knowledge_content=knowledge_content, 
        config=config, 
        provider=provider,
        api_key=api_key,
        generation_model=generation_model, 
        generation_prompt=decoded_prompt
    )
    db_test_paper = services.create_test_paper(
        db,
        name=name,
        source_content=knowledge_content,
        config=config,  # [New] Pass config
        generation_prompt=decoded_prompt,  # [New] Pass decoded_prompt
        ai_response=ai_response
    )

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

    return schemas.GenerateTestResponse(
        test_id=str(db_test_paper.id), 
        name=db_test_paper.name, 
        questions=questions_data
    )


@router.get("/generate-stream-test/{test_id}")
async def generate_stream_test(
    test_id: int,
    db: Session = Depends(get_db),
    provider: str = Header(..., alias="X-Provider"),
    api_key: str = Header(..., alias="X-Api-Key"),
    generation_model: str = Header(..., alias="X-Generation-Model")
):
    print(f"Received generation_model: {generation_model}")
    db_test_paper = services.get_test_paper_by_id(db, test_id)
    if not db_test_paper:
        raise HTTPException(status_code=404, detail="Test paper not found")

    knowledge_content = db_test_paper.source_content
    config = schemas.GenerateTestConfig.model_validate(db_test_paper.config)
    decoded_prompt = db_test_paper.generation_prompt

    stream_generator = services.generate_test_stream_from_ai(
        knowledge_content=knowledge_content, 
        config=config, 
        provider=provider,
        api_key=api_key,
        generation_model=generation_model, 
        generation_prompt=decoded_prompt
    )

    async def db_saving_stream_generator():
        # Initialize a structure to hold the complete test paper data for DB saving
        db_test_paper_data = {"title": "", "questions": []}

        async for chunk in stream_generator:
            if chunk.startswith('data:'):
                data_str = chunk[len('data:'):].strip()
                if data_str and data_str != '[DONE]':
                    try:
                        json_data = json.loads(data_str)
                        event_type = json_data.get('type')
                        content = json_data.get('content')

                        if event_type == 'metadata' and content and 'title' in content:
                            db_test_paper_data['title'] = content['title']
                        elif event_type == 'question' and content:
                            db_test_paper_data['questions'].append(content)
                        
                    except json.JSONDecodeError:
                        pass
            yield chunk
        
        # After the stream is finished, save the complete test paper to the database
        if db_test_paper_data['questions']:
            services.update_test_paper(db, test_id=test_id, ai_response=db_test_paper_data)
    return StreamingResponse(db_saving_stream_generator(), media_type="text/event-stream")


@router.get("/test-papers/{test_id}", response_model=schemas.GenerateTestResponse)
async def get_test(test_id: int, db: Session = Depends(get_db)):
    test_paper = services.get_test_paper_by_id(db, test_id)
    questions_to_return = [
        schemas.QuestionModel(
            id=str(q.id),
            type=q.question_type,
            stem=q.stem,
            options=q.options,
            answer=q.correct_answer
        )
        for q in test_paper.questions
    ]

    return schemas.GenerateTestResponse(
        test_id=str(test_paper.id), 
        name=test_paper.name, 
        questions=questions_to_return
    )