import pandas as pd
import os
import logging
from sqlalchemy.orm import Session
from app.db.vector_db import SessionLocal, LaborLaw
from app.core.model_loader import ml_engine

logger = logging.getLogger("uvicorn.error")

def ingest_labor_laws(file_path: str):
    db: Session = SessionLocal()
    embed_model = ml_engine.get_bge_model()
    
    try:
        # 파일 경로 설정 로직 (기존 유지)
        if not os.path.exists(file_path):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, "data", "근로기준법_조항.csv")
            
        logger.info(f"🔎 파일 읽기 시도 중: {os.path.abspath(file_path)}")
        
        # utf-8-sig 인코딩을 사용하여 눈에 안 보이는 BOM(\ufeff) 제거
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        df.columns = [col.strip() for col in df.columns]
        
        laws_to_add = []
        
        logger.info(f"⏳ {len(df)}건의 법령 데이터 벡터화 시작...")

        for _, row in df.iterrows():
            # 1. 컬럼 매핑 (이미지 기반)
            article_num = str(row['조 번호']).strip()     # 제1조
            paragraph_num = str(row['조항 번호']).strip() # 제1조 (또는 제2조 1항 등)
            keyword = str(row['조(키워드)']).strip()      # 제1조(목적)
            summary = str(row['요약 내용']).strip()      # 헌법에 따라...
            full_content = str(row['통합 내용']).strip()  # 제1조(목적) 헌법에 따라...
            
            # 3. 벡터화 (BGE-M3)
            # 검색 정확도를 높이기 위해 '요약 내용'이나 '통합 내용' 중 선택하여 임베딩합니다.
            # 현재는 통합 내용 임베딩 -> 추후 검증 단계에서 정확도 부족 시 요약 내용을 임베딩
            embedding = embed_model.encode(summary).tolist()

            # 4. ORM 객체 매핑
            law_entry = LaborLaw(
                article_num=article_num,
                paragraph_num=paragraph_num,
                keyword=keyword, 
                summary=summary,
                law_content=full_content,  
                embedding=embedding
            )
            laws_to_add.append(law_entry)

        # 5. 벌크 저장
        db.bulk_save_objects(laws_to_add)
        db.commit()
        logger.info(f"✅ 법령 데이터 {len(laws_to_add)}건 적재 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 데이터 적재 중 치명적 오류: {e}")
        raise e
    finally:
        db.close()