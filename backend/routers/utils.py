# routers/utils.py

import logging
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from dependencies import configure_genai

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
        # 根据 provider 配置 genai
        configure_genai(api_key, provider)
        
        # 使用请求中指定的模型名称初始化模型
        model = genai.GenerativeModel(request.model_name)
        
        # 生成简短内容以测试 API Key 和模型的有效性
        model.generate_content("say hi")  # 发送一个简单的请求
        
        return {"message": "API Key is valid and connectivity is successful."}
    except Exception as e:
        logger.error(f"Connectivity test failed for model {request.model_name}: {e}")
        # 返回更详细的错误信息，帮助前端调试
        raise HTTPException(status_code=400, detail=f"Connectivity test failed: {str(e)}")