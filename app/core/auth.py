import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from typing import Optional

# 1. 헤더에서 'Authorization: Bearer <토큰>'을 찾아내는 도구
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google", auto_error=False)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    if not token:
        return None # 토큰 없으면 그냥 None 반환 (에러 X)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None # 토큰이 잘못되어도 분석은 가능하게 None 반환

