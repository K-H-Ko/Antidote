import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))  # app/core
app_dir = os.path.dirname(current_dir)                    # app
env_path = os.path.join(app_dir, ".env")                  # 루트의 .env 참조

class Settings(BaseSettings):
    # [1] Project Info
    PROJECT_NAME: str = "Antidote"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # [2] PostgreSQL & pgvector Config
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str  # .env의 전체 URL을 그대로 주입받음

    # [3] AI Model Names
    RoBERTa_BASE_MODEL: str
    koELECTRA_SMALL_MODEL: str
    BGE_M3_MODEL: str
    RoBERTa_SUBFOLDER: str = "cross_encoder"
    koELECTRA_SUBFOLDER: str = "Toxic"
    
    # [4] Gemini-api
    GEMINI_API_KEY: str
    GEMINI_MODEL_LIST: str  # [수정부분]
    @property
    def gemini_models(self) -> list:
        """쉼표로 구분된 문자열을 리스트로 변환"""
        return [m.strip() for m in self.GEMINI_MODEL_LIST.split(",")]
    
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24시간 
    GOOGLE_CLIENT_ID: str

    # [5] Vector Dimensions
    BGE_M3_DIMENSION: int = 1024
    KOELECTRA_BASE_DIMENSION: int = 768
    KOELECTRA_SMALL_DIMENSION: int = 512
    
    # 파이프라인 하위 호환성을 위한 기본 차원
    VECTOR_DIMENSION: int = 1024

    # [6] Model Settings
    MAX_SEQ_LENGTH: int = 512

    # Pydantic 설정: .env 파일을 읽어오는 핵심 로직
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,  # 대소문자 구분 없이 .env 키와 매칭
        extra='ignore'         # 정의되지 않은 추가 환경 변수는 무시
    )

# 싱글톤 객체 생성
settings = Settings()