import logging
from sqlalchemy.orm import Session
from app.db.vector_db import SessionLocal, init_db
from app.db.vector_db import LaborLaw, Precedent 

logger = logging.getLogger("uvicorn.error")

async def startup_event():
    logger.info("🚀 Antidote 백엔드 서비스를 시작합니다...")
    
    # 1. DB 초기화 (Table 생성 및 pgvector 확장 확인)
    try:
        init_db()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")

    db: Session = SessionLocal()
    try:
        # 2. 기초 법령 데이터 자동 적재 확인
        law_count = db.query(LaborLaw).count()
        if law_count == 0:
            logger.info("📡 기초 법령 데이터가 없습니다. 자동 벡터 적재를 시작합니다...")
            # 순환 참조 방지를 위해 함수 내부에서 임포트
            from app.scripts.ingest_laws import ingest_labor_laws
            csv_path_law = "data/근로기준법_조항.csv"
            ingest_labor_laws(csv_path_law)
        else:
            logger.info(f"✅ 기존 법령 데이터 확인됨 ({law_count}건). 자동 적재를 건너뜁니다.")
            
        # 3. 실제 판례 데이터 자동 적재 확인
        precedent_count = db.query(Precedent).count()
        if precedent_count == 0:
            logger.info("📡 실제 판례 데이터가 없습니다. 자동 벡터 적재를 시작합니다...")
            from app.scripts.ingest_precedents import ingest_precedents
            csv_path_pre = "data/실제판례.json"
            ingest_precedents(csv_path_pre)
        else:
            logger.info(f"✅ 기존 판례 데이터 확인됨 ({precedent_count}건).")
            
    except Exception as e:
        logger.error(f"❌ 데이터 적재 프로세스 중 오류 발생: {e}")
    finally:
        db.close()

    # 4. AI 모델 로더 상태 확인
    try:
        from app.core.model_loader import ml_engine
        logger.info(f"💡 AI 엔진 준비 상태: {ml_engine.device}")
    except Exception as e:
        logger.error(f"❌ AI 엔진 로드 실패: {e}")