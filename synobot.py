# synobot.py

import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# RAG 전용 라이브러리 임포트
try:
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

import streamlit as st

# =====================================================================
# [AI 시스템 프롬프트]
# =====================================================================
SYSTEM_PROMPT = """
You are 'SynoBot', an expert SIB R&D engineer powered by OpenAI.
Answer questions accurately and professionally in Korean based on SIB knowledge.
- 반드시 SIB 수석 연구원(엔지니어)의 전문적인 브리핑 스타일로 작성하되, 사무적이고 정중한 '합쇼체(~입니다, ~합니다)'로 답변하십시오.
- 모든 답변은 도트 블릿('- ')을 사용하여 핵심을 명확히 나열하십시오.
- "아래는 분석 내용입니다" 같은 불필요한 서론은 쓰지 마십시오.
- 유저의 질문에 대해 [Retrieved Context] (검색된 문서)가 제공될 경우, 반드시 그 문서의 사실을 기반으로 답변하고 출처(문서명)를 언급하십시오.
"""

# =====================================================================
# [내장 학습 데이터: 알트리스 양산 기술]
# =====================================================================
ALTRIS_TEXT = """
# 코인셀 및 용량 계산 (Coin-cell & capacity calculations)
- 나트륨 금속을 이용한 하프셀은 디글라임(diglyme) 용액 내 1M NaPF6 전해질과 폴리올레핀 분리막 사용 권장.
- 하프셀 테스트는 "무한한 나트륨" 환경에서 용량을 결정하는 데 주로 유용하며, 나트륨 금속 대비 전압을 제공함.
- 나트륨 대비 0V는 나트륨 도금(plating)이 시작되는 지점임.
- 이 테스트에는 단면 코팅 전극을 사용함.
- [해석]: 하프셀 평가를 위한 표준 실험 환경 조성과 나트륨 석출(Plating) 방지를 위한 전압 기준 설정 지침임.

# 전극 준비 (Electrode preparation)
- 전극은 수령 상태 그대로 사용 가능하며, 양면 시트를 단면으로 전환 시 건조 전 물과 티슈로 닦아낼 수 있음.
- 셀 조립 전 전극의 철저한 건조가 매우 중요함.
- 건조 조건: 1 mBar 미만 진공, 온도 170°C~200°C.
- 건조 시간: 최소 12시간, 가급적 24시간 권장.
- 단면 전극은 건조 중 고정하지 않으면 말릴 수 있음 (Curling 현상).
- 양극은 건조 환경을 벗어나면 습기를 매우 빠르게 재흡수하므로 주의 요망.
- [해석]: 고성능 나트륨 배터리 제작을 위한 필수적인 고온 진공 건조 조건 및 수분 관리 주의사항임.

# 양극 하프셀 예시 - 건조 상태 비교
- 건조된 양극(Dry)과 건조되지 않은 양극(Wet)의 예시.
- 4.2V까지 충전 시 수분 추출(Water extraction) 여부 확인 가능.
- 왼쪽 사진(Wet)은 수분 추출이 명확히 보이나 오른쪽(Dry)은 건조된 상태임.
- 양극 하프셀은 후속 테스트 전 건조 설비를 검증하기에 매우 적합함.

# 양극 하프셀 코인셀 예시
- 전해질: 디글라임 내 1M NaPF6, double PP 분리막.
- 전극 로딩 레벨: 12.79 +/- 0.29 mg/cm2.
- 사용된 전해질 양: 70 uL.
# [핵심 성능 지표: KPI]
- 초기 쿨롱 효율(ICE): 90% ~ 95% 이상 달성 (표준 가이드 준수 시)
- 이론적 비용량: 약 160 mAh/g
- 작동 전압 범위: 2.0V ~ 4.2V (vs. Na/Na+)
- [중요] 만약 ICE가 90% 미만(예: 80%대)으로 측정될 경우, 이는 소재 결함이 아니라 전극 내 '잔류 수분'과 전해질의 부반응에 의한 비가역 용량 손실로 간주함. 

# [전문가 분석 가이드]
- 유저가 ICE에 대해 물으면, 반드시 '90~95%'를 목표로 삼아야 함을 강조하십시오.
- 80%대의 낮은 효율은 '건조 공정 불량'의 신호임을 경고하십시오.
"""

def get_openai_client(api_key):
    if OpenAI is None: raise ImportError("openai library is not installed.")
    return OpenAI(api_key=api_key)

# 웹 서버용 메모리 기반 DB 생성 (앱 켤 때 1번만 자동 학습)
@st.cache_resource(show_spinner="시노봇이 알트리스 문서를 학습 중입니다...")
def load_and_train_db(api_key):
    if not RAG_AVAILABLE: return None
    try:
        embeddings = OpenAIEmbeddings(api_key=api_key)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_text(ALTRIS_TEXT)
        docs = [Document(page_content=c, metadata={"source": "Altris_Technical_Note_2026"}) for c in chunks]
        
        # 임시 메모리에 DB 구축 (웹에 아주 빠르고 적합함)
        db = Chroma.from_documents(docs, embeddings)
        return db
    except Exception as e:
        print(f"DB 학습 에러: {e}")
        return None

def generate_auto_briefing(sim_result, api_key):
    client = get_openai_client(api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\n[Current Simulation State]\n{sim_result}\n\n[Basic Knowledge]\n{ALTRIS_TEXT}"},
        {"role": "user", "content": "입력된 시뮬레이션 데이터를 분석하여 핵심 엔지니어링 브리핑을 3~4줄로 명확히 작성해 주십시오. (서론 생략)"}
    ]
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.3)
    return response.choices[0].message.content

def generate_chat_reply(chat_history, sim_result, api_key):
    client = get_openai_client(api_key)
    
    last_user_msg = ""
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    retrieved_context = ALTRIS_TEXT
    if RAG_AVAILABLE and last_user_msg:
        try:
            db = load_and_train_db(api_key)
            if db:
                docs = db.similarity_search(last_user_msg, k=3)
                if docs:
                    retrieved_context = "\n\n".join([f"[{d.metadata.get('source', '')}] {d.page_content}" for d in docs])
        except Exception: pass

    final_system_prompt = SYSTEM_PROMPT + f"\n\n[Retrieved Context (참고 문서)]\n{retrieved_context}"
    if sim_result: final_system_prompt += f"\n\n[Current Simulation State]\n{sim_result}"

    messages = [{"role": "system", "content": final_system_prompt}]
    for msg in chat_history: messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.5)
    return response.choices[0].message.content