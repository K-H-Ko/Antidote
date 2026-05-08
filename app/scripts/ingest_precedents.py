# scripts/seed_precedents.py
import json
import os
from sqlalchemy.orm import Session
from app.db.vector_db import SessionLocal
from sentence_transformers import SentenceTransformer
from app.db.vector_db import Precedent  # 기존에 정의한 SQLAlchemy 모델
from app.core.config import settings
from app.core.model_loader import ml_engine


# BGE-M3 모델 가져오기
embed_model = ml_engine.get_bge_model()

def ingest_precedents(file_path: str):
    db: Session = SessionLocal()

        # 파일 존재 여부를 먼저 확인하고, 없으면 절대 경로로 재시도
    if not os.path.exists(file_path):
        # 현재 파일(ingest_laws.py)의 위치를 기준으로 프로젝트 루트를 찾아 경로 재설정
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, "data", "실제판례.json")
    # 2. JSON 데이터 읽기
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    batch_size = 500  # 500개 단위로 설정
    total_data = len(raw_data)

    for i, item in enumerate(raw_data):
        try:
            content_to_embed = item.get("판례내용(요약)")
            if not content_to_embed:
                continue

            embedding = embed_model.encode(content_to_embed).tolist()

            new_precedent = Precedent(
                case_number=item.get("사건번호"),
                violated_article=item.get("위반조항"),
                content=content_to_embed,
                embedding=embedding
            )
            db.add(new_precedent)

            # 500개마다 커밋 후 세션 비우기
            if (i + 1) % batch_size == 0:
                db.commit()
                print(f"✅ 중간 저장 완료: {i + 1}/{total_data}")

        except Exception as e:
            db.rollback() # 에러 발생 시 현재 배치 취소
            print(f"❌ {i}번째 데이터 오류로 롤백됨: {e}")
            continue

    # 루프 종료 후 남은 데이터 최종 커밋 (예: 2043개일 경우 마지막 43개)
    db.commit()
    print(f"🎊 모든 데이터 적재 프로세스가 완료되었습니다! (총 {total_data}건)")
