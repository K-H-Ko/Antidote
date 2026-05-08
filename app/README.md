## 🚀 시작 가이드 (Getting Started)

#이 프로젝트는 근로계약서의 독소 조항을 분석하고 수정안을 제안하는 RAG 기반 서비스입니다.

#모델은 따로 다운로드 받아 프로젝트 내부에 위치시켜 .env파일에 경로 추가 ex) app/models/koELECTRA_small

```bash
# venv 가상환경에서 진행 할 것 (없으면 만들고 진행)

# 필수 패키지 설치
pip install -r requirements.txt

# 서버 실행 (서버 실행 시 DB 세팅 및 모델 로드 및 근로기준법 DB 저장 로직 자동 수행)
python -m app.main

# 테스트 스크립트
python -m app.test.test_flow
```
