from sqlalchemy import Column, Integer, Text, String, Float, DateTime, create_engine, text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
import logging

from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

Base = declarative_base()

# 1. 실제 판례 데이터 테이블 (Case Law)
class Precedent(Base):
    """
    사건번호, 위반조항을 기반으로 판례 내용을 벡터화하여 저장
    """
    __tablename__ = 'precedents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String, unique=True, index=True, nullable=False) # 사건번호
    violated_article = Column(String, index=True)                       # 위반조항 (예: 근로기준법 제43조)
    content = Column(Text, nullable=False)                             # 판례 내용 원문
    embedding = Column(Vector(settings.BGE_M3_DIMENSION), nullable=False) # bge-m3 벡터
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# 2. 근로기준법 데이터 테이블 (Statutes)
class LaborLaw(Base):
    """
    수정된 CSV 구조를 반영한 근로기준법 데이터 테이블
    """
    __tablename__ = 'labor_laws'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 1. 고유 식별 정보 (검색 및 필터링용)
    article_num = Column(String, index=True)   # 조 번호 (제1조)
    paragraph_num = Column(String, index=True) # 조항 번호 (제1조 1항 등)
    keyword = Column(String, index=True)       # 조(키워드) (제1조(목적) 등)
    
    # 2. 내용 정보 (검색 및 응답용)
    summary = Column(Text, nullable=True)      # 추천 요약 (LLM에게 제공할 핵심 요약)
    law_content = Column(Text, nullable=False) # 통합 내용 (원문 전체)
    
    # 4. 벡터화 정보 (BGE-M3)
    embedding = Column(Vector(settings.BGE_M3_DIMENSION), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# 3. 구글 연동 분석 히스토리 테이블 (Analysis History)
class AnalysisHistory(Base):
    """
    구글 로그인 유저의 분석 이력을 통합 관리하는 테이블
    """
    __tablename__ = 'analysis_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 구글에서 제공하는 고유 식별자 (sub)
    google_id = Column(String, index=True, nullable=False)
    
    # 메타데이터
    doc_name = Column(String, nullable=False)          # 파일명 또는 "텍스트 분석"
    mode = Column(String, nullable=False)              # "file" 또는 "text"
    
    # 분석 요약 및 결과
    total_risk_score = Column(Float, nullable=False)   # 전체 위험도 점수
    missing_clause_report = Column(Text, nullable=True)
    results = Column(JSON, nullable=False)             # analysis_results 리스트 전체 저장
    
    # 시간 정보 (서버 시간 기준 KST 변환은 서비스 로직에서 처리 권장)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# --- DB 엔진 및 초기화 ---
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """DB 초기화 및 벡터 인덱스 최적화"""
    try:
        with engine.connect() as conn:
            # 1. 벡터 익스텐션 활성화
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            
            # 2. 테이블 생성
            Base.metadata.create_all(bind=engine)
            
            # 3. 인덱스 생성
            # 벡터 검색 최적화 (HNSW)
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_precedents_v ON precedents USING hnsw (embedding vector_cosine_ops);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_labor_laws_v ON labor_laws USING hnsw (embedding vector_cosine_ops);"))
            
            # [추가] 히스토리 조회 최적화 (최신순 5개 필터링용)
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_history_user_date ON analysis_history (google_id, created_at DESC);"))
            
            conn.commit()
            
            logger.info("✅ Antidote 4-Tier DB Schema (Auth 포함) 구축 완료")
    except SQLAlchemyError as e:
        logger.error(f"❌ DB 초기화 실패: {e}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()