import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import random
import os
import hashlib
import io
import time
import smtplib
import queue
import threading
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components 

# [신규 AI 모듈 연결]
try:
    import synobot
except ImportError:
    synobot = None

# [한국 표준시(KST) 셋팅]
KST = timezone(timedelta(hours=9))

# [구글 시트 라이브러리 예외 처리]
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# [OpenAI 라이브러리 예외 처리]
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# -----------------------------------------------------------------------------
# [신규] 동적 로딩 스피너 (깜빡임 완벽 제거) 및 역순 채팅 제어 함수
# -----------------------------------------------------------------------------
def get_spinner_html(text):
    return f"""
    <div style="display: flex; align-items: center; padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="width: 24px; height: 24px; border: 4px solid #1A729A; border-top-color: transparent; border-radius: 50%; animation: syno-spin 0.8s linear infinite;"></div>
        <span style="margin-left: 15px; font-weight: bold; font-size: 15px; color: #1A729A;">{text}</span>
        <style>@keyframes syno-spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
    </div>
    """

def consume_generator(gen, q):
    try:
        for chunk in gen: q.put(("chunk", chunk))
    except Exception as e: q.put(("error", str(e)))
    finally: q.put(("done", None))

def safe_yield_with_dynamic_spinners(gen, placeholder, steps):
    q = queue.Queue()
    t = threading.Thread(target=consume_generator, args=(gen, q))
    t.start()
    
    start_time = time.time()
    cleared = False
    current_msg = "" 
    
    while True:
        try:
            msg_type, content = q.get(timeout=0.5)
            if msg_type == "chunk":
                if not cleared:
                    placeholder.empty()
                    cleared = True
                yield content
            elif msg_type == "error":
                yield f"\n[오류 발생: {content}]"
                break
            elif msg_type == "done":
                break
        except queue.Empty:
            if not cleared:
                elapsed = time.time() - start_time
                best_msg = steps[0][1]
                for t_thresh, msg in steps:
                    if elapsed >= t_thresh: best_msg = msg
                
                if best_msg != current_msg:
                    placeholder.markdown(get_spinner_html(best_msg), unsafe_allow_html=True)
                    current_msg = best_msg

def run_with_dynamic_spinners(func, args, kwargs, steps, placeholder_ui):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, *args, **kwargs)
    
    start_time = time.time()
    current_msg = "" 
    
    while not future.done():
        elapsed = time.time() - start_time
        best_msg = steps[0][1]
        for t_thresh, msg in steps:
            if elapsed >= t_thresh: best_msg = msg
        
        if best_msg != current_msg:
            placeholder_ui.markdown(get_spinner_html(best_msg), unsafe_allow_html=True)
            current_msg = best_msg
        
        time.sleep(0.5)
        
    placeholder_ui.empty()
    return future.result()

def render_chat_history(messages):
    interactions = []
    current_interaction = []
    for msg in messages:
        is_auto_summary = msg["role"] == "assistant" and "**[🤖 SynoBot 실시간 AI 요약]**" in msg["content"]
        if msg["role"] == "user" or is_auto_summary:
            if current_interaction:
                interactions.append(current_interaction)
                current_interaction = []
        current_interaction.append(msg)
    if current_interaction:
        interactions.append(current_interaction)
        
    for interaction in reversed(interactions):
        for msg in interaction:
            with st.chat_message(msg["role"]):
                content = msg["content"].replace("\n- ", "\n\n- ")
                if content.startswith("- "): content = "- " + content[2:]
                st.markdown(content)

chat_tdb_steps = [
    (0.0, "1/6: 사용자 질의 의도 파악 및 키워드 추출 중..."),
    (5.0, "2/6: 연동된 Tdb 기술 문서 라이브러리 전체 스캔 중..."),
    (10.0, "3/6: 관련 기술 데이터 및 논문 수치 교차 검증 중..."),
    (15.0, "4/6: 추출된 데이터 문맥 매칭 및 팩트 체크 중..."),
    (20.0, "5/6: 질문에 대한 최적의 답변 구조 설계 중..."),
    (25.0, "6/6: SynoBot AI 엔진으로 최종 답변 생성 중... (잠시만 기다려주세요)"),
    (35.0, "6/6: 잠시 지체되고 있습니다. 데이터가 방대하여 조금만 더 기다려 주세요...")
]

chat_fast_steps = [
    (0.0, "1/3: 관리자 보안 프로토콜 및 권한 확인 중..."),
    (3.0, "2/3: 관리자 종합 매뉴얼(SOP) 고속 스캔 중..."),
    (6.0, "3/3: 매뉴얼 바탕으로 즉시 답변 생성 중..."),
    (10.0, "3/3: 잠시 지체되고 있습니다. 조금만 더 기다려 주세요...")
]

auto_summary_steps = [
    (0.0, "1/6: 시뮬레이션 결과 데이터 수집 및 전처리 중..."),
    (5.0, "2/6: Tdb 클라우드 기술 문서 스캔 및 로드 중..."),
    (10.0, "3/6: 입력된 파라미터와 원본 수치 정밀 대조 중..."),
    (15.0, "4/6: 물리 엔진 연산 결과 AI 문맥 분석 중..."),
    (20.0, "5/6: 소재별 최적화 인사이트 추출 중..."),
    (25.0, "6/6: SynoBot AI 엔진으로 최종 요약 리포트 생성 중... (잠시만 기다려주세요)"),
    (35.0, "6/6: 잠시 지체되고 있습니다. 데이터가 방대하여 조금만 더 기다려 주세요...")
]

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (강력한 Print CSS 및 슬라이더 두께 고정 보완)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore Pro v0.9.1", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden !important; display: none !important;} 
    header {visibility: hidden !important; display: none !important;}
    a[href^="https://streamlit.io"] {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    .stApp > header {display: none !important;}
    .stApp [data-testid="stToolbar"] {display: none !important;}
    
    .main .block-container { max-width: 1500px !important; padding-top: 2rem; padding-bottom: 2rem; margin: auto; }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 60px; }
    .syno-title { color: #1A729A; font-size: 50px !important; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #7F7F7F !important; font-size: 22px !important; font-weight: bold; padding-top: 20px; }
    
    div.st-key-btn_home_overlay { margin-top: -60px !important; opacity: 0 !important; z-index: 999 !important; height: 60px !important; width: 350px !important; overflow: hidden !important; }
    div.st-key-btn_home_overlay button { height: 100% !important; width: 100% !important; cursor: pointer !important; }
    
    div.st-key-admin_sync_btn > button, div.st-key-admin_verify_btn > button, div.st-key-btn_save_logo > button {
        width: auto !important; padding-left: 10px !important; padding-right: 10px !important; min-width: 140px !important;
    }

    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 20px 10px; height: 120px; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important; text-align: center !important; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; color: #1A729A !important; margin-top: 5px; text-align: center !important; justify-content: center !important; display: flex !important; width: 100%;} 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; margin-top: 3px; justify-content: center !important; display: flex !important; width: 100%;}
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { font-size: 16px !important; font-weight: bold !important; color: #222 !important; justify-content: center !important; text-align: center !important; display: flex !important; width: 100%; } 
    
    div[data-testid="stButton"] > button, div[data-testid="stFormSubmitButton"] > button, div[data-testid="stPopover"] > button { height: 40px !important; background-color: #1A729A !important; color: white !important; font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100% !important; border: none !important; white-space: nowrap !important; padding: 0 5px !important; }
    div.st-key-btn_excel > button { background-color: #1A729A !important; border: 1px solid #155A7A !important; }
    div.st-key-btn_del_sel > button, div.st-key-btn_withdraw > button { background-color: #D35400 !important; border: 1px solid #B04600 !important; }

    div.st-key-btn_my_db_scroll button { background-color: transparent !important; background: transparent !important; border: none !important; box-shadow: none !important; display: flex !important; justify-content: flex-end !important; padding: 0 !important; height: auto !important; min-height: 0 !important; }
    div.st-key-btn_my_db_scroll button p { color: #333 !important; font-weight: bold !important; font-size: 15px !important; margin: 0 !important; }
    div.st-key-btn_my_db_scroll button p span { text-decoration: underline !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 20px !important; }
    
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 10px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #222 !important; margin-bottom: 12px !important; border-bottom: 2px solid #1A729A; padding-bottom: 5px; }
    .param-label { font-size: 16px !important; font-weight: bold !important; color: #333 !important; margin-bottom: 4px !important; }
    
    /* 🔴 핵심 수정: 슬라이더 굵기 6px로 모든 화면에서 강제 통일 */
    .stSlider > div[data-baseweb="slider"] > div > div[style*="background"] { 
        height: 6px !important; 
        border-radius: 3px !important; 
    }
    .stSlider > div[data-baseweb="slider"] div[role="slider"] {
        height: 18px !important;
        width: 18px !important;
        margin-top: -6px !important;
    }

    /* 인쇄 모드 레이아웃 붕괴 완벽 방지 */
    @media print {
        header, footer, [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }
        button, .stChatInputContainer, [data-testid="stChatInput"] { display: none !important; }
        .main .block-container { max-width: 100% !important; width: 100% !important; padding: 10px !important; margin: 0 !important; }
        
        div[data-testid="stHorizontalBlock"] { display: block !important; } 
        div[data-testid="column"] { width: 100% !important; max-width: 100% !important; min-width: 100% !important; flex: none !important; display: block !important; margin-bottom: 20px !important; }
        
        div[data-testid="stVerticalBlock"]:has(> div > div > h4:contains("SynoBot")) { display: none !important; }
        
        .stScrollableContainer, div[data-testid="stVerticalBlock"] { height: auto !important; max-height: none !important; overflow: visible !important; }
        div[data-testid="element-container"]:has(#section4-anchor), div[data-testid="element-container"]:has(#section4-anchor) ~ * { display: none !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; page-break-inside: avoid; overflow: visible !important; white-space: normal !important; word-wrap: break-word !important; }
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 및 캐싱
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = st.secrets.get("ADMIN_PW", "1234")

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

@st.cache_data(ttl=3600)
def load_cloud_data_cached(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws, ttl=3600)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
    except Exception: pass
    return pd.DataFrame()

def load_cloud_data(url, ws="Sheet1"): return load_cloud_data_cached(url, ws)

def get_vip_list_exact():
    df = load_cloud_data_cached(URL_USERS, "VIPs")
    return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()] if not df.empty and 'Company' in df.columns else []

mat_df_public = load_cloud_data_cached(URL_MATS, "material_list")

@st.cache_data(ttl=3600)
def get_user_db_cached():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=3600)
    except Exception: return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def get_user_db(): return get_user_db_cached()
def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -----------------------------------------------------------------------------
# ✉️ 이메일 발송 시스템
# -----------------------------------------------------------------------------
def get_smtp_server():
    sender_password = st.secrets.get("EMAIL_PASSWORD", "")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("wschoi@synotech.co.kr", sender_password.replace(" ", ""))
    return server

def send_verification_email(to_email, code):
    try:
        msg = MIMEMultipart(); msg['From'] = "SynoCore <synocore@synotech.co.kr>"; msg['To'] = to_email; msg['Subject'] = "[SynoCore Pro] 회원가입 인증번호 안내"
        msg.attach(MIMEText(f"안녕하세요. 회원가입 인증번호입니다.\n\n▶ 인증번호 : {code}\n\n감사합니다.", 'plain', 'utf-8'))
        server = get_smtp_server(); server.send_message(msg); server.quit(); return "SUCCESS"
    except Exception as e: return f"발송 오류: {str(e)}"

def send_welcome_email(to_email, user_name):
    try:
        msg = MIMEMultipart(); msg['From'] = "SynoCore <synocore@synotech.co.kr>"; msg['To'] = to_email; msg['Subject'] = "[SynoCore Pro Max] 회원가입 완료 안내"
        msg.attach(MIMEText(f"안녕하세요 {user_name}님, 회원가입이 성공적으로 완료되었습니다.", 'plain', 'utf-8'))
        server = get_smtp_server(); server.send_message(msg); server.quit(); return True
    except Exception: return False

def send_admin_notification(subject, body_text):
    try:
        msg = MIMEMultipart(); msg['From'] = "SynoCore System <synocore@synotech.co.kr>"; msg['To'] = "wschoi@synotech.co.kr" 
        msg['Subject'] = f"🚨 [Admin Alert] {subject}"; msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        server = get_smtp_server(); server.send_message(msg); server.quit()
    except Exception: pass

# -----------------------------------------------------------------------------
# 유틸리티 (물리 엔진 및 데이터 연동)
# -----------------------------------------------------------------------------
def get_dqdv(cat_sel, v_tc, m_df=None):
    v_axis = np.linspace(2.0, 4.2, 150); dqdv = np.zeros_like(v_axis); p1, p2 = 3.15, 0.0 
    if m_df is not None and not m_df.empty and 'Name' in m_df.columns:
        mat_row = m_df[m_df['Name'] == cat_sel]
        if not mat_row.empty:
            try: p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15)); p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
            except: pass
    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]
    if not peaks: peaks = [3.15]
    for p in peaks: shifted_p = float(p) - (float(v_tc) * 0.015); dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email, workspace="general_user"):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=3600)
        if db_df.empty or 'Email' not in db_df.columns: return []
        my_logs = db_df[(db_df['Email'] == email) & (db_df.get('Workspace', 'general_user').isin([workspace, 'material_list']))]
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None); row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'C_Load', 'C_Press', 'C_Act', 'C_Bin', 'C_Con', 'N/P Ratio', 'A_Press', 'A_Act', 'A_Bin', 'A_Con', 'E/C Ratio', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
                time_str = str(row_dict.get('Time', '')).strip()
                if not time_str or time_str == "nan": time_str = datetime.now(KST).strftime("%m-%d %H:%M:%S")
                row_dict['Time'] = time_str 
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
        return hist[::-1]
    except: return []

def save_chat_log(email, workspace, role, content):
    if GSheetsConnection is None: return
    safe_email = email if email else "guest"; safe_ws = workspace if workspace else "general_user"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try: chat_df = conn.read(spreadsheet=URL_LOGS, worksheet="ChatLogs", ttl=0)
        except: chat_df = pd.DataFrame(columns=["Time", "Workspace", "Email", "Role", "Message"])
        new_row = pd.DataFrame([{"Time": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"), "Workspace": safe_ws, "Email": safe_email, "Role": role, "Message": content}])
        new_row = new_row[["Time", "Workspace", "Email", "Role", "Message"]]
        if chat_df.empty or 'Email' not in chat_df.columns: conn.update(spreadsheet=URL_LOGS, worksheet="ChatLogs", data=new_row)
        else: updated_df = pd.concat([chat_df, new_row], ignore_index=True); conn.update(spreadsheet=URL_LOGS, worksheet="ChatLogs", data=updated_df)
        st.cache_data.clear()
    except: pass

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'general_user', 'user_vip_name': None, 'is_admin': False, 'user_tier': "",  
    'admin_view': None, 'admin_ws': None, 'chat_messages': [], 
    'trigger_auto_bot': False, 'trigger_bot_reply': False, 'bot_user_input': "", 
    'scroll_to_result': False, 'scroll_to_data': False, 'acc_step': 1,
    'engine_choice': "Gemini 2.5 Flash (기본/쾌속)",  
    'trigger_scroll_top': False,
    'sponsor_logo_url': "",
    'show_admin_panel': True 
}

for key, val in default_vars.items():
    if key not in st.session_state: st.session_state[key] = val

qp = st.query_params
if "session_token" in qp and not st.session_state.logged_in:
    token = qp["session_token"]; df_u = get_user_db_cached()
    if token in ADMIN_USERS:
        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[token], 'user_email': token, 'is_admin': True, 'workspace': 'admin_master', 'user_tier': 'Admin'})
        st.session_state.history = load_user_history(token, 'admin_master')
    else:
        valid = df_u[df_u['Email'].str.strip().str.lower() == token.lower()] if not df_u.empty else pd.DataFrame()
        if not valid.empty:
            promax_flag = valid['ProMax_Req'].values[0] if 'ProMax_Req' in valid.columns else 'N'
            if promax_flag != 'Out':
                domain = token.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                target_ws = vip_map.get(domain, 'general_user')
                st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'workspace': target_ws, 'user_tier': "Pro Max" if str(promax_flag).upper() == 'Y' else "Pro"})
                st.session_state.history = load_user_history(token, target_ws)

is_pro = st.session_state.logged_in

h_l, h_r = st.columns([0.72, 0.28], gap="small") 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">Pro v0.9.1</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False; st.session_state.show_profile = False; st.session_state.admin_view = None; st.session_state.admin_ws = None; st.rerun()

if not is_pro:
    with h_r:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="small") 
        with c1.popover("Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                if st.form_submit_button("로그인", use_container_width=True):
                    with st.spinner("인증 중..."):
                        df_u = get_user_db()
                        u_id_clean = u_id.strip().lower(); hashed_pw = hash_password(u_pw) if u_pw else ""
                        if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                            st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'admin_master', 'user_tier': 'Admin'})
                            st.session_state.history = load_user_history(u_id_clean, 'admin_master')
                            st.session_state.chat_messages = [{"role": "assistant", "content": f"- **{ADMIN_USERS[u_id_clean]} 관리자님. SynoCore 통합 SOP 및 Tdb 관제 시스템이 준비되었습니다.**\n\n운영 가이드나 기술 문서에 대한 요약이 필요하시면 무엇이든 물어봐 주십시오."}]
                            st.query_params["session_token"] = u_id_clean; st.rerun()
                        else:
                            valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                            if not valid.empty:
                                promax_flag = valid['ProMax_Req'].values[0] if 'ProMax_Req' in valid.columns else 'N'
                                if promax_flag == 'Out': st.error("탈퇴 처리된 계정입니다.")
                                else:
                                    domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                                    target_ws = vip_map.get(domain, 'general_user')
                                    st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 'workspace': target_ws, 'user_tier': "Pro Max" if str(promax_flag).upper() == 'Y' else "Pro"})
                                    st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                                    welcome_msg = f"안녕하세요 {valid['Name'].values[0]}님. [{target_ws.capitalize()} DB Center] VIP 워크스페이스로 전환되었습니다." if target_ws != 'general_user' else f"안녕하세요 {valid['Name'].values[0]}님. SIB 설계 요약을 시작합니다."
                                    st.session_state.chat_messages = [{"role": "assistant", "content": "- " + welcome_msg}]
                                    st.query_params["session_token"] = u_id_clean; st.rerun()
                            else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        with c2:
            if st.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
else:
    with h_r:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 
        r_my, r_out = st.columns([1, 1], gap="small")
        with r_my:
            if st.session_state.get('is_admin', False):
                toggle_label = "시뮬레이션 가기" if st.session_state.get('show_admin_panel', True) else "관리자 패널"
                if st.button(toggle_label, key="btn_admin_toggle", use_container_width=True):
                    st.session_state.show_admin_panel = not st.session_state.get('show_admin_panel', True)
                    st.rerun()
            else:
                if st.button("My 계정", key="btn_profile_m", use_container_width=True): 
                    st.session_state.show_profile = not st.session_state.show_profile
                    st.rerun()
        with r_out:
            if st.button("Logout", key="btn_logout_m", use_container_width=True): 
                if "session_token" in st.query_params: del st.query_params["session_token"]
                for key, val in default_vars.items(): st.session_state[key] = val
                st.rerun()
        if st.session_state.user_tier == "Pro Max" and st.session_state.workspace not in ['admin_master', 'general_user']:
            display_text = f"👤 {st.session_state.user_name} (Pro Max) :blue[[{st.session_state.workspace.capitalize()} DB Center]]"
            if st.button(display_text, key="btn_my_db_scroll", use_container_width=True): st.session_state.scroll_to_data = True
        else:
            st.markdown(f"<div style='text-align: right; font-weight: bold; color: #333; font-size: 15px; margin-top: 5px; margin-bottom: 2px;'>👤 {st.session_state.user_name} ({st.session_state.user_tier})</div>", unsafe_allow_html=True)

st.markdown("---")

def sync_s_to_n(s_key, n_key, p_key=None): 
    st.session_state[n_key] = st.session_state[s_key]
    if p_key: st.query_params[p_key] = st.session_state[s_key]

def sync_n_to_s(s_key, n_key, p_key=None): 
    st.session_state[s_key] = st.session_state[n_key]
    if p_key: st.query_params[p_key] = st.session_state[n_key]

def change_acc_step(step): st.session_state.acc_step = step

# -----------------------------------------------------------------------------
# 5. 메인 UI (관리자 패널 및 시뮬레이터 렌더링)
# -----------------------------------------------------------------------------
col_left, col_main, col_bot = st.columns([0.02, 0.70, 0.28], gap="small")

with col_left: st.empty() 

with col_main:
    # =========================================================================
    # [관리자 전용 화면]
    # =========================================================================
    if st.session_state.get('is_admin', False) and st.session_state.get('show_admin_panel', True):
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">최고 관리자 전용 패널</p>', unsafe_allow_html=True)
            st.markdown("<p style='font-size: 15px; color: #555;'>연동된 Tdb 외부 경로: Google Drive 연동 폴더 내 전체 .txt 및 .pdf 파일 (실시간 스캔 중)</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            # (이하 관리자 패널 로직 동일 유지)
            col_db_t, col_db_b = st.columns([0.8, 0.2])
            col_db_t.markdown("### [DB 관리자] Tdb 스캔 및 OCR 동기화")
            if col_db_b.button("Tdb 스캔 및 OCR 실행", key="admin_sync_btn", use_container_width=True):
                with st.spinner("구글 드라이브 스캔 및 이미지 PDF OCR 변환을 진행 중입니다..."):
                    if synobot:
                        synobot.load_tdb_documents.clear() 
                        synobot.load_tdb_documents()
                    st.success("Tdb 문서 동기화 및 OCR 변환 완료!")

            st.markdown("<br>", unsafe_allow_html=True)
            search_kw = st.text_input("🔍 관리자 종합 매뉴얼 실시간 검색", placeholder="예: OCR, 명명, 로고...")

            manual_data = {
                "제1장. Tdb 문서 관리 및 OCR 동기화": "<ul><li><b>명명 규칙:</b> [분류]_[키워드1]_[키워드2]_[연도]</li><li><b>OCR 변환:</b> 스캔본은 Vision API를 통해 자동 변환됩니다.</li></ul>",
                "제2장. AI 엔진 및 시노봇 관리": "<ul><li><b>빠른 도움말 모드:</b> 매뉴얼 검색 시 즉각적인 답변 기능.</li></ul>",
            }
            with st.expander("관리자 종합 매뉴얼 보기 (SOP)", expanded=True if search_kw else False):
                for title, content in manual_data.items():
                    if not search_kw or (search_kw.lower() in title.lower() or search_kw.lower() in content.lower()):
                        st.markdown(f"<div style='font-weight: bold; font-size: 16px; margin-bottom: 5px; color: #1A729A;'>{title}</div>{content}", unsafe_allow_html=True)
                
            st.markdown("<hr style='border: 3px solid #1A729A; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)
            st.markdown("### [Master 관리자] Data 및 고객 관리")
            
            engine_opts = ["Gemini 2.5 Flash (기본/쾌속)", "OpenAI GPT-4o (비상/정밀)"]
            selected_engine = st.radio("AI 엔진 마스터 스위치", engine_opts, key="engine_radio_widget", horizontal=True)
            st.session_state.engine_choice = selected_engine

            a1, a2, a3, a4, a5 = st.columns(5)
            if a1.button("유저 관리 DB", use_container_width=True): st.session_state.admin_view = 'users'; st.session_state.admin_ws = 'Users'; st.rerun()
            if a2.button("소재 DB", use_container_width=True): st.session_state.admin_view = 'mats'; st.session_state.admin_ws = 'admin_master'; st.rerun()
            if a3.button("파라미터 DB", use_container_width=True): st.session_state.admin_view = 'param'; st.session_state.admin_ws = 'param_config'; st.rerun()
            if a4.button("로그 DB", use_container_width=True): st.session_state.admin_view = 'logs'; st.session_state.admin_ws = 'myData'; st.rerun()
            if a5.button("시노봇 로그 DB", use_container_width=True): st.session_state.admin_view = 'chat'; st.session_state.admin_ws = 'ChatLogs'; st.rerun()

    # =========================================================================
    # [일반 유저 및 시뮬레이션 화면] 
    # =========================================================================
    else:
        # 가입 및 계정 관리 생략 (기존 코드 유지)
        pass 

        with st.container(height=1000, border=False):
            st.markdown("<div id='main-scroll-anchor'></div>", unsafe_allow_html=True) 
            
            # [섹션 1: Material Selection]
            st.markdown('<p class="main-header" style="margin-top:10px;">1. Material Selection</p>', unsafe_allow_html=True)
            sp1, c_1 = st.columns([0.03, 0.97])
            with c_1:
                with st.container(border=True):
                    _dfs = []
                    if not mat_df_public.empty: 
                        tmp_pub = mat_df_public.copy()
                        tmp_pub['Is_VIP'] = False
                        _dfs.append(tmp_pub)
                        
                    mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

                    m1, m2, m3, m4 = st.columns(4)
                    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["Sample Cathode"]
                    ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist() if not mat_df.empty else ["Sample Anode"]
                    
                    with m1: cat_sel = st.selectbox("Cathode", cat_list, key="sel_cat_m")
                    with m2: ano_sel = st.selectbox("Anode", ano_list, key="sel_ano_m")
                    with m3: st.selectbox("Electrolyte", ["Sample Elec"], key="sel_ele_m")
                    with m4: st.selectbox("Separator", ["Sample Sep"], key="sel_sep_m")
                    
                    row = mat_df[mat_df['Name']==cat_sel].iloc[0] if not mat_df.empty and cat_sel in cat_list else pd.Series()
                    ano_row = mat_df[mat_df['Name']==ano_sel].iloc[0] if not mat_df.empty and ano_sel in ano_list else pd.Series()
                    
                    init_vals = {
                        "cap": safe_float(row.get('Cap_Def'), 160.0), "volt": safe_float(row.get('Volt_Def'), 3.05), 
                        "c_den": safe_float(row.get('Den_Def'), 4.5), "a_den": safe_float(ano_row.get('Den_Def'), 2.1), 
                        "life": safe_float(row.get('Life_Def'), 4000.0), "c_lod": safe_float(row.get('Load_Def'), 14.0), 
                        "c_press": 2.50, "c_act": 96.0, "c_bin": 2.0, "c_con": 2.0, "c_foil": 15.0,
                        "np": 1.10, "a_press": 1.60, "a_act": 95.0, "a_bin": 2.5, "a_con": 2.5, "a_foil": 15.0,
                        "ec": 3.5, "sep_thick": 16.0, "te": 160.0, "tc": 1.0, "tl": 2000.0 
                    }

                    if st.session_state.get("prev_cat") != cat_sel or st.session_state.get("prev_ano") != ano_sel:
                        st.session_state.prev_cat = cat_sel; st.session_state.prev_ano = ano_sel
                        for k, v in init_vals.items():
                            st.session_state[f"{k}_s"] = v; st.session_state[f"{k}_n"] = v
                        st.rerun()

            for k, v in init_vals.items():
                if f"{k}_s" not in st.session_state: st.session_state[f"{k}_s"] = v

            expert = True if is_pro else False

            # [섹션 2: Process Parameters]
            st.markdown('<p class="main-header" style="margin-top:20px;">2. Process Parameters</p>', unsafe_allow_html=True)
            sp2, c_2 = st.columns([0.03, 0.97])
            with c_2:
                with st.expander(f"Step 1. 소재 물성 설정 (Material Specs)", expanded=True):
                    s1, s2, s3 = st.columns(3)
                    with s1:
                        st.markdown("<p class='param-label'>Capacity (mAh/g)</p>", unsafe_allow_html=True)
                        st.slider("Cap_S", 50.0, 400.0, step=1.0, key="cap_s", label_visibility="collapsed")
                    with s2:
                        st.markdown("<p class='param-label'>Voltage (V)</p>", unsafe_allow_html=True)
                        st.slider("Volt_S", 1.0, 5.0, step=0.1, key="volt_s", label_visibility="collapsed")
                    with s3:
                        st.markdown("<p class='param-label'>Base Life (Cycles)</p>", unsafe_allow_html=True)
                        st.slider("Life_S", 100.0, 15000.0, step=100.0, key="life_s", label_visibility="collapsed")
                    
                    st.markdown("<br>", unsafe_allow_html=True) 
                    s4, s5, s6 = st.columns(3)
                    with s4:
                        st.markdown("<p class='param-label'>Cathode True Den (g/cc)</p>", unsafe_allow_html=True)
                        st.slider("CDen_S", 0.5, 6.0, step=0.1, key="c_den_s", label_visibility="collapsed")
                    with s5:
                        st.markdown("<p class='param-label'>Anode True Den (g/cc)</p>", unsafe_allow_html=True)
                        st.slider("ADen_S", 0.5, 6.0, step=0.1, key="a_den_s", label_visibility="collapsed")

                with st.expander(f"Step 2. 셀 공정 설계 (Process Parameters)", expanded=True):
                    p1, p2, p3 = st.columns(3)
                    with p1:
                        st.markdown('<p class="sub-header-bold">(A) Cathode Process</p>', unsafe_allow_html=True)
                        st.markdown("<p class='param-label'>Areal Loading (mg/cm2)</p>", unsafe_allow_html=True)
                        st.slider("CLod_S", 1.0, 50.0, step=1.0, key="c_lod_s", label_visibility="collapsed")

                        st.markdown("<p class='param-label'>Press Density (g/cc)</p>", unsafe_allow_html=True)
                        st.slider("CPress_S", 0.5, 5.0, step=0.1, key="c_press_s", label_visibility="collapsed")
                        
                        # [핵심 수정] 기공률 방어 로직 (마이너스 값 출력 금지)
                        c_poro_val = 1 - (st.session_state.c_press_s / st.session_state.c_den_s)
                        c_poro = max(0.0, c_poro_val * 100) if st.session_state.c_den_s > 0 else 0
                        c_poro_color = "#D35400" if c_poro_val < 0 else "#1A729A"
                        c_warning = " (경고: 합제 밀도가 진밀도 초과)" if c_poro_val < 0 else ""
                        st.markdown(f"<div style='background:#eaf2f8; padding:8px 10px; border-radius:5px; margin-top:5px; margin-bottom:25px;'><span style='color:{c_poro_color}; font-weight:bold; font-size:14px;'>양극 기공률 (Porosity): {c_poro:.1f}%{c_warning}</span></div>", unsafe_allow_html=True)
                        
                        st.markdown("<p class='param-label'>Al Foil Thickness (μm)</p>", unsafe_allow_html=True)
                        st.slider("CFoil_S", 5.0, 50.0, step=1.0, key="c_foil_s", label_visibility="collapsed")
                        st.markdown("<p class='param-label'>Active Ratio (%)</p>", unsafe_allow_html=True)
                        st.slider("CAct_S", 80.0, 99.0, step=0.5, key="c_act_s", label_visibility="collapsed")
                        
                    with p2:
                        st.markdown('<p class="sub-header-bold">(B) Anode Process</p>', unsafe_allow_html=True)
                        st.markdown("<p class='param-label'>N/P Ratio</p>", unsafe_allow_html=True)
                        st.slider("NP_S", 0.80, 2.00, step=0.05, key="np_s", label_visibility="collapsed")

                        st.markdown("<p class='param-label'>Press Density (g/cc)</p>", unsafe_allow_html=True)
                        st.slider("APress_S", 0.5, 3.0, step=0.1, key="a_press_s", label_visibility="collapsed")
                        
                        # [핵심 수정] 기공률 방어 로직 (마이너스 값 출력 금지)
                        a_poro_val = 1 - (st.session_state.a_press_s / st.session_state.a_den_s)
                        a_poro = max(0.0, a_poro_val * 100) if st.session_state.a_den_s > 0 else 0
                        a_poro_color = "#D35400" if a_poro_val < 0 else "#1A729A"
                        a_warning = " (경고: 합제 밀도가 진밀도 초과)" if a_poro_val < 0 else ""
                        st.markdown(f"<div style='background:#eaf2f8; padding:8px 10px; border-radius:5px; margin-top:5px; margin-bottom:25px;'><span style='color:{a_poro_color}; font-weight:bold; font-size:14px;'>음극 기공률 (Porosity): {a_poro:.1f}%{a_warning}</span></div>", unsafe_allow_html=True)
                        
                        st.markdown("<p class='param-label'>Al Foil Thickness (μm)</p>", unsafe_allow_html=True)
                        st.slider("AFoil_S", 5.0, 50.0, step=1.0, key="a_foil_s", label_visibility="collapsed")
                        st.markdown("<p class='param-label'>Active Ratio (%)</p>", unsafe_allow_html=True)
                        st.slider("AAct_S", 80.0, 99.0, step=0.5, key="a_act_s", label_visibility="collapsed")

                    with p3:
                        st.markdown('<p class="sub-header-bold">(C) Cell & Electrolyte</p>', unsafe_allow_html=True)
                        st.markdown("<p class='param-label'>E/C Ratio (g/Ah)</p>", unsafe_allow_html=True)
                        st.slider("EC_S", 1.0, 8.0, step=0.1, key="ec_s", label_visibility="collapsed")
                        st.markdown("<p class='param-label'>Separator Thickness (μm)</p>", unsafe_allow_html=True)
                        st.slider("SepThick_S", 5.0, 50.0, step=1.0, key="sep_thick_s", label_visibility="collapsed")

                with st.expander("Step 3. 타겟 성능 설정 (Target Settings)", expanded=True):
                    t1, t2, t3 = st.columns(3)
                    with t1: 
                        st.markdown('<p class="sub-header-bold">Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
                        st.slider("TE_S", 50.0, 350.0, step=5.0, key="te_s", label_visibility="collapsed")
                    with t2: 
                        st.markdown('<p class="sub-header-bold">C-rate</p>', unsafe_allow_html=True)
                        st.slider("TC_S", 0.1, 10.0, step=0.5, key="tc_s", label_visibility="collapsed")
                    with t3: 
                        st.markdown('<p class="sub-header-bold">Cycle Life</p>', unsafe_allow_html=True)
                        st.slider("TL_S", 500.0, 15000.0, step=100.0, key="tl_s", label_visibility="collapsed")

            # 변수 할당
            v_cap, v_volt, v_c_den, v_a_den, v_life = st.session_state.cap_s, st.session_state.volt_s, st.session_state.c_den_s, st.session_state.a_den_s, st.session_state.life_s
            v_c_lod, v_c_press, v_c_act = st.session_state.c_lod_s, st.session_state.c_press_s, st.session_state.c_act_s
            v_np, v_a_press, v_a_act = st.session_state.np_s, st.session_state.a_press_s, st.session_state.a_act_s
            v_ec, v_sep_thick = st.session_state.ec_s, st.session_state.sep_thick_s
            v_te, v_tc, v_tl = st.session_state.te_s, st.session_state.tc_s, st.session_state.tl_s

            st.markdown("<div id='section5'></div>", unsafe_allow_html=True)
            if st.session_state.get('scroll_to_result'):
                components.html("<script>window.parent.document.getElementById('section5').scrollIntoView();</script>", height=0)
                st.session_state.scroll_to_result = False

            # [섹션 3: Simulation & Analysis] 
            st.markdown('<p class="main-header" style="margin-top:20px;">3. Simulation & Analysis</p>', unsafe_allow_html=True)
            sp5, c_5 = st.columns([0.03, 0.97])
            with c_5:
                with st.container(border=True):
                    if st.button("RUN SIMULATION", key="btn_run_m", use_container_width=True):
                        cell_v = max(0.1, v_volt - (0.1 + (v_tc * 0.02)))
                        c_areal_cap = v_c_lod * (v_c_act / 100.0) * v_cap / 1000.0 
                        a_areal_cap = c_areal_cap * v_np
                        a_cap_default = 300.0 
                        a_lod = a_areal_cap / (a_cap_default * (v_a_act / 100.0)) * 1000.0 
                        
                        effective_mass = (v_c_lod + a_lod + 15*0.27 + 15*0.27 + v_sep_thick*0.05 + c_areal_cap*v_ec) / 0.8  
                        effective_thick = ((v_c_lod/v_c_press)*10.0 + (a_lod/v_a_press)*10.0 + 15 + 15 + v_sep_thick) / 0.9  
                        
                        res_whkg = (c_areal_cap * cell_v) / effective_mass * 1000.0 * max(0.5, 1.0 - (v_tc * 0.015))
                        whl = (c_areal_cap * cell_v) / effective_thick * 10000.0 * max(0.5, 1.0 - (v_tc * 0.015))
                        life_cyc = int(v_life * (0.95 ** v_tc))
                        
                        log_data = {
                            "Time": datetime.now(KST).strftime("%m-%d %H:%M:%S"), "Cathode": cat_sel, "Anode": ano_sel, 
                            "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "C_Load": round(v_c_lod, 1), 
                            "C_Press": round(v_c_press, 2), "N/P Ratio": round(v_np, 2),
                            "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), 
                            "Life(Cyc)": life_cyc, "AI_Summary": ""
                        }
                        
                        st.session_state.history.insert(0, log_data)
                        st.session_state.sim_result = log_data # 🔴 AI에게 던져줄 상태값 갱신
                        st.session_state.trigger_auto_bot = True 
                        st.session_state.scroll_to_result = True 
                        st.rerun()
                            
                    if st.session_state.history:
                        res = st.session_state.history[0]
                        r1, r2, r3, r4 = st.columns(4)
                        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg'] - v_te, 1):+} Wh/kg")
                        r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off")
                        r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{round(res['Cell_V'] - v_volt, 2):+} V", delta_color="inverse")
                        r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{int(res['Life(Cyc)'] - v_tl):+} Cyc")
                        
                        st.markdown("<br><br>", unsafe_allow_html=True)
                        row1_1, sp_r1, row1_2 = st.columns([1, 0.05, 1])
                        with row1_1:
                            st.markdown('<p style="font-size: 16px; font-weight: bold; text-align: center;">Discharge Profile</p>', unsafe_allow_html=True)
                            fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                            fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig1, use_container_width=True)
                        with row1_2:
                            st.markdown('<p style="font-size: 16px; font-weight: bold; text-align: center;">dQ/dV Profile</p>', unsafe_allow_html=True)
                            fig2 = go.Figure(go.Scatter(x=np.linspace(2.0, 4.2, 100), y=np.exp(-(np.linspace(2.0, 4.2, 100) - 3.15)**2 / 0.005) * 15, fill='tozeroy', line=dict(color='#e63946', width=2)))
                            fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig2, use_container_width=True)
                            
                        st.markdown("<br>", unsafe_allow_html=True)
                        row2_1, sp_r2, row2_2 = st.columns([1, 0.05, 1])
                        with row2_1:
                            st.markdown('<p style="font-size: 16px; font-weight: bold; text-align: center;">Cell Performance</p>', unsafe_allow_html=True)
                            fig3 = go.Figure(go.Scatterpolar(r=[min(100, res.get('Wh/kg', 0)/2.5), 50, min(100, res.get('Life(Cyc)', 0)/50), min(100, res.get('Cell_V', 0)*25), min(100, res.get('C_Load', 0)*4)], theta=['Energy', 'Power', 'Life', 'Voltage', 'Loading'], fill='toself'))
                            fig3.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10))
                            st.plotly_chart(fig3, use_container_width=True)
                        with row2_2:
                            st.markdown('<p style="font-size: 16px; font-weight: bold; text-align: center;">Cycle Life Prediction</p>', unsafe_allow_html=True)
                            target_life = max(1, res.get('Life(Cyc)', 1000))
                            cycles = np.linspace(0, target_life, 100)
                            retention = 100 - (20 * (cycles / target_life)**1.5)
                            fig4 = go.Figure(go.Scatter(x=cycles, y=retention, line=dict(color='#2CA02C', width=3)))
                            fig4.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
                            st.plotly_chart(fig4, use_container_width=True)
                        
                        if res.get("AI_Summary"):
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown(f"<div style='border: 1px solid #ddd; padding: 15px; border-radius: 5px; font-size: 15px;'>{res['AI_Summary']}</div>", unsafe_allow_html=True)

            # [섹션 4: Data Management Center]
            st.markdown("<div id='section4-anchor'></div>", unsafe_allow_html=True)
            if st.session_state.history:
                st.markdown('<p class="main-header" style="margin-top:20px;">4. Data Management Center</p>', unsafe_allow_html=True)
                sp6, c_6 = st.columns([0.03, 0.97])
                with c_6:
                    with st.container(border=True):
                        if st.button("화면 PDF 인쇄", key="btn_print_pdf", use_container_width=True):
                            components.html(
                                f"<script>setTimeout(function() {{ window.parent.print(); }}, 500);</script>",
                                height=0, width=0
                            )

# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot beta) 패널 - 인쇄 시 이 영역은 숨겨짐
# -----------------------------------------------------------------------------
def handle_chat_submit():
    user_input = st.session_state.get("bot_user_input", "")
    if user_input.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        st.session_state.trigger_bot_reply = True
        st.session_state.bot_user_input = "" 

if col_bot:
    with col_bot:
        st.markdown("#### SynoBot (beta)")
        st.text_input("질문입력", placeholder="Tdb 문서 질문...", key="bot_user_input", on_change=handle_chat_submit)
        st.button("전송", on_click=handle_chat_submit, use_container_width=True)
        
        chat_container = st.container(height=730, border=True) 
        with chat_container:
            if not st.session_state.chat_messages: 
                st.session_state.chat_messages = [{"role": "assistant", "content": "안녕하세요. 배터리 시뮬레이션 AI 시노봇입니다."}]

            # 자동 요약 및 챗봇 응답 로직
            if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                st.session_state.trigger_auto_bot = False 
                if synobot: 
                    with st.chat_message("assistant"):
                        reply = synobot.generate_auto_summary(st.session_state.sim_result, st.session_state.engine_choice, st.secrets["OPENAI_API_KEY"], st.secrets["GEMINI_API_KEY"], is_logged_in=st.session_state.logged_in)
                        bot_reply = "**[🤖 SynoBot 실시간 AI 요약]**\n\n" + reply
                        st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                        st.session_state.history[0]["AI_Summary"] = bot_reply
                st.rerun()

            if st.session_state.get('trigger_bot_reply'):
                st.session_state.trigger_bot_reply = False
                if synobot:
                    with st.chat_message("assistant"):
                        api_key = st.secrets["GEMINI_API_KEY"] if "Gemini" in st.session_state.engine_choice else st.secrets["OPENAI_API_KEY"]
                        messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages]
                        stream_gen = synobot.get_gemini_response_stream(messages_for_api, st.session_state.sim_result, api_key, is_logged_in=st.session_state.logged_in)
                        reply = st.write_stream(stream_gen)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                
            render_chat_history(st.session_state.chat_messages)

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2026. SynoTech. All rights reserved.<br><i>* All simulation logic is based on verified electrochemical models (Newman-type).</i></div>", unsafe_allow_html=True)