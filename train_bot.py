# train_bot.py (1회성 학습 스크립트)

import synobot
import os

# 대표님의 OpenAI API 키를 입력하세요.
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 

# 학습시킬 알트리스 슬라이드 노트 (여기에 제미나이가 해석한 내용을 붙여넣으시면 됩니다)
altris_text = """
슬라이드 1: 프러시안 화이트(PW) 양극재는 나트륨 이온 배터리에서 가장 뛰어난 성능을 보입니다.
슬라이드 2: PW 양극재의 가장 큰 특징은 수분 재흡수입니다. 따라서 코팅 후 진공 상태(<1mBar)에서 170도~200도로 12시간 이상 건조하는 것이 절대적으로 중요합니다.
슬라이드 3: N/P Ratio는 1.15를 권장합니다. 하드카본 음극의 고율 방전 시 용량 저하를 고려해야 나트륨 금속 석출을 막을 수 있습니다.
슬라이드 4: 양극 슬러리 레시피는 Fennac(활물질) 93%, C65 3%, CMC 1%, SBR 3%가 표준입니다.
슬라이드 5: 알트리스 배터리의 수명은 C/2 속도로 충방전 시 12,000 사이클 이상을 보장합니다.
(대표님이 가지고 계신 텍스트를 여기에 길게 복사/붙여넣기 하세요)
"""

print("🧠 시노봇 문서 학습을 시작합니다...")
result = synobot.ingest_text_to_db(altris_text, "Altris_JSC_PPT_Note_2026", api_key)
print(result)