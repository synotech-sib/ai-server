import os
import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# PDF 해석 부품
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
# [1] 시노봇 시스템 지침 (Persona) - 출처 표기 로직 적용
# =====================================================================
SYSTEM_PROMPT = """
You are 'SynoBot', an elite SIB R&D engineer for SynoCore.
- 당신은 구글 드라이브의 Tdb(Technical Database) 자료를 실시간으로 참조하여 답변합니다.
- 알트리스(Altris) 관련 기술 지표(ICE, Cathode 등)는 반드시 제공된 문서 내 수치를 근거로 답하십시오.
- 실제 참고한 파일의 원본 이름은 사용자에게 절대 노출하지 마십시오.
- 답변의 맨 마지막 줄에는 반드시 아래 문구를 정확히 그대로 추가하십시오:
  "[출처] 시노봇 AI가 학습한 내부 자료임."
"""

# =====================================================================
# [2] 구글 드라이브 실시간 하위 폴더 스캔 함수 (스캔본 PDF 대응)
# =====================================================================
def load_tdb_documents():
    """Secrets의 폴더 ID 하위에 있는 모든 PDF/TXT 파일을 재귀적으로 읽어옵니다."""
    context = ""
    
    try:
        FOLDER_ID = st.secrets["GDRIVE_FOLDER_ID"]
        creds_info = st.secrets["gdrive_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        return f"⚠️ Secrets 설정 오류: {e}"

    def recursive_fetch(folder_id):
        inner_context = ""
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # 하위 폴더면 다시 파고들기
                inner_context += recursive_fetch(item['id'])
            elif item['mimeType'] in ['text/plain', 'application/pdf']:
                try:
                    request = service.files().get_media(fileId=item['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                    fh.seek(0)

                    if item['mimeType'] == 'text/plain':
                        content = fh.read().decode('utf-8', errors='ignore')
                        inner_context += f"\n\n--- [참조 데이터] ---\n{content}"
                        
                    elif item['mimeType'] == 'application/pdf' and PdfReader:
                        reader = PdfReader(fh)
                        pdf_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                        
                        # [핵심] 스캔본(이미지) PDF 대응 로직
                        if not pdf_text.strip():
                            inner_context += f"\n\n--- [참조 데이터] ---\n[내부 경고: 이 파일({item['name']})은 스캔본이므로 텍스트 인식이 불가능합니다.]"
                        else:
                            inner_context += f"\n\n--- [참조 데이터] ---\n{pdf_text}"
                except Exception as e:
                    pass # 파일 읽기 실패 시 조용히 넘어감
        return inner_context

    context = recursive_fetch(FOLDER_ID)
    return context if context else "Tdb 폴더 내에 유효한 기술 자료가 없습니다."

# =====================================================================
# [3] AI 엔진 응답 함수 (Gemini / OpenAI)
# =====================================================================
def get_gemini_response_stream(messages, sim_result, api_key):
    if genai is None:
        yield "⚠️ google-generativeai 라이브러리가 필요합니다."
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
    
    retrieved_context = load_tdb_documents()
    last_user_msg = messages[-1]["content"]
    
    full_prompt = f"### [Google Drive Tdb Context]\n{retrieved_context}\n\n"
    if sim_result: full_prompt += f"### [Simulation State]\n{sim_result}\n\n"
    full_prompt += f"### User Question: {last_user_msg}"
    
    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"\n⚠️ Gemini 엔진 오류: {e}"

def get_openai_response_stream(messages, sim_result, api_key):
    if OpenAI is None:
        yield "⚠️ openai 라이브러리가 필요합니다."
        return
        
    client = OpenAI(api_key=api_key)
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n### [Context]\n{retrieved_context}"
    if sim_result: sys_content += f"\n\n### [Sim State]\n{sim_result}"
    
    full_messages = [{"role": "system", "content": sys_content}] + [m for m in messages if m["role"] != "system"]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            temperature=0.3, stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"\n⚠️ OpenAI 엔진 오류: {e}"

def generate_auto_briefing(sim_result, engine_choice, openai_key, gemini_key):
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n[Context]\n{retrieved_context}\n\n[Sim State]\n{sim_result}"
    user_prompt = "분석 브리핑을 3~4줄로 작성하십시오."
    
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