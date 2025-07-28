from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 数据库连接可以保留在这里，或者移动到单独的 database.py 文件
DATABASE_URL = "sqlite:///./test.db" # 使用相对路径更具可移植性
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()