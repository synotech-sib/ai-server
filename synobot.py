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
# [1] 시노봇 시스템 지침 (업데이트된 관리자 종합 매뉴얼)
# =====================================================================
ADMIN_HELP_SOP = """
[관리자 종합 매뉴얼 (SOP)]
제1장. Tdb 문서 관리 및 OCR 동기화
- 명명 규칙: [분류]_[키워드1]_[키워드2]_[연도] (예: MAT_알트리스 양극재_코인셀 평가_2025)
- 분류: MAT(소재), PRO(공정), ANL(분석), PPR(논문), MKT(관련시장)
- OCR 실행: 스캔본 PDF 업로드 후 'Tdb 스캔 및 OCR 실행' 버튼을 누르면 Vision API를 통해 고정밀 텍스트로 자동 변환됩니다.

제2장. AI 엔진 및 시노봇 관리
- 평상시 'Gemini 2.5 Flash'를 사용하며, 정밀 분석 시 'OpenAI GPT-4o'로 스위칭합니다.
- 빠른 도움말 모드: 체크 시 무거운 Tdb 스캔을 건너뛰고 매뉴얼 내용만 바탕으로 1초 만에 즉답합니다.

제3장. Data Source 및 유저 관리
- 유저 관리: 가입자의 Pro Max 등급 승인 및 탈퇴 처리를 화면에서 직접 수행합니다.
- DB 직접 관리: 소재, 파라미터, 로그 DB를 화면에서 수정 후 클라우드에 영구 저장합니다.

제4장. VIP 소재 관리 및 공개용 마스킹 처리
- VIP 직접 추가: Pro Max 고객은 메인 화면의 '내 전용 DB에 새 소재 추가'를 통해 비공개 소재를 자체 등록할 수 있습니다.
- 공개용 마스킹 배포: 일반 유저 공개 시, 소재 DB 에디터에서 VIP 데이터를 복사해 'material_list'에 넣고 핵심 수치를 너프하여 배포합니다.

제5장. 스폰서 로고 설정
- 하단 푸터 로고는 GitHub 저장소 원본 링크(raw URL)를 사용하여 깨짐을 방지합니다.

제6장. 파라미터 실시간 검증
- UI에 설정된 파라미터 값들이 Tdb 원본 기술 문서와 일치하는지 '파라미터 일치 검증' 버튼을 통해 교차 검증합니다.
"""

def get_system_prompt(is_admin=False, is_logged_in=True):
    base_prompt = """You are 'SynoBot', an elite SIB R&D engineer for SynoCore.
- 당신은 구글 드라이브의 Tdb(Technical Database) 자료를 실시간으로 참조하여 답변합니다.
- 알트리스(Altris) 관련 기술 지표(ICE, Cathode 등)는 반드시 제공된 문서 내 수치를 근거로 답하십시오.
- 사용자의 언어(한국어/영어)에 맞춰 자연스럽게 대답하고 대화 맥락을 유지하십시오.
- '브리핑'이라는 단어 대신 '요약'이라는 단어를 사용하십시오.
- 다음 동의어 사전을 숙지하여 검색 및 매핑에 활용하십시오: "Prussian White" = "PW" = "알트리스 양극재", "Hard Carbon" = "HC" = "A-Grade" """
    
    # [수정] 비로그인 유저 대상 강력한 일괄 마스킹 지침
    if not is_logged_in:
        base_prompt += """
- [최우선 보안 규칙] 비로그인 유저에게 답변할 때, 특정 제조사명 및 브랜드(예: Altris, 알트리스, AK Chemical, AC Chemical, 애경케미칼, HiNa, CATL 등 영문/한글 불문)는 절대 노출하지 마십시오.
- 회사명은 부분 마스킹(예: AO Chemical)을 금지하고, 묶어서 전체를 'OOOO'로 일괄 마스킹하십시오. (예: 'Altris의 PW' -> 'OOOO의 PW', '알트리스 양극재' -> 'OOOO 양극재', 'AC Chemical' -> 'OOOO').
"""
    
    # [수정] [Rec.] 태그 적용 규칙 명확화 및 출처 문구 보호
    base_prompt += """
- [추천 태그 규칙] 추천하는 소재를 "리스트(목록) 형태"로 나열할 때만 항목명 앞에 영문 '[Rec.]' 태그를 붙이십시오.
- 일반 설명, 줄글(문장), 결론, 또는 출처 표기 영역 안에서는 '[Rec.]' 태그를 절대 사용하지 마십시오.
"""

    if is_admin:
        return base_prompt + f"\n\n{ADMIN_HELP_SOP}\n- 관리자의 질문에는 위의 [관리자 종합 매뉴얼]을 바탕으로 명확히 답변하십시오.\n- 관리자 답변 시에는 반드시 참조한 [실제 파일명]을 모두 나열하십시오."
    else:
        return base_prompt + "\n- 실제 참고한 파일의 원본 이름은 사용자에게 절대 노출하지 마십시오.\n- 답변의 맨 마지막 줄에는 어떠한 추가 텍스트나 태그 변형 없이, 오직 아래 지정된 문구만 정확히 그대로 출력하십시오:\n\n[출처] 시노봇 AI가 학습한 내부 자료임."

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
            if response.error.message: raise Exception(response.error.message)
            if response.full_text_annotation:
                extracted_text += f"\n--- [Page {i+1}] ---\n" + response.full_text_annotation.text
        return extracted_text
    except Exception as e:
        return f"\n[OCR 추출 실패: {e}]"

# =====================================================================
# [3] 구글 드라이브 실시간 하위 폴더 스캔 및 캐시 (자동 OCR 연동)
# =====================================================================
def clean_text_parsing(raw_text):
    if isinstance(raw_text, bytes):
        cleaned = raw_text.decode('utf-8-sig', errors='ignore')
    else:
        cleaned = raw_text.encode('utf-8', 'ignore').decode('utf-8-sig')
    return cleaned.replace('\r\n', '\n').strip()

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
                        content = clean_text_parsing(fh.read())
                        inner_context += f"\n\n--- [참조 데이터: {item['name']}] ---\n{content}"
                    elif item['mimeType'] == 'application/pdf' and PdfReader:
                        pdf_bytes = fh.getvalue()
                        reader = PdfReader(io.BytesIO(pdf_bytes))
                        pdf_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                        if not pdf_text.strip():
                            inner_context += f"\n\n--- [참조 데이터: {item['name']} (고정밀 OCR 자동 변환됨)] ---" + extract_text_with_vision(pdf_bytes)
                        else:
                            inner_context += f"\n\n--- [참조 데이터: {item['name']}] ---\n{pdf_text}"
                except Exception: pass 
        return inner_context

    context = recursive_fetch(FOLDER_ID)
    return context if context else "Tdb 폴더 내에 자료가 없습니다."

# =====================================================================
# [4] AI 엔진 챗봇 응답 함수
# =====================================================================
def get_gemini_response_stream(messages, sim_result, api_key, is_admin=False, use_tdb=True, is_logged_in=True):
    genai.configure(api_key=api_key)
    system_instruction = get_system_prompt(is_admin, is_logged_in)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
    
    retrieved_context = load_tdb_documents() if use_tdb else "[빠른 도움말 모드 작동 중: Tdb 문서 로드가 생략되었습니다. 관리자 종합 매뉴얼(SOP) 내용만 바탕으로 즉시 답변하십시오.]"
    last_user_msg = messages[-1]["content"]
    
    full_prompt = f"### [Google Drive Tdb Context]\n{retrieved_context}\n\n"
    if sim_result: full_prompt += f"### [Simulation State]\n{sim_result}\n\n"
    full_prompt += f"### User Question: {last_user_msg}"
    
    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e: yield f"\n경고: Gemini 엔진 오류: {e}"

def get_openai_response_stream(messages, sim_result, api_key, is_admin=False, use_tdb=True, is_logged_in=True):
    client = OpenAI(api_key=api_key)
    system_instruction = get_system_prompt(is_admin, is_logged_in)
    
    retrieved_context = load_tdb_documents() if use_tdb else "[빠른 도움말 모드 작동 중: Tdb 문서 로드가 생략되었습니다. 관리자 종합 매뉴얼(SOP) 내용만 바탕으로 즉시 답변하십시오.]"
    sys_content = system_instruction + f"\n\n### [Context]\n{retrieved_context}"
    if sim_result: sys_content += f"\n\n### [Sim State]\n{sim_result}"
    full_messages = [{"role": "system", "content": sys_content}] + [m for m in messages if m["role"] != "system"]
    
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=full_messages, temperature=0.3, stream=True)
        for chunk in response:
            if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content
    except Exception as e: yield f"\n경고: OpenAI 엔진 오류: {e}"

def generate_auto_summary(sim_result, engine_choice, openai_key, gemini_key, is_logged_in=True):
    retrieved_context = load_tdb_documents()
    sys_content = get_system_prompt(is_admin=False, is_logged_in=is_logged_in) + f"\n\n[Context]\n{retrieved_context}\n\n[Sim State]\n{sim_result}"
    user_prompt = "분석 요약을 3~4줄로 작성하십시오. 추천하는 소재가 있다면 리스트 항목에만 영문 [Rec.] 태그를 접두어로 사용하십시오."
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
        return f"자동 요약 생성 오류: {e}"

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
        return [{"항목": "오류", "현재입력값": "-", "Tdb권장값": "-", "상태": "비교 실패", "수정UI위치": "-", "원문발췌": "데이터 파싱 에러"}]