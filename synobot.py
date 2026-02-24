# synobot.py

import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# 🔥 RAG 전용 라이브러리 임포트
try:
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain.docstore.document import Document
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# =====================================================================
# [AI 시스템 프롬프트 (Persona & Rules)]
# =====================================================================
SYSTEM_PROMPT = """
You are 'SynoBot', an expert SIB R&D engineer powered by OpenAI.
Answer questions accurately and professionally in Korean based on SIB knowledge.
- 반드시 SIB 수석 연구원(엔지니어)의 전문적인 브리핑 스타일로 작성하되, 사무적이고 정중한 '합쇼체(~입니다, ~합니다)'로 답변하십시오.
- 모든 답변은 도트 블릿('- ')을 사용하여 핵심을 명확히 나열하십시오.
- "아래는 분석 내용입니다", "다음은 데이터에 대한 브리핑입니다" 등과 같은 불필요한 서론이나 인사말은 절대 쓰지 말고, 곧바로 핵심 데이터 분석 본론부터 출력하십시오.
- 유저의 질문에 대해 [Retrieved Context] (검색된 문서)가 제공될 경우, 반드시 그 문서의 사실을 기반으로 답변하고 출처를 언급하십시오. (예: "Altris 기술 자료에 따르면...")
"""

# DB가 비어있거나 검색이 안 될 때를 대비한 기본 지식(Fallback)
DEFAULT_KB = """
[Altris SIB 양산 설계 핵심 노하우 요약]
1. 건조: PW 양극재는 진공(<1mBar) 170~200°C에서 12~24시간 건조 필수.
2. N/P Ratio: 석출 방지를 위해 1.15 이상 보수적 설계.
3. 양극 레시피: Fennac 93 : C65 3 : CMC 1 : SBR 3
4. 전해액: 하프셀은 1M NaPF6 in Diglyme, 양산 풀셀은 카보네이트계(EC/PC/EMC/DEC) + VC/DTD.
"""

def get_openai_client(api_key):
    if OpenAI is None:
        raise ImportError("openai library is not installed.")
    return OpenAI(api_key=api_key)

def get_chroma_db(api_key):
    """로컬 벡터 데이터베이스(ChromaDB)를 연결하거나 생성합니다."""
    if not RAG_AVAILABLE:
        return None
    embeddings = OpenAIEmbeddings(api_key=api_key)
    # 현재 폴더 안에 'syno_vectordb'라는 이름으로 DB 폴더가 자동 생성됩니다.
    db = Chroma(persist_directory="./syno_vectordb", embedding_function=embeddings)
    return db

def generate_auto_briefing(sim_result, api_key):
    """시뮬레이션 직후 자동 생성되는 진단 리포트 (RAG 검색 생략, 빠른 속도)"""
    client = get_openai_client(api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\n[Current Simulation State]\n{sim_result}\n\n[Basic Knowledge]\n{DEFAULT_KB}"},
        {"role": "user", "content": "입력된 시뮬레이션 데이터를 분석하여 핵심 엔지니어링 브리핑을 3~4줄로 명확히 작성해 주십시오. (서론 생략)"}
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
    )
    return response.choices[0].message.content

def generate_chat_reply(chat_history, sim_result, api_key):
    """유저와의 대화 시 Vector DB를 검색(RAG)하여 답변하는 로직"""
    client = get_openai_client(api_key)
    
    # 1. 유저의 마지막 질문 추출
    last_user_msg = ""
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    # 2. Vector DB 검색 (RAG 수행)
    retrieved_context = DEFAULT_KB
    if RAG_AVAILABLE and last_user_msg:
        try:
            db = get_chroma_db(api_key)
            # 유저 질문과 가장 유사한 문서 3개를 찾아옵니다.
            docs = db.similarity_search(last_user_msg, k=3)
            if docs:
                retrieved_context = "\n\n".join([f"[{d.metadata.get('source', '사내기술문서')}] {d.page_content}" for d in docs])
        except Exception as e:
            print(f"Vector DB Search Error: {e}") # DB가 비어있을 경우 Fallback 지식 사용

    # 3. 프롬프트 조합 (시스템 룰 + 시뮬레이션 결과 + 검색된 문서 지식)
    final_system_prompt = SYSTEM_PROMPT + f"\n\n[Retrieved Context (참고 문서)]\n{retrieved_context}"
    if sim_result:
        final_system_prompt += f"\n\n[Current Simulation State]\n{sim_result}"

    messages = [{"role": "system", "content": final_system_prompt}]
    
    # 4. 누적 대화 기록 주입
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content

# =====================================================================
# 🛠️ 관리자 전용: 문서 학습(업로드) 유틸리티 함수
# =====================================================================
def ingest_text_to_db(text_content, source_name, api_key):
    """
    이 함수를 호출하면 텍스트를 쪼개어 Vector DB에 영구 저장(학습)합니다.
    """
    if not RAG_AVAILABLE:
        return "라이브러리(langchain, chromadb)가 설치되어 있지 않습니다."
    
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    try:
        # 긴 문서를 의미 단위로 쪼갬 (청킹)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_text(text_content)
        
        # Document 객체로 변환
        docs = [Document(page_content=chunk, metadata={"source": source_name}) for chunk in chunks]
        
        # DB에 저장
        db = get_chroma_db(api_key)
        db.add_documents(docs)
        db.persist() # 로컬 폴더에 영구 저장
        return f"✅ 성공: '{source_name}' 문서({len(chunks)}개 조각)가 시노봇의 뇌에 저장되었습니다."
    except Exception as e:
        return f"❌ 실패: {str(e)}"