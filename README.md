# 🛡️ Antidote - AI 기반 근로계약 보호 시스템 <br>(AI-Powered Legal Analysis & Risk Detection)

<br>
<video src="https://github.com/K-H-Ko/Antidote/raw/main/document/시연영상_AI_근로계약_보호시스템.mp4" width="100%" controls autoplay muted loop>
  브라우저가 비디오 태그를 지원하지 않습니다.
</video>
<br><br>

**Antidote**는 근로계약서 내의 잠재적 리스크를 탐지하고, 공신력 있는 법령 및 판례 데이터를 근거로 제시하는 **지능형 법률 보조 솔루션**입니다. 단순한 텍스트 추출을 넘어, 다단계 AI 추론 파이프라인을 통해 사용자의 권리를 보호합니다.

---

## ✨ Project Overview

본 프로젝트는 복잡한 법률 용어로 구성된 근로계약서를 AI가 분석하여, **독소 조항(Toxic Clauses)** 여부를 판별하고 이에 대응하는 **최신 근로기준법 및 관련 판례**를 사용자에게 매칭해 줍니다.

- **Target**: 근로계약서 검토가 필요한 일반 근로자 및 인사 담당자
- **Core Value**: 법률 정보 비대칭 해소 및 계약 리스크 최소화

---

## 🏗️ System Architecture

Antidote는 **RAG(Retrieval-Augmented Generation)** 패턴을 기반으로 설계되었으며, 데이터의 정확도와 추론의 신뢰성을 높이기 위해 다단계 아키텍처를 채택했습니다.

### 1. Data Pipeline & Vector DB

- **Legal Knowledge Base**: 근로기준법을 조/항/제 단위로 세분화하여 벡터화(Vectorization) 완료.
- **Precedents DB**: 전처리된 판례 데이터를 임베딩하여 유사도 검색이 가능한 벡터 저장소 구축.
- **High-Speed Parsing**: `PyMuPDF`를 활용한 PDF 구조 분석 및 청크(Chunk) 최적화.

### 2. Multi-Stage AI Inference (In-Progress)

단일 모델의 한계를 극복하기 위해 역할별로 특화된 모델들을 체인(Chain) 형태로 연결합니다.

- **Embedding & Retrieval**: `bge-m3` 모델을 통해 문맥적 의미가 유사한 법령 및 판례 Top-N 추출.
- **Risk Classification**: `koELECTRA-small` 기반의 경량화된 분류기를 통한 독소 조항 1차 스캐닝.
- **Reasoning & Validation**: `RoBERTa-base` 모델을 활용하여 검색된 근거의 신뢰도를 검증하고 최종 답변 생성.

---

## 📂 Project Structure

```text
Antidote/
├── app/                      # Backend Core Logic (FastAPI)
│   ├── controller/           # API 비즈니스 로직 제어
│   ├── core/                 # 설정(config), 보안, 공통 모듈
│   ├── data/                 # 정적 데이터 및 리소스
│   ├── db/                   # 데이터베이스 연결 및 세션 관리
│   ├── models(생략)/         # AI 모델 파일 (huggingface 로드)
│   ├── routes/               # API 엔드포인트 정의
│   ├── schemas/              # Pydantic 모델 (Request/Response 타입)
│   ├── scripts/              # 유틸리티 스크립트 및 데이터 전처리
│   ├── services/             # 법률 분석(Analyzer), 검색 로직
│   └── venv(생략)/           # 가상 환경 (Python Virtual Environment)
├── document/                 # 프로젝트 관련 문서 (기획서, PND, 시연영상 등)
├── frontend/                 # Frontend Source (React/Next.js)
│   ├── node_modules/         # 프론트엔드 의존성 라이브러리
│   ├── public/               # 정적 자산 (이미지, 파비콘 등)
│   ├── src/                  # React 소스 코드 및 컴포넌트
│   ├── .env(생략)            # 환경 변수 (보안 주의)
│   └── .env.sample           # 환경 변수 샘플
├── .env(생략)                # 환경 변수 설정 파일 (보안 주의)
├── .env.sample               # 환경 변수 샘플 양식
├── docker-compose.yml        # Docker 컨테이너 설정
├── lifecycle.py              # 앱 생명주기 관리 (Startup/Shutdown)
├── main.py                   # FastAPI 앱 실행 진입점
├── README.md                 # 프로젝트 설명 문서
└── requirements.txt          # 백엔드 라이브러리 의존성 목록
```
