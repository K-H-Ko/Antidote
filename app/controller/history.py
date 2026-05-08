from fastapi import status, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.vector_db import get_db
from app.services.history_service import HistoryService
from app.core.auth import get_current_user  # JWT에서 유저 ID를 추출하는 함수
from app.schemas.history import HistoryResponse 
from app.schemas.analysis import AnalysisReport

async def get_recent_history(
    current_user_id: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> List[HistoryResponse]:
    """최근 분석 이력 5개 조회"""
    history = await HistoryService.get_recent_history(db, current_user_id)
    return history

async def get_history_detail(
    history_id: int, 
    current_user_id: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # DB에서 데이터 조회
    history_item = await HistoryService.get_history_detail(db, current_user_id, history_id)
    
    if not history_item:
        return None
    
    # DB의 results 필드(JSON 형식)와 기타 필드들을 AnalysisReport 스키마에 매핑
    return AnalysisReport(
        status="success",
        doc_name=history_item.doc_name,
        mode=history_item.mode,          # "text" | "file" — DB에서 가져온 값
        results=history_item.results,
        missing_clause_report=history_item.missing_clause_report,
        total_risk_score=history_item.total_risk_score,
        analyzed_at=history_item.created_at.strftime("%Y-%m-%d %H:%M:%S")
    )

async def delete_history(
    history_id: int,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 분석 이력 삭제"""
    success = await HistoryService.delete_history_item(db, current_user_id, history_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="삭제할 이력을 찾을 수 없거나 권한이 없습니다."
        )
    
    return {"status": "success", "message": "이력이 성공적으로 삭제되었습니다."}