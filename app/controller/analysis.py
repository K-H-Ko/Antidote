from fastapi import UploadFile, WebSocketDisconnect, File, status, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import asyncio
import logging
from fastapi import Depends 
from sqlalchemy.orm import Session  

from app.services.analyzer import LegalAnalyzer
from app.schemas.analysis import TextInput
from app.db.vector_db import get_db
from app.core.auth import get_current_user

logger = logging.getLogger("uvicorn.error")
analyzer = LegalAnalyzer()

async def contract(file: UploadFile = File(...), db: Session = Depends(get_db), google_id: str = Depends(get_current_user)):
    """[Case A] 파일 업로드 -> analyze 직접 호출"""
    try:
        logger.info(f"📥 파일 분석 요청: {file.filename}")
        
        # 1. 검증
        allowed_extensions = (".pdf", ".png", ".jpg", ".jpeg", ".jfif")
        if not file.filename.lower().endswith(allowed_extensions):
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

        # 2. 데이터 읽기
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="파일이 너무 큽니다.")

        # 3. [핵심] analyze_pdf를 거치지 않고 바로 analyze 호출
        # 파일 모드이므로 raw_bytes에 데이터를 전달합니다.
        report_data = await analyzer.analyze(
            text="", 
            doc_name=file.filename, 
            mode="file", 
            raw_bytes=content,
            db=db,              
            google_id=google_id 
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(report_data)
        )

    except HTTPException as he: raise he
    except Exception as e:
        logger.error(f"❌ 파일 분석 오류: {e}")
        return JSONResponse(status_code=500, content={"message": "분석 오류", "error": str(e)})
    finally:
        await file.close()

async def analyze_text(data: TextInput,db: Session = Depends(get_db), google_id: str = Depends(get_current_user)):
    """[Case B] 텍스트 입력 -> analyze 직접 호출"""
    try:
        logger.info(f"📝 텍스트 분석 요청: {data.doc_name}")
        
        # 텍스트 모드이므로 raw_bytes는 None(기본값)으로 둡니다.
        report_data = await analyzer.analyze(
            text=data.content, 
            doc_name=data.doc_name,
            mode="text",
            db=db,             
            google_id=google_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(report_data)
        )
    except Exception as e:
        logger.error(f"❌ 텍스트 분석 오류: {e}")
        return JSONResponse(status_code=500, content={"message": "분석 오류", "error": str(e)})
    
# [추가] WebSocket
async def websocket_analyze(websocket: WebSocket):
    """
    WebSocket을 통한 실시간 진행률 스트리밍 분석
    
    클라이언트에서 다음과 같이 요청:
    {
        "token": "JWT access_token",  // 로그인 사용자 확인용
        "content": "텍스트 내용",
        "doc_name": "문서명",
        "mode": "text" | "file"
    }
    
    서버에서 실시간 응답:
    {
        "step": 1-5 | "complete",
        "message": "단계별 메시지",
        "progress": 20-100,
        "data": {} // step="complete"일 때만 전체 결과 포함
    }
    """
    await websocket.accept()
    
    try:
        # 1. 클라이언트로부터 데이터 수신
        data = await websocket.receive_json()
        
        token = data.get("token")
        content = data.get("content", "")
        doc_name = data.get("doc_name", "WebSocket Input")
        mode = data.get("mode", "text")
        raw_bytes = data.get("raw_bytes")  # 파일 모드일 때
        
        logger.info(f"⚖️  분석 요청: {doc_name} (mode: {mode})")
        
        # 2. JWT 토큰 검증 (로그인 사용자 확인)
        from app.core.auth import get_current_user
        google_id = None
        if token:
            try:
                import jwt
                from app.core.config import settings
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) # algorithms는 리스트 형태여야 함
                google_id = payload.get("sub")
            except Exception as e:
                print(str(e))
                logger.warning(f"⚠️ JWT 디코드 실패: {e}")
                google_id = None  # 토큰 없어도 분석은 가능
        # 3. DB 세션 생성
        from app.db.vector_db import SessionLocal
        db = SessionLocal()
        
        try:
            # 4. 진행 상황을 보낼 콜백 함수 정의
            async def progress_callback(step, message, progress):
                await websocket.send_json({"step": step, "message": message, "progress": progress, "data": None})

            # 분석 태스크 생성
            analyze_task = asyncio.create_task(
                analyzer.analyze(
                    text=content,              # 수신한 텍스트
                    doc_name=doc_name,          # 문서명
                    mode=mode,                  # 'text' 또는 'file'
                    raw_bytes=raw_bytes,        # 파일 데이터 (있는 경우)
                    db=db,                      # DB 세션
                    google_id=google_id,        # 사용자 ID
                    progress_callback=progress_callback
                )
            )
            # 클라이언트 disconnect 감지 태스크
            disconnect_task = asyncio.create_task(websocket.receive_text())

            done, pending = await asyncio.wait(
                [analyze_task, disconnect_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # pending 태스크 정리
            for t in pending:
                t.cancel()

            if analyze_task in done:
                # 정상 완료
                report_data = analyze_task.result()
                await websocket.send_json({"step": "complete", "progress": 100, "data": jsonable_encoder(report_data)})
            else:
                # 클라이언트가 먼저 떠남 → 분석 취소
                logger.info("클라이언트 연결 종료 → 분석 취소")

        except (WebSocketDisconnect, asyncio.CancelledError):
            if analyze_task and not analyze_task.done():
                analyze_task.cancel()
            logger.info("분석 중단: 클라이언트 연결 해제")
        except Exception as e:
            logger.error(f"WebSocket 오류: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ WebSocket 분석 오류: {e}")
        await websocket.send_json({
            "error": str(e),
            "step": "error"
        })
    
    finally:
        await websocket.close()    