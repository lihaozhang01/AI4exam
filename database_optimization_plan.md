# AI4Exam 数据库集成与优化方案

## 1. 目标

为 `AI4Exam` 应用添加数据库支持，实现以下功能：

-   持久化存储生成的试卷。
-   记录用户的答题历史和结果。
-   为未来的用户管理、试卷分享、统计分析等高级功能奠定基础。

本文档将以AI协作友好的方式，分步描述实施计划。

## 2. 技术选型

-   **数据库**: `SQLite` - 轻量级、无需独立服务、单个文件存储，非常适合开发和中小型应用，便于快速启动。
-   **ORM (对象关系映射)**: `SQLAlchemy` - Python中最流行的ORM库，功能强大，可以让我们用Python类来操作数据库表，避免编写原生SQL。
-   **数据库迁移工具**: `Alembic` - 与 `SQLAlchemy` 配套使用，可以管理数据库结构的变更历史，方便迭代升级。

## 3. 实施步骤

### 第1步：环境准备 - 安装依赖

首先，需要为后端环境添加新的Python包。AI助手可以通过运行以下命令来完成：

```bash
pip install sqlalchemy alembic
```

安装完成后，需要将这两个库更新到 `backend/requirements.txt` 文件中。

### 第2步：数据库模型设计 (`backend/models.py`)

我们需要定义数据模型来映射数据库中的表。模型需要重新设计，以清晰地表示试卷、题目和答案之间的关系。

**建议的模型结构：**

-   `TestPaper` (试卷表): 存储试卷的元数据，如创建时间、知识源（文本或文件名）、唯一ID等。
-   `Question` (题目表): 存储每一道题的详细信息，包括题干、类型（单选、多选等）、选项、正确答案、所属试卷ID等。
-   `UserAnswer` (用户答案表): 存储用户对每个题目的作答，包括所选答案、得分、答题时间等。

AI助手可以根据这个结构，修改 `backend/models.py` 文件。

**示例 `models.py`:**

```python
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class TestPaper(Base):
    __tablename__ = 'test_papers'
    id = Column(Integer, primary_key=True)
    source_type = Column(String(50)) # 'text' or 'file'
    source_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    questions = relationship('Question', back_populates='test_paper')

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    test_paper_id = Column(Integer, ForeignKey('test_papers.id'))
    question_type = Column(String(50)) # e.g., 'single_choice', 'essay'
    stem = Column(Text)
    options = Column(JSON) # For multiple choice
    correct_answer = Column(JSON)
    test_paper = relationship('TestPaper', back_populates='questions')

# ... 可以后续添加 UserAnswer 模型 ...

# 数据库连接设置
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 第3步：数据库初始化与迁移管理 (Alembic)

1.  **初始化Alembic**: 在 `backend` 目录下，AI助手需要运行以下命令来创建迁移环境：
    ```bash
    alembic init alembic
    ```
2.  **配置Alembic**: 修改生成的 `alembic.ini` 和 `alembic/env.py` 文件，使其能够识别我们的 `SQLAlchemy` 模型。
3.  **生成迁移脚本**: 每当 `models.py` 中的模型发生变化时，运行 `alembic revision --autogenerate -m "Initial migration"` 来自动生成数据库结构变更的脚本。
4.  **应用迁移**: 运行 `alembic upgrade head` 来将变更应用到数据库中，创建或更新表结构。

### 第4步：改造后端API (`backend/main.py`)

核心改动是将原先直接返回JSON的逻辑，替换为将生成的试卷数据存入数据库。

**改造思路:**

1.  **引入数据库会话**: 在 `/generate-test` 接口中，通过依赖注入 `get_db` 函数来获取数据库会话(session)。
2.  **保存数据**: 当AI模型生成试卷内容后，不再直接返回，而是：
    -   创建一个 `TestPaper` 对象。
    -   为每一道题创建一个 `Question` 对象，并与 `TestPaper` 关联。
    -   通过 `db.add()` 和 `db.commit()` 将这些对象存入数据库。
3.  **返回试卷ID**: 接口成功后，返回新创建试卷的 `id`。
4.  **创建新接口**: 新增一个 `/get-test/{test_id}` 接口，用于根据ID从数据库中获取试卷详情并返回给前端。

### 第5步：前端页面调整 (`ai4exam-frontend`)

前端也需要相应调整来配合后端的改动：

1.  `TestFormPage.jsx` 在提交生成请求后，会收到一个 `test_id`。
2.  收到 `test_id` 后，页面自动跳转到 `TestPaperPage.jsx`，并将 `test_id` 作为URL参数（例如 `/test/123`）。
3.  `TestPaperPage.jsx` 在加载时，从URL中获取 `test_id`，然后调用后端的 `/get-test/{test_id}` 接口来获取试卷数据并渲染页面。

## 4. 后续展望

完成以上步骤后，应用将拥有一个健壮的数据持久化层，为以下功能的实现铺平了道路：

-   **历史试卷列表**: 在前端创建一个页面，展示所有历史生成的试卷。
-   **用户答题与评分**: 实现用户提交答案、后端自动评分并将结果存入 `UserAnswer` 表。
-   **性能优化**: 对于已经生成过的知识源，可以直接从数据库中调取历史试卷，避免重复调用AI模型，节省成本和时间。