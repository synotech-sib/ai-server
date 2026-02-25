import os
import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# PDF 및 AI 엔진 라이브러리
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# =====================================================================
# [1] 시노봇 페르소나 및 시스템 지침
# =====================================================================
SYSTEM_PROMPT = """
You are 'SynoBot', an elite SIB R&D engineer and global technical advisor for SynoCore.
- 당신은 시노코어 구글 드라이브 Tdb(Technical Database)의 최신 기술 자료를 바탕으로 답변하는 전문가입니다.
- 질문자가 사용하는 언어(한국어, 영어 등)에 맞춰 유연하게 대답하십시오.
- 한국어 답변 시, 알트리스(Altris) 관련 기술 용어(예: ICE, Cathode, Prussian White)는 영어 원문을 병기하십시오.
- 불필요한 서론은 생략하고, 도트 블릿('- ')을 사용하여 핵심을 명확히 나열하십시오.
- 답변 시 참고한 파일의 이름을 [출처: 파일명] 형태로 반드시 명시하십시오.
"""

# =====================================================================
# [2] 구글 드라이브 실시간 연동 함수
# =====================================================================
def load_tdb_documents():
    """Secrets에 저장된 폴더 ID와 서비스 계정 키를 사용하여 드라이브 파일을 읽어옵니다."""
    context = ""
    
    # 1. Secrets에서 설정값 로드
    try:
        # 폴더 ID 가져오기
        FOLDER_ID = st.secrets["GDRIVE_FOLDER_ID"]
        # 서비스 계정 인증 정보 가져오기
        creds_info = st.secrets["gdrive_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        return f"⚠️ Secrets 설정 오류 (GDRIVE_FOLDER_ID 또는 인증키 확인 필요): {e}"

    try:
        # 2. 폴더 내 파일 목록 조회 (TXT 및 PDF만 대상)
        query = f"'{FOLDER_ID}' in parents and (mimeType = 'text/plain' or mimeType = 'application/pdf') and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])

        if not items:
            return "구글 드라이브 Tdb 폴더에 읽을 수 있는 문서가 없습니다."

        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']

            # 3. 파일 실시간 다운로드 (메모리 내 처리)
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.seek(0)

            # 4. 내용 추출
            if mime_type == 'text/plain':
                text = fh.read().decode('utf-8', errors='ignore')
                context += f"\n\n--- [출처: {file_name}] ---\n{text}"
            
            elif mime_type == 'application/pdf' and PdfReader:
                reader = PdfReader(fh)
                pdf_text = ""
                for page in reader.pages:
                    t = page.extract_text()
                    if t: pdf_text += t + "\n"
                if pdf_text.strip():
                    context += f"\n\n--- [출처: {file_name}] ---\n{pdf_text}"

        return context if context else "읽어올 수 있는 텍스트 데이터가 없습니다."

    except Exception as e:
        return f"❌ 구글 드라이브 연동 중 오류 발생: {str(e)}"

# =====================================================================
# [3] AI 엔진 1: 제미나이 (Gemini 2.5 Flash) 스트리밍
# =====================================================================
def get_gemini_response_stream(messages, sim_result, api_key):
    if genai is None:
        yield "⚠️ google-generativeai 라이브러리 필요"
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=SYSTEM_PROMPT
    )
    
    # 이전 대화 히스토리 구성
    history = []
    for msg in messages[:-1]:
        if msg["role"] == "system": continue 
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
        
    chat = model.start_chat(history=history)
    
    # 실시간 지식 창고 데이터 로드
    retrieved_context = load_tdb_documents()
    last_user_msg = messages[-1]["content"]
    
    full_prompt = f"### [Google Drive Tdb Context]\n{retrieved_context}\n\n"
    if sim_result:
        full_prompt += f"### [Simulation State]\n{sim_result}\n\n"
    full_prompt += f"### User Question: {last_user_msg}"
    
    try:
        response = chat.send_message(full_prompt, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"\n⚠️ Gemini 엔진 오류: {e}"

# =====================================================================
# [4] AI 엔진 2: OpenAI (GPT-4o-mini) 스트리밍
# =====================================================================
def get_openai_response_stream(messages, sim_result, api_key):
    if OpenAI is None:
        yield "⚠️ openai 라이브러리 필요"
        return
        
    client = OpenAI(api_key=api_key)
    retrieved_context = load_tdb_documents()
    
    sys_content = SYSTEM_PROMPT + f"\n\n### [Google Drive Tdb Context]\n{retrieved_context}"
    if sim_result:
        sys_content += f"\n\n### [Simulation State]\n{sim_result}"
        
    full_messages = [{"role": "system", "content": sys_content}]
    full_messages += [m for m in messages if m["role"] != "system"]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=full_messages,
            temperature=0.3,
            stream=True
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content: yield content
    except Exception as e:
        yield f"\n⚠️ OpenAI 엔진 오류: {e}"

# =====================================================================
# [5] 자동 브리핑 생성 함수
# =====================================================================
def generate_auto_briefing(sim_result, engine_choice, openai_key, gemini_key):
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n[Tdb Context]\n{retrieved_context}\n\n[Simulation State]\n{sim_result}"
    user_prompt = "이 시뮬레이션 데이터를 분석하여 핵심 엔지니어링 브리핑을 3~4줄로 작성하십시오."
    
    try:
        if "Gemini" in engine_choice:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=sys_content)
            return model.generate_content(user_prompt).text
        else:
            client = OpenAI(api_key=openai_key)
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":sys_content},{"role":"user","content":user_prompt}], temperature=0.3)
            return res.choices[0].message.content
    except Exception as e:
        return f"자동 브리핑 생성 오류: {e}"