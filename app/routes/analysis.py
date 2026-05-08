from fastapi import APIRouter
from app.controller import analysis

router = APIRouter(prefix="/analysis", tags=["Legal Analysis"])

# [Case A] PDF 파일 업로드 분석
router.add_api_route("/contract", analysis.contract, methods=["POST"])

# [Case B] 사용자 직접 입력 텍스트 분석
router.add_api_route("/text", analysis.analyze_text, methods=["POST"])

# [추가] WebSocket - 실시간 진행률 스트리밍
router.add_api_websocket_route("/ws/analyze", analysis.websocket_analyze)