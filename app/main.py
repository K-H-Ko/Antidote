import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.lifecycle import startup_event  
from app.routes import analysis, history, auth

# 로깅 설정
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info(f"Starting up {settings.PROJECT_NAME}...")
        await startup_event() 
        yield  # 애플리케이션 실행 중
        
    except Exception as e:
        logger.critical(f"App startup failed: {e}")
        raise SystemExit(1) from e
    finally:
        logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="근로계약서 독소조항 분석 서비스 'Antidote'",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 불러오기
app.include_router(analysis.router) # /analysis/...
app.include_router(history.router)  # /history/...
app.include_router(auth.router)     # /auth/... (구글 로그인용)

@app.get("/", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "app": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs"
    }

if __name__ == "__main__":
    # 포트 번호 8000 사용
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)