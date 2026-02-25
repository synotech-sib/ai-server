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
# [1] 시노봇 시스템 지침 (Persona)
# =====================================================================
SYSTEM_PROMPT = """
You are 'SynoBot', an elite SIB R&D engineer for SynoCore.
- 당신은 구글 드라이브의 Tdb(Technical Database) 자료를 실시간으로 참조하여 답변합니다.
- 알트리스(Altris) 관련 기술 지표(ICE, Cathode 등)는 반드시 제공된 문서 내 수치를 근거로 답하십시오.
- 답변 끝에는 항상 참고한 파일명을 [출처: 파일명] 형태로 적어주십시오.
"""

# =====================================================================
# [2] 구글 드라이브 실시간 '천리안' 스캔 함수
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

    # 모든 하위 폴더의 파일을 찾기 위한 쿼리
    def fetch_files_recursive(folder_id):
        all_text = ""
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])

        for item in items:
            # 1. 하위 폴더일 경우 (재귀적으로 다시 탐색)
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                all_text += fetch_files_recursive(item['id'])
            
            # 2. 파일일 경우 (TXT 또는 PDF만 읽기)
            elif item['mimeType'] in ['text/plain', 'application/pdf']:
                file_id = item['id']
                file_name = item['name']
                
                try:
                    request = service.files().get_media(fileId=file_id)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                    fh.seek(0)

                    if item['mimeType'] == 'text/plain':
                        content = fh.read().decode('utf-8', errors='ignore')
                        all_text += f"\n\n--- [출처: {file_name}] ---\n{content}"
                    elif item['mimeType'] == 'application/pdf' and PdfReader:
                        reader = PdfReader(fh)
                        pdf_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                        all_text += f"\n\n--- [출처: {file_name}] ---\n{pdf_text}"
                except:
                    pass
        return all_text

    context = fetch_files_recursive(FOLDER_ID)
    return context if context else "Tdb 폴더 내에 유효한 기술 자료가 없습니다."

# =====================================================================
# [3] AI 엔진 응답 함수 (Gemini / OpenAI)
# =====================================================================
def get_gemini_response_stream(messages, sim_result, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
    
    retrieved_context = load_tdb_documents()
    last_user_msg = messages[-1]["content"]
    
    full_prompt = f"### [Google Drive Tdb Context]\n{retrieved_context}\n\n"
    if sim_result: full_prompt += f"### [Simulation State]\n{sim_result}\n\n"
    full_prompt += f"### User Question: {last_user_msg}"
    
    response = model.generate_content(full_prompt, stream=True)
    for chunk in response:
        if chunk.text: yield chunk.text

def get_openai_response_stream(messages, sim_result, api_key):
    client = OpenAI(api_key=api_key)
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n### [Context]\n{retrieved_context}"
    if sim_result: sys_content += f"\n\n### [Sim State]\n{sim_result}"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": sys_content}] + [m for m in messages if m["role"] != "system"],
        temperature=0.3, stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content

def generate_auto_briefing(sim_result, engine_choice, openai_key, gemini_key):
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n[Context]\n{retrieved_context}\n\n[Sim State]\n{sim_result}"
    user_prompt = "분석 브리핑을 3~4줄로 작성하십시오."
    if "Gemini" in engine_choice:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=sys_content)
        return model.generate_content(user_prompt).text
    else:
        client = OpenAI(api_key=openai_key)
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":sys_content},{"role":"user","content":user_prompt}], temperature=0.3)
        return res.choices[0].message.content