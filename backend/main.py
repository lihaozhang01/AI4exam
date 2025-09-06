# main.py

import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 從 models 導入資料庫相關設定
from models import Base
from database import engine
# 從 routers 導入所有路由器模組
from routers import tests, grading, history, utils, history_test_papers, export

# --- App and Configuration Setup ---

# 在應用啟動時創建資料庫表
Base.metadata.create_all(bind=engine)

# 配置日誌記錄
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI智能试卷助手 - 后端API",
    description="为AI智能试卷助手提供生成试卷、批改题目等功能的API服务。",
    version="1.0.0",
)

# 設定 CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 掛載 API 路由器 ---
# 將不同模組的路由器包含到主應用中
app.include_router(tests.router)
app.include_router(grading.router)
app.include_router(history.router, prefix="/history")
app.include_router(history_test_papers.router, prefix="/history_test_papers")
app.include_router(utils.router)
app.include_router(export.router)

@app.get("/", tags=["Root"])
async def read_root():
    """一個簡單的根端點，用於確認服務正在運行。"""
    return {"message": "Welcome to the AI Test Paper Assistant API!"}


# --- 啟動伺服器 ---
if __name__ == "__main__":
    # 使用 uvicorn 來運行 FastAPI 應用
    # host="0.0.0.0" 使其可以在局域網內被訪問
    uvicorn.run(app, host="0.0.0.0", port=8000)