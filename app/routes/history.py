from fastapi import APIRouter, Depends
from app.controller import history as history_controller
from app.schemas.analysis import AnalysisReport

router = APIRouter(prefix="/history", tags=["User Analysis History"])

# 최근 이력 5개 조회
router.add_api_route(
    "/recent", 
    history_controller.get_recent_history, 
    methods=["GET"],
    summary="로그인 유저의 최근 분석 이력 5개 조회"
)

# 특정 이력 상세 조회 
router.add_api_route(
    "/{history_id}", 
    history_controller.get_history_detail, 
    methods=["GET"],
    response_model=AnalysisReport,
    summary="분석 이력 상세 데이터 조회"
)

# 특정 이력 삭제
router.add_api_route(
    "/{history_id}", 
    history_controller.delete_history, 
    methods=["DELETE"],
    summary="분석 이력 개별 삭제"
)