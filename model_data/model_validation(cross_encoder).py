# pip install pandas numpy torch transformers datasets evaluate scikit-learn seaborn matplotlib accelerate

import os
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)
from datasets import Dataset
import evaluate
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 윈도우용 맑은 고딕 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'

# 마이너스 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False

# 모델 폴더 경로를 지정.
MODEL_PATH = r"D:/PJ/Advanced_PJ/Antidote/model_data/model/cross_encoder_model_v8"
# 검증 데이터셋 파일 경로를 지정.
# VAL_DATA_PATH = r"D:/PJ/Advanced_PJ/Law_Data/dataset/Validation_Set(label)/Validation(cross_encoder)2.csv"
# 전체 학습 데이터 오탐 진행시
VAL_DATA_PATH = r"D:/PJ/Advanced_PJ/Antidote/model_data/Law_Data/dataset/Training_Set(label)/학습데이터(8차)/cross_encoder_data_increase_8.csv"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ 검증 장치: {device}")

# 모델 및 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    attn_implementation="eager"
).to(device)

# 검증 데이터셋 로드 및 전처리
def load_val_data(file_path):
    # 환경의 인코딩에 맞춰 로드
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        
    df = df.dropna(subset=['clause_text', 'Judgment', 'label'])
    
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    return Dataset.from_pandas(df)

def tokenize_function(examples):
    return tokenizer(
        examples['clause_text'],
        examples['Judgment'],
        truncation=True,
        max_length=512,
        padding=False
    )

val_raw_dataset = load_val_data(VAL_DATA_PATH)
tokenized_val = val_raw_dataset.map(tokenize_function, batched=True)

# 평가 지표 및 Trainer 설정
metric = evaluate.combine(["accuracy", "f1", "precision", "recall"])

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return metric.compute(predictions=predictions, references=labels)

# 시각화용 함수 정의
def visualize_attention(clause_text, judgment_text, model, tokenizer, layer_idx=11):
    model.config.output_attentions = True
    inputs = tokenizer(clause_text, judgment_text, return_tensors="pt", truncation=True, max_length=128).to(device)
    
    with torch.no_grad(): # 메모리 절약을 위해 gradient 계산 비활성화
        outputs = model(**inputs)
        
    attentions = outputs.attentions
    # 11번 레이어의 헤드별 평균 어텐션 추출
    target_attention = attentions[layer_idx][0].detach().cpu().numpy()
    avg_attention = np.mean(target_attention, axis=0)
    
    tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(avg_attention, xticklabels=tokens, yticklabels=tokens, cmap='viridis')
    plt.title(f'Attention Map - Layer {layer_idx+1}')
    plt.xticks(rotation=45)
    plt.show()

test_args = TrainingArguments(
    output_dir="./test_results",
    per_device_eval_batch_size=8,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=test_args,
    eval_dataset=tokenized_val,
    processing_class=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
    compute_metrics=compute_metrics,
)

# 검증 실행 및 결과 출력
print("\n🚀 정밀 검증(Inference)을 시작합니다...")
predictions_output = trainer.predict(tokenized_val)

# 로짓(Logits)을 확률(Softmax)로 변환
logits = torch.tensor(predictions_output.predictions)
probs = F.softmax(logits, dim=-1).numpy() # [[부적합확률, 적합확률], ...]

pred_labels = np.argmax(predictions_output.predictions, axis=1)
true_labels = predictions_output.label_ids

results = predictions_output.metrics
# --- 결과 리포트 출력 ---
print("\n" + "="*50)
print("📊 [검증 결과 요약]")
print(f"- Accuracy:  {results.get('test_accuracy', results.get('eval_accuracy')):.4f}")
print(f"- F1-Score:  {results.get('test_f1', results.get('eval_f1')):.4f}")
print(f"- Precision: {results.get('test_precision', results.get('eval_precision')):.4f}")
print(f"- Recall:    {results.get('test_recall', results.get('eval_recall')):.4f}")
print("="*50)

print("\n📝 [상세 분류 리포트]")
print(classification_report(true_labels, pred_labels, target_names=['부적합(0)', '적합(1)']))

# 시각화: 혼동 행렬 (Confusion Matrix)
plt.figure(figsize=(8, 6))
cm = confusion_matrix(true_labels, pred_labels)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Pred 0', 'Pred 1'], yticklabels=['True 0', 'True 1'])
plt.title('Confusion Matrix - Legal Precision Review')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()
plt.rcParams['font.size'] = 8


# 오답 데이터 분석(모델이 틀린 조항들만 모아서 확인)
df_val = val_raw_dataset.to_pandas()
df_val['pred'] = pred_labels
df_val['prob_0'] = probs[:, 0]        # 부적합(0)일 확률
df_val['prob_1'] = probs[:, 1]        # 적합(1)일 확률
df_val['confidence'] = np.max(probs, axis=1) # 모델이 선택한 라벨에 대한 확신도

# 틀린 사례만 필터링
incorrect_cases = df_val[df_val['label'] != df_val['pred']]

if not incorrect_cases.empty:
    print(f"\n⚠️ 모델이 틀린 사례 ({len(incorrect_cases)}건) 분석 (확신도 높은 순):")
    # 모델이 아주 확신하며 틀린 것부터 정렬
    display_cols = ['clause_text', 'label', 'pred', 'confidence', 'prob_1']
    print(incorrect_cases[display_cols].sort_values(by='confidence', ascending=False).head(10))
    
    # 가장 확신도가 높은(제일 어이없게 틀린) 1순위 오답을 그래프로 확인
    print("\n🔍 최상위 오답 사례에 대한 어텐션 분석 그래프를 생성합니다...")
    top_error = incorrect_cases.sort_values(by='confidence', ascending=False).iloc[0]
    
    visualize_attention(
        clause_text=top_error['clause_text'],
        judgment_text=top_error['Judgment'],
        model=model,
        tokenizer=tokenizer,
        layer_idx=11
    )
    
    # 오답 리스트를 엑셀로 저장
    incorrect_cases.to_csv("D:/PJ/Advanced_PJ/Antidote/model_data/Law_Data/false_data/error_analysis_8.csv", index=False, encoding="utf-8-sig")