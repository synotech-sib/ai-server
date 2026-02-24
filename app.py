import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import hashlib
import io
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components 

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
st.set_page_config(page_title="SynoCore Pro Max 2.4", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden !important; display: none !important;} 
    header {visibility: hidden !important; display: none !important;}
    
    .main .block-container {
        max-width: 1500px !important; 
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: auto; 
    }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 60px; }
    .syno-title { color: #1A729A; font-size: 44px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #D35400; font-size: 20px; font-weight: bold; padding-top: 16px; }
    
    div.st-key-btn_home_overlay {
        margin-top: -60px !important; opacity: 0 !important; z-index: 999 !important;
        height: 60px !important; width: 350px !important; overflow: hidden !important;
    }
    div.st-key-btn_home_overlay button { height: 100% !important; width: 100% !important; cursor: pointer !important; }
    
    /* 기본 버튼 디자인 */
    div[data-testid="stButton"] > button, div[data-testid="stFormSubmitButton"] > button, div[data-testid="stPopover"] > button {
        height: 40px !important; background-color: #1A729A !important; color: white !important; 
        font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100% !important; border: none !important;
    }

    /* VIP DB 센터 하단 텍스트 링크 전용 버튼 (한줄 통합) */
    div.st-key-btn_my_db_scroll button {
        background: transparent !important; border: none !important; box-shadow: none !important;
        display: inline-flex !important; padding: 0 !important; height: auto !important; min-height: 0 !important;
    }
    div.st-key-btn_my_db_scroll button p { color: #333 !important; font-weight: bold !important; font-size: 15px !important; margin: 0 !important; }
    div.st-key-btn_my_db_scroll button p span { text-decoration: underline !important; }
    
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; border-bottom: 2px solid #1A729A; padding-bottom: 5px; }
    .param-label { font-size: 14px; font-weight: 600; color: #444; margin-bottom: 2px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 설정 및 캐싱 적용 (로그인 속도 개선)
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = st.secrets.get("ADMIN_PW", "Please_Set_Password_In_Secrets")

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

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
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default

# -----------------------------------------------------------------------------
# ✉️ [이메일 발송 시스템 + 관리자 알림 추가]
# -----------------------------------------------------------------------------
def get_smtp_server():
    sender_password = st.secrets.get("EMAIL_PASSWORD", "")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("wschoi@synotech.co.kr", sender_password.replace(" ", ""))
    return server

def send_verification_email(to_email, code):
    try:
        msg = MIMEMultipart(); msg['From'] = "SynoCore <synocore@synotech.co.kr>"; msg['To'] = to_email; msg['Subject'] = "[SynoCore Pro] 회원가입 인증번호"
        msg.attach(MIMEText(f"인증번호 : {code}\n\n위 6자리를 입력해 주시기 바랍니다.", 'plain', 'utf-8'))
        server = get_smtp_server(); server.send_message(msg); server.quit()
        return "SUCCESS"
    except Exception as e: return str(e)

def send_welcome_email(to_email, user_name):
    try:
        msg = MIMEMultipart(); msg['From'] = "SynoCore <synocore@synotech.co.kr>"; msg['To'] = to_email; msg['Subject'] = "[SynoCore Pro Max] 가입 완료 안내"
        msg.attach(MIMEText(f"{user_name}님, 가입이 완료되었습니다. 서비스를 이용해 보세요.", 'plain', 'utf-8'))
        server = get_smtp_server(); server.send_message(msg); server.quit()
        return True
    except Exception: return False

def send_admin_notification(subject, body_text):
    try:
        msg = MIMEMultipart(); msg['From'] = "SynoCore System <synocore@synotech.co.kr>"; msg['To'] = "wschoi@synotech.co.kr"; msg['Subject'] = f"🚨 [Admin Alert] {subject}"
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
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
    for p in peaks: dqdv += np.exp(-(v_axis - (float(p) - (float(v_tc) * 0.015)))**2 / (2 * 0.05**2)) * 15
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
                for k in ['Cap(mAh/g)', 'Volt(V)', 'C_Load', 'C_Press', 'C_Act', 'C_Bin', 'C_Con', 'N/P Ratio', 'A_Press', 'A_Act', 'A_Bin', 'A_Con', 'E/C Ratio', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: 
                    row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
                time_str = str(row_dict.get('Time', '')).strip()
                row_dict['Time'] = time_str if time_str and time_str != "nan" else (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
        return hist[::-1]
    except: return []

def save_chat_log(email, workspace, role, content):
    if GSheetsConnection is None: return
    safe_email = email if email else "guest"
    safe_ws = workspace if workspace else "general_user"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try: chat_df = conn.read(spreadsheet=URL_LOGS, worksheet="ChatLogs", ttl=0)
        except: chat_df = pd.DataFrame(columns=["Time", "Workspace", "Email", "Role", "Message"])
        new_row = pd.DataFrame([{"Time": (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S"), "Workspace": safe_ws, "Email": safe_email, "Role": role, "Message": content}])
        updated_df = new_row if chat_df.empty else pd.concat([chat_df, new_row], ignore_index=True)
        conn.update(spreadsheet=URL_LOGS, worksheet="ChatLogs", data=updated_df)
    except: pass

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 모듈 
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'general_user', 'user_vip_name': None, 'is_admin': False, 'user_tier': "",  
    'admin_view': None, 'admin_ws': None, 'chat_messages': [], 'trigger_auto_bot': False, 'trigger_bot_reply': False,
    'bot_user_input': "", 'scroll_to_result': False, 'scroll_to_data': False, 'acc_step': 1
}

for key, val in default_vars.items():
    if key not in st.session_state: st.session_state[key] = val

is_pro = st.session_state.logged_in

h_l, h_r = st.columns([0.72, 0.28], gap="small") 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">2.4 (beta)</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False; st.session_state.show_profile = False; st.rerun()

if not is_pro:
    with h_r:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="small") 
        with c1.popover("🔑 Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                if st.form_submit_button("로그인", use_container_width=True):
                    df_u = get_user_db_cached()
                    u_id_clean = u_id.strip().lower()
                    
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'admin_master', 'user_tier': 'Admin'})
                        st.session_state.history = load_user_history(u_id_clean, 'admin_master')
                        st.session_state.chat_messages = [{"role": "assistant", "content": f"- 안녕하세요 {ADMIN_USERS[u_id_clean]}님. [관리자 모드] 브리핑을 시작하겠습니다."}]
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hash_password(u_pw))] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            promax_flag = valid['ProMax_Req'].values[0] if 'ProMax_Req' in valid.columns else 'N'
                            if promax_flag == 'Out': st.error("탈퇴 처리된 계정입니다.")
                            else:
                                domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                                target_ws = vip_map.get(domain, 'general_user')
                                st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'workspace': target_ws, 'user_tier': "Pro Max" if str(promax_flag).upper() == 'Y' else "Pro"})
                                st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                                st.session_state.chat_messages = [{"role": "assistant", "content": f"- 안녕하세요 {valid['Name'].values[0]}님. 시노코어 SIB 설계 브리핑을 시작합니다."}]
                                st.rerun()
                        else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        with c2:
            if st.button("계정 가입 ㅣ Pro Mode", use_container_width=True): st.session_state.show_reg = not st.session_state.show_reg; st.rerun()
else:
    with h_r:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 
        r_my, r_out = st.columns([1, 1], gap="small")
        with r_my:
            if st.button("My 계정", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        with r_out:
            if st.button("Logout", use_container_width=True): 
                for key, val in default_vars.items(): st.session_state[key] = val
                st.rerun()
        
        # 🔥 헤더 한 줄 통합 UI 적용
        c_align = st.columns([1])
        with c_align[0]:
            if st.session_state.user_tier == "Pro Max" and st.session_state.workspace not in ['admin_master', 'general_user']:
                if st.button(f"👤 {st.session_state.user_name} (Pro Max) :blue[[{st.session_state.workspace.capitalize()} DB Center]]", key="btn_my_db_scroll", use_container_width=True):
                    st.session_state.scroll_to_data = True
            else:
                st.markdown(f"<div style='text-align: right; font-weight: bold; color: #333; font-size: 15px; margin-top: 5px;'>👤 {st.session_state.user_name} ({st.session_state.user_tier})</div>", unsafe_allow_html=True)

st.markdown("---")

# 🔥 모바일 방어 - URL 파라미터 동기화 로직
def sync_s_to_n(s_key, n_key, p_key=None): 
    st.session_state[n_key] = st.session_state[s_key]
    if p_key: st.query_params[p_key] = st.session_state[s_key]

def sync_n_to_s(s_key, n_key, p_key=None): 
    st.session_state[s_key] = st.session_state[n_key]
    if p_key: st.query_params[p_key] = st.session_state[n_key]

def change_acc_step(step): st.session_state.acc_step = step

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 & 봇 UI 구조 
# -----------------------------------------------------------------------------
col_left, col_main, col_bot = st.columns([0.02, 0.70, 0.28], gap="small")

with col_left: st.empty() 

with col_main:
    # --- 가입 영역 ---
    if st.session_state.show_reg and not st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">📝 계정 가입 (Pro Mode)</p>', unsafe_allow_html=True)
            if st.session_state.reg_stage == 0:
                e_in = st.text_input("1. 회사 이메일 주소")
                if st.button("인증번호 발송", use_container_width=True):
                    v_code = str(random.randint(100000, 999999))
                    if send_verification_email(e_in, v_code) == "SUCCESS": 
                        st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
            elif st.session_state.reg_stage == 1:
                v_in = st.text_input("인증번호 6자리 입력")
                if st.button("인증 확인", use_container_width=True):
                    if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
            elif st.session_state.reg_stage == 2:
                p1, p2 = st.columns(2); pw1 = p1.text_input("Password", type="password"); pw2 = p2.text_input("Password 확인", type="password") 
                c1, c2 = st.columns(2); n_name = c1.text_input("이름"); n_comp = c2.text_input("Company")
                c3, c4 = st.columns(2); n_dept = c3.text_input("부서"); n_job = c4.text_input("직책")
                c5, c6 = st.columns(2); n_phone = c5.text_input("연락처"); n_purpose = c6.text_input("사용용도")
                is_vip_request = st.checkbox(":red[네, Pro Max Mode로 가입을 신청합니다.]")
                agree_sec = st.checkbox("보안 및 개인정보 처리 사항 동의 (필수)")
                
                if st.button("가입신청 완료", disabled=not (pw1 and pw1==pw2 and n_name and agree_sec), use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "Dept": n_dept, "Job": n_job, "Phone": n_phone, "Purpose": n_purpose, "ProMax_Req": "Y" if is_vip_request else "N", "RegDate": (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")}])
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                    st.cache_data.clear(); send_welcome_email(st.session_state.temp_email, n_name)
                    send_admin_notification("신규 회원 가입 알림", f"이름: {n_name}\n회사: {n_comp}\n목적: {n_purpose}\nProMax 신청: {'Y' if is_vip_request else 'N'}")
                    st.success("가입 완료!"); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

    # --- 프로필 및 탈퇴 영역 ---
    if st.session_state.get('show_profile') and st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
            df_u = get_user_db_cached(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
            c1, c2 = st.columns([1, 1])
            m_pw = c1.text_input("새 Password", type="password")
            current_tier = "Pro Max" if u_row.get('ProMax_Req', 'N') == 'Y' else "Pro"
            m_tier = c2.radio("계정 권한 (Pro / Pro Max)", ["Pro", "Pro Max"], index=1 if current_tier == "Pro Max" else 0, horizontal=True)
            
            if st.button("개인정보 수정 완료", use_container_width=True):
                conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                df_update.at[idx, 'ProMax_Req'] = 'Y' if m_tier == "Pro Max" else 'N'
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.cache_data.clear()
                
                if current_tier == "Pro" and m_tier == "Pro Max":
                    send_admin_notification("Pro Max 등급업 승인 요청", f"사용자: {st.session_state.user_email}\n관리자 패널 VIPs 시트에서 도메인을 추가해 주셔야 활성화됩니다.")
                
                st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()
            
            st.markdown("---")
            if st.checkbox("⚠️ 탈퇴 신청 (체크 시 활성화)"):
                del_col1, del_col2 = st.columns([0.7, 0.3])
                del_reason = del_col1.text_input("탈퇴 사유 입력", placeholder="탈퇴사유를 기입해 주세요.", label_visibility="collapsed")
                if del_col2.button("탈퇴 확인", use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                    df_update.at[idx, 'ProMax_Req'] = 'Out' # Soft Delete
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.cache_data.clear()
                    send_admin_notification("회원 탈퇴 발생", f"계정: {st.session_state.user_email}\n사유: {del_reason}")
                    for key, val in default_vars.items(): st.session_state[key] = val
                    st.rerun()

    # --- 메인 시뮬레이터 패널 시작 ---
    with st.container(height=950, border=False):
        st.markdown("<div id='main-scroll-anchor'></div>", unsafe_allow_html=True) 
        
        # [섹션 1] Material Selection
        with st.container(border=True):
            st.markdown(f'<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
            physical_ws = "material_list" if st.session_state.workspace == "general_user" else st.session_state.workspace
            df_vip = load_cloud_data_cached(URL_MATS, physical_ws) if is_pro and st.session_state.workspace != "general_user" else pd.DataFrame()
            _dfs = []
            if not df_vip.empty: tmp_vip = df_vip.copy(); tmp_vip['Is_VIP'] = True; _dfs.append(tmp_vip.iloc[::-1])
            if not mat_df_public.empty: tmp_pub = mat_df_public.copy(); tmp_pub['Is_VIP'] = False; _dfs.append(tmp_pub)
            mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

            m1, m2, m3, m4 = st.columns(4)
            cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["Sample Cathode"]
            ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist() if not mat_df.empty else ["Sample Anode"]
            vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist() if not mat_df.empty else []
            
            # 🔥 공식 파트너사 인증 뱃지 로직
            def format_mat_name(name): 
                prefix = "💎 " if name in vip_names else ""
                if any(p in name for p in ["Tiamat", "Altris", "HiNa"]): prefix += "☑️ "
                return f"{prefix}{name}"
            
            with m1: cat_sel = st.selectbox("**Cathode**", cat_list, format_func=format_mat_name)
            with m2: ano_sel = st.selectbox("**Anode**", ano_list, format_func=format_mat_name)
            with m3: st.selectbox("**Electrolyte**", ["Sample Elec"])
            with m4: st.selectbox("**Separator**", ["Sample Sep"])
            
            row = mat_df[mat_df['Name']==cat_sel].iloc[0] if not mat_df.empty and cat_sel in cat_list else pd.Series()
            init_vals = {
                "cap": safe_float(row.get('Cap_Def'), 160.0), "volt": safe_float(row.get('Volt_Def'), 3.05), "den": safe_float(row.get('Den_Def'), 4.5), "life": safe_float(row.get('Life_Def'), 4000.0),
                "c_lod": safe_float(row.get('Load_Def'), 14.0), "c_press": 2.50, "c_act": 96.0, "c_bin": 2.0, "c_con": 2.0,
                "np": 1.10, "a_press": 1.60, "a_act": 95.0, "a_bin": 2.5, "a_con": 2.5,
                "ec": 3.5, "te": 160.0, "tc": 1.0, "tl": 2000.0 
            }

        # 🔥 세션 & URL 파라미터 초기화
        qp = st.query_params
        for k, v in init_vals.items():
            param_val = float(qp[k]) if k in qp else v
            if f"{k}_s" not in st.session_state: st.session_state[f"{k}_s"] = param_val
            if f"{k}_n" not in st.session_state: st.session_state[f"{k}_n"] = param_val

        # 🔥 지능형 아코디언 UI 적용 (Step 1 ~ 3)
        st.markdown('<p class="main-header" style="margin-top:20px;">2. Cell Design Parameters</p>', unsafe_allow_html=True)
        
        with st.expander(f"{'✅ ' if st.session_state.acc_step > 1 else ''}Step 1. 소재 물성 설정 (Material Specs)", expanded=(st.session_state.acc_step == 1)):
            s1, s2, s3, s4 = st.columns(4)
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
                st.markdown("<p class='param-label'>True Density (g/cc)</p>", unsafe_allow_html=True)
                d1, d2 = st.columns([0.7, 0.3])
                d1.slider("Den_S", 1.0, 5.0, step=0.1, key="den_s", on_change=sync_s_to_n, args=("den_s", "den_n", "den"), label_visibility="collapsed")
                d2.number_input("Den_N", 1.0, 5.0, step=0.01, key="den_n", on_change=sync_n_to_s, args=("den_s", "den_n", "den"), label_visibility="collapsed")
            with s4:
                st.markdown("<p class='param-label'>Base Life (Cycles)</p>", unsafe_allow_html=True)
                lf1, lf2 = st.columns([0.7, 0.3])
                lf1.slider("Life_S", 500.0, 10000.0, step=100.0, key="life_s", on_change=sync_s_to_n, args=("life_s", "life_n", "life"), label_visibility="collapsed")
                lf2.number_input("Life_N", 500.0, 10000.0, step=10.0, key="life_n", on_change=sync_n_to_s, args=("life_s", "life_n", "life"), label_visibility="collapsed")
            st.button("다음 단계: 공정 설계 ➡️", key="btn_next_1", on_click=change_acc_step, args=(2,))

        with st.expander(f"{'✅ ' if st.session_state.acc_step > 2 else ''}Step 2. 셀 공정 설계 (Process Parameters)", expanded=(st.session_state.acc_step == 2)):
            p1, p2, p3 = st.columns(3)
            with p1:
                st.markdown("<p class='param-label'>Areal Loading (mg/cm2)</p>", unsafe_allow_html=True)
                cl1, cl2 = st.columns([0.7, 0.3])
                cl1.slider("CLod_S", 5.0, 45.0, step=1.0, key="c_lod_s", on_change=sync_s_to_n, args=("c_lod_s", "c_lod_n", "c_lod"), label_visibility="collapsed")
                cl2.number_input("CLod_N", 5.0, 45.0, step=0.1, key="c_lod_n", on_change=sync_n_to_s, args=("c_lod_s", "c_lod_n", "c_lod"), label_visibility="collapsed")
                
                # 🔥 수식 툴팁 추가
                st.markdown("<p class='param-label'>Press Density (g/cc)</p>", unsafe_allow_html=True, help="합제 밀도. 높을수록 부피당 에너지 밀도가 상승하나 전해액 침투(Porosity)가 저하됩니다.")
                cpr1, cpr2 = st.columns([0.7, 0.3])
                cpr1.slider("CPress_S", 1.5, 4.0, step=0.1, key="c_press_s", on_change=sync_s_to_n, args=("c_press_s", "c_press_n", "c_press"), label_visibility="collapsed")
                cpr2.number_input("CPress_N", 1.5, 4.0, step=0.01, key="c_press_n", on_change=sync_n_to_s, args=("c_press_s", "c_press_n", "c_press"), label_visibility="collapsed")
                
            with p2:
                st.markdown("<p class='param-label'>N/P Ratio</p>", unsafe_allow_html=True, help="N/P Ratio = (Anode Capacity) / (Cathode Capacity). 나트륨 석출 방지를 위해 1.05 이상 권장.")
                n1, n2 = st.columns([0.7, 0.3])
                n1.slider("NP_S", 0.95, 1.50, step=0.05, key="np_s", on_change=sync_s_to_n, args=("np_s", "np_n", "np"), label_visibility="collapsed")
                n2.number_input("NP_N", 0.95, 1.50, step=0.01, key="np_n", on_change=sync_n_to_s, args=("np_s", "np_n", "np"), label_visibility="collapsed")
                
                st.markdown("<p class='param-label'>E/C Ratio (g/Ah)</p>", unsafe_allow_html=True, help="전해액/용량 비율. 2.5 이하시 수명 급감.")
                e1, e2 = st.columns([0.7, 0.3])
                e1.slider("EC_S", 1.0, 8.0, step=0.1, key="ec_s", on_change=sync_s_to_n, args=("ec_s", "ec_n", "ec"), label_visibility="collapsed")
                e2.number_input("EC_N", 1.0, 8.0, step=0.01, key="ec_n", on_change=sync_n_to_s, args=("ec_s", "ec_n", "ec"), label_visibility="collapsed")
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

        # 🔥 섹션 5 명칭 변경 반영 [5. Simulation & Analysis]
        st.markdown("<div id='section5'></div>", unsafe_allow_html=True)
        if st.session_state.get('scroll_to_result'):
            components.html("<script>window.parent.document.getElementById('section5').scrollIntoView();</script>", height=0)
            st.session_state.scroll_to_result = False

        with st.container(border=True):
            st.markdown('<p class="main-header">5. Simulation & Analysis</p>', unsafe_allow_html=True)
            if st.button("🚀 RUN SIMULATION", use_container_width=True):
                cell_v = max(0.1, st.session_state.volt_s - (0.1 + (st.session_state.tc_s * 0.02)))
                res_whkg = ((st.session_state.cap_s * (96.0/100) * cell_v) / 2.5) * max(0.5, 1.0 - (st.session_state.tc_s * 0.015))
                life_cyc = int(st.session_state.life_s * (0.95 ** st.session_state.tc_s))
                cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
                v_axis, dqdv = get_dqdv(cat_sel, st.session_state.tc_s, mat_df)
                
                log_data = {
                    "Time": cur_time, "Cathode": cat_sel, "Cap(mAh/g)": st.session_state.cap_s, "Volt(V)": st.session_state.volt_s,
                    "N/P Ratio": st.session_state.np_s, "C-rate": st.session_state.tc_s, "Wh/kg": round(res_whkg, 1), 
                    "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc, "dq_x": v_axis, "dq_y": dqdv
                }
                
                st.session_state.history.insert(0, log_data); st.session_state.sim_result = log_data; 
                st.session_state.trigger_auto_bot = True; st.session_state.scroll_to_result = True 
                st.rerun()

            if st.session_state.history:
                res = st.session_state.history[0]
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg'] - st.session_state.te_s, 1):+} Wh/kg")
                r3.metric("Cell Voltage", f"{res['Cell_V']} V")
                r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc")
                
                g1, g2 = st.columns(2)
                with g1:
                    fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                    fig1.update_layout(title="Discharge Profile", height=260, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig1, use_container_width=True)
                with g2:
                    fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                    fig2.update_layout(title="dQ/dV Profile", height=260, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig2, use_container_width=True)

        # 🔥 섹션 6 명칭 변경 반영 [6. Data Management Center]
        st.markdown("<div id='section6'></div>", unsafe_allow_html=True)
        if st.session_state.get('scroll_to_data'):
            components.html("<script>window.parent.document.getElementById('section6').scrollIntoView();</script>", height=0)
            st.session_state.scroll_to_data = False

        if is_pro and st.session_state.history:
            with st.container(border=True):
                st.markdown('<p class="main-header">6. Data Management Center</p>', unsafe_allow_html=True)
                # 데이터 매니지먼트 테이블 로직 (기존과 동일하게 최신순 정렬 유지)
                df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y', 'AI_Briefing'], errors='ignore')
                st.dataframe(df_history, use_container_width=True)

# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot) AI 패널 
# -----------------------------------------------------------------------------
if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (Beta)")
        chat_container = st.container(height=800, border=True) 
        with chat_container:
            for message in reversed(st.session_state.chat_messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

# 🔥 7. 푸터 (학술 보증 텍스트 추가)
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2026. SynoTech. All rights reserved.<br><i>* All simulation logic is based on verified electrochemical models (Newman-type) and official material data from partners.</i></div>", unsafe_allow_html=True)