from sqlalchemy.orm import Session
from app.db.vector_db import SessionLocal, LaborLaw, Precedent
from app.core.model_loader import ml_engine

class DBSearch:
    def get_related_data(self, query_text: str, top_k: int = 10):
        db = SessionLocal()
        try:
            model = ml_engine.get_bge_model()
            query_embedding = model.encode(query_text).tolist()

            # 2. 법령 검색: 거리(distance)를 계산하여 라벨링하고 함께 가져옵니다.
            law_dist_expr = LaborLaw.embedding.cosine_distance(query_embedding)
            law_results = db.query(
                LaborLaw, 
                law_dist_expr.label('dist')
            ).order_by(law_dist_expr).limit(top_k).all()

            # 결과 객체에 distance 속성 동적 주입
            laws = []
            for obj, dist in law_results:
                obj.distance = round(dist, 4) # 소수점 4자리까지 반올림
                laws.append(obj)

            # 3. 판례 검색: 동일하게 거리 값을 포함합니다.
            pre_dist_expr = Precedent.embedding.cosine_distance(query_embedding)
            pre_results = db.query(
                Precedent, 
                pre_dist_expr.label('dist')
            ).order_by(pre_dist_expr).limit(top_k).all()

            precedents = []
            for obj, dist in pre_results:
                obj.distance = round(dist, 4)
                precedents.append(obj)

            return laws, precedents
        finally:
            db.close()