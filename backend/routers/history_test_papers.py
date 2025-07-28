from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, defer
from typing import List, Optional
from datetime import datetime

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import services
import schemas
import models
from database import get_db

router = APIRouter(
    tags=["History Test Papers"]
)

@router.get("/", response_model=List[schemas.history.TestPaper])
def get_test_papers_history(
    search: Optional[str] = Query(None, description="Filters papers where the name contains the search term."),
    sort_by: Optional[str] = Query("created_at", description="The field to sort by.", enum=["name", "created_at"]),
    order: Optional[str] = Query("desc", description="The sort order.", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    """
    Fetches a list of unique test paper templates.
    """
    # Defer loading of source_content to avoid fetching large data
    query = db.query(models.TestPaper).options(defer(models.TestPaper.source_content))

    if search:
        query = query.filter(models.TestPaper.name.contains(search))

    if sort_by == "name":
        if order == "asc":
            query = query.order_by(models.TestPaper.name.asc())
        else:
            query = query.order_by(models.TestPaper.name.desc())
    elif sort_by == "created_at":
        if order == "asc":
            query = query.order_by(models.TestPaper.created_at.asc())
        else:
            query = query.order_by(models.TestPaper.created_at.desc())

    test_papers = query.all()
    # 为None的题目数量字段提供默认值
    for paper in test_papers:
        if paper.total_objective_questions is None:
            paper.total_objective_questions = 0
        if paper.total_essay_questions is None:
            paper.total_essay_questions = 0

    return test_papers


@router.delete("/{paper_id}", status_code=204)
def delete_test_paper_and_results(paper_id: int, db: Session = Depends(get_db)):
    # 检查试卷是否存在
    paper = db.query(models.TestPaper).filter(models.TestPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Test paper not found")

    # 删除所有相关的提交记录
    db.query(models.TestPaperResult).filter(models.TestPaperResult.test_paper_id == paper_id).delete()

    # 删除试卷本身
    db.delete(paper)
    db.commit()

    return