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
st.set_page_config(page_title="SynoCore Pro Max 1.9 (beta)", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden !important; display: none !important;} 
    header {visibility: hidden !important; display: none !important;}
    a[href^="https://streamlit.io"] {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    .stApp > header {display: none !important;}
    .stApp [data-testid="stToolbar"] {display: none !important;}
    
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
        margin-top: -60px !important;
        opacity: 0 !important;
        z-index: 999 !important;
        height: 60px !important;
        width: 350px !important;
        overflow: hidden !important;
    }
    div.st-key-btn_home_overlay button { height: 100% !important; width: 100% !important; cursor: pointer !important; }
    
    div[data-testid="stMetric"] { 
        background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; 
        padding: 15px 15px 10px 15px; height: 120px; display: flex; flex-direction: column; justify-content: flex-start; 
    }
    div[data-testid="stMetricValue"] { font-size: 26px !important; color: #1A729A !important; margin-top: 5px; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; margin-top: 3px; }
    
    div[data-testid="stButton"] > button, div[data-testid="stFormSubmitButton"] > button {
        height: 40px !important; background-color: #1A729A !important; color: white !important; 
        font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100%; border: none !important;
        white-space: nowrap !important;
        padding: 0 5px !important;
    }

    div.st-key-btn_excel > button {
        height: 40px !important; background-color: #1A729A !important; color: white !important; 
        font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100%; border: 1px solid #155A7A !important;
        white-space: nowrap !important;
    }
    div.st-key-btn_excel > button:hover { background-color: #155A7A !important; border: 1px solid #104058 !important; }

    div.st-key-btn_del_sel > button {
        height: 40px !important; background-color: #D35400 !important; color: white !important; 
        font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100%; border: 1px solid #B04600 !important;
        white-space: nowrap !important;
    }
    div.st-key-btn_del_sel > button:hover { background-color: #B04600 !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 20px !important; 
    }
    
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; border-bottom: 2px solid #1A729A; padding-bottom: 5px; }
    .param-label { font-size: 14px; font-weight: 600; color: #444; margin-bottom: 2px; }
    
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 15px; padding-right: 5px; white-space: nowrap; }
    
    div[data-testid="stToggle"] {
        display: flex !important;
        justify-content: flex-end !important;
        margin-left: auto !important;
        float: right !important;
        width: 100% !important;
        padding: 0px !important;
        background-color: transparent !important; 
        border: none !important;
        margin-top: 5px !important;
    }
    div[data-testid="stToggle"] > label { 
        margin-bottom: 0px !important; font-size: 14px !important; color: #333 !important; 
        display: flex; justify-content: flex-end;
    }
    
    div[data-testid="stVerticalBlock"]:has(#main-scroll-anchor) {
        scrollbar-width: none !important; 
        -ms-overflow-style: none !important;  
    }
    div[data-testid="stVerticalBlock"]:has(#main-scroll-anchor)::-webkit-scrollbar {
        display: none !important; 
    }

    div[data-testid="stChatMessage"] {
        display: flex !important;
        flex-direction: column !important; 
        align-items: flex-start !important;
        gap: 5px !important;
        padding: 10px !important;
    }

    /* 🔥 모바일 최적화 CSS 추가 (제목 크기 및 로그인 팝업 깨짐 방지) */
    @media (max-width: 768px) {
        .header-container { flex-direction: column; align-items: flex-start; height: auto; margin-bottom: 10px; }
        .syno-title { font-size: 32px !important; margin-right: 0px; }
        .syno-subtitle { font-size: 16px !important; padding-top: 5px; }
        div[data-testid="stPopoverBody"] { width: 90vw !important; max-width: 450px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 설정
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = st.secrets.get("ADMIN_PW", "Please_Set_Password_In_Secrets")

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

def load_cloud_data(url, ws="Sheet1"):
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
    df = load_cloud_data(URL_USERS, "VIPs")
    return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()] if not df.empty and 'Company' in df.columns else []

mat_df_public = load_cloud_data(URL_MATS, "material_list")
param_df = load_cloud_data(URL_PARAM, "param_config")

sys_params = {}
if not param_df.empty and 'Parameter_ID' in param_df.columns:
    sys_params = param_df.set_index('Parameter_ID').to_dict('index')

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default

def safe_int(val, default):
    try: return int(float(val)) if val != "" and not pd.isna(val) else default
    except: return default

# -----------------------------------------------------------------------------
# ✉️ [이메일 발송 시스템] 
# -----------------------------------------------------------------------------
def send_verification_email(to_email, code):
    sender_email = "wschoi@synotech.co.kr"
    sender_password = st.secrets.get("EMAIL_PASSWORD", "여기에_16자리_앱비밀번호를_입력하세요")
    try:
        msg = MIMEMultipart()
        msg['From'] = f"SynoCore Admin <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "[SynoCore Pro] 회원가입 인증번호 안내"
        body = f"안녕하세요. SynoCore Pro Max 플랫폼 회원가입을 위한 인증번호 안내입니다.\n\n▶ 인증번호 : {code}\n\n위 인증번호 6자리를 회원가입 창에 입력해 주시기 바랍니다.\n감사합니다."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password.replace(" ", "")) 
        server.send_message(msg)
        server.quit()
        return True
    except Exception: return False

def send_welcome_email(to_email, user_name):
    sender_email = "wschoi@synotech.co.kr"
    sender_password = st.secrets.get("EMAIL_PASSWORD", "여기에_16자리_앱비밀번호를_입력하세요")
    try:
        msg = MIMEMultipart()
        msg['From'] = f"SynoCore Admin <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "[SynoCore Pro Max] 회원가입 완료 안내"
        body = f"안녕하세요 {user_name}님,\n\nSynoCore Pro Max 플랫폼의 회원가입이 성공적으로 완료되었습니다.\n이제 설정하신 계정으로 로그인하여 차세대 배터리 시뮬레이션 서비스를 이용해 보시기 바랍니다.\n\n감사합니다."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password.replace(" ", "")) 
        server.send_message(msg)
        server.quit()
        return True
    except Exception: return False

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
    for p in peaks:
        shifted_p = float(p) - (float(v_tc) * 0.015); dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email, workspace="material_list"):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
        if db_df.empty or 'Email' not in db_df.columns: return []
        my_logs = db_df[(db_df['Email'] == email) & (db_df.get('Workspace', 'material_list') == workspace)]
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None); row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'C_Load', 'C_Press', 'C_Act', 'C_Bin', 'C_Con', 'N/P Ratio', 'A_Press', 'A_Act', 'A_Bin', 'A_Con', 'E/C Ratio', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: 
                    row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
                
                time_str = str(row_dict.get('Time', '')).strip()
                if not time_str or time_str == "nan":
                    time_str = (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
                row_dict['Time'] = time_str 
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
        return hist[::-1]
    except: return []

def save_chat_log(email, workspace, role, content):
    if GSheetsConnection is None: return
    safe_email = email if email else "Guest"
    safe_ws = workspace if workspace else "None"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            chat_df = conn.read(spreadsheet=URL_LOGS, worksheet="ChatLogs", ttl=0)
        except Exception:
            chat_df = pd.DataFrame(columns=["Time", "Email", "Workspace", "Role", "Message"])
        new_row = pd.DataFrame([{
            "Time": (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S"),
            "Email": safe_email,
            "Workspace": safe_ws,
            "Role": role,
            "Message": content
        }])
        if chat_df.empty or 'Email' not in chat_df.columns:
            conn.update(spreadsheet=URL_LOGS, worksheet="ChatLogs", data=new_row)
        else:
            updated_df = pd.concat([chat_df, new_row], ignore_index=True)
            conn.update(spreadsheet=URL_LOGS, worksheet="ChatLogs", data=updated_df)
        st.cache_data.clear()
    except Exception: pass

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 모듈 
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'material_overall', 'user_vip_name': None, 'is_admin': False, 'user_tier': "",
    'admin_view': None, 'admin_ws': None, 'chat_messages': [], 
    'show_bot': True, 'trigger_auto_bot': False, 'trigger_bot_reply': False,
    'bot_user_input': "", 'scroll_to_result': False 
}

for key, val in default_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

h_l, h_r = st.columns([0.72, 0.28], gap="small") 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">1.9 (beta)</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False; st.session_state.show_profile = False
        st.session_state.admin_view = None; st.session_state.admin_ws = None; st.rerun()

with h_r:
    is_pro = st.session_state.logged_in
    if not is_pro:
        c1, c2 = st.columns([1, 1])
        with c1.popover("🔑 Login"):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                submit_login = st.form_submit_button("로그인", use_container_width=True)
                
                if submit_login:
                    df_u = get_user_db()
                    u_id_clean = u_id.strip().lower()
                    hashed_pw = hash_password(u_pw) if u_pw else ""
                    
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_overall', 'user_tier': 'Admin'})
                        st.session_state.history = load_user_history(u_id_clean, 'material_overall'); st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            promax_flag = valid['ProMax_Req'].values[0] if 'ProMax_Req' in valid.columns else 'N'
                            if promax_flag == 'Out':
                                st.error("탈퇴 처리된 계정입니다.")
                            else:
                                domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                                tier_str = "Pro Max" if str(promax_flag).upper() == 'Y' else "Pro"
                                st.session_state.update({
                                    'logged_in': True, 'user_name': str(valid['Name'].values[0]), 
                                    'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 
                                    'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list',
                                    'user_tier': tier_str
                                })
                                st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace); st.rerun()
                        else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): 
            st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([1.3, 1, 1], gap="small")
        display_tier = st.session_state.user_tier
        if st.session_state.user_tier == "Pro Max" and st.session_state.workspace not in ['material_overall', 'material_list']:
            display_tier = f"Pro Max [{st.session_state.workspace.capitalize()} DB Center]"

        with r_name: st.markdown(f'<div class="user-greeting">{st.session_state.user_name} ({display_tier})</div>', unsafe_allow_html=True)
        with r_my:
            if st.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        with r_out:
            if st.button("Logout", key="btn_logout_m", use_container_width=True): 
                for key, val in default_vars.items(): st.session_state[key] = val
                st.rerun()

    bot_active = st.toggle("**💬 SynoBot 활성화**", value=st.session_state.show_bot, key="bot_toggle_ui")
    if bot_active != st.session_state.show_bot:
        st.session_state.show_bot = bot_active; st.rerun()

st.markdown("---")

# 🔥 양방향 동기화 콜백
def sync_s_to_n(s_key, n_key): st.session_state[n_key] = st.session_state[s_key]
def sync_n_to_s(s_key, n_key): st.session_state[s_key] = st.session_state[n_key]

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드] (생략 없이 원본 유지)
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    if st.session_state.admin_view is not None or st.session_state.show_profile is False:
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
            
            a1, a2, a3, a4, a5 = st.columns(5)
            
            if a1.button("👥 유저 관리 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'users' else 'users'; st.session_state.admin_ws = 'Users'; st.rerun()
            if a2.button("🔋 소재 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'mats' else 'mats'; st.session_state.admin_ws = 'material_overall'; st.rerun()
            if a3.button("⚙️ 파라미터 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'param' else 'param'; st.session_state.admin_ws = 'param_config'; st.rerun()
            if a4.button("💾 로그 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'logs' else 'logs'; st.session_state.admin_ws = 'myData'; st.rerun()
            if a5.button("💬 챗봇 로그 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'chat' else 'chat'; st.session_state.admin_ws = 'ChatLogs'; st.rerun()

            if st.session_state.admin_view:
                st.markdown("---")
                st.markdown(f'<p class="sub-header-bold">🛠️ 인라인 데이터베이스 편집기</p>', unsafe_allow_html=True)
                
                if st.session_state.admin_view == 'users': target_url = URL_USERS; ws_options = ["Users", "VIPs"]
                elif st.session_state.admin_view == 'mats': target_url = URL_MATS; ws_options = ["material_overall", "material_list"] + get_vip_list_exact()
                elif st.session_state.admin_view == 'param': target_url = URL_PARAM; ws_options = ["param_config"]
                elif st.session_state.admin_view == 'logs': target_url = URL_LOGS; ws_options = ["myData"]
                elif st.session_state.admin_view == 'chat': target_url = URL_LOGS; ws_options = ["ChatLogs"] 
                
                if len(ws_options) > 1:
                    sel_ws_admin = st.selectbox("📂 편집할 워크스페이스(탭) 선택", ws_options, index=ws_options.index(st.session_state.admin_ws) if st.session_state.admin_ws in ws_options else 0)
                    if sel_ws_admin != st.session_state.admin_ws:
                        st.session_state.admin_ws = sel_ws_admin; st.rerun()
                
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'material_overall':
                        st.caption("ℹ️ 'material_overall'은 공용 및 모든 VIP 데이터가 취합된 **읽기 전용(Read-only)** 통합 뷰입니다.")
                        vips = get_vip_list_exact(); dfs = []
                        for v in vips:
                            tmp = load_cloud_data(target_url, v)
                            if not tmp.empty: dfs.append(tmp.iloc[::-1]) 
                        tmp_public = load_cloud_data(target_url, "material_list")
                        if not tmp_public.empty: dfs.append(tmp_public)
                        df_admin = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                        df_admin = df_admin.drop_duplicates(subset=['Name'], keep='first') if not df_admin.empty else pd.DataFrame()
                        st.dataframe(df_admin, use_container_width=True)
                    else:
                        df_admin = conn.read(spreadsheet=target_url, worksheet=st.session_state.admin_ws, ttl=600) 
                        st.caption("ℹ️ 빈 행을 클릭하여 데이터를 추가하거나, 행을 선택해 `Delete` 키로 삭제할 수 있습니다.")
                        
                        original_cols = df_admin.columns.tolist()
                        df_display = df_admin.copy()
                        is_log_view = (st.session_state.admin_view == 'logs')
                        
                        if st.session_state.admin_view == 'users' and st.session_state.admin_ws == 'Users':
                            df_display['구분'] = df_display['ProMax_Req'].apply(lambda x: 'Pro Max' if str(x).upper() == 'Y' else ('Out' if str(x) == 'Out' else 'Pro'))
                            display_order = ['구분', 'Name', 'Company', 'Dept', 'Job', 'Phone', 'Purpose', 'RegDate', 'Email']
                            df_display = df_display[[c for c in display_order if c in df_display.columns]]
                            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}")
                            if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                                try:
                                    save_df = edited_df.copy()
                                    save_df['ProMax_Req'] = save_df['구분'].apply(lambda x: 'Y' if x == 'Pro Max' else ('Out' if x == 'Out' else 'N'))
                                    save_df = save_df.drop(columns=['구분'])
                                    merged = pd.merge(save_df, df_admin[['Email', 'Password']], on='Email', how='left')
                                    final_cols = ['Email', 'Password', 'Name', 'Company', 'Dept', 'Job', 'Phone', 'Purpose', 'ProMax_Req', 'RegDate']
                                    final_save = merged[[c for c in final_cols if c in merged.columns]].fillna("")
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=final_save)
                                    st.cache_data.clear(); st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e: st.error(f"저장 중 오류 발생: {e}")

                        elif is_log_view and not df_display.empty:
                            df_display['Workspace'] = df_display['Workspace'].replace({'material_overall': 'admin', 'material_list': 'pro_user'})
                            front_cols = [c for c in ['Workspace', 'Email', 'Time'] if c in original_cols]
                            other_cols = [c for c in original_cols if c not in front_cols]
                            df_display = df_display[front_cols + other_cols]
                            df_display = df_display.iloc[::-1].reset_index(drop=True)
                            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_logs")
                            if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                                try:
                                    save_df = edited_df.copy()
                                    save_df = save_df.iloc[::-1].reset_index(drop=True)
                                    save_df['Workspace'] = save_df['Workspace'].replace({'admin': 'material_overall', 'pro_user': 'material_list'})
                                    if set(original_cols) == set(save_df.columns): save_df = save_df[original_cols]
                                    edited_df_safe = save_df.fillna("")
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=edited_df_safe)
                                    st.cache_data.clear(); st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e: st.error(f"저장 중 오류 발생: {e}")
                        
                        elif st.session_state.admin_view != 'users':
                            if st.session_state.admin_view == 'chat': 
                                if not df_display.empty: df_display = df_display.iloc[::-1].reset_index(drop=True)
                                
                            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}")
                            if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                                try:
                                    save_df = edited_df.copy()
                                    if st.session_state.admin_view == 'chat' and not save_df.empty: save_df = save_df.iloc[::-1].reset_index(drop=True)
                                    if set(original_cols) == set(save_df.columns): save_df = save_df[original_cols]
                                    edited_df_safe = save_df.fillna("")
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=edited_df_safe)
                                    st.cache_data.clear(); st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e: st.error(f"저장 중 오류 발생: {e}")
                except Exception as e:
                    pass
                
                st.markdown("---")
                st.markdown('<p class="sub-header-bold">👁️ 하단 시뮬레이터 테스트 (VIP 시점)</p>', unsafe_allow_html=True)
                vip_opts = ["material_overall", "material_list"] + get_vip_list_exact()
                sel_ws = st.selectbox("**🔒 테스트 워크스페이스 선택**", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
                if sel_ws != st.session_state.workspace:
                    st.session_state.workspace = sel_ws; st.session_state.history = load_user_history(st.session_state.user_email, sel_ws); st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문
# -----------------------------------------------------------------------------
if st.session_state.get('show_bot', True):
    col_left, col_main, col_bot = st.columns([0.02, 0.70, 0.28], gap="small")
else:
    col_left, col_main = st.columns([0.02, 0.98], gap="small")
    col_bot = None

with col_left: st.empty() 

with col_main:
    # --- 가입 및 프로필 영역 (기존 유지, 생략 없이 작동) ---
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
                                if send_verification_email(e_in, v_code): st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
                                else: st.error("이메일 발송 실패. 관리자에게 문의하세요.")
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
                is_vip_request = st.checkbox(":red[Pro Max Mode] 가입합니다. (VIP 전용 DB 구축)")
                agree_sec = st.checkbox("보안 및 개인정보 처리 사항에 동의합니다.")
                if st.button("가입신청", disabled=not (pw1 and pw1==pw2 and n_name and agree_sec), use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "Dept": n_dept, "Job": n_job, "Phone": n_phone, "Purpose": n_purpose, "ProMax_Req": "Y" if is_vip_request else "N", "RegDate": (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")}])
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                    if is_vip_request:
                        domain = st.session_state.temp_email.split('@')[1].split('.')[0].lower(); vip_df = load_cloud_data(URL_USERS, "VIPs")
                        if domain not in [str(x).lower().strip() for x in vip_df['Company'].dropna()]:
                            conn.update(spreadsheet=URL_USERS, worksheet="VIPs", data=pd.concat([vip_df, pd.DataFrame([{"Company": domain}])], ignore_index=True))
                            try: conn.update(spreadsheet=URL_MATS, worksheet=domain, data=pd.DataFrame(columns=["Name", "Category", "Cap_Def", "Volt_Def", "Den_Def"]))
                            except: pass
                    st.cache_data.clear(); send_welcome_email(st.session_state.temp_email, n_name); st.success("가입신청 완료! 로그인 해주세요.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

    if st.session_state.get('show_profile') and st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
            if not st.session_state.get('is_admin', False):
                df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
                st.markdown(f"**이메일(ID):** {st.session_state.user_email}")
                c1, c2 = st.columns([1, 1]); m_pw = c1.text_input("새 Password (변경 시에만 입력)", type="password")
                current_tier = "Pro Max" if u_row.get('ProMax_Req', 'N') == 'Y' else "Pro"
                m_tier = c2.radio("계정 권한 (Pro / Pro Max)", ["Pro", "Pro Max"], index=1 if current_tier == "Pro Max" else 0, horizontal=True)
                c3, c4 = st.columns(2); m_name = c3.text_input("이름", value=u_row.get('Name', '')); m_comp = c4.text_input("Company", value=u_row.get('Company', ''))
                c5, c6 = st.columns(2); m_dept = c5.text_input("부서", value=u_row.get('Dept', '')); m_job = c6.text_input("담당업무", value=u_row.get('Job', ''))
                c7, c8 = st.columns(2); m_phone = c7.text_input("연락처", value=u_row.get('Phone', '')); m_purpose = c8.text_input("사용용도", value=u_row.get('Purpose', ''))
                st.markdown("<br>", unsafe_allow_html=True); del_col, reason_col = st.columns([1, 3])
                del_check = del_col.checkbox("⚠️ 탈퇴 신청 (체크 시 비활성화)"); del_reason = reason_col.text_input("탈퇴 사유", placeholder="사유 기입", disabled=not del_check, label_visibility="collapsed")
                if st.button("개인정보 수정 완료", use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                    if del_check: 
                        df_update.at[idx, 'ProMax_Req'] = 'Out'; df_update.at[idx, 'Purpose'] = f"[탈퇴] {del_reason}"
                        conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.cache_data.clear(); st.success("탈퇴 처리되었습니다."); time.sleep(1)
                        for key, val in default_vars.items(): st.session_state[key] = val
                        st.rerun()
                    else:
                        if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                        df_update.at[idx, 'Name'] = m_name; df_update.at[idx, 'Company'] = m_comp; df_update.at[idx, 'Dept'] = m_dept
                        df_update.at[idx, 'Job'] = m_job; df_update.at[idx, 'Phone'] = m_phone; df_update.at[idx, 'Purpose'] = m_purpose; df_update.at[idx, 'ProMax_Req'] = 'Y' if m_tier == "Pro Max" else 'N'
                        conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.cache_data.clear(); st.session_state.user_name = m_name; st.session_state.user_tier = m_tier; st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()

    # --- 메인 시뮬레이터 패널 시작 ---
    with st.container(height=900, border=False):
        st.markdown("<div id='main-scroll-anchor'></div>", unsafe_allow_html=True) 
        
        # [섹션 1] Material Selection
        with st.container(border=True):
            ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
            st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
            sp1, c_1 = st.columns([0.02, 0.98])
            with c_1:
                # 데이터 병합 및 정리 (생략 없이 작동)
                if is_pro and st.session_state.workspace == "material_overall":
                    vips = get_vip_list_exact(); dfs = []
                    for v in vips:
                        tmp = load_cloud_data(URL_MATS, v)
                        if not tmp.empty: tmp['Is_VIP'] = True; dfs.append(tmp.iloc[::-1]) 
                    if not mat_df_public.empty: tmp_pub = mat_df_public.copy(); tmp_pub['Is_VIP'] = False; dfs.append(tmp_pub)
                    mat_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                    mat_df = mat_df.drop_duplicates(subset=['Name'], keep='first') if not mat_df.empty else pd.DataFrame()
                    df_vip = pd.DataFrame()
                else:
                    df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame()
                    _dfs = []
                    if not df_vip.empty: tmp_vip = df_vip.copy(); tmp_vip['Is_VIP'] = True; _dfs.append(tmp_vip.iloc[::-1])
                    if not mat_df_public.empty: tmp_pub = mat_df_public.copy(); tmp_pub['Is_VIP'] = False; _dfs.append(tmp_pub)
                    mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

                m1, m2, m3, m4 = st.columns(4)
                if not mat_df.empty and 'Category' in mat_df.columns:
                    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist(); ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
                    ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist(); sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
                    vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist()
                    def format_mat_name(name): return f"💎 {name}" if name in vip_names else name
                    
                    with m1: cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], format_func=format_mat_name, key="sel_cat_m")
                    with m2: ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], format_func=format_mat_name, key="sel_ano_m")
                    with m3: st.selectbox("**Electrolyte**", ele_list if ele_list else ["Sample Elec"], format_func=format_mat_name, key="sel_ele_m")
                    with m4: st.selectbox("**Separator**", sep_list if sep_list else ["Sample Sep"], format_func=format_mat_name, key="sel_sep_m")
                    
                    row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
                    # DB에 입력된 Cathode Default 파라미터 로드
                    def_cap_min, def_cap_max, def_cap_val = safe_float(row.get('Cap_Min'), 100.0), safe_float(row.get('Cap_Max'), 250.0), safe_float(row.get('Cap_Def'), 160.0)
                    def_vlt_min, def_vlt_max, def_vlt_val = safe_float(row.get('Volt_Min'), 2.0), safe_float(row.get('Volt_Max'), 4.5), safe_float(row.get('Volt_Def'), 3.05)
                    def_den_min, def_den_max, def_den_val = safe_float(row.get('Den_Min'), 1.0), safe_float(row.get('Den_Max'), 5.0), safe_float(row.get('Den_Def'), 4.5)
                    def_lif_min, def_lif_max, def_lif_val = safe_float(row.get('Life_Min'), 500.0), safe_float(row.get('Life_Max'), 10000.0), safe_float(row.get('Life_Def'), 4000.0)
                    def_lod_min, def_lod_max, def_lod_val = safe_float(row.get('Load_Min'), 5.0), safe_float(row.get('Load_Max'), 45.0), safe_float(row.get('Load_Def'), 14.0)
                else:
                    st.warning("Cloud 소재 로드 실패. 앱이 기본값으로 작동합니다.")
                    cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
                    def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, 160.0; def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05
                    def_den_min, def_den_max, def_den_val = 1.0, 5.0, 4.5; def_lif_min, def_lif_max, def_lif_val = 500.0, 10000.0, 4000.0
                    def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
                st.markdown("<br>", unsafe_allow_html=True)

        # 🔥 전체 14개 공정/스펙 파라미터 세션 초기화 (param_config 대신 명시적 할당)
        init_vals = {
            # 섹션 2: Material Specs
            "cap": float(def_cap_val), "volt": float(def_vlt_val), "den": float(def_den_val), "life": float(def_lif_val),
            # 섹션 3: Cathode Process
            "c_lod": float(def_lod_val), "c_press": 2.50, "c_act": 96.0, "c_bin": 2.0, "c_con": 2.0,
            # 섹션 3: Anode Process
            "np": 1.10, "a_press": 1.60, "a_act": 95.0, "a_bin": 2.5, "a_con": 2.5,
            # 섹션 3: Cell
            "ec": 3.5,
            # 섹션 4: Target
            "te": 160.0, "tc": 1.0, "tl": 2000.0 # 💡 에너지 밀도 기본값을 160.0으로 밸런스 조정 (100~250 범위 내)
        }
        for k, v in init_vals.items():
            if f"{k}_s" not in st.session_state: st.session_state[f"{k}_s"] = v
            if f"{k}_n" not in st.session_state: st.session_state[f"{k}_n"] = v

        # [섹션 2] Material Specs Expert Mode
        with st.container(border=True):
            st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
            sp2, c_2 = st.columns([0.03, 0.97])
            with c_2:
                expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True)
                s1, s2, s3, s4 = st.columns(4)
                
                with s1:
                    st.markdown("<p class='param-label'>Capacity (mAh/g)</p>", unsafe_allow_html=True)
                    v1, v2 = st.columns([0.7, 0.3])
                    v1.slider("Cap_S", float(def_cap_min), float(def_cap_max), step=1.0, key="cap_s", on_change=sync_s_to_n, args=("cap_s", "cap_n"), label_visibility="collapsed")
                    v2.number_input("Cap_N", float(def_cap_min), float(def_cap_max), step=0.1, key="cap_n", on_change=sync_n_to_s, args=("cap_s", "cap_n"), label_visibility="collapsed")
                    v_cap = st.session_state.cap_s
                    
                with s2:
                    st.markdown("<p class='param-label'>Voltage (V)</p>", unsafe_allow_html=True)
                    vv1, vv2 = st.columns([0.7, 0.3])
                    vv1.slider("Volt_S", float(def_vlt_min), float(def_vlt_max), step=0.1, key="volt_s", on_change=sync_s_to_n, args=("volt_s", "volt_n"), label_visibility="collapsed")
                    vv2.number_input("Volt_N", float(def_vlt_min), float(def_vlt_max), step=0.01, key="volt_n", on_change=sync_n_to_s, args=("volt_s", "volt_n"), label_visibility="collapsed")
                    v_volt = st.session_state.volt_s
                    
                with s3:
                    st.markdown("<p class='param-label'>True Density (g/cc)</p>", unsafe_allow_html=True)
                    d1, d2 = st.columns([0.7, 0.3])
                    d1.slider("Den_S", float(def_den_min), float(def_den_max), step=0.1, key="den_s", on_change=sync_s_to_n, args=("den_s", "den_n"), label_visibility="collapsed", disabled=not expert)
                    d2.number_input("Den_N", float(def_den_min), float(def_den_max), step=0.01, key="den_n", on_change=sync_n_to_s, args=("den_s", "den_n"), label_visibility="collapsed", disabled=not expert)
                    v_den = st.session_state.den_s
                    
                with s4:
                    st.markdown("<p class='param-label'>Base Life (Cycles)</p>", unsafe_allow_html=True)
                    lf1, lf2 = st.columns([0.7, 0.3])
                    lf1.slider("Life_S", float(def_lif_min), float(def_lif_max), step=100.0, key="life_s", on_change=sync_s_to_n, args=("life_s", "life_n"), label_visibility="collapsed", disabled=not expert)
                    lf2.number_input("Life_N", float(def_lif_min), float(def_lif_max), step=10.0, key="life_n", on_change=sync_n_to_s, args=("life_s", "life_n"), label_visibility="collapsed", disabled=not expert)
                    v_life = st.session_state.life_s

        # 🔥 [섹션 3] Process Parameters
        with st.container(border=True):
            st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
            sp3, c_3 = st.columns([0.03, 0.97])
            with c_3:
                show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True)
                p1, p2, p3 = st.columns(3)
                
                # --- (A) Cathode (양극재) ---
                with p1:
                    st.markdown('<p class="sub-header-bold">(A) Cathode Process</p>', unsafe_allow_html=True)
                    st.markdown("<p class='param-label'>Areal Loading (mg/cm2)</p>", unsafe_allow_html=True)
                    cl1, cl2 = st.columns([0.7, 0.3])
                    cl1.slider("CLod_S", float(def_lod_min), float(def_lod_max), step=1.0, key="c_lod_s", on_change=sync_s_to_n, args=("c_lod_s", "c_lod_n"), label_visibility="collapsed")
                    cl2.number_input("CLod_N", float(def_lod_min), float(def_lod_max), step=0.1, key="c_lod_n", on_change=sync_n_to_s, args=("c_lod_s", "c_lod_n"), label_visibility="collapsed")
                    v_c_lod = st.session_state.c_lod_s
                    
                    st.markdown("<p class='param-label'>Press Density (g/cc)</p>", unsafe_allow_html=True)
                    cpr1, cpr2 = st.columns([0.7, 0.3])
                    cpr1.slider("CPress_S", 1.5, 4.0, step=0.1, key="c_press_s", on_change=sync_s_to_n, args=("c_press_s", "c_press_n"), label_visibility="collapsed", disabled=not show_adv)
                    cpr2.number_input("CPress_N", 1.5, 4.0, step=0.01, key="c_press_n", on_change=sync_n_to_s, args=("c_press_s", "c_press_n"), label_visibility="collapsed", disabled=not show_adv)
                    v_c_press = st.session_state.c_press_s
                    
                    st.markdown("<p class='param-label'>Active Ratio (%)</p>", unsafe_allow_html=True)
                    ca1, ca2 = st.columns([0.7, 0.3])
                    ca1.slider("CAct_S", 80.0, 99.0, step=0.5, key="c_act_s", on_change=sync_s_to_n, args=("c_act_s", "c_act_n"), label_visibility="collapsed")
                    ca2.number_input("CAct_N", 80.0, 99.0, step=0.1, key="c_act_n", on_change=sync_n_to_s, args=("c_act_s", "c_act_n"), label_visibility="collapsed")
                    v_c_act = st.session_state.c_act_s
                    
                    st.markdown("<p class='param-label'>Binder Ratio (%)</p>", unsafe_allow_html=True)
                    cb1, cb2 = st.columns([0.7, 0.3])
                    cb1.slider("CBin_S", 0.0, 10.0, step=0.5, key="c_bin_s", on_change=sync_s_to_n, args=("c_bin_s", "c_bin_n"), label_visibility="collapsed")
                    cb2.number_input("CBin_N", 0.0, 10.0, step=0.1, key="c_bin_n", on_change=sync_n_to_s, args=("c_bin_s", "c_bin_n"), label_visibility="collapsed")
                    v_c_bin = st.session_state.c_bin_s
                    
                    st.markdown("<p class='param-label'>Conductive Carbon (%)</p>", unsafe_allow_html=True)
                    cc1, cc2 = st.columns([0.7, 0.3])
                    cc1.slider("CCon_S", 0.0, 10.0, step=0.5, key="c_con_s", on_change=sync_s_to_n, args=("c_con_s", "c_con_n"), label_visibility="collapsed")
                    cc2.number_input("CCon_N", 0.0, 10.0, step=0.1, key="c_con_n", on_change=sync_n_to_s, args=("c_con_s", "c_con_n"), label_visibility="collapsed")
                    v_c_con = st.session_state.c_con_s
                    
                    porosity = max(0.0, (1 - (v_c_press / v_den)) * 100) if v_den > 0 else 0
                    
                # --- (B) Anode (음극재) ---
                with p2:
                    st.markdown('<p class="sub-header-bold">(B) Anode Process</p>', unsafe_allow_html=True)
                    st.markdown("<p class='param-label'>N/P Ratio</p>", unsafe_allow_html=True)
                    n1, n2 = st.columns([0.7, 0.3])
                    n1.slider("NP_S", 0.95, 1.50, step=0.05, key="np_s", on_change=sync_s_to_n, args=("np_s", "np_n"), label_visibility="collapsed")
                    n2.number_input("NP_N", 0.95, 1.50, step=0.01, key="np_n", on_change=sync_n_to_s, args=("np_s", "np_n"), label_visibility="collapsed")
                    v_np = st.session_state.np_s
                    
                    st.markdown("<p class='param-label'>Press Density (g/cc)</p>", unsafe_allow_html=True)
                    apr1, apr2 = st.columns([0.7, 0.3])
                    apr1.slider("APress_S", 0.8, 2.0, step=0.1, key="a_press_s", on_change=sync_s_to_n, args=("a_press_s", "a_press_n"), label_visibility="collapsed", disabled=not show_adv)
                    apr2.number_input("APress_N", 0.8, 2.0, step=0.01, key="a_press_n", on_change=sync_n_to_s, args=("a_press_s", "a_press_n"), label_visibility="collapsed", disabled=not show_adv)
                    v_a_press = st.session_state.a_press_s
                    
                    st.markdown("<p class='param-label'>Active Ratio (%)</p>", unsafe_allow_html=True)
                    aa1, aa2 = st.columns([0.7, 0.3])
                    aa1.slider("AAct_S", 80.0, 99.0, step=0.5, key="a_act_s", on_change=sync_s_to_n, args=("a_act_s", "a_act_n"), label_visibility="collapsed")
                    aa2.number_input("AAct_N", 80.0, 99.0, step=0.1, key="a_act_n", on_change=sync_n_to_s, args=("a_act_s", "a_act_n"), label_visibility="collapsed")
                    v_a_act = st.session_state.a_act_s
                    
                    st.markdown("<p class='param-label'>Binder Ratio (%)</p>", unsafe_allow_html=True)
                    ab1, ab2 = st.columns([0.7, 0.3])
                    ab1.slider("ABin_S", 0.0, 10.0, step=0.5, key="a_bin_s", on_change=sync_s_to_n, args=("a_bin_s", "a_bin_n"), label_visibility="collapsed")
                    ab2.number_input("ABin_N", 0.0, 10.0, step=0.1, key="a_bin_n", on_change=sync_n_to_s, args=("a_bin_s", "a_bin_n"), label_visibility="collapsed")
                    v_a_bin = st.session_state.a_bin_s
                    
                    st.markdown("<p class='param-label'>Conductive Carbon (%)</p>", unsafe_allow_html=True)
                    ac1, ac2 = st.columns([0.7, 0.3])
                    ac1.slider("ACon_S", 0.0, 10.0, step=0.5, key="a_con_s", on_change=sync_s_to_n, args=("a_con_s", "a_con_n"), label_visibility="collapsed")
                    ac2.number_input("ACon_N", 0.0, 10.0, step=0.1, key="a_con_n", on_change=sync_n_to_s, args=("a_con_s", "a_con_n"), label_visibility="collapsed")
                    v_a_con = st.session_state.a_con_s

                # --- (C) Cell & Electrolyte ---
                with p3:
                    st.markdown('<p class="sub-header-bold">(C) Cell & Electrolyte</p>', unsafe_allow_html=True)
                    st.markdown("<p class='param-label'>E/C Ratio (g/Ah)</p>", unsafe_allow_html=True)
                    e1, e2 = st.columns([0.7, 0.3])
                    e1.slider("EC_S", 1.0, 8.0, step=0.1, key="ec_s", on_change=sync_s_to_n, args=("ec_s", "ec_n"), label_visibility="collapsed", disabled=not show_adv)
                    e2.number_input("EC_N", 1.0, 8.0, step=0.01, key="ec_n", on_change=sync_n_to_s, args=("ec_s", "ec_n"), label_visibility="collapsed", disabled=not show_adv)
                    v_ec = st.session_state.ec_s
                    
                # 하단 판정 및 경고 로직
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption(f"**💡 양극재 예상 공극률 (Cathode Porosity): {porosity:.1f}%**")
                w1, w2, w3 = st.columns(3)
                
                with w1:
                    total_c_mix = v_c_act + v_c_bin + v_c_con
                    if abs(total_c_mix - 100.0) > 0.1: st.error(f"⚠️ 양극재 믹스 비율 불일치 (현재: {total_c_mix:.1f}%)")
                    elif porosity < 20.0: st.error("⚠️ 공극률 부족: 전해액 침투 불량 위험!")
                        
                with w2:
                    total_a_mix = v_a_act + v_a_bin + v_a_con
                    if abs(total_a_mix - 100.0) > 0.1: st.error(f"⚠️ 음극재 믹스 비율 불일치 (현재: {total_a_mix:.1f}%)")
                    elif v_np < 1.05: st.error("⚠️ N/P Ratio 위험: 나트륨 석출(Na-Plating) 단락 위험!")
                    elif v_np >= 1.15: st.warning("⚠️ N/P Ratio 과다: 에너지 밀도 하락!")
                        
                with w3:
                    if show_adv and v_ec < 2.0: st.error("⚠️ E/C Ratio 부족: 전해액 고갈 및 수명 저하 위험!")

        # 🔥 [섹션 4] Target Settings (라벨 변경 및 범위 변경)
        with st.container(border=True):
            st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
            sp4, c_4 = st.columns([0.03, 0.97])
            with c_4:
                t1, t2, t3 = st.columns(3)
                with t1: 
                    # 💡 명칭 변경 및 100~250 범위 적용
                    st.markdown('<p class="sub-header-bold">Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
                    te1, te2 = st.columns([0.7, 0.3])
                    te1.slider("TE_S", 100.0, 250.0, step=5.0, key="te_s", on_change=sync_s_to_n, args=("te_s", "te_n"), label_visibility="collapsed")
                    te2.number_input("TE_N", 100.0, 250.0, step=1.0, key="te_n", on_change=sync_n_to_s, args=("te_s", "te_n"), label_visibility="collapsed")
                    v_te = st.session_state.te_s
                    
                with t2: 
                    st.markdown('<p class="sub-header-bold">C-rate</p>', unsafe_allow_html=True)
                    tc1, tc2 = st.columns([0.7, 0.3])
                    tc1.slider("TC_S", 0.1, 10.0, step=0.5, key="tc_s", on_change=sync_s_to_n, args=("tc_s", "tc_n"), label_visibility="collapsed")
                    tc2.number_input("TC_N", 0.1, 10.0, step=0.1, key="tc_n", on_change=sync_n_to_s, args=("tc_s", "tc_n"), label_visibility="collapsed")
                    v_tc = st.session_state.tc_s
                    
                with t3: 
                    # 💡 명칭 변경
                    st.markdown('<p class="sub-header-bold">Cycle Life</p>', unsafe_allow_html=True)
                    tl1, tl2 = st.columns([0.7, 0.3])
                    tl1.slider("TL_S", 500.0, 10000.0, step=100.0, key="tl_s", on_change=sync_s_to_n, args=("tl_s", "tl_n"), label_visibility="collapsed")
                    tl2.number_input("TL_N", 500.0, 10000.0, step=10.0, key="tl_n", on_change=sync_n_to_s, args=("tl_s", "tl_n"), label_visibility="collapsed")
                    v_tl = st.session_state.tl_s

        # 🔥 섹션 5 스크롤 앵커 추가
        st.markdown("<div id='section5'></div>", unsafe_allow_html=True)
        if st.session_state.get('scroll_to_result'):
            components.html("<script>window.parent.document.getElementById('section5').scrollIntoView();</script>", height=0)
            st.session_state.scroll_to_result = False

        # [섹션 5] Simulation Control & Analysis
        with st.container(border=True):
            st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
            sp5, c_5 = st.columns([0.03, 0.97])
            with c_5:
                btn_text = "🚀 RUN SIMULATION" if st.session_state.history else "🚀 RUN SIMULATION ㅡ 아직 실행 이력이 없습니다."
                if st.button(btn_text, key="btn_run_m", use_container_width=True):
                    # 💡 물리 엔진 연산에 분리된 양극 활물질 비율(C_Act) 적용
                    cell_v = max(0.1, v_volt - (0.1 + (v_tc * 0.02)))
                    res_whkg = ((v_cap * (v_c_act/100) * cell_v) / 2.5) * max(0.5, 1.0 - (v_tc * 0.015))
                    whl = res_whkg * v_c_press * 0.8  
                    life_cyc = int(v_life * (0.95 ** v_tc))
                    cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
                    v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                    
                    # 로그 데이터 딕셔너리 최신화 (모든 파라미터 저장)
                    log_data = {
                        "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel, 
                        "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), 
                        "C_Load": round(v_c_lod, 1), "C_Press": round(v_c_press, 2), "C_Act": round(v_c_act, 1), "C_Bin": round(v_c_bin, 1), "C_Con": round(v_c_con, 1),
                        "N/P Ratio": round(v_np, 2), "A_Press": round(v_a_press, 2), "A_Act": round(v_a_act, 1), "A_Bin": round(v_a_bin, 1), "A_Con": round(v_a_con, 1),
                        "E/C Ratio": round(v_ec, 2), "C-rate": round(v_tc, 1), 
                        "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), 
                        "Life(Cyc)": life_cyc, "dq_x": v_axis, "dq_y": dqdv, "AI_Briefing": ""
                    }
                    
                    is_dup = False
                    if st.session_state.history:
                        check_keys = ["Cathode", "Anode", "Cap(mAh/g)", "Volt(V)", "C_Load", "C_Press", "C_Act", "C_Bin", "C_Con", "N/P Ratio", "A_Act", "C-rate"]
                        if all(log_data[k] == st.session_state.history[0].get(k) for k in check_keys if k in log_data and k in st.session_state.history[0]): 
                            is_dup = True

                    if is_dup: st.warning("⚠️ 이전 실행과 동일한 조건입니다.")
                    else:
                        with st.spinner("🚀 물리 엔진 연산 중..."):
                            time.sleep(0.6) 
                            st.session_state.history.insert(0, log_data); st.session_state.sim_result = log_data; 
                            st.session_state.trigger_auto_bot = True; 
                            st.session_state.scroll_to_result = True 
                            st.rerun()

                if st.session_state.history:
                    st.markdown("---")
                    st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록</p>', unsafe_allow_html=True)
                    log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg" for h in st.session_state.history]
                    res = st.session_state.history[st.selectbox("기록", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")]
                    
                    st.markdown("---")
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg'] - v_te, 1):+} Wh/kg")
                    r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off")
                    r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{round(res['Cell_V'] - v_volt, 2):+} V", delta_color="inverse")
                    r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{int(res['Life(Cyc)'] - v_tl):+} Cyc")
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">Discharge Profile</p>', unsafe_allow_html=True)
                        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                        fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9")
                        st.plotly_chart(fig1, use_container_width=True)
                        
                    with g2:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">dQ/dV Profile</p>', unsafe_allow_html=True)
                        fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                        fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9")
                        st.plotly_chart(fig2, use_container_width=True)
                        
                    with g3:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">Cell Performance</p>', unsafe_allow_html=True)
                        fig3 = go.Figure(go.Scatterpolar(r=[min(100, res.get('Wh/kg', 0)/2.5), min(100, res.get('C-rate', 1)*20), min(100, res.get('Life(Cyc)', 0)/50), min(100, res.get('Cell_V', 0)*25), min(100, res.get('C_Load', 0)*4)], theta=['Energy', 'Power', 'Life', 'Voltage', 'Loading'], fill='toself', line=dict(color='#E4B526', width=2)))
                        fig3.update_layout(polar=dict(bgcolor="#f4f6f9", radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10))
                        st.plotly_chart(fig3, use_container_width=True)

                    st.markdown("---")
                    st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
                    df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    if not df_history.empty and 'Time' in df_history.columns: df_history['Time'] = df_history['Time'].astype(str)
                    st.dataframe(df_history, use_container_width=True, column_config={"Time": st.column_config.TextColumn("Time")})

        if is_pro and st.session_state.history:
            with st.container(border=True):
                st.markdown('<p class="main-header">6. Data Management & Past Records (Pro)</p>', unsafe_allow_html=True)
                sp6, c_6 = st.columns([0.03, 0.97])
                with c_6:
                    db_df_all = pd.DataFrame(); selected_times = []
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        db_df_all = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                        if not db_df_all.empty and 'Email' in db_df_all.columns:
                            today_str = (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
                            if 'Time' in db_df_all.columns: db_df_all['Time'] = db_df_all['Time'].replace("", today_str).fillna(today_str)
                            my_saved_data = db_df_all[(db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace)]
                            if not my_saved_data.empty:
                                my_saved_data = my_saved_data.sort_values(by='Time', ascending=False)
                                df_display = my_saved_data.drop(columns=['Email', 'Workspace', 'dq_x', 'dq_y'], errors='ignore').copy()
                                df_display['User Comment'] = df_display.get('User Comment', "").fillna("")
                                df_display['Time'] = df_display['Time'].astype(str)
                                core_cols = ['Time', 'User Comment', 'Cathode', 'Anode']; other_cols = [c for c in df_display.columns if c not in core_cols]
                                df_display = df_display[core_cols + other_cols]; df_display.insert(0, "선택", False)
                                original_comments = df_display['User Comment'].tolist()
                                disabled_cols = [col for col in df_display.columns if col not in ["선택", "User Comment"]]
                                
                                st.caption("💡 **Tip:** 아래 테이블의 `📝 코멘트 입력` 열을 더블클릭하여 메모 기입 후 `Enter`를 누르면 클라우드에 자동 저장됩니다.")
                                edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, disabled=disabled_cols, column_config={"Time": st.column_config.TextColumn("Time", disabled=True), "User Comment": st.column_config.TextColumn("📝 코멘트 입력 (더블클릭)", width="large")})
                                
                                if edited_df['User Comment'].tolist() != original_comments:
                                    if 'User Comment' not in db_df_all.columns: db_df_all['User Comment'] = ""
                                    for idx, row in edited_df.iterrows():
                                        mask = (db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & (db_df_all['Time'] == row['Time'])
                                        if mask.any(): db_df_all.loc[mask, 'User Comment'] = row['User Comment']
                                    conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all); st.cache_data.clear()
                                selected_times = edited_df[edited_df["선택"] == True]["Time"].tolist()
                            else: st.info("클라우드 DB에 이전에 저장된 데이터가 없습니다.")
                    except Exception as e: st.warning("데이터베이스 연결에 실패했습니다.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    btn1, btn2, btn3, btn4 = st.columns(4)
                    
                    if btn1.button("💾 계정에 저장", key="btn_save_my", use_container_width=True):
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                            if not db_df.empty and not db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                                st.warning("이미 저장된 결과입니다.")
                            else:
                                save_record = res.copy(); save_record['Email'] = st.session_state.user_email; save_record['Workspace'] = st.session_state.workspace; save_record['User Comment'] = ""; save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True)); st.cache_data.clear(); st.success("저장 완료!"); st.rerun() 
                        except Exception as e: st.error("저장 오류")

                    if btn2.button("🗑️ 선택 삭제", key="btn_del_sel", use_container_width=True):
                        if not selected_times: st.warning("항목을 체크해주세요.")
                        elif not db_df_all.empty:
                            mask = ~((db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & (db_df_all['Time'].isin(selected_times)))
                            conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all[mask]); st.cache_data.clear(); st.success("삭제 완료!"); st.rerun()

                    df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_export.to_excel(writer, index=False)
                        file_data = buffer.getvalue(); file_name = f"SynoCore_Logs_{(datetime.utcnow() + timedelta(hours=9)).strftime('%m%d_%H%M')}.xlsx"; mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    except ImportError:
                        file_data = df_export.to_csv(index=False).encode('utf-8-sig'); file_name = f"SynoCore_Logs_{(datetime.utcnow() + timedelta(hours=9)).strftime('%m%d_%H%M')}.csv"; mime_type = "text/csv"
                    btn3.download_button("📥 엑셀 다운로드", data=file_data, file_name=file_name, mime=mime_type, key="btn_excel", use_container_width=True)

                    if btn4.button("📄 화면 PDF 인쇄", key="btn_print_pdf", use_container_width=True):
                        components.html("<script>window.parent.print();</script>", height=0)

# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot) AI 패널 
# -----------------------------------------------------------------------------
SYSTEM_KNOWLEDGE = """
You are 'SynoBot', an expert SIB R&D engineer powered by OpenAI.
Answer questions accurately and professionally in Korean based on SIB knowledge.
- 반드시 SIB 수석 연구원(엔지니어)의 전문적인 브리핑 스타일로 작성하되, 사무적이고 정중한 '합쇼체(~입니다, ~합니다)'로 답변하십시오.
- 모든 답변은 도트 블릿('- ')을 사용하여 핵심을 명확히 나열하십시오.
"""

def handle_chat_submit():
    user_input = st.session_state.get("bot_user_input", "")
    if user_input.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        save_chat_log(st.session_state.user_email, st.session_state.workspace, "User", user_input)
        st.session_state.trigger_bot_reply = True
        st.session_state.bot_user_input = "" 

if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (Beta)")
        c_in1, c_in2 = st.columns([0.75, 0.25])
        c_in1.text_input("질문입력", label_visibility="collapsed", placeholder="시노봇에게 질문하기...", key="bot_user_input", on_change=handle_chat_submit)
        c_in2.button("전송", on_click=handle_chat_submit, use_container_width=True, key="btn_chat_send")
        
        chat_container = st.container(height=730, border=True) 
        with chat_container:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            if OpenAI is None: st.error("⚠️ `openai` 라이브러리가 필요합니다.")
            elif "OPENAI_API_KEY" not in st.secrets: st.warning("⚠️ API 키가 설정되지 않았습니다.")
            else:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                if not st.session_state.chat_messages: st.session_state.chat_messages = [{"role": "assistant", "content": "- 안녕하세요. 배터리 설계 전문 AI 시노봇입니다.\n- 좌측의 결과 또는 SIB 지식에 대해 질문해 주십시오."}]

                if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                    st.session_state.trigger_auto_bot = False 
                    api_messages = [{"role": "system", "content": SYSTEM_KNOWLEDGE + f"\n\n[State]\n{st.session_state.sim_result}"}, {"role": "user", "content": "데이터를 분석하여 브리핑해 주십시오."}]
                    with st.chat_message("assistant"):
                        with st.spinner("분석 중..."):
                            try:
                                reply = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages).choices[0].message.content
                                bot_reply = "📊 **[실시간 AI 진단]**\n\n" + reply
                                st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                                if st.session_state.history: st.session_state.history[0]["AI_Briefing"] = bot_reply
                                save_chat_log(st.session_state.user_email, st.session_state.workspace, "AI_Auto", bot_reply)
                            except Exception: pass
                    st.rerun()

                if st.session_state.get('trigger_bot_reply'):
                    st.session_state.trigger_bot_reply = False
                    api_messages = [{"role": "system", "content": SYSTEM_KNOWLEDGE + (f"\n\n[State]\n{st.session_state.sim_result}" if st.session_state.sim_result else "")}]
                    api_messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages])
                    with st.chat_message("assistant"):
                        with st.spinner("작성 중..."):
                            try:
                                reply = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages).choices[0].message.content
                                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                                save_chat_log(st.session_state.user_email, st.session_state.workspace, "AI", reply)
                            except Exception: pass
                    st.rerun()

                for message in reversed(st.session_state.chat_messages):
                    with st.chat_message(message["role"]):
                        content = message["content"].replace("\n- ", "\n\n\- ")
                        if content.startswith("- "): content = "\- " + content[2:]
                        st.markdown(content)

# 7. 푸터 
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)