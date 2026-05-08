from fastapi import APIRouter
from app.controller import auth as auth_controller
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    token: str

@router.post("/google")
async def google_login(request: LoginRequest):
    return await auth_controller.process_google_login(request.token)