# routers/utils.py

import logging
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException

from dependencies import configure_genai

router = APIRouter(
    tags=["Utilities"]
)

logger = logging.getLogger(__name__)

@router.post("/test-connectivity")
async def test_connectivity(_: None = Depends(configure_genai)):
    try:
        # `configure_genai` 依賴項已經處理了金鑰設定。
        # 這裡執行一個輕量級的 API 呼叫來進一步確認金鑰的有效性。
        genai.list_models()
        return {"message": "API Key is valid and connectivity is successful."}
    except Exception as e:
        logger.error(f"Connectivity test failed during model listing: {e}")
        raise HTTPException(status_code=400, detail=f"Connectivity test failed: {e}")