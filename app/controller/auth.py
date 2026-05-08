import jwt
from datetime import datetime, timezone, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
from app.core.config import settings

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def process_google_login(token: str):
    try:
        # 구글 ID 토큰 검증
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), 
            settings.GOOGLE_CLIENT_ID)
        google_id = id_info.get("sub") # 고유 식별자
        
        # 우리 서비스 전용 JWT 발급
        access_token = create_access_token(data={"sub": google_id})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": id_info.get("email"), "name": id_info.get("name")}
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="구글 인증 실패")