import re
from typing import List, Dict

class TextProcessor:
    def __init__(self):
        # 기존 조항 패턴 유지
        self.struct_pattern = r'(제\s*\d+\s*조(?:\s*\(.*?\))?|①|②|③|④|⑤|\d+\.)'
        # 질문 분리를 위한 패턴 (물음표 또는 줄바꿈 기준)
        self.question_pattern = r'(?<=[?])|(?<=\n)'

    def clean_for_embedding(self, text: str) -> str:
        clean_text = re.sub(self.struct_pattern, '', text)
        clean_text = re.sub(r'[^\w\s.가-힣]', ' ', clean_text)
        return " ".join(clean_text.split()).strip()

    def smart_chunking(self, text: str) -> List[Dict[str, str]]:
        # 1. 연속된 공백 제거 및 줄바꿈 정제
        processed_text = re.sub(r' +', ' ', text).strip()
        combined_chunks = []
        
        matches = list(re.finditer(self.struct_pattern, processed_text))
        
        if matches:
            # --- [Case 1] 조항 형식이 있는 계약서 형태 ---
            for i in range(len(matches)):
                start_pos = matches[i].start()
                end_pos = matches[i+1].start() if i + 1 < len(matches) else len(processed_text)
                full_clause = processed_text[start_pos:end_pos].strip()
                if len(full_clause) > 5:
                    combined_chunks.append(full_clause)
        else:
            # --- [Case 2] 조항 형식이 없는 일반 질문 형태 ---
            # 줄바꿈(\n)으로 먼저 나눕니다. 사용자가 엔터로 구분했을 가능성이 높기 때문입니다.
            lines = processed_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # 각 라인 내부에서 '?' 또는 '. ' 또는 '!'를 기준으로 2차 분리합니다.
                # (긍정 후방 탐색을 사용하여 구분 기호를 유지하며 자릅니다)
                sub_sentences = re.split(r'(?<=[?.!])', line)
                
                for s in sub_sentences:
                    clean_s = s.strip()
                    if len(clean_s) > 2:
                        # 마침표나 물음표가 아예 없는 평서문형 질문일 경우 마침표 강제 추가 (LLM 인식용)
                        if not clean_s.endswith(('?', '.', '!')):
                            clean_s += "."
                        combined_chunks.append(clean_s)

        return [{"original": c, "for_embedding": self.clean_for_embedding(c)} for c in combined_chunks]

    def clean_pdf_text(self, text_input) -> str:
        if isinstance(text_input, list):
            text = "\n".join(map(str, text_input))
        else:
            text = str(text_input)

        text = re.sub(r'([^\n])\s*(\d+\.)(?=\s|$)', r'\1\n\2', text)
        text = re.sub(r'([^\n])\s*(제\s*\d+\s*조)', r'\1\n\2', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()