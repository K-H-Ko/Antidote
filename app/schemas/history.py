from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .analysis import ResultDetail  

# 1. 히스토리 저장 및 조회를 위한 베이스 스키마
class HistoryBase(BaseModel):
    doc_name: str
    mode: str
    total_risk_score: float
    results: List[ResultDetail]
    missing_clause_report: Optional[str] = Field(
        None, 
        description="해당 문서 전체에서 누락된 조항에 대한 종합 안내 문구"
    )

# 2. 히스토리 생성 시 사용 (HistoryBase를 그대로 상속)
class HistoryCreate(HistoryBase):
    pass

# 3. 프론트엔드 반환용 (ID와 생성일시 포함)
class HistoryResponse(HistoryBase):
    id: int
    created_at: datetime = Field(..., description="분석이 수행된 날짜 및 시간")

    class Config:
        # SQLAlchemy 모델 객체를 Pydantic으로 자동 변환하기 위한 설정
        from_attributes = True