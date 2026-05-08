import fitz
import torch
import logging
import json
import asyncio
import torch.nn.functional as F
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from tenacity import retry
from google.genai import types

from app.core.model_loader import ml_engine
from .db_search import DBSearch
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.history_service import HistoryService

logger = logging.getLogger("uvicorn.error")

class LegalAnalyzer:
    def __init__(self):
        self.db_search = DBSearch()
        self.client, self.model_list = ml_engine.get_gemini_client()
    
        # 모델 엔진 로드   
        self.small_model, self.small_tokenizer = ml_engine.get_small_model()
        self.base_model, self.base_tokenizer = ml_engine.get_base_model()
        self.device = ml_engine.device
        
    async def _safe_generate(self, prompt, config, timeout_seconds=10.0): # [여기부터 raise last_exception 까지 추가 부분]
        """
        [라운드 로빈 순환 호출 전략]
        - 각 모델당 최대 10초 대기, 응답 없거나 에러 시 즉시 다음 모델 시도.
        - 전체 모델 리스트를 한 바퀴 도는 것을 1사이클로 하여 총 3사이클 반복.
        """
        max_cycles = 3           # 총 3회전
        last_exception = None
        
        # 모델 리스트를 순서대로 시도
        for cycle in range(max_cycles):
            # logger.info(f"🔄 Gemini 순환 호출 {cycle + 1}사이클 시작")
            for model in self.model_list:
                try:
                    # 호출 시 전달받은 timeout_seconds 사용
                    response = await asyncio.wait_for(
                        self.client.aio.models.generate_content(
                            model=model,
                            contents=[prompt],
                            config=types.GenerateContentConfig(
                                temperature=config.get("temperature", 0.1),
                                response_mime_type="application/json"
                            )
                        ),
                        timeout=timeout_seconds
                    )
                    # 성공 시 즉시 결과 반환
                    return response
                
                except (asyncio.TimeoutError, Exception) as e:
                    last_exception = e
                    error_msg = str(e)

                    # 에러 타입 판정
                    if isinstance(e, asyncio.TimeoutError):
                        reason = "타임아웃"
                    elif "503" in error_msg or "429" in error_msg:
                        reason = "과부하"
                    else:
                        reason = "서버 에러"

                    # 로그 한 번만 기록
                    logger.warning(f"⚠️ {model} ({cycle + 1}회차): {reason}. 다음 모델로 전환합니다.")

                    # 503/429일 때만 추가 대기
                    if reason == "과부하":
                        wait_time = (cycle + 1) * 2
                        logger.info(f"   → {wait_time}초 대기 후 재시도합니다.")
                        await asyncio.sleep(wait_time)
                    continue

        # 모든 사이클을 다 돌았는데도 실패한 경우
        logger.error(f"❌ 총 {max_cycles}사이클(총 {len(self.model_list) * max_cycles}회 시도) 모두 실패.")
        raise last_exception

    # 파일첨부시 적용 할 프롬프트
    async def _extract_clauses_from_file(self, file_content: bytes, mime_type: str = "application/pdf") -> Dict[str, Any]:
        """[멀티모달] 파일(PDF/이미지)에서 직접 독소조항 후보를 추출 및 정제"""
        
        # 프론트엔드에서 보낸 Data URL(base64) 처리
        if isinstance(file_content, str) and "," in file_content:
            # 'data:application/pdf;base64,abc...' -> 'abc...' 만 추출
            file_content = file_content.split(",")[1]
            
        # 1. 파일 데이터를 제미나이 입력 형식으로 변환
        content_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": file_content
            }
        }

        prompt = f"""
        당신은 법률 계약서 전문 OCR 및 근로기준법 전문 감사관입니다. 
        제공된 파일을 분석하여 (임무1) 필수 조항 누락 여부를 판별하고,
        (임무2) 근로자에게 애매한 조항 또는 불리하거나 법적 분쟁 소지가 있는 '독소조항' 후보들만 선택적으로 추출하세요.

        [데이터 유효성 검사 (is_valid)]
            - 제공된 파일이 '근로계약서'이거나 '약관', '계약관련' 또는 '노동법 관련 문서'가 맞다면 내용이 아무리 부실하더라도 "is_valid": true 로 설정하세요.
            - 오직 계약 관련이 아예 없는 문서(잡지, 성적표, 풍경 사진 등)일 때만 "is_valid": false로 설정하세요.
            - 제목 페이지 또는 목차 페이지가 있다면 마지막 페이지까지 확인 후에 판단 하세요.
        
        [임무1: 필수 항목 체크(근로기준법 제17조)]
        다음 항목들이 계약서에 명시되어 있는지 확인하고, 누락된 항목이 있다면 'missing_elements' 리스트에 담으세요.
         (단, 빈 계약서 일 수도 있으니 아래 내용이 제목으로라도 명시 되어있으면 제외하고, 계약서안에 제목도 없이 아무것도 명시 안되어 있는것만 작성하세요)
         (예시: 임금:__원, 지급일: 매월 __일, 등 내용이 비어 있어도 명시되어 있다면 누락 아님)
            1. 임금의 구성항목, 지급방법
            2. 소정근로시간 및 휴게시간
            3. 제55조에 따른 유급주휴일 (매주_일, 주휴일 매주_요일 등 휴일 관련 내용 있으면 누락 아님)
            4. 제60조에 따른 연차 유급휴가
            5. 근무 장소 및 종사하여야 할 업무
            6. 근로계약서 교부 내용(사본을 근로자에게 1부 교부한다)
            
        [임무2: 독소 조항 추출 필터링]
        [추출 모드: 엄격한 독소 조항 필터링]
        다음에 해당하는 일반적인 정보는 **절대로 추출하지 마세요**:
        1. 단순 근로 조건: 일급/월급 금액, 근무 장소, 단순 업무 내용, 계약 기간 등 단순 팩트 나열.
        2. 표준적인 조항: 법령을 그대로 준수하는 지극히 평범한 문구.
        3. 무의미한 텍스트(페이지 번호, 계약서 제목, 단순 인사말 등)는 모두 무시하세요.
            - 예시: 제 O조, O항, 근로시간:, 계약기간:, 급여(급료):, 임금:__원, O시간, O시 O분, 일급:OOO,OOO원, ___년__월_일 등등

        [반드시 추출해야 할 '독소 조항' 상세 카테고리]
        ※ 추출 원칙: 조금이라도 근로자의 권리를 제한하거나 회사(사용자)의 권한을 무한정 확대하는 문구라면, '일반 조항'으로 간주하지 말고 반드시 '독소 조항' 후보로 추출하세요. 판단이 애매할 때는 '추출'하는 것을 원칙으로 합니다.
        1. 사용자 편의적 일방 결정권 (Unilateral Rights)
        - "회사의 사정에 따라", "경영상의 이유로", "합의 없이", "변경할 수 있다", "결정한다" 등의 표현.
        - 직무 변경, 근무지 이전, 임금 삭감 등의 결정권을 회사에 전적으로 부여한 경우.
        2. 징계 및 해고의 절차적 위법성 (Arbitrary Termination)
        - "즉시 해고", "계약 자동 해지", "이의 없이 수용", "권고사직을 받아들임" 등의 표현.
        - 근로기준법상 정당한 이유나 절차(30일 전 예고 등)를 무시하고 즉시 효력을 발생하는 문구.
        3. 근로기준법 위반 위약금 및 손해배상 (Illegal Penalty)
        - "중도 퇴사 시 교육비 반환", "손해액의 N배 배상", "위약금", "임금에서 상계함" 등의 표현.
        - 근로기준법 제20조(위약금 예정의 금지) 위반 소지가 있는 모든 배상 약정.
        4. 권리 행사 방해 및 부제소 특약 (Rights Waiver)
        - "민/형사상 이의 제기 금지", "비밀 유지 위반 시 퇴직금 반납", "영업비밀 보호를 위해 경업 금지" 등.
        - 사용자의 위법 행위에도 불구하고 근로자가 법적 권리를 행사하지 못하도록 압박하는 문구.
        5. 포괄적 의무 및 휴게권 침해 (Extensive Duty)
        - "업무 외의 지시 준수", "휴게 시간 중 대기", "24시간 연락 유지", "포괄임금제로 모든 수당 포함" 등.
        - 업무 범위를 모호하게 넓히거나, 법정 휴게 시간/연차 사용을 실질적으로 제한하는 문구.
        6. 기타 불평등 조항 (Miscellaneous)
        - 수습 기간 중 임금을 최저임금 미만으로 지급하거나, 연장/야간/휴일 근로를 사전 합의 없이 강제하는 문구.
        
        7. [데이터 처리 지침]:
          추출된 각 조항은 다음 두 가지 처리를 거쳐야 합니다
           - text: 문서에 적힌 원문 문장 그대로 추출 (제O조와 같은 머리말은 제외하고 본문만)
              - 예시: "갑은 근로계약을 체결함과 동시에 본 계약서를 사본하여 을에게 교부함."
           - reverse: 해당 계약 조항이 침해하는 **'근로자의 법적 권리'**를 식별하고, 이를 임베딩 모델이 인식하기 쉬운 표준 법률 문구로 아래 형식 참고하여 재구성합니다.(독소조항이 아니라면 정제 하지 말 것.)
              1) 형식 전환: "~할 수 없다", "~를 금지한다"와 같은 계약서식 부정 표현을 **"근로기준법 조항에 정확히 명시된 "~의 원칙","~할 의무","~인정 된다","~지급해야 한다"**와 같은 법령·판례식 규범 표현으로 역치환하십시오.
              2) 키워드 추출: 해당 조항의 핵심 테마(예: 해고, 임금, 휴게시간, 위약금)를 파악하여, '해고의 정당성', '임금 전액 지급의 원칙' 등 벡터 DB가 검색하기 유리한 **'가상의 정답 문구'**를 생성하십시오.
        8. 추출할 조항이 많을시 가장 위험도가 높은 핵심 조항 위주로 최대 10개까지만 리스트에 담으세요.

        [반환 형식: JSON]
        {{
            "is_valid": True/False (계약,약관 관련 문서: True, 계약관련 없음: Flase 와 안내 메시지를 작성하세요.)
            "guide_message": "false(무관)일 때 안내 문구(소프트 거절 멘트 50자 이내)",
            "missing_elements": ["누락된 항목 명칭 1", "누락된 항목 명칭 2",...], (누락항목이 있을때만 작성)
            "items": [
                {{
                    "text": "추출된 조항 원문 1",
                    "type": "ANALYSIS",
                    "reverse": "법률 규범으로 정제된 문구 1"
                }},
                {{
                    "text": "추출된 조항 원문 2",
                    "type": "ANALYSIS",
                    "reverse": "법률 규범으로 정제된 문구 2"
                }}
            ]
        }}
        """

        try:
            # 파일 분석을 위해 타임아웃을 35~50초로 넉넉하게 설정하여 호출
            response = await self._safe_generate(
                prompt=[prompt, content_part], # 텍스트 프롬프트와 파일 데이터를 함께 전달
                config={"temperature": 0.1, "response_mime_type": "application/json"},
                timeout_seconds=40.0 # 파일 분석 전용 긴 타임아웃
            )
            
            # print("\n" + "="*50)
            # print(f"[Gemini File Analysis Success]\n{response.text}")
            # print("="*50 + "\n")
                        
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"File Extraction Error: {e}")
            return {"is_valid": True, "items": []}
    
    # 텍스트만 입력시 적용 할 프롬프트
    async def _split_and_classify_with_llm(self, text: str) -> Dict[str, Any]:
        """[통합] 가드레일 + 문장 분리/분류 + 단순 질문 답변을 한 번에 처리"""
        if not self.client: 
            return {"is_valid": True, "items": [{"text": text, "type": "GENERAL"}]}

        prompt = f"""
        당신은 법률 상담 서비스의 전처리 전문가입니다. 다음 단계를 엄격히 준수하세요.
        
        [단계 1: 유효성 검사]
        사용자 입력이 '근로계약', '노동법', '고용 관계', '약관 분석'과 관련이 있는지 판단하세요.
        실제 계약서의 조항 문체(예: ~한다, ~있다, ~된다 등) 또는 문구, 권리/의무가 명시된 구체적인 계약 내용 일때(True)
        - 관련 없다면: "is_valid": false 와 안내 메시지를 작성하세요.
        - 관련 있다면: "is_valid": true 로 설정하고 단계 2로 진행하세요.
        
        [단계 2: 분리 및 분류]
        사용자가 입력한 다음 텍스트를 분석하여 법 또는 계약 조항과 관련있는 질문이라면, 
        다음 2가지 중 하나를 선택하여 처리하세요.
        
        [분류 기준]
        1. GENERAL: 일반적인 궁금증, 법률 상식 질문, 노동법 관련 Q&A(예: 주휴수당 기준이 뭐야?)
            - "answer" 필드에 질문의 핵심을 파악하여 2~3문장 내외로 명확하게 답변하세요.
            - 답변의 근거가 되는 2026년 현재 시행 중인 대한민국 법령(근로기준법)이 있다면 아래 원칙에 따라 답변해주세요
              1) 근거 법령: 반드시 '대한민국 근로기준법' 및 관련 시행령을 기준으로 답변하세요.
              2) 인용 형식: 가능한 경우 "근로기준법 제OO조(제목)에 따르면..."과 같은 형식을 사용하세요.
              3) 엄격한 사실주의: 본인이 학습한 데이터 중 확신이 없거나, 개정되어 불확실한 수치(예: 2026년 최저임금 등)는 절대로 확답하지 마세요.
              4) 방어적 답변: 법령에 명시되지 않은 주관적 해석이 필요한 경우 "고용노동부 가이드라인에 따르면..." 혹은 "판례의 태도에 따라 달라질 수 있으나..."라는 단서를 붙이세요.
              5) 모름 선언: 근로기준법 범위를 벗어나거나 근거가 명확하지 않은 경우, "해당 내용은 법령상 명시적 규정이 없으므로 전문가(노무사) 상담이 필요합니다"라고 답변하세요.
        2. ANALYSIS: 실제 계약서의 조항 문체(예: ~한다, ~있다, ~된다 등) 또는 문구, 권리/의무가 명시된 구체적인 계약 내용 일때,
            - reverse: 입력된 계약 조항이 침해하는 **'근로자의 법적 권리'**를 식별하고, 이를 임베딩 모델이 인식하기 쉬운 표준 법률 문구로 아래 형식 참고하여 재구성합니다.(독소조항이 아니라면 정제 하지 말 것.)
              1) 형식 전환: "~할 수 없다", "~를 금지한다"와 같은 계약서식 부정 표현을 **"근로기준법 조항에 정확히 명시된 "~의 원칙","~할 의무","~인정 된다","~지급해야 한다"**와 같은 법령·판례식 규범 표현으로 역치환하십시오.
              2) 키워드 추출: 해당 조항의 핵심 테마(예: 해고, 임금, 휴게시간, 위약금)를 파악하여, '해고의 정당성', '임금 전액 지급의 원칙' 등 벡터 DB가 검색하기 유리한 **'가상의 정답 문구'**를 생성하십시오.
        
        [입력 텍스트]
        "{text}"

        [반환 형식: JSON]
        {{
            "is_valid": true/false,
            "guide_message": "false(무관)일 때 안내 문구(소프트 거절 멘트 50자 이내)",
            "items": [
                {{
                    "text": "원문 문장", 
                    "type": "GENERAL", 
                    "answer": "직접 작성한 법률 답변 (GENERAL일 때만)"
                }},
                {{
                    "text": "원문 문장", 
                    "type": "ANALYSIS", 
                    "reverse": "정제된 문구 (ANALYSIS일 때만)"
                }}
            ]
        }}
        """
        try:
            response = await self._safe_generate(
                prompt,
                {"temperature": 0.1, "response_mime_type": "application/json"}
            )
            
            # print("\n" + "="*50)
            # print(f"[Gemini Guardrail Raw Response]\n{response.text}")
            # print("="*50 + "\n")
            
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Integrated LLM Error: {type(e).__name__} - {e}")
            return {"is_valid": True, "items": [{"text": text, "type": "GENERAL", "answer": "답변을 생성하지 못했습니다."}]}
        
    async def _generate_batch_legal_report(self, analysis_data: list) -> dict:
        if not analysis_data:
            return []

        # 1. 누락 정보 취합 (문서 전체에서 누락된 항목들을 하나의 텍스트로 병합)
        all_missing_items = [data.get('missing_summary') for data in analysis_data if data.get('missing_summary')]
        unique_missing_items = list(set(all_missing_items)) # 중복 제거
        
        items_context = []
        for i, data in enumerate(analysis_data):
            law = data.get('law')
            precedent = data.get('precedent')
            
            law_info = f"[{law.keyword}] {law.summary}" if law else "근로기준법 원칙에 따라 분석 필요"
            pre_info = f"[{precedent.case_number}] {precedent.content} (유사도: {data.get('pre_score', 0):.2f}%)" if precedent else "관련 데이터 없음"
            
            items_context.append(f"""
            ### [분석 대상 조항 {i+1}]
            - 조항 내용: "{data['clause']}"
            - 참고 법률: {law_info}
            - 관련 판례: {pre_info}
            """)

        # 2. 누락 항목이 있을 경우에만 프롬프트에 분석 지침 추가
        missing_instruction = ""
        if unique_missing_items:
            missing_instruction = f"""
            5. 누락 사항 종합 분석 (missing_clause_report):
                - 현재 계약서에서 누락된 것으로 파악된 항목들: {", ".join(unique_missing_items)}
                - 위 항목들이 계약서 전체의 안전성에 미치는 영향을 분석하여 하나의 종합 안내 문구를 작성하세요.
                - 형식: "해당 계약서에는 (항목명) 등이 누락되어 있습니다. 근로자의 권리 보호를 위해 해당 내용을 포함하여 계약서를 재작성하거나 별도의 부속 합의서를 체결하십시오."
            """
        else:
            missing_instruction = "5. 누락 사항 종합 분석: 누락된 항목이 없으므로 'missing_clause_report' 필드는 null로 반환하세요."
        
        prompt = f"""
        당신은 대한민국 법률 분석 전문가입니다. 
        제시된 각 계약 조항들의 위험성을 정밀 분석하고, 사용자를 보호하기 위한 수정안을 리스트 순서대로 제시하세요.

        {"".join(items_context)}

        [임무: 정밀 분석 및 검증]
        1. 분석: 참고 데이터를 바탕으로 해당 조항이 사용자(근로자)에게 불리한 이유를 'reason'에 기술하세요.
            - 참고 데이터가 정확하지 않을 수 있습니다 질문에 직접적으로 연관지을 수 없거나, 근거자료로 사용불가 하면 절대 참고 및 인용하지 마세요.
            - 질문 조항 자체가 독소조항인지 애매하다면, 어떤 상황에 따라 독소조항이 될 수 있는지 정확한 예시로 답변 
        2. **판례 검증**: 
            - '관련 판례'의 **유사도가 40.00% 미만**인 경우, 해당 조항과 맥락이 다르다고 판단하여 'precedents' 리스트를 **빈 값([])**으로 처리하세요.
            - 40.00% 이상인 경우에도 내용을 정확히 파악하여 질문에 대해 근거자료로 확실하다고 판단 될 때만 참고하여 포함하세요. 
        3. 법적 근거: 
            - 'legal_basis'에는 반드시 전달받은 [참고 데이터]의 법령 정보를 우선적으로 사용하세요.(단, 참고 데이터를 확실히 파악 후 질문에 근거 사유가 될 때만 사용하세요) 
            - 전달받은 법령 데이터가 질문에 확실한 근거자료가 된다면 오직 1개의 데이터만 리스트에 담으세요. 
            - 제공받은 [참고 데이터]의 법령 정보가 본인 판단과 일치 하지 않은 경우에는 아래의 가이드로 판단하여 근거로 사용한 법령 정보를 1개만 리스트에 반드시 담으세요.
                *[판단 가이드]:
                  질문의 근거가 되는 2026년 현재 시행 중인 대한민국 법령(근로기준법)이 있다면 아래 원칙에 의해서만 사용할 것
                    1) 근거 법령: 반드시 '대한민국 근로기준법' 및 관련 시행령을 기준으로 하세요.
                    2) 인용 형식: 가능한 경우 "근로기준법 제OO조(제목)에 따르면..."과 같은 형식을 사용하세요.
                    3) 엄격한 사실주의: 본인이 학습한 데이터 중 확신이 없거나, 개정되어 불확실한 수치(예: 2026년 최저임금 등)는 절대로 사용하지 마세요.
                    4) 방어적 답변: 법령에 명시되지 않은 주관적 해석이 필요한 경우 "고용노동부 가이드라인에 따르면..." 혹은 "판례의 태도에 따라 달라질 수 있으나..."라는 단서를 붙이세요.
                    5) 모름 선언: 근로기준법 범위를 벗어나거나 근거가 명확하지 않은 경우, "해당 내용은 법령상 명시적 규정이 없으므로 전문가(노무사) 상담이 필요합니다"라고 답변하세요. 
        4. 대안 제시: 불리한 조항을 무효화하거나 완화할 수 있는 '표준 수정 문구'를 'proposed_text'에 작성하세요.
        {missing_instruction}
        
        [출력 JSON 형식]
        반드시 아래와 같은 구조의 JSON 리스트([])로 응답하세요:
        {{
            "analyses": [
                {{
                    "reason": "판단 근거 (100자 이내)",
                    "proposed_text": "수정 제안 문구",
                    "legal_basis": [{{ "title": "조항명", "summary": "내용 요약" }}],
                    "precedents": [{{ "title": "사건번호", "content": "판결 요지" }}]
                }},
                ...
            ],
            "missing_clause_report": "문서 전체 누락 사항에 대한 종합 안내 문구 (없으면 null)"
        }}
        """

        try:
            # 배치 처리를 위해 타임아웃을 조금 더 넉넉하게 설정 (30초)
            response = await self._safe_generate(
                prompt,
                {"temperature": 0.1, "response_mime_type": "application/json"},
                timeout_seconds=30.0
            )
            
            # print("\n" + "="*50)
            # print(f"[Gemini Batch Analysis Success]\n{response.text}")
            # print("="*50 + "\n")
            
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Batch Analysis Report Error: {e}")
            # 에러 발생 시 모든 항목에 대해 기본 에러 객체 반환
            return [{
                "reason": "데이터 처리 중 오류가 발생했습니다.", 
                "proposed_text": "전문가와 상담을 권장합니다.", 
                "legal_basis": [], 
                "precedents": []
            } for _ in range(len(analysis_data))]

    async def analyze(
        self, 
        text: str, 
        doc_name: str, 
        mode: str = "text", 
        raw_bytes: bytes = None, 
        db: Session = None, 
        google_id: str = None, 
        progress_callback = None
    ):
        
        """
        [전체 통합 분석 함수]
        1. 모드별 문장 분리 및 유형 분류
        2. 조항별 위험도 탐지(KoELECTRA) 및 RAG(Vector DB + Re-ranking)
        3. 수집된 모든 데이터를 단 한 번의 LLM 호출로 배치 처리(Report 생성)
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 0. 입력값 유효성 체크
        if mode != "file" and (not text or not text.strip()):
            return {
                "status": "invalid_query", 
                "message": "분석할 내용이 발견되지 않았습니다. 내용이 비어 있는지 확인해 주세요.", 
                "results": []
            }
        
        current_time = datetime.now().strftime("%H:%M:%S")  # 터미널 log 전용(시간log)
        
        # [추가] [Progress Step 1] 조항 분류
        if progress_callback:
            await progress_callback(step=1, message="조항 내용 정밀분석 중입니다.", progress=20)    
            print(f"\n[{current_time}] [STEP 1] 🔎 조항 내용 정밀분석 중...")
            
        # --- [STEP 1] 모드별 1차 처리: 문장 분리 및 유형 분류 ---
        analysis_results = []
        all_scores = []
        batch_input_data = [] # 배치를 위한 재료 저장소
        missing_summary = None # 파일 모드 전용 누락 항목 요약

        if mode == "file":
            # 파일 모드: 멀티모달 OCR 및 독소조항 추출 호출
            mime_type = "image/jpeg" if doc_name.lower().endswith(('.jpg', '.jpeg', '.png')) else "application/pdf"
            llm_res = await self._extract_clauses_from_file(raw_bytes, mime_type)
            
            # 파일 모드 전용 필드: missing_elements(누락된 항목들)
            missing_list = llm_res.get("missing_elements", [])
            if missing_list:
                missing_summary = ", ".join(missing_list)
            
            parsed_items = llm_res.get("items", [])
        else:
            # 텍스트 모드: 가드레일 및 단순질문/조항 분류 호출
            llm_res = await self._split_and_classify_with_llm(text)
            parsed_items = llm_res.get("items", [])

        print(f"\n[{current_time}] [STEP 1] 📄 조항 분류 완료: {len(parsed_items)}개의 후보 식별")

        # --- [STEP 2] 서비스 관련성 가드레일 체크 ---
        if not llm_res.get("is_valid", True):
            return {
                "status": "invalid_query", 
                "message": llm_res.get("guide_message", "Antidote는 근로계약 전문 분석 서비스입니다."), 
                "results": []
            }

        # API 서버 보호를 위한 미세 대기
        await asyncio.sleep(0.5)
        
        # --- [STEP 3] 항목별 루프 (데이터 수집 및 정밀 판별) ---
        for item in parsed_items:
            original_text = item.get('text', '').strip() 
            if not original_text:
                continue 
            
            res_type = item.get('type', 'GENERAL')

            if res_type == "GENERAL":
                # [CASE A] 단순 질문: LLM 배치 호출 없이 즉시 결과 추가
                analysis_results.append({
                    "clause": original_text,
                    "result_type": "GENERAL",
                    "level": "SAFE",
                    "score": 0.0,
                    "reason": "일반 법률 문의 답변",
                    "proposed_text": item.get("answer", "답변을 생성하지 못했습니다."), 
                    "tags": ["#일반문의"],
                    "legal_basis": [],
                    "precedents": []
                })
            else:
                
                # [추가] [Progress Step 2] 독소 여부 판별
                if progress_callback:
                    await progress_callback(step=2, message="해당 조항에 대한 독소 여부 판별 중입니다.", progress=40)
                    print(f"\n[{current_time}] [STEP 2] 🔍 독소조항 분석: KoELECTRA 위험도 분석 중...")
                
                # [CASE B] ANALYSIS: 정밀 분석을 위한 재료 수집
                # 3-1. KoELECTRA 위험 탐지 (점수 측정)
                inputs = self.small_tokenizer(
                    original_text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=settings.MAX_SEQ_LENGTH, 
                    padding=True
                ).to(self.device)
                
                with torch.no_grad():
                    probs = F.softmax(self.small_model(**inputs).logits, dim=-1)
                    confidence = probs[0][1].item() * 100
                
                print(f"\n>>> [Model Inference]")
                print(f" - Clause Snippet: {original_text[:100]}...")
                print(f" \n- Danger Confidence: {confidence:.2f}%") # 소수점 2자리까지 출력
                
                all_scores.append(confidence)
                
                # [추가] [Progress Step 3] 벡터 검색
                if confidence >= 20 and progress_callback:
                    await progress_callback(step=3, message="관련 법령 및 실제 판례 검색중입니다.", progress=60)
                    print(f"\n[{current_time}] [STEP 3] 📚 벡터 검색: 관련 법령 및 판례(DB) 검색중...")
                    
                # 3-2. 정밀 리랭킹 (RAG)
                refined_law = None
                refined_pre = None
                pre_top_score = 0.0 # 판례 점수만 별도 저장
                # 위험도가 어느 정도 있을 때만 RAG 수행
                if confidence >= 20:
                    reverse = item.get('reverse', '').strip()
                    search_query = reverse if reverse else original_text
                    raw_laws, raw_pres = self.db_search.get_related_data(search_query, 10)
                    
                    # [추가] [Progress Step 4] 정밀 검증
                    if progress_callback:
                        await progress_callback(step=4, message="관련 법령 및 판례 정밀 검증 중입니다.", progress=80)
                        print(f"\n[{current_time}] [STEP 4] ⚖️  법령/판례 Re-ranker: Cross-Encoder 기반 데이터 정밀 검증")
                    
                    # print(f"\n[Vector DB Search Results for chunk: {original_text[:30]}...]")
                    # print(f" - Retrieved Laws ({len(raw_laws)}): {[l.keyword for l in raw_laws]}")
                    # print(f" - Retrieved Precedents ({len(raw_pres)}): {[p.case_number for p in raw_pres]}")
                    # print("-" * 30)
               
                    # --- 법령 리랭킹 ---
                    if raw_laws:
                        law_scores = []
                        seen_laws = set()
                        print(f"▶ 법령 검색 결과 상세 (임베딩 거리 & 리랭킹 점수):")
                        for law in raw_laws:
                            if law.keyword in seen_laws: continue
                            l_inputs = self.base_tokenizer(original_text, law.summary, return_tensors="pt", truncation=True, max_length=settings.MAX_SEQ_LENGTH, padding=True).to(self.device)
                            with torch.no_grad():
                                l_probs = F.softmax(self.base_model(**l_inputs).logits, dim=-1)
                                re_score = l_probs[0][1].item() * 100 # 백분율 변환
                                law_scores.append((l_probs[0][1].item(), law))
                                
                                # 임베딩 거리(Vector Distance) 가져오기
                                vector_dist = getattr(law, 'distance', 'N/A')
                                # 두 가지 점수를 한 줄에 출력
                                print(f"   - {law.keyword:<15} | 1차(임베딩 거리): {vector_dist} | 2차(정밀 점수): {re_score:.2f}%")

                            seen_laws.add(law.keyword)
                        law_scores.sort(key=lambda x: x[0], reverse=True)
                        refined_law = law_scores[0][1] if law_scores else None

                    # --- 판례 리랭킹 ---
                    if raw_pres:
                        pre_scores = []
                        seen_pre = set()
                        print(f"\n▶ 판례 검색 결과 상세 (임베딩 거리 & 리랭킹 점수):")
                        for pre in raw_pres:
                            if pre.case_number in seen_pre: continue
                            p_inputs = self.base_tokenizer(original_text, pre.content, return_tensors="pt", truncation=True, max_length=settings.MAX_SEQ_LENGTH, padding=True).to(self.device)
                            with torch.no_grad():
                                p_probs = F.softmax(self.base_model(**p_inputs).logits, dim=-1)
                                score = p_probs[0][1].item() * 100 # 백분율
                                pre_scores.append((score, pre))

                                # 임베딩 거리(Vector Distance) 가져오기
                                vector_dist = getattr(pre, 'distance', 'N/A')
                                # 두 가지 점수를 한 줄에 출력
                                print(f"   - {pre.case_number:<15} | 1차(임베딩 거리): {vector_dist} | 2차(정밀 점수): {score:.2f}%")

                            seen_pre.add(pre.case_number)
                        pre_scores.sort(key=lambda x: x[0], reverse=True)
                        if pre_scores:
                            pre_top_score, refined_pre = pre_scores[0]
                print(f"\n{'-'*60}")            
                # 3-3. 배치를 위해 조항 재료 수집 (리포트 생성을 위한 모든 정보 통합)
                batch_input_data.append({
                    "clause": original_text,
                    "confidence": confidence,
                    "law": refined_law,
                    "precedent": refined_pre,
                    "pre_score": pre_top_score,
                    "missing_summary": missing_summary # 파일 모드일 때만 데이터가 존재함
                })

        missing_clause_report = None  # 누락 사항 리포트를 담을 변수 초기화
        
        # [추가] [Progress Step 5] 최종 리포트 생성
        if progress_callback:
            await progress_callback(step=5, message="최종 리포트 생성 중입니다.", progress=95)
            print(f"[{current_time}] [STEP 5] 📋 최종 리포트 생성: 독소조항 분석 결과 및 LLM 대안 솔루션 작성중...")
        
        # --- [STEP 4] [수정] 수집된 ANALYSIS 조항들에 대해 단 한 번의 LLM 배치 호출 ---
        if batch_input_data:
            # 4-1. 배치 리포트 생성 (이제 응답은 {"analyses": [], "missing_clause_report": ""} 형태)
            batch_result = await self._generate_batch_legal_report(batch_input_data)
            
            # LLM 응답에서 데이터 분리
            batch_reports = batch_result.get("analyses", [])
            missing_clause_report = batch_result.get("missing_clause_report")
            
            # 4-2. 배치 결과를 최종 리스트에 매칭하여 결합
            for i, report in enumerate(batch_reports):
                if i >= len(batch_input_data): break
                
                source = batch_input_data[i]
                conf = source['confidence']
                
                level = "EXTREME" if conf >= 80 else "DANGER" if conf >= 60 else \
                        "WARNING" if conf >= 40 else "CAUTION" if conf >= 20 else "SAFE"
                
                analysis_results.append({
                    "clause": source['clause'],
                    "result_type": "ANALYSIS",
                    "level": level,
                    "score": round(conf, 2),
                    "reason": report.get("reason", "조항 분석 완료"),
                    "proposed_text": report.get("proposed_text", ""),
                    "tags": ["#부당계약", "#검토필요"] if level != "SAFE" else ["#안전조항"],
                    "legal_basis": report.get("legal_basis", []),
                    "precedents": report.get("precedents", [])
                })

        # --- [추가] 분석 결과가 아예 없는 경우 (파일 모드 한정 SAFE 메시지) ---
        if not analysis_results and mode == "file":
            analysis_results.append({
                "clause": "계약서 전체 검토 결과",
                "result_type": "ANALYSIS",
                "level": "SAFE",
                "score": 0.0,
                "reason": "Antidote 분석 결과, 해당 문서에서 근로자에게 불리하게 작용할 수 있는 독소 조항이 발견되지 않았습니다.",
                "proposed_text": "다만, 우측에 누락 항목이나 명시되지 않은 구체적인 특약 사항 등은 서명 전 실무자나 전문가를 통해 다시 한번 확인하시기 바랍니다.",
                "tags": ["#안전한계약서", "#검토완료"],
                "legal_basis": [],
                "precedents": [],
            })
            if missing_summary:
                missing_clause_report = missing_summary
        
        total_risk_score=round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
        if db and google_id:
            await HistoryService.save_analysis_result(
                db=db,
                google_id=google_id,
                doc_name=doc_name,
                mode=mode,
                report_data=analysis_results,
                missing_clause_report= missing_clause_report,
                total_risk_score=total_risk_score
            )
        # --- [STEP 5] 최종 결과 반환 ---
        return {
            "status": "success",
            "doc_name": doc_name,
            "results": analysis_results,            
            "missing_clause_report": missing_clause_report, 
            "total_risk_score": total_risk_score,
            "analyzed_at": now
        }