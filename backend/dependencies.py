# dependencies.py

import os
import logging
from typing import Optional
import google.generativeai as genai
from fastapi import Header, HTTPException

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_genai(api_key: str, provider: str):
    """根据提供的 API Key 和提供商配置生成 AI 模型。"""
    if not api_key:
        logger.error("API Key is missing.")
        raise HTTPException(status_code=400, detail="API Key is missing. Please provide it.")

    try:
        # 只有当提供商是 'google' 时才配置 genai
        if provider == 'google':
            genai.configure(api_key=api_key)
        # 对于其他提供商，我们不需要在这里配置，因为它们会在 services/ai.py 中的 get_llm_client 函数中被配置
    except Exception as e:
        logger.error(f"Failed to configure Generative AI for provider {provider}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Generative AI: {e}")