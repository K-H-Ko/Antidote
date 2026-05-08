from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TextInput(BaseModel):
    content: str
    doc_name: Optional[str] = None

class LegalBasis(BaseModel):
    title: str
    summary: str

class PrecedentDetail(BaseModel):
    title: str
    content: str

# --- 수정 및 추가된 부분 ---
class ResultDetail(BaseModel):
    clause: str
    result_type: str        # "GENERAL" (질문) 또는 "ANALYSIS" (조항)
    level: str              # SAFE, CAUTION, WARNING, DANGER, EXTREME           
    score: float
    # 개별 렌더링을 위한 필드 추가
    reason: str = ""       # 판단 근거
    proposed_text: str = "" # 수정 제안 문구
    tags: List[str] = []
    legal_basis: List[LegalBasis] = []
    precedents: List[PrecedentDetail] = []

class AnalysisReport(BaseModel):
    status: str
    doc_name: str
    mode: Optional[str] = "text"   # "text" | "file" — 히스토리 조회 시 프론트로 전달
    total_risk_score: float
    missing_clause_report: Optional[str] = None
    results: List[ResultDetail]
    analyzed_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))