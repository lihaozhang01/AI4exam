# routers/history.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import services
import schemas
from database import get_db

router = APIRouter(
    tags=["History"]
)

from models import TestPaper, TestPaperResult

@router.get("/", response_model=List[schemas.history.TestPaperResult])
def get_submission_history(
    search: str = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session = Depends(get_db)
):
    """
    从数据库中获取提交历史记录，支持搜索和排序。
    **优化：此端点现在将搜索和排序逻辑直接下推到数据库执行，以提高性能。**
    """
    query = db.query(TestPaperResult).join(TestPaper, TestPaperResult.test_paper_id == TestPaper.id)

    # 搜索逻辑
    if search:
        query = query.filter(TestPaper.name.ilike(f"%{search}%"))

    # 排序逻辑
    sort_column = TestPaper.name if sort_by == 'name' else TestPaperResult.created_at
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    results = query.all()

    # 为旧数据中可能为None的题目数量字段提供默认值
    # 这一步仍然需要在应用层处理，因为数据库中的NULL值需要转换
    for result in results:
        if result.test_paper:
            if result.test_paper.total_objective_questions == 0:
                result.correct_objective_questions = 0
            elif result.correct_objective_questions is None:
                result.correct_objective_questions = 0

            if result.test_paper.total_objective_questions is None:
                result.test_paper.total_objective_questions = 0
            if result.test_paper.total_essay_questions is None:
                result.test_paper.total_essay_questions = 0

    return results


@router.get("/{result_id}", response_model=schemas.TestPaperResult)
def get_history_result(result_id: int, db: Session = Depends(get_db)):
    result = services.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@router.delete("/{result_id}", status_code=204)
def delete_history_result(result_id: int, delete_paper: bool = False, db: Session = Depends(get_db)):
    # 首先获取测试结果
    result = services.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")

    test_paper_id = result.test_paper_id

    # 删除测试结果，如果需要，此函数也会处理关联试卷的删除
    success = services.delete_test_result(db, result_id, delete_paper)
    if not success:
        raise HTTPException(status_code=404, detail="Test result not found during deletion")

    return