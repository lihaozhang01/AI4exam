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

    client_options = None
    if provider == 'siliconflow':
        client_options = {"base_url": "https://api.siliconflow.cn/v1"}
    elif provider == 'volcengine':
        # 火山引擎的 base_url 可能需要根据实际情况调整
        client_options = {"base_url": "https://maas-api.ml-platform-cn-beijing.volces.com/v1"}

    try:
        genai.configure(
            api_key=api_key,
            transport='rest',
            client_options=client_options
        )
    except Exception as e:
        logger.error(f"Failed to configure Generative AI for provider {provider}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Generative AI: {e}")