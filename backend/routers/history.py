# routers/history.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import services
import schemas
from models import get_db

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("/", response_model=List[schemas.TestPaperResult])
def get_history(db: Session = Depends(get_db)):
    return services.get_all_test_results(db)


@router.get("/{result_id}", response_model=schemas.TestPaperResult)
def get_history_result(result_id: int, db: Session = Depends(get_db)):
    result = services.get_test_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@router.delete("/{result_id}", status_code=204)
def delete_history_result(result_id: int, db: Session = Depends(get_db)):
    success = services.delete_test_result(db, result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test result not found")
    # 遵循 RESTful 風格，DELETE 成功不返回 body，只返回 204 No Content
    return