# routers/utils.py

import logging
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import google.generativeai as genai
from openai import AsyncOpenAI

from services import ai as services_ai

router = APIRouter(
    tags=["Utilities"]
)

logger = logging.getLogger(__name__)

class ConnectivityTestRequest(BaseModel):
    model_name: str

@router.post("/test-connectivity")
async def test_connectivity(
    request: ConnectivityTestRequest,
    api_key: str = Header(..., alias="X-Api-Key"),
    provider: str = Header(..., alias="X-Provider")
):
    try:
        client = services_ai.get_llm_client(provider, api_key)

        if provider == 'google':
            model = client.GenerativeModel(request.model_name)
            model.generate_content("say hi")
        else:
            # For OpenAI-compatible clients
            await client.chat.completions.create(
                model=request.model_name,
                messages=[{"role": "user", "content": "say hi"}],
                max_tokens=10
            )
        
        return {"message": "API Key is valid and connectivity is successful."}
    except Exception as e:
        logger.error(f"Connectivity test failed for model {request.model_name} with provider {provider}: {e}")
        raise HTTPException(status_code=400, detail=f"Connectivity test failed: {str(e)}")