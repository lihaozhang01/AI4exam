# dependencies.py

import os
import logging
from typing import Optional
import google.generativeai as genai
from fastapi import Header, HTTPException

# 配置日誌記錄
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_genai(x_api_key: Optional[str] = Header(None, alias="X-Api-Key")):
    """Dependency to configure Google AI with API key from header or environment."""
    api_key = x_api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("API Key is missing from 'X-Api-Key' header and environment.")
        raise HTTPException(status_code=400, detail="Google API Key is missing. Provide it in the 'X-Api-Key' header.")
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to configure Google AI: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Google AI: {e}")