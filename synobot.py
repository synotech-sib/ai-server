import os
import io
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# PDF 해석 부품
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# OCR 추출 부품 (Google Cloud Vision & pdf2image)
try:
    from google.cloud import vision
    from google.api_core.client_options import ClientOptions
    from pdf2image import convert_from_bytes
except ImportError:
    vision = None
    ClientOptions = None
    convert_from_bytes = None

# AI 엔진 부품
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# =====================================================================
# [1] 시노봇 시스템 지침 (관리자 권한에 따른 동적 생성)
# =====================================================================
ADMIN_HELP_SOP = """
[관리자 운영 수칙(SOP)]
1. 파일 명명 규칙: [분류]_[키워드1]_[키워드2]_[연도] (예: MAT_알트리스 양극재_코인셀 평가_2025)
2. OCR 처리: 텍스트 선택이 안 되는 PDF(스캔본)는 시스템이 자동으로 감지하여 'Tdb 스캔 및 OCR 실행' 기능을 통해 AI가 자동 변환함.
"""

def get_system_prompt(is_admin=False):
    base_prompt = """You are 'SynoBot', an elite SIB R&D engineer for SynoCore.
- 당신은 구글 드라이브의 Tdb(Technical Database) 자료를 실시간으로 참조하여 답변합니다.
- 알트리스(Altris) 관련 기술 지표(ICE, Cathode 등)는 반드시 제공된 문서 내 수치를 근거로 답하십시오."""
    
    if is_admin:
        # 관리자 전용: 출처 파일명 나열 + 운영 가이드 숙지
        return base_prompt + f"\n\n{ADMIN_HELP_SOP}\n- 관리자의 질문에는 위의 [운영 수칙]을 바탕으로 답변하십시오.\n- 관리자 답변 시에는 반드시 참조한 [실제 파일명]을 모두 나열하십시오."
    else:
        # 일반 유저: 보안 처리 (고정 문구)
        return base_prompt + "\n- 실제 참고한 파일의 원본 이름은 사용자에게 절대 노출하지 마십시오.\n- 답변의 맨 마지막 줄에는 반드시 아래 문구를 정확히 그대로 추가하십시오:\n  \"[출처] 시노봇 AI가 학습한 내부 자료임.\""


# =====================================================================
# [2] Google Vision API (이미지 PDF 정밀 OCR - API 키 인증)
# =====================================================================
def extract_text_with_vision(pdf_bytes):
    if not vision or not convert_from_bytes:
        return "\n[시스템 알림: Vision API 관련 라이브러리(google-cloud-vision, pdf2image)가 서버에 설치되지 않았습니다.]"
    
    try:
        api_key = st.secrets["GOOGLE_VISION_API_KEY"]
        client_options = ClientOptions(api_key=api_key)
        client = vision.ImageAnnotatorClient(client_options=client_options)
        
        images = convert_from_bytes(pdf_bytes, dpi=200)
        extracted_text = ""
        
        for i, image in enumerate(images):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            content = img_byte_arr.getvalue()

            vision_image = vision.Image(content=content)
            response = client.document_text_detection(image=vision_image)
            
            if response.error.message:
                raise Exception(response.error.message)
                
            if response.full_text_annotation:
                extracted_text += f"\n--- [Page {i+1}] ---\n"
                extracted_text += response.full_text_annotation.text

        return extracted_text
    except Exception as e:
        return f"\n[OCR 추출 실패: {e}]"


# =====================================================================
# [3] 구글 드라이브 실시간 하위 폴더 스캔 및 캐시 (자동 OCR 연동)
# =====================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_tdb_documents():
    context = ""
    try:
        FOLDER_ID = st.secrets["GDRIVE_FOLDER_ID"]
        creds_info = st.secrets["gdrive_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        return f"경고: Secrets 설정 오류: {e}"

    def recursive_fetch(folder_id):
        inner_context = ""
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                inner_context += recursive_fetch(item['id'])
            elif item['mimeType'] in ['text/plain', 'application/pdf']:
                try:
                    request = service.files().get_media(fileId=item['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done: _, done = downloader.next_chunk()
                    fh.seek(0)

                    if item['mimeType'] == 'text/plain':
                        content = fh.read().decode('utf-8', errors='ignore')
                        inner_context += f"\n\n--- [참조 데이터: {item['name']}] ---\n{content}"
                    
                    elif item['mimeType'] == 'application/pdf' and PdfReader:
                        pdf_bytes = fh.getvalue()
                        reader = PdfReader(io.BytesIO(pdf_bytes))
                        pdf_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                        
                        if not pdf_text.strip():
                            inner_context += f"\n\n--- [참조 데이터: {item['name']} (고정밀 OCR 자동 변환됨)] ---"
                            ocr_text = extract_text_with_vision(pdf_bytes)
                            inner_context += ocr_text
                        else:
                            inner_context += f"\n\n--- [참조 데이터: {item['name']}] ---\n{pdf_text}"
                except Exception:
                    pass 
        return inner_context

    context = recursive_fetch(FOLDER_ID)
    return context if context else "Tdb 폴더 내에 자료가 없습니다."


# =====================================================================
# [4] AI 엔진 챗봇 응답 함수 (빠른 도움말 use_tdb 플래그 적용)
# =====================================================================
def get_gemini_response_stream(messages, sim_result, api_key, is_admin=False, use_tdb=True):
    genai.configure(api_key=api_key)
    system_instruction = get_system_prompt(is_admin)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
    
    # [핵심] use_tdb가 False면 무거운 문서 스캔을 패스하고 1초만에 즉답 유도
    if use_tdb:
        retrieved_context = load_tdb_documents()
    else:
        retrieved_context = "[빠른 도움말 모드 작동 중: Tdb 문서 로드가 생략되었습니다. 관리자 운영 가이드(SOP) 내용만 바탕으로 즉시 답변하십시오.]"
        
    last_user_msg = messages[-1]["content"]
    
    full_prompt = f"### [Google Drive Tdb Context]\n{retrieved_context}\n\n"
    if sim_result: full_prompt += f"### [Simulation State]\n{sim_result}\n\n"
    full_prompt += f"### User Question: {last_user_msg}"
    
    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e: yield f"\n경고: Gemini 엔진 오류: {e}"

def get_openai_response_stream(messages, sim_result, api_key, is_admin=False, use_tdb=True):
    client = OpenAI(api_key=api_key)
    system_instruction = get_system_prompt(is_admin)
    
    if use_tdb:
        retrieved_context = load_tdb_documents()
    else:
        retrieved_context = "[빠른 도움말 모드 작동 중: Tdb 문서 로드가 생략되었습니다. 관리자 운영 가이드(SOP) 내용만 바탕으로 즉시 답변하십시오.]"
    
    sys_content = system_instruction + f"\n\n### [Context]\n{retrieved_context}"
    if sim_result: sys_content += f"\n\n### [Sim State]\n{sim_result}"
    
    full_messages = [{"role": "system", "content": sys_content}] + [m for m in messages if m["role"] != "system"]
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=full_messages, temperature=0.3, stream=True)
        for chunk in response:
            if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content
    except Exception as e: yield f"\n경고: OpenAI 엔진 오류: {e}"

def generate_auto_briefing(sim_result, engine_choice, openai_key, gemini_key):
    retrieved_context = load_tdb_documents()
    sys_content = get_system_prompt(is_admin=False) + f"\n\n[Context]\n{retrieved_context}\n\n[Sim State]\n{sim_result}"
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

# =====================================================================
# [5] Material 파라미터 검증
# =====================================================================
def check_parameter_discrepancy(current_params, engine_choice, api_key):
    context = load_tdb_documents() 
    prompt = f"""
    당신은 배터리 소재 스펙 검증 AI입니다. 
    아래 [현재 입력된 파라미터]와 [Tdb 기술 문서]를 비교하여 일치 여부를 분석하십시오.
    결과를 반드시 아래 형식의 순수 JSON 배열로 반환하십시오 (마크다운 금지).
    [현재 입력된 파라미터]\n{current_params}
    [Tdb 기술 문서]\n{context}
    [출력 예시]
    [{{"항목": "Cathode 용량", "현재입력값": "150", "Tdb권장값": "160", "상태": "불일치 경고"}}]
    """
    try:
        if "Gemini" in engine_choice:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            res = model.generate_content(prompt).text
        else:
            client = OpenAI(api_key=api_key)
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.1).choices[0].message.content
        return json.loads(res.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        return [{"항목": "오류", "현재입력값": "-", "Tdb권장값": "-", "상태": "비교 실패"}]