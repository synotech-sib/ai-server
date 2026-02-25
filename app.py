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
# 1. 페이지 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore Pro Max", layout="wide")

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
    
    div[data-testid="stSelectbox"] label p { font-size: 16px !important; font-weight: bold !important; color: #222 !important; }
    div[data-testid="stTextInput"] label, div[data-testid="stTextInput"] label * { font-size: 16px !important; font-weight: 500 !important; color: #222 !important; } 
    div[data-testid="stCheckbox"] label p { font-size: 15px !important; color: #222 !important; font-weight: normal !important; } 
    
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #222 !important; margin-bottom: 12px !important; border-bottom: 2px solid #1A729A; padding-bottom: 5px; }
    .param-label { font-size: 16px !important; font-weight: bold !important; color: #333 !important; margin-bottom: 4px !important; }
    div[data-testid="stExpander"] summary p { font-size: 18px !important; font-weight: normal !important; color: #1A729A !important; }
    
    div[data-testid="stVerticalBlock"]:has(#main-scroll-anchor) { scrollbar-width: none !important; -ms-overflow-style: none !important;  }
    div[data-testid="stVerticalBlock"]:has(#main-scroll-anchor)::-webkit-scrollbar { display: none !important; }

    /* PDF 인쇄 제어 */
    @media print {
        header, footer, [data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(1),
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) { display: none !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) { width: 100% !important; max-width: 100% !important; flex: 0 0 100% !important; }
        button { display: none !important; }
        div[data-testid="element-container"]:has(#section4-anchor),
        div[data-testid="element-container"]:has(#section4-anchor) ~ * { display: none !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    }

    @media (max-width: 768px) {
        .header-container { flex-direction: column; align-items: flex-start; height: auto; margin-bottom: 10px; }
        .syno-title { font-size: 38px !important; margin-right: 0px; }
        .syno-subtitle { font-size: 16px !important; padding-top: 5px; }
        div[data-testid="stPopoverBody"] { width: 90vw !important; max-width: 450px !important; }
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

def hash_password(password): return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=600)
def load_cloud_data_cached(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws, ttl=600)
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

@st.cache_data(ttl=600)
def get_user_db_cached():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
    except Exception: return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def get_user_db(): return get_user_db_cached()
def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default

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
        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
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
    'engine_choice': "Gemini 1.5 Flash (기본/쾌속)"  # 엔진 스위치 기본값
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
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">Pro Max 2.6</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False; st.session_state.show_profile = False; st.session_state.admin_view = None; st.session_state.admin_ws = None; st.rerun()

if not is_pro:
    with h_r:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="small") 
        with c1.popover("🔑 Login", use_container_width=True):
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
                            st.session_state.chat_messages = [{"role": "assistant", "content": f"- 안녕하세요 {ADMIN_USERS[u_id_clean]}님. [관리자 모드] 통합 브리핑을 시작하겠습니다."}]
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
                                    welcome_msg = f"안녕하세요 {valid['Name'].values[0]}님. [{target_ws.capitalize()} DB Center] VIP 워크스페이스로 전환되었습니다." if target_ws != 'general_user' else f"안녕하세요 {valid['Name'].values[0]}님. SIB 설계 브리핑을 시작합니다."
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
            if st.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
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
# 👑 최고 관리자 패널 (듀얼 엔진 스위치 탑재 + 파라미터 검증 기능 추가)
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    if st.session_state.admin_view is not None or st.session_state.show_profile is False:
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
            
            # [신규 추가: AI 엔진 마스터 스위치]
            st.session_state.engine_choice = st.radio(
                "🧠 AI 엔진 마스터 스위치",
                ["Gemini 1.5 Flash (기본/쾌속)", "OpenAI GPT-4o (비상/정밀)"],
                index=0 if "Gemini" in st.session_state.engine_choice else 1,
                horizontal=True
            )
            st.info("📂 연동된 Tdb 외부 경로: `SynoBot_db/` 폴더 내 전체 .txt 및 .pdf 파일")
            st.markdown("---")
            
            # [신규 추가] 🔍 Tdb 파라미터 실시간 검증
            st.markdown("### 🔍 Tdb 파라미터 실시간 검증")
            col_t, col_b = st.columns([0.8, 0.2])
            refresh_clicked = col_b.button("🔄 새로고침", key="admin_refresh_btn")

            if refresh_clicked or "param_diff_table" not in st.session_state:
                with st.spinner("Tdb 문서와 현재 파라미터를 비교 분석 중입니다..."):
                    try:
                        cur_cat = st.session_state.get('sel_cat_m', '알 수 없음')
                        cur_ano = st.session_state.get('sel_ano_m', '알 수 없음')
                        cur_cap = st.session_state.get('cap_s', 160.0)
                        cur_volt = st.session_state.get('volt_s', 3.05)
                        cur_te = st.session_state.get('te_s', 100.0)

                        current_materials = f"- Cathode: {cur_cat}\n- Anode: {cur_ano}\n- Cap: {cur_cap} mAh/g\n- Volt: {cur_volt} V\n- Target Energy: {cur_te} Wh/kg"

                        api_key = st.secrets["GEMINI_API_KEY"] if "Gemini" in st.session_state.engine_choice else st.secrets["OPENAI_API_KEY"]
                        
                        if synobot:
                            diff_result = synobot.check_parameter_discrepancy(current_materials, st.session_state.engine_choice, api_key)
                            st.session_state.param_diff_table = pd.DataFrame(diff_result)
                    except Exception as e:
                        st.error(f"검증 오류: {e}")

            if "param_diff_table" in st.session_state and not st.session_state.param_diff_table.empty:
                def highlight_mismatch(row):
                    is_mismatch = '불일치' in str(row['상태']) or '⚠️' in str(row['상태'])
                    return ['background-color: #ffe6e6' if is_mismatch else '' for _ in row]
                styled_df = st.session_state.param_diff_table.style.apply(highlight_mismatch, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            st.markdown("---")
            
            a1, a2, a3, a4, a5 = st.columns(5)
            if a1.button("👥 유저 관리 DB", use_container_width=True): st.session_state.admin_view = 'users'; st.session_state.admin_ws = 'Users'; st.rerun()
            if a2.button("🔋 소재 DB", use_container_width=True): st.session_state.admin_view = 'mats'; st.session_state.admin_ws = 'admin_master'; st.rerun()
            if a3.button("⚙️ 파라미터 DB", use_container_width=True): st.session_state.admin_view = 'param'; st.session_state.admin_ws = 'param_config'; st.rerun()
            if a4.button("💾 로그 DB", use_container_width=True): st.session_state.admin_view = 'logs'; st.session_state.admin_ws = 'myData'; st.rerun()
            if a5.button("💬 시노봇 로그 DB", use_container_width=True): st.session_state.admin_view = 'chat'; st.session_state.admin_ws = 'ChatLogs'; st.rerun()

            if st.session_state.admin_view:
                st.markdown("---")
                st.markdown(f'<p class="sub-header-bold">🛠️ 인라인 데이터베이스 편집기</p>', unsafe_allow_html=True)
                
                if st.session_state.admin_view == 'users': target_url = URL_USERS; ws_options = ["Users", "VIPs"]
                elif st.session_state.admin_view == 'mats': target_url = URL_MATS; ws_options = ["admin_master", "general_user"] + get_vip_list_exact()
                elif st.session_state.admin_view == 'param': target_url = URL_PARAM; ws_options = ["param_config"]
                elif st.session_state.admin_view == 'logs': target_url = URL_LOGS; ws_options = ["myData"]
                elif st.session_state.admin_view == 'chat': target_url = URL_LOGS; ws_options = ["ChatLogs"] 
                
                if len(ws_options) > 1:
                    sel_ws_admin = st.selectbox("📂 편집할 워크스페이스(탭) 선택", ws_options, index=ws_options.index(st.session_state.admin_ws) if st.session_state.admin_ws in ws_options else 0)
                    if sel_ws_admin != st.session_state.admin_ws: st.session_state.admin_ws = sel_ws_admin; st.rerun()
                
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'admin_master':
                        st.info("ℹ️ 'admin_master'은 공용 및 모든 VIP 데이터가 취합된 **읽기 전용(Read-only)** 통합 뷰입니다.")
                        vips = get_vip_list_exact(); dfs = []
                        for v in vips:
                            tmp = load_cloud_data(target_url, v)
                            if not tmp.empty: tmp['Source (VIP)'] = v; dfs.append(tmp)
                        tmp_public = load_cloud_data(target_url, "material_list")
                        if not tmp_public.empty: tmp_public['Source (VIP)'] = 'Public'; dfs.append(tmp_public)
                        df_admin = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                        st.dataframe(df_admin, use_container_width=True)
                    else:
                        read_ws = "material_list" if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'general_user' else st.session_state.admin_ws
                        df_admin = conn.read(spreadsheet=target_url, worksheet=read_ws, ttl=600) 
                        df_display = df_admin.copy()
                        if st.session_state.admin_view in ['logs', 'chat'] and 'Time' in df_display.columns: df_display = df_display.sort_values(by='Time', ascending=False).reset_index(drop=True)
                        elif st.session_state.admin_view == 'users' and 'RegDate' in df_display.columns: df_display = df_display.sort_values(by='RegDate', ascending=False).reset_index(drop=True)
                        edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}")
                        if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                            conn.update(spreadsheet=target_url, worksheet=read_ws, data=edited_df.fillna("")); st.cache_data.clear(); st.success("저장 완료!")
                except Exception as e: pass

# -----------------------------------------------------------------------------
# 5. 메인 UI 및 시뮬레이터 본문
# -----------------------------------------------------------------------------
col_left, col_main, col_bot = st.columns([0.02, 0.70, 0.28], gap="small")

with col_left: st.empty() 

with col_main:
    # --- 가입 및 프로필 영역 ---
    if st.session_state.show_reg and not st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">📝 계정 가입 (Pro Mode)</p>', unsafe_allow_html=True)
            if st.session_state.reg_stage == 0:
                with st.form("form_reg_email", border=False):
                    e_in = st.text_input("1. 회사 이메일 주소")
                    if st.form_submit_button("인증번호 발송", use_container_width=True):
                        if not e_in or "@" not in e_in: st.error("올바른 이메일 주소를 입력해주세요.")
                        else:
                            v_code = str(random.randint(100000, 999999))
                            with st.spinner("📧 이메일을 발송 중입니다..."):
                                email_res = send_verification_email(e_in, v_code)
                                if email_res == "SUCCESS": st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
                                else: st.error(f"🚨 이메일 발송 실패 상세 원인: {email_res}")
            elif st.session_state.reg_stage == 1:
                st.info(f"📧 [{st.session_state.temp_email}]로 인증번호가 발송되었습니다.")
                with st.form("form_reg_code", border=False):
                    v_in = st.text_input("인증번호 6자리 입력")
                    if st.form_submit_button("인증 확인", use_container_width=True):
                        if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
                        else: st.error("인증번호가 일치하지 않습니다.")
            elif st.session_state.reg_stage == 2:
                p1, p2 = st.columns(2)
                pw1 = p1.text_input("2. Password", type="password"); pw2 = p2.text_input("Password 확인", type="password") 
                c1, c2 = st.columns(2); n_name = c1.text_input("3. 이름"); n_comp = c2.text_input("4. Company (회사명)")
                c3, c4 = st.columns(2); n_dept = c3.text_input("5. 부서"); n_job = c4.text_input("6. 직책/담당업무")
                c5, c6 = st.columns(2); n_phone = c5.text_input("7. 연락처"); n_purpose = c6.text_input("8. 사용용도")
                
                st.markdown("---")
                st.markdown("#### 💎 Pro Max 계정 승인 요청 (선택)")
                st.info("Pro Max 계정은 일반 Pro와 달리 귀사만의 독립적인 소재/공정 데이터베이스(VIP 전용 DB Center)를 별도 구축해 드리는 기업 맞춤형 서비스입니다.")
                is_vip_request = st.checkbox("네, Pro Max Mode로 가입을 신청합니다. (관리자 승인 필요)") 
                
                st.markdown("---")
                st.markdown("#### 🔒 보안 및 개인정보 처리 방침 (필수)")
                terms_text = """[SynoCore Pro Max 개인정보 수집 및 이용 동의]
1. 수집 항목: 이름, 회사명, 부서, 직책, 연락처, 이메일, 사용용도
2. 이용 목적: B2B 서비스 제공, 본인 확인, VIP DB 권한 부여, 고객 대응
3. 보유 기간: 회원 탈퇴 시까지 영구 안전 보관 (탈퇴 즉시 보안 정책에 따라 파기 처리)"""
                with st.expander("개인정보 처리 방침 상세 내용 보기"):
                    st.markdown(f"<div style='background-color: #f4f6f9; border: 1px solid #ced4da; border-radius: 5px; padding: 15px; font-size: 15px; color: #212529; height: 120px; overflow-y: auto; line-height: 1.6;'>{terms_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                agree_sec = st.checkbox("위 보안 및 개인정보 처리 사항을 확인하였으며, 이에 동의합니다. (필수)")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("가입신청 완료", disabled=not (pw1 and pw1==pw2 and n_name and agree_sec), use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "Dept": n_dept, "Job": n_job, "Phone": n_phone, "Purpose": n_purpose, "ProMax_Req": "Y" if is_vip_request else "N", "RegDate": datetime.now(KST).strftime("%Y-%m-%d")}])
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                    
                    if is_vip_request:
                        domain = st.session_state.temp_email.split('@')[1].split('.')[0].lower(); vip_df = load_cloud_data(URL_USERS, "VIPs")
                        if domain not in [str(x).lower().strip() for x in vip_df['Company'].dropna()]:
                            conn.update(spreadsheet=URL_USERS, worksheet="VIPs", data=pd.concat([vip_df, pd.DataFrame([{"Company": domain}])], ignore_index=True))
                            try: conn.update(spreadsheet=URL_MATS, worksheet=domain, data=pd.DataFrame(columns=["Name", "Category", "Cap_Def", "Volt_Def", "Den_Def"]))
                            except: pass
                            
                    st.cache_data.clear(); send_welcome_email(st.session_state.temp_email, n_name)
                    send_admin_notification("신규 회원 가입 알림", f"이름: {n_name}\n회사: {n_comp}\n목적: {n_purpose}\nProMax 신청: {'Y' if is_vip_request else 'N'}")
                    st.success("가입신청 완료! 로그인 해주세요.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

    if st.session_state.get('show_profile') and st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
            if not st.session_state.get('is_admin', False):
                df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
                st.markdown(f"**이메일(ID):** {st.session_state.user_email}")
                
                c1, c2 = st.columns([1, 1]); m_pw = c1.text_input("새 Password (변경 시에만 입력)", type="password")
                current_tier = "Pro Max" if str(u_row.get('ProMax_Req', 'N')).upper() == 'Y' else "Pro"
                m_tier = c2.radio("계정 권한 (Pro / Pro Max)", ["Pro", "Pro Max"], index=1 if current_tier == "Pro Max" else 0, horizontal=True)
                
                c3, c4 = st.columns(2)
                m_name = c3.text_input("이름", value=u_row.get('Name', ''))
                m_comp = c4.text_input("Company", value=u_row.get('Company', ''))
                
                c5, c6 = st.columns(2)
                m_dept = c5.text_input("부서", value=u_row.get('Dept', ''))
                m_job = c6.text_input("담당업무", value=u_row.get('Job', ''))
                
                c7, c8 = st.columns(2)
                m_phone = c7.text_input("연락처", value=u_row.get('Phone', ''))
                m_purpose = c8.text_input("사용용도", value=u_row.get('Purpose', ''))
                
                if st.button("개인정보 수정 완료", use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                    if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                    df_update.at[idx, 'Name'] = m_name; df_update.at[idx, 'Company'] = m_comp; df_update.at[idx, 'Dept'] = m_dept
                    df_update.at[idx, 'Job'] = m_job; df_update.at[idx, 'Phone'] = m_phone; df_update.at[idx, 'Purpose'] = m_purpose; df_update.at[idx, 'ProMax_Req'] = 'Y' if m_tier == "Pro Max" else 'N'
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.cache_data.clear()
                    
                    if current_tier == "Pro" and m_tier == "Pro Max":
                        send_admin_notification("Pro Max 등급업 승인 요청", f"계정: {st.session_state.user_email}\n관리자 패널에서 승인이 필요합니다.")
                        
                    st.session_state.user_name = m_name; st.session_state.user_tier = m_tier; st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()
                
                st.markdown("---")
                del_check = st.checkbox("⚠️ 탈퇴 신청 (체크 시 활성화)")
                if del_check:
                    del_col1, del_col2 = st.columns([0.7, 0.3])
                    del_reason = del_col1.text_input("탈퇴 사유 입력", placeholder="탈퇴사유를 기입해 주세요.", label_visibility="collapsed")
                    if del_col2.button("탈퇴 확인", key="btn_withdraw", use_container_width=True):
                        conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                        idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                        df_update.at[idx, 'ProMax_Req'] = 'Out' 
                        df_update.at[idx, 'Purpose'] = f"[탈퇴] {del_reason}" if del_reason else "[탈퇴] 사유 없음"
                        conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.cache_data.clear()
                        send_admin_notification("회원 탈퇴 발생", f"계정: {st.session_state.user_email}\n사유: {del_reason}")
                        if "session_token" in st.query_params: del st.query_params["session_token"]
                        st.success("탈퇴 처리되었습니다. 이용해 주셔서 감사합니다."); time.sleep(1.5)
                        for key, val in default_vars.items(): st.session_state[key] = val
                        st.rerun()

    with st.container(height=1000, border=False):
        st.markdown("<div id='main-scroll-anchor'></div>", unsafe_allow_html=True) 
        
        # [섹션 1]
        st.markdown('<p class="main-header" style="margin-top:10px;">1. Material Selection</p>', unsafe_allow_html=True)
        sp1, c_1 = st.columns([0.03, 0.97])
        with c_1:
            with st.container(border=True):
                physical_ws = "material_list" if st.session_state.workspace == "general_user" else st.session_state.workspace
                df_vip = load_cloud_data(URL_MATS, physical_ws) if is_pro and st.session_state.workspace != "general_user" else pd.DataFrame()
                _dfs = []
                if not df_vip.empty: tmp_vip = df_vip.copy(); tmp_vip['Is_VIP'] = True; _dfs.append(tmp_vip.iloc[::-1])
                if not mat_df_public.empty: tmp_pub = mat_df_public.copy(); tmp_pub['Is_VIP'] = False; _dfs.append(tmp_pub)
                mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

                m1, m2, m3, m4 = st.columns(4)
                cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["Sample Cathode"]
                ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist() if not mat_df.empty else ["Sample Anode"]
                vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist() if not mat_df.empty else []
                
                def format_mat_name(name): 
                    prefix = "💎 " if name in vip_names else ""
                    if any(p in name for p in ["Tiamat", "Altris", "HiNa"]): prefix += "☑️ "
                    return f"{prefix}{name}"
                
                with m1: cat_sel = st.selectbox("Cathode", cat_list, format_func=format_mat_name, key="sel_cat_m")
                with m2: ano_sel = st.selectbox("Anode", ano_list, format_func=format_mat_name, key="sel_ano_m")
                with m3: st.selectbox("Electrolyte", ["Sample Elec"], key="sel_ele_m")
                with m4: st.selectbox("Separator", ["Sample Sep"], key="sel_sep_m")
                
                row = mat_df[mat_df['Name']==cat_sel].iloc[0] if not mat_df.empty and cat_sel in cat_list else pd.Series()
                init_vals = {
                    "cap": safe_float(row.get('Cap_Def'), 160.0), "volt": safe_float(row.get('Volt_Def'), 3.05), "c_den": safe_float(row.get('Den_Def'), 4.5), 
                    "a_den": 2.1, "life": safe_float(row.get('Life_Def'), 4000.0),
                    "c_lod": safe_float(row.get('Load_Def'), 14.0), "c_press": 2.50, "c_act": 96.0, "c_bin": 2.0, "c_con": 2.0, "c_foil": 15.0,
                    "np": 1.10, "a_press": 1.60, "a_act": 95.0, "a_bin": 2.5, "a_con": 2.5, "a_foil": 15.0,
                    "ec": 3.5, "sep_thick": 16.0, "te": 160.0, "tc": 1.0, "tl": 2000.0 
                }

        qp = st.query_params
        for k, v in init_vals.items():
            param_val = float(qp[k]) if k in qp else v
            if f"{k}_s" not in st.session_state: st.session_state[f"{k}_s"] = param_val
            if f"{k}_n" not in st.session_state: st.session_state[f"{k}_n"] = param_val

        expert = True if is_pro else False

        st.markdown('<p class="main-header" style="margin-top:20px;">2. Process Parameters</p>', unsafe_allow_html=True)
        sp2, c_2 = st.columns([0.03, 0.97])
        with c_2:
            with st.expander(f"{'✅ ' if st.session_state.acc_step > 1 else ''}Step 1. 소재 물성 설정 (Material Specs)", expanded=(st.session_state.acc_step == 1)):
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown("<p class='param-label'>Capacity (mAh/g)</p>", unsafe_allow_html=True)
                    v1, v2 = st.columns([0.7, 0.3])
                    v1.slider("Cap_S", 100.0, 250.0, step=1.0, key="cap_s", on_change=sync_s_to_n, args=("cap_s", "cap_n", "cap"), label_visibility="collapsed")
                    v2.number_input("Cap_N", 100.0, 250.0, step=0.1, key="cap_n", on_change=sync_n_to_s, args=("cap_s", "cap_n", "cap"), label_visibility="collapsed")
                with s2:
                    st.markdown("<p class='param-label'>Voltage (V)</p>", unsafe_allow_html=True)
                    vv1, vv2 = st.columns([0.7, 0.3])
                    vv1.slider("Volt_S", 2.0, 4.5, step=0.1, key="volt_s", on_change=sync_s_to_n, args=("volt_s", "volt_n", "volt"), label_visibility="collapsed")
                    vv2.number_input("Volt_N", 2.0, 4.5, step=0.01, key="volt_n", on_change=sync_n_to_s, args=("volt_s", "volt_n", "volt"), label_visibility="collapsed")
                with s3:
                    st.markdown("<p class='param-label'>Base Life (Cycles)</p>", unsafe_allow_html=True)
                    lf1, lf2 = st.columns([0.7, 0.3])
                    lf1.slider("Life_S", 500.0, 10000.0, step=100.0, key="life_s", on_change=sync_s_to_n, args=("life_s", "life_n", "life"), label_visibility="collapsed", disabled=not expert)
                    lf2.number_input("Life_N", 500.0, 10000.0, step=10.0, key="life_n", on_change=sync_n_to_s, args=("life_s", "life_n", "life"), label_visibility="collapsed", disabled=not expert)
                
                st.markdown("<br>", unsafe_allow_html=True) 
                
                s4, s5, s6 = st.columns(3)
                with s4:
                    st.markdown("<p class='param-label'>Cathode True Den (g/cc)</p>", unsafe_allow_html=True)
                    d1, d2 = st.columns([0.7, 0.3])
                    d1.slider("CDen_S", 1.0, 5.0, step=0.1, key="c_den_s", on_change=sync_s_to_n, args=("c_den_s", "c_den_n", "c_den"), label_visibility="collapsed", disabled=not expert)
                    d2.number_input("CDen_N", 1.0, 5.0, step=0.01, key="c_den_n", on_change=sync_n_to_s, args=("c_den_s", "c_den_n", "c_den"), label_visibility="collapsed", disabled=not expert)
                with s5:
                    st.markdown("<p class='param-label'>Anode True Den (g/cc)</p>", unsafe_allow_html=True)
                    ad1, ad2 = st.columns([0.7, 0.3])
                    ad1.slider("ADen_S", 1.0, 5.0, step=0.1, key="a_den_s", on_change=sync_s_to_n, args=("a_den_s", "a_den_n", "a_den"), label_visibility="collapsed", disabled=not expert)
                    ad2.number_input("ADen_N", 1.0, 5.0, step=0.01, key="a_den_n", on_change=sync_n_to_s, args=("a_den_s", "a_den_n", "a_den"), label_visibility="collapsed", disabled=not expert)
                with s6:
                    st.empty() 
                    
                st.button("다음 단계: 공정 설계 ➡️", key="btn_next_1", on_click=change_acc_step, args=(2,))

            with st.expander(f"{'✅ ' if st.session_state.acc_step > 2 else ''}Step 2. 셀 공정 설계 (Process Parameters)", expanded=(st.session_state.acc_step == 2)):
                p1, p2, p3 = st.columns(3)
                with p1:
                    st.markdown('<p class="sub-header-bold">(A) Cathode Process</p>', unsafe_allow_html=True)
                    st.markdown("<p class='param-label'>Areal Loading (mg/cm2)</p>", unsafe_allow_html=True)
                    cl1, cl2 = st.columns([0.7, 0.3])
                    cl1.slider("CLod_S", 5.0, 45.0, step=1.0, key="c_lod_s", on_change=sync_s_to_n, args=("c_lod_s", "c_lod_n", "c_lod"), label_visibility="collapsed")
                    cl2.number_input("CLod_N", 5.0, 45.0, step=0.1, key="c_lod_n", on_change=sync_n_to_s, args=("c_lod_s", "c_lod_n", "c_lod"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label' title='합제 밀도. 높을수록 부피당 에너지 밀도가 상승하나 전해액 침투(Porosity)가 저하됩니다.'>Press Density (g/cc) ❔</p>", unsafe_allow_html=True)
                    cpr1, cpr2 = st.columns([0.7, 0.3])
                    cpr1.slider("CPress_S", 1.5, 4.0, step=0.1, key="c_press_s", on_change=sync_s_to_n, args=("c_press_s", "c_press_n", "c_press"), label_visibility="collapsed", disabled=not expert)
                    cpr2.number_input("CPress_N", 1.5, 4.0, step=0.01, key="c_press_n", on_change=sync_n_to_s, args=("c_press_s", "c_press_n", "c_press"), label_visibility="collapsed", disabled=not expert)
                    
                    c_poro = (1 - st.session_state.c_press_s / st.session_state.c_den_s) * 100 if st.session_state.c_den_s > 0 else 0
                    st.markdown(f"<div style='background:#eaf2f8; padding:8px 10px; border-radius:5px; margin-top:5px; margin-bottom:25px;'><span style='color:#1A729A; font-weight:bold; font-size:14px;'>📊 양극 기공률 (Porosity): {c_poro:.1f}%</span></div>", unsafe_allow_html=True)
                    
                    st.markdown("<p class='param-label'>Al Foil Thickness (μm)</p>", unsafe_allow_html=True)
                    cf1, cf2 = st.columns([0.7, 0.3])
                    cf1.slider("CFoil_S", 8.0, 30.0, step=1.0, key="c_foil_s", on_change=sync_s_to_n, args=("c_foil_s", "c_foil_n", "c_foil"), label_visibility="collapsed")
                    cf2.number_input("CFoil_N", 8.0, 30.0, step=0.1, key="c_foil_n", on_change=sync_n_to_s, args=("c_foil_s", "c_foil_n", "c_foil"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Active Ratio (%)</p>", unsafe_allow_html=True)
                    ca1, ca2 = st.columns([0.7, 0.3])
                    ca1.slider("CAct_S", 80.0, 99.0, step=0.5, key="c_act_s", on_change=sync_s_to_n, args=("c_act_s", "c_act_n", "c_act"), label_visibility="collapsed")
                    ca2.number_input("CAct_N", 80.0, 99.0, step=0.1, key="c_act_n", on_change=sync_n_to_s, args=("c_act_s", "c_act_n", "c_act"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Binder Ratio (%)</p>", unsafe_allow_html=True)
                    cb1, cb2 = st.columns([0.7, 0.3])
                    cb1.slider("CBin_S", 0.0, 10.0, step=0.5, key="c_bin_s", on_change=sync_s_to_n, args=("c_bin_s", "c_bin_n", "c_bin"), label_visibility="collapsed")
                    cb2.number_input("CBin_N", 0.0, 10.0, step=0.1, key="c_bin_n", on_change=sync_n_to_s, args=("c_bin_s", "c_bin_n", "c_bin"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Conductive Carbon (%)</p>", unsafe_allow_html=True)
                    cc1, cc2 = st.columns([0.7, 0.3])
                    cc1.slider("CCon_S", 0.0, 10.0, step=0.5, key="c_con_s", on_change=sync_s_to_n, args=("c_con_s", "c_con_n", "c_con"), label_visibility="collapsed")
                    cc2.number_input("CCon_N", 0.0, 10.0, step=0.1, key="c_con_n", on_change=sync_n_to_s, args=("c_con_s", "c_con_n", "c_con"), label_visibility="collapsed")
                    
                with p2:
                    st.markdown('<p class="sub-header-bold">(B) Anode Process</p>', unsafe_allow_html=True)
                    st.markdown("<p class='param-label' title='N/P Ratio = (Anode Capacity) / (Cathode Capacity). 나트륨 석출 방지를 위해 1.05 이상 권장.'>N/P Ratio ❔</p>", unsafe_allow_html=True)
                    n1, n2 = st.columns([0.7, 0.3])
                    n1.slider("NP_S", 0.95, 1.50, step=0.05, key="np_s", on_change=sync_s_to_n, args=("np_s", "np_n", "np"), label_visibility="collapsed")
                    n2.number_input("NP_N", 0.95, 1.50, step=0.01, key="np_n", on_change=sync_n_to_s, args=("np_s", "np_n", "np"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Press Density (g/cc)</p>", unsafe_allow_html=True)
                    apr1, apr2 = st.columns([0.7, 0.3])
                    apr1.slider("APress_S", 0.8, 2.0, step=0.1, key="a_press_s", on_change=sync_s_to_n, args=("a_press_s", "a_press_n", "a_press"), label_visibility="collapsed", disabled=not expert)
                    apr2.number_input("APress_N", 0.8, 2.0, step=0.01, key="a_press_n", on_change=sync_n_to_s, args=("a_press_s", "a_press_n", "a_press"), label_visibility="collapsed", disabled=not expert)
                    
                    a_poro = (1 - st.session_state.a_press_s / st.session_state.a_den_s) * 100 if st.session_state.a_den_s > 0 else 0
                    st.markdown(f"<div style='background:#eaf2f8; padding:8px 10px; border-radius:5px; margin-top:5px; margin-bottom:25px;'><span style='color:#1A729A; font-weight:bold; font-size:14px;'>📊 음극 기공률 (Porosity): {a_poro:.1f}%</span></div>", unsafe_allow_html=True)
                    
                    st.markdown("<p class='param-label'>Al Foil Thickness (μm)</p>", unsafe_allow_html=True)
                    af1, af2 = st.columns([0.7, 0.3])
                    af1.slider("AFoil_S", 8.0, 30.0, step=1.0, key="a_foil_s", on_change=sync_s_to_n, args=("a_foil_s", "a_foil_n", "a_foil"), label_visibility="collapsed")
                    af2.number_input("AFoil_N", 8.0, 30.0, step=0.1, key="a_foil_n", on_change=sync_n_to_s, args=("a_foil_s", "a_foil_n", "a_foil"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Active Ratio (%)</p>", unsafe_allow_html=True)
                    aa1, aa2 = st.columns([0.7, 0.3])
                    aa1.slider("AAct_S", 80.0, 99.0, step=0.5, key="a_act_s", on_change=sync_s_to_n, args=("a_act_s", "a_act_n", "a_act"), label_visibility="collapsed")
                    aa2.number_input("AAct_N", 80.0, 99.0, step=0.1, key="a_act_n", on_change=sync_n_to_s, args=("a_act_s", "a_act_n", "a_act"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Binder Ratio (%)</p>", unsafe_allow_html=True)
                    ab1, ab2 = st.columns([0.7, 0.3])
                    ab1.slider("ABin_S", 0.0, 10.0, step=0.5, key="a_bin_s", on_change=sync_s_to_n, args=("a_bin_s", "a_bin_n", "a_bin"), label_visibility="collapsed")
                    ab2.number_input("ABin_N", 0.0, 10.0, step=0.1, key="a_bin_n", on_change=sync_n_to_s, args=("a_bin_s", "a_bin_n", "a_bin"), label_visibility="collapsed")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Conductive Carbon (%)</p>", unsafe_allow_html=True)
                    ac1, ac2 = st.columns([0.7, 0.3])
                    ac1.slider("ACon_S", 0.0, 10.0, step=0.5, key="a_con_s", on_change=sync_s_to_n, args=("a_con_s", "a_con_n", "a_con"), label_visibility="collapsed")
                    ac2.number_input("ACon_N", 0.0, 10.0, step=0.1, key="a_con_n", on_change=sync_n_to_s, args=("a_con_s", "a_con_n", "a_con"), label_visibility="collapsed")

                with p3:
                    st.markdown('<p class="sub-header-bold">(C) Cell & Electrolyte</p>', unsafe_allow_html=True)
                    st.markdown("<p class='param-label' title='전해액/용량 비율. 2.5 이하시 수명 급감 위험.'>E/C Ratio (g/Ah) ❔</p>", unsafe_allow_html=True)
                    e1, e2 = st.columns([0.7, 0.3])
                    e1.slider("EC_S", 1.0, 8.0, step=0.1, key="ec_s", on_change=sync_s_to_n, args=("ec_s", "ec_n", "ec"), label_visibility="collapsed", disabled=not expert)
                    e2.number_input("EC_N", 1.0, 8.0, step=0.01, key="ec_n", on_change=sync_n_to_s, args=("ec_s", "ec_n", "ec"), label_visibility="collapsed", disabled=not expert)
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                    st.markdown("<p class='param-label'>Separator Thickness (μm)</p>", unsafe_allow_html=True)
                    st1, st2 = st.columns([0.7, 0.3])
                    st1.slider("SepThick_S", 5.0, 30.0, step=1.0, key="sep_thick_s", on_change=sync_s_to_n, args=("sep_thick_s", "sep_thick_n", "sep_thick"), label_visibility="collapsed")
                    st2.number_input("SepThick_N", 5.0, 30.0, step=0.1, key="sep_thick_n", on_change=sync_n_to_s, args=("sep_thick_s", "sep_thick_n", "sep_thick"), label_visibility="collapsed")
                    
                st.button("다음 단계: 타겟 성능 ➡️", key="btn_next_2", on_click=change_acc_step, args=(3,))

            with st.expander("Step 3. 타겟 성능 설정 (Target Settings)", expanded=(st.session_state.acc_step == 3)):
                t1, t2, t3 = st.columns(3)
                with t1: 
                    st.markdown('<p class="sub-header-bold">Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
                    te1, te2 = st.columns([0.7, 0.3])
                    te1.slider("TE_S", 100.0, 250.0, step=5.0, key="te_s", on_change=sync_s_to_n, args=("te_s", "te_n", "te"), label_visibility="collapsed")
                    te2.number_input("TE_N", 100.0, 250.0, step=1.0, key="te_n", on_change=sync_n_to_s, args=("te_s", "te_n", "te"), label_visibility="collapsed")
                with t2: 
                    st.markdown('<p class="sub-header-bold">C-rate</p>', unsafe_allow_html=True)
                    tc1, tc2 = st.columns([0.7, 0.3])
                    tc1.slider("TC_S", 0.1, 10.0, step=0.5, key="tc_s", on_change=sync_s_to_n, args=("tc_s", "tc_n", "tc"), label_visibility="collapsed")
                    tc2.number_input("TC_N", 0.1, 10.0, step=0.1, key="tc_n", on_change=sync_n_to_s, args=("tc_s", "tc_n", "tc"), label_visibility="collapsed")
                with t3: 
                    st.markdown('<p class="sub-header-bold">Cycle Life</p>', unsafe_allow_html=True)
                    tl1, tl2 = st.columns([0.7, 0.3])
                    tl1.slider("TL_S", 500.0, 10000.0, step=100.0, key="tl_s", on_change=sync_s_to_n, args=("tl_s", "tl_n", "tl"), label_visibility="collapsed")
                    tl2.number_input("TL_N", 500.0, 10000.0, step=10.0, key="tl_n", on_change=sync_n_to_s, args=("tl_s", "tl_n", "tl"), label_visibility="collapsed")

        # 변수 할당
        v_cap, v_volt, v_c_den, v_a_den, v_life = st.session_state.cap_s, st.session_state.volt_s, st.session_state.c_den_s, st.session_state.a_den_s, st.session_state.life_s
        v_c_lod, v_c_press, v_c_act, v_c_bin, v_c_con, v_c_foil = st.session_state.c_lod_s, st.session_state.c_press_s, st.session_state.c_act_s, st.session_state.c_bin_s, st.session_state.c_con_s, st.session_state.c_foil_s
        v_np, v_a_press, v_a_act, v_a_bin, v_a_con, v_a_foil = st.session_state.np_s, st.session_state.a_press_s, st.session_state.a_act_s, st.session_state.a_bin_s, st.session_state.a_con_s, st.session_state.a_foil_s
        v_ec, v_sep_thick = st.session_state.ec_s, st.session_state.sep_thick_s
        v_te, v_tc, v_tl = st.session_state.te_s, st.session_state.tc_s, st.session_state.tl_s

        st.markdown("<div id='section5'></div>", unsafe_allow_html=True)
        if st.session_state.get('scroll_to_result'):
            components.html("<script>window.parent.document.getElementById('section5').scrollIntoView();</script>", height=0)
            st.session_state.scroll_to_result = False

        # [섹션 3] 
        st.markdown('<p class="main-header" style="margin-top:20px;">3. Simulation & Analysis</p>', unsafe_allow_html=True)
        sp5, c_5 = st.columns([0.03, 0.97])
        with c_5:
            with st.container(border=True):
                if st.button("🚀 RUN SIMULATION", key="btn_run_m", use_container_width=True):
                    cell_v = max(0.1, v_volt - (0.1 + (v_tc * 0.02)))
                    
                    c_areal_cap = v_c_lod * (v_c_act / 100.0) * v_cap / 1000.0 
                    a_areal_cap = c_areal_cap * v_np
                    a_cap_default = 300.0 
                    a_lod = a_areal_cap / (a_cap_default * (v_a_act / 100.0)) * 1000.0 
                    
                    m_cat = v_c_lod
                    m_ano = a_lod
                    m_c_foil = v_c_foil * 0.27 
                    m_a_foil = v_a_foil * 0.27 
                    m_sep = v_sep_thick * 0.05 
                    m_elec = c_areal_cap * v_ec 
                    
                    total_mass = m_cat + m_ano + m_c_foil + m_a_foil + m_sep + m_elec
                    effective_mass = total_mass / 0.8  
                    
                    t_cat = (v_c_lod / v_c_press) * 10.0
                    t_ano = (a_lod / v_a_press) * 10.0
                    total_thick = t_cat + t_ano + v_c_foil + v_a_foil + v_sep_thick
                    effective_thick = total_thick / 0.9  
                    
                    res_whkg = (c_areal_cap * cell_v) / effective_mass * 1000.0 * max(0.5, 1.0 - (v_tc * 0.015))
                    whl = (c_areal_cap * cell_v) / effective_thick * 10000.0 * max(0.5, 1.0 - (v_tc * 0.015))
                    
                    life_cyc = int(v_life * (0.95 ** v_tc))
                    cur_time = datetime.now(KST).strftime("%m-%d %H:%M:%S")
                    v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                    
                    log_data = {
                        "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel, 
                        "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), 
                        "C_Load": round(v_c_lod, 1), "C_Press": round(v_c_press, 2), "C_Act": round(v_c_act, 1), "C_Bin": round(v_c_bin, 1), "C_Con": round(v_c_con, 1),
                        "N/P Ratio": round(v_np, 2), "A_Press": round(v_a_press, 2), "A_Act": round(v_a_act, 1), "A_Bin": round(v_a_bin, 1), "A_Con": round(v_a_con, 1),
                        "E/C Ratio": round(v_ec, 2), "C-rate": round(v_tc, 1), 
                        "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), 
                        "Life(Cyc)": life_cyc, "dq_x": v_axis, "dq_y": dqdv, "AI_Briefing": ""
                    }
                    
                    with st.spinner("🚀 물리 엔진 연산 중..."):
                        time.sleep(0.5) 
                        st.session_state.history.insert(0, log_data); st.session_state.sim_result = log_data; 
                        st.session_state.trigger_auto_bot = True 
                        st.session_state.scroll_to_result = True 
                        st.rerun()
                        
                if st.session_state.history:
                    selected_idx = 0
                    if "log_table_sel" in st.session_state:
                        sel_rows = st.session_state.log_table_sel.get("selection", {}).get("rows", [])
                        if sel_rows: selected_idx = sel_rows[0]
                    if selected_idx >= len(st.session_state.history): selected_idx = 0
                        
                    res = st.session_state.history[selected_idx]
                    
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg'] - v_te, 1):+} Wh/kg")
                    r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off")
                    r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{round(res['Cell_V'] - v_volt, 2):+} V", delta_color="inverse")
                    r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{int(res['Life(Cyc)'] - v_tl):+} Cyc")
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    g1, sp_g1, g2, sp_g2, g3 = st.columns([1, 0.08, 1, 0.08, 1])
                    
                    with g1:
                        st.markdown('<p style="font-size: 16px; font-weight: bold; color: #222; text-align: center; margin-bottom: 10px;">Discharge Profile</p>', unsafe_allow_html=True)
                        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                        fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9")
                        st.plotly_chart(fig1, use_container_width=True)
                        
                    with g2:
                        st.markdown('<p style="font-size: 16px; font-weight: bold; color: #222; text-align: center; margin-bottom: 10px;">dQ/dV Profile</p>', unsafe_allow_html=True)
                        fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                        fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9")
                        st.plotly_chart(fig2, use_container_width=True)
                        
                    with g3:
                        st.markdown('<p style="font-size: 16px; font-weight: bold; color: #222; text-align: center; margin-bottom: 10px;">Cell Performance</p>', unsafe_allow_html=True)
                        fig3 = go.Figure(go.Scatterpolar(r=[min(100, res.get('Wh/kg', 0)/2.5), min(100, res.get('C-rate', 1)*20), min(100, res.get('Life(Cyc)', 0)/50), min(100, res.get('Cell_V', 0)*25), min(100, res.get('C_Load', 0)*4)], theta=['Energy', 'Power', 'Life', 'Voltage', 'Loading'], fill='toself', line=dict(color='#E4B526', width=2)))
                        fig3.update_layout(polar=dict(bgcolor="#f4f6f9", radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10))
                        st.plotly_chart(fig3, use_container_width=True)
                    
                    if res.get("AI_Briefing"):
                        st.markdown("<br>", unsafe_allow_html=True)
                        show_ai = st.checkbox("**:red[펼쳐보기]** 🤖 위 시뮬레이션 데이터 분석 결과를 정리해 보여 드립니다.", value=False, key=f"chk_ai_report_{res['Time']}")
                            
                        if show_ai:
                            with st.container(border=True):
                                clean_briefing = res['AI_Briefing'].replace("아래는 주어진 데이터에 대한 분석 및 브리핑입니다.", "").strip()
                                st.markdown(f"<div style='font-size: 15px; color: #333; line-height: 1.6;'>{clean_briefing}</div>", unsafe_allow_html=True)

                    if len(st.session_state.history) > 0:
                        st.markdown("<br><p class='sub-header-bold' style='font-size: 16px !important;'>🕒 당일 시뮬레이션 누적 기록 (클릭하여 과거 결과 바로 조회 가능)</p>", unsafe_allow_html=True)
                        df_session = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y', 'AI_Briefing'], errors='ignore')
                        df_session.insert(0, 'No.', range(len(df_session), 0, -1))
                        try: st.dataframe(df_session, use_container_width=True, hide_index=True, key="log_table_sel", on_select="rerun", selection_mode="single-row")
                        except TypeError: st.dataframe(df_session, use_container_width=True, hide_index=True)

        st.markdown("<div id='section6'></div>", unsafe_allow_html=True)
        if st.session_state.get('scroll_to_data'):
            components.html("<script>window.parent.document.getElementById('section6').scrollIntoView();</script>", height=0)
            st.session_state.scroll_to_data = False

        st.markdown("<div id='section4-anchor'></div>", unsafe_allow_html=True)

        # [섹션 4]
        if is_pro and st.session_state.history:
            st.markdown('<p id="section4-header" class="main-header" style="margin-top:20px;">4. Data Management Center</p>', unsafe_allow_html=True)
            sp6, c_6 = st.columns([0.03, 0.97])
            with c_6:
                with st.container(border=True):
                    st.caption("ℹ️ 표 안의 **[User Comment]** 셀을 더블클릭하여 해당 시뮬레이션에 대한 메모를 남기실 수 있습니다.")
                    db_df_all = pd.DataFrame(); selected_times = []
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        db_df_all = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                        if not db_df_all.empty and 'Email' in db_df_all.columns:
                            my_saved_data = db_df_all[(db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'general_user').isin([st.session_state.workspace, 'material_list']))]
                            if not my_saved_data.empty:
                                my_saved_data = my_saved_data.sort_values(by='Time', ascending=False)
                                df_display = my_saved_data.drop(columns=['Email', 'Workspace', 'dq_x', 'dq_y'], errors='ignore').copy()
                                df_display['User Comment'] = df_display.get('User Comment', "").fillna("")
                                df_display['Time'] = df_display['Time'].astype(str)
                                core_cols = ['Time', 'User Comment', 'Cathode', 'Anode']; other_cols = [c for c in df_display.columns if c not in core_cols]
                                df_display = df_display[core_cols + other_cols]; df_display.insert(0, "선택", False)
                                original_comments = df_display['User Comment'].tolist()
                                disabled_cols = [col for col in df_display.columns if col not in ["선택", "User Comment"]]
                                
                                edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, disabled=disabled_cols, column_config={"Time": st.column_config.TextColumn("Time", disabled=True), "User Comment": st.column_config.TextColumn("📝 코멘트 입력", width="large")})
                                
                                if edited_df['User Comment'].tolist() != original_comments:
                                    if 'User Comment' not in db_df_all.columns: db_df_all['User Comment'] = ""
                                    for idx, row in edited_df.iterrows():
                                        mask = (db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'general_user').isin([st.session_state.workspace, 'material_list'])) & (db_df_all['Time'] == row['Time'])
                                        if mask.any(): db_df_all.loc[mask, 'User Comment'] = row['User Comment']
                                    conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all); st.cache_data.clear()
                                selected_times = edited_df[edited_df["선택"] == True]["Time"].tolist()
                            else: st.info("클라우드 DB에 이전에 저장된 데이터가 없습니다.")
                    except Exception as e: st.warning("데이터베이스 연결에 실패했습니다.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    btn1, btn2, btn3, btn4 = st.columns(4)
                    
                    if btn1.button("💾 임시 기록 전체 저장", key="btn_save_my", use_container_width=True):
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                            new_records = []
                            for record in st.session_state.history:
                                if db_df.empty or db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == record['Time'])].empty:
                                    s_rec = record.copy(); s_rec['Email'] = st.session_state.user_email; s_rec['Workspace'] = st.session_state.workspace; s_rec['User Comment'] = ""; s_rec.pop('dq_x', None); s_rec.pop('dq_y', None)
                                    new_records.append(s_rec)
                                    
                            if new_records:
                                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame(new_records)], ignore_index=True)); st.cache_data.clear(); st.success(f"당일 임시 기록 {len(new_records)}건이 모두 클라우드에 영구 저장되었습니다!"); st.rerun() 
                            else:
                                st.warning("이미 모든 기록이 클라우드에 저장되어 있습니다.")
                        except Exception as e: st.error("저장 오류")

                    if btn2.button("🗑️ 선택 삭제", key="btn_del_sel", use_container_width=True):
                        if not selected_times: st.warning("항목을 체크해주세요.")
                        elif not db_df_all.empty:
                            mask = ~((db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'general_user').isin([st.session_state.workspace, 'material_list'])) & (db_df_all['Time'].isin(selected_times)))
                            conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all[mask]); st.cache_data.clear(); st.success("삭제 완료!"); st.rerun()

                    df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_export.to_excel(writer, index=False)
                        file_data = buffer.getvalue(); file_name = f"SynoCore_Logs_{datetime.now(KST).strftime('%m%d_%H%M')}.xlsx"; mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    except ImportError:
                        file_data = df_export.to_csv(index=False).encode('utf-8-sig'); file_name = f"SynoCore_Logs_{datetime.now(KST).strftime('%m%d_%H%M')}.csv"; mime_type = "text/csv"
                    btn3.download_button("📥 당일 엑셀 다운로드", data=file_data, file_name=file_name, mime=mime_type, key="btn_excel", use_container_width=True)

                    if btn4.button("📄 화면 PDF 인쇄", key="btn_print_pdf", use_container_width=True):
                        components.html("<script>window.parent.print();</script>", height=0)


# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot beta) 패널 [완벽한 역순 정렬 & 자동 스크롤 적용]
# -----------------------------------------------------------------------------
def handle_chat_submit():
    user_input = st.session_state.get("bot_user_input", "")
    if user_input.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        save_chat_log(st.session_state.user_email, st.session_state.workspace, "user", user_input)
        st.session_state.trigger_bot_reply = True
        st.session_state.bot_user_input = "" 

if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (beta)")
        
        c_in1, c_in2 = st.columns([0.75, 0.25])
        c_in1.text_input("질문입력", label_visibility="collapsed", placeholder="Tdb 문서나 SIB 기술에 대해 질문하세요...", key="bot_user_input", on_change=handle_chat_submit)
        c_in2.button("전송", on_click=handle_chat_submit, use_container_width=True, key="btn_chat_send")
        
        chat_container = st.container(height=730, border=True) 
        with chat_container:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            try:
                OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
                GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
            except Exception:
                st.warning("⚠️ `.streamlit/secrets.toml`에 API 키를 설정해주세요.")
                st.stop()

            if not st.session_state.chat_messages: 
                st.session_state.chat_messages = [{"role": "assistant", "content": "안녕하세요. 배터리 시뮬레이션 AI 시노봇입니다. 시뮬레이션 결과 뿐만 아니라 중간에도 질문해 주세요."}]

            # 1. 시뮬레이션 직후 자동 브리핑
            if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                st.session_state.trigger_auto_bot = False 
                if synobot: 
                    with st.chat_message("assistant"):
                        with st.spinner(f"{st.session_state.engine_choice.split(' ')[0]} 엔진으로 결과 분석 중..."):
                            try:
                                reply = synobot.generate_auto_briefing(st.session_state.sim_result, st.session_state.engine_choice, OPENAI_API_KEY, GEMINI_API_KEY)
                                bot_reply = f"📊 **[실시간 AI 진단 ({st.session_state.engine_choice.split(' ')[0]})]**\n\n" + reply
                                st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                                if st.session_state.history: st.session_state.history[0]["AI_Briefing"] = bot_reply
                                save_chat_log(st.session_state.user_email, st.session_state.workspace, "AI_auto", bot_reply)
                            except Exception as e: st.error(f"AI 브리핑 생성 오류: {e}")
                time.sleep(0.5); st.rerun()

            # 2. 챗봇 질문-응답 처리 및 스트리밍
            if st.session_state.get('trigger_bot_reply'):
                st.session_state.trigger_bot_reply = False
                
                if synobot:
                    with st.chat_message("assistant"):
                        with st.spinner("시노코어 기술 데이터베이스(Tdb) 분석 중..."):
                            try:
                                messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages]
                                api_key = GEMINI_API_KEY if "Gemini" in st.session_state.engine_choice else OPENAI_API_KEY
                                
                                if "Gemini" in st.session_state.engine_choice:
                                    stream_gen = synobot.get_gemini_response_stream(messages_for_api, st.session_state.sim_result, api_key)
                                else:
                                    stream_gen = synobot.get_openai_response_stream(messages_for_api, st.session_state.sim_result, api_key)

                                reply = st.write_stream(stream_gen)
                                
                                # 대화 기록에 답변 추가
                                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                                save_chat_log(st.session_state.user_email, st.session_state.workspace, "AI", reply)
                                
                            except Exception as e: st.error(f"AI 응답 오류: {e}")
                
                # 방금 추가된 최신 답변(마지막 요소)을 제외한 나머지를 역순으로 순회
                for message in reversed(st.session_state.chat_messages[:-1]):
                    with st.chat_message(message["role"]):
                        content = message["content"].replace("\n- ", "\n\n- ")
                        if content.startswith("- "): content = "- " + content[2:]
                        st.markdown(content)
                        
            else:
                # 일반 렌더링 시 (항상 완벽한 최신순 정렬)
                for message in reversed(st.session_state.chat_messages):
                    with st.chat_message(message["role"]):
                        content = message["content"].replace("\n- ", "\n\n- ")
                        if content.startswith("- "): content = "- " + content[2:]
                        st.markdown(content)

        # [스크롤 마법] 채팅 컨테이너가 렌더링 된 직후 무조건 맨 위(0)로 올리기
        components.html(
            """
            <script>
            var containers = window.parent.document.querySelectorAll('.stScrollToBottom, .stScrollableContainer, [data-testid="stVerticalBlock"]');
            if (containers && containers.length > 0) {
                containers.forEach(function(container) {
                    container.scrollTop = 0;
                });
            }
            </script>
            """,
            height=0
        )

# 7. 푸터 
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2026. SynoTech. All rights reserved.<br><i>* All simulation logic is based on verified electrochemical models (Newman-type) and official material data from partners.</i></div>", unsafe_allow_html=True)