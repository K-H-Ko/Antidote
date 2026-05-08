import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.vector_db import AnalysisHistory
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class HistoryService:
    @staticmethod
    async def save_analysis_result(
        db: Session, 
        google_id: str, 
        doc_name: str, 
        mode: str, 
        report_data: List[Dict[str, Any]],    # 기본값이 없는 인자를 앞으로 배치
        missing_clause_report: Optional[str] = None,
        total_risk_score: float = 0.0   # 기본값이 있는 인자를 가장 뒤로 배치
    ) -> bool:
        """
        분석 결과를 DB에 저장합니다. (로그인 유저 전용)
        """
        try:
            # 1. 새로운 히스토리 객체 생성
            new_history = AnalysisHistory(
                google_id=google_id,
                doc_name=doc_name,
                mode=mode,
                total_risk_score=total_risk_score,      # 인자로 받은 점수 사용
                missing_clause_report = missing_clause_report,
                results=report_data
            )
            
            db.add(new_history)
            db.commit()
            db.refresh(new_history)
            
            logger.info(f"✅ 히스토리 저장 완료 (User: {google_id}, ID: {new_history.id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 히스토리 저장 실패: {str(e)}")
            return False

    @staticmethod
    async def get_recent_history(db: Session, google_id: str, limit: int = 5) -> List[AnalysisHistory]:
        """
        특정 사용자의 최근 분석 이력을 최신순으로 가져옵니다.
        """
        try:
            return db.query(AnalysisHistory)\
                .filter(AnalysisHistory.google_id == google_id)\
                .order_by(desc(AnalysisHistory.created_at))\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"❌ 히스토리 조회 실패: {str(e)}")
            return []

    @staticmethod
    async def get_history_detail(db: Session, google_id: str, history_id: int) -> Optional[AnalysisHistory]:
        """
        특정 ID의 분석 이력 상세 내용을 가져옵니다. (본인 데이터인지 확인)
        """
        try:
            return db.query(AnalysisHistory).filter(
                AnalysisHistory.id == history_id,
                AnalysisHistory.google_id == google_id
            ).first()
        except Exception as e:
            logger.error(f"❌ 히스토리 상세 조회 실패: {str(e)}")
            return None

    @staticmethod
    async def delete_history_item(db: Session, google_id: str, history_id: int) -> bool:
        """
        특정 분석 이력을 삭제합니다. (본인 확인 절차 포함)
        """
        try:
            target = db.query(AnalysisHistory).filter(
                AnalysisHistory.id == history_id,
                AnalysisHistory.google_id == google_id
            ).first()
            
            if target:
                db.delete(target)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 히스토리 삭제 실패: {str(e)}")
            return False