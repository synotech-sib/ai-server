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
import streamlit.components.v1 as components # 🔥 [추가] JS 제어 및 인쇄용 컴포넌트

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
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    .main .block-container {
        max-width: 1400px !important; 
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
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    
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
    div[data-testid="stChatMessage"] > div:first-child { margin-bottom: 5px !important; }
    div[data-testid="stChatMessage"] > div:nth-child(2) {
        margin-left: 0px !important; 
        padding-left: 0px !important;
        width: 100% !important; 
    }

    div[data-testid="stDataEditor"] th, 
    div[data-testid="stDataEditor"] th span, 
    div[data-testid="stDataEditor"] th div {
        color: #000000 !important;
        font-weight: 800 !important;
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
    sender_password = "여기에_16자리_앱비밀번호를_입력하세요"
    try:
        if "EMAIL_PASSWORD" in st.secrets: sender_password = st.secrets["EMAIL_PASSWORD"]
    except: pass

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
    except Exception as e:
        return False

def send_welcome_email(to_email, user_name):
    sender_email = "wschoi@synotech.co.kr"
    sender_password = "여기에_16자리_앱비밀번호를_입력하세요"
    try:
        if "EMAIL_PASSWORD" in st.secrets: sender_password = st.secrets["EMAIL_PASSWORD"]
    except: pass

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
    except Exception as e:
        return False

# -----------------------------------------------------------------------------
# 유틸리티 (물리 엔진)
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
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: row_dict[k] = float(row_dict.get(k, 0))
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

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 모듈 
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'material_overall', 'user_vip_name': None, 'is_admin': False, 'user_tier': "",
    'admin_view': None, 'admin_ws': None, 'chat_messages': [], 
    'show_bot': True,
    'trigger_auto_bot': False,
    'trigger_bot_reply': False
}
for key, val in default_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

h_l, h_r = st.columns([0.72, 0.28], gap="small") 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">1.9 (beta)</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False
        st.session_state.show_profile = False
        st.session_state.admin_view = None
        st.session_state.admin_ws = None
        st.rerun()

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
                        st.session_state.history = load_user_history(u_id_clean, 'material_overall')
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                            
                            promax_flag = valid['ProMax_Req'].values[0] if 'ProMax_Req' in valid.columns else 'N'
                            tier_str = "Pro Max" if str(promax_flag).upper() == 'Y' else "Pro"
                            
                            st.session_state.update({
                                'logged_in': True, 
                                'user_name': str(valid['Name'].values[0]), 
                                'user_email': str(valid['Email'].values[0]), 
                                'user_vip_name': vip_map.get(domain), 
                                'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list',
                                'user_tier': tier_str
                            });
                            st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                            st.rerun()
                        else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): 
            st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([1.3, 1, 1], gap="small")
        with r_name:
            st.markdown(f'<div class="user-greeting">{st.session_state.user_name} ({st.session_state.user_tier})</div>', unsafe_allow_html=True)
        with r_my:
            if st.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        with r_out:
            if st.button("Logout", key="btn_logout_m", use_container_width=True): 
                for key, val in default_vars.items(): st.session_state[key] = val
                st.rerun()

    bot_active = st.toggle("**💬 SynoBot 활성화**", value=st.session_state.show_bot, key="bot_toggle_ui")
    if bot_active != st.session_state.show_bot:
        st.session_state.show_bot = bot_active
        st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드] 
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    if st.session_state.admin_view is not None or st.session_state.show_profile is False:
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
            a1, a2, a3, a4 = st.columns(4)
            
            if a1.button("👥 유저 관리 DB", use_container_width=True):
                if st.session_state.admin_view == 'users': st.session_state.admin_view = None
                else: st.session_state.admin_view = 'users'; st.session_state.admin_ws = 'Users'
                st.rerun()
            if a2.button("🔋 소재 DB", use_container_width=True):
                if st.session_state.admin_view == 'mats': st.session_state.admin_view = None
                else: st.session_state.admin_view = 'mats'; st.session_state.admin_ws = 'material_overall'
                st.rerun()
            if a3.button("⚙️ 파라미터 DB", use_container_width=True):
                if st.session_state.admin_view == 'param': st.session_state.admin_view = None
                else: st.session_state.admin_view = 'param'; st.session_state.admin_ws = 'param_config'
                st.rerun()
            if a4.button("💾 로그 DB", use_container_width=True):
                if st.session_state.admin_view == 'logs': st.session_state.admin_view = None
                else: st.session_state.admin_view = 'logs'; st.session_state.admin_ws = 'myData'
                st.rerun()

            if st.session_state.admin_view:
                st.markdown("---")
                st.markdown(f'<p class="sub-header-bold">🛠️ 인라인 데이터베이스 편집기</p>', unsafe_allow_html=True)
                
                if st.session_state.admin_view == 'users':
                    target_url = URL_USERS
                    ws_options = ["Users", "VIPs"]
                elif st.session_state.admin_view == 'mats':
                    target_url = URL_MATS
                    ws_options = ["material_overall", "material_list"] + get_vip_list_exact()
                elif st.session_state.admin_view == 'param':
                    target_url = URL_PARAM
                    ws_options = ["param_config"]
                elif st.session_state.admin_view == 'logs':
                    target_url = URL_LOGS
                    ws_options = ["myData"]
                
                if len(ws_options) > 1:
                    sel_ws_admin = st.selectbox("📂 편집할 워크스페이스(탭) 선택", ws_options, index=ws_options.index(st.session_state.admin_ws) if st.session_state.admin_ws in ws_options else 0)
                    if sel_ws_admin != st.session_state.admin_ws:
                        st.session_state.admin_ws = sel_ws_admin
                        st.rerun()
                
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'material_overall':
                        st.caption("ℹ️ 'material_overall'은 공용 및 모든 VIP 데이터가 취합된 **읽기 전용(Read-only)** 통합 뷰입니다. (수정은 개별 탭에서 진행해주세요.)")
                        vips = get_vip_list_exact()
                        dfs = []
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
                            df_display['구분'] = df_display['ProMax_Req'].apply(lambda x: 'Pro Max' if str(x).upper() == 'Y' else 'Pro')
                            display_order = ['구분', 'Name', 'Company', 'Dept', 'Job', 'Phone', 'Purpose', 'RegDate', 'Email']
                            df_display = df_display[[c for c in display_order if c in df_display.columns]]
                            
                            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}")
                            
                            if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                                try:
                                    save_df = edited_df.copy()
                                    save_df['ProMax_Req'] = save_df['구분'].apply(lambda x: 'Y' if x == 'Pro Max' else 'N')
                                    save_df = save_df.drop(columns=['구분'])
                                    
                                    merged = pd.merge(save_df, df_admin[['Email', 'Password']], on='Email', how='left')
                                    final_cols = ['Email', 'Password', 'Name', 'Company', 'Dept', 'Job', 'Phone', 'Purpose', 'ProMax_Req', 'RegDate']
                                    final_save = merged[[c for c in final_cols if c in merged.columns]].fillna("")
                                    
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=final_save)
                                    st.cache_data.clear()
                                    st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e:
                                    st.error(f"저장 중 오류 발생: {e}")

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
                                    
                                    if set(original_cols) == set(save_df.columns):
                                        save_df = save_df[original_cols]
                                        
                                    edited_df_safe = save_df.fillna("")
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=edited_df_safe)
                                    st.cache_data.clear()
                                    st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e:
                                    st.error(f"저장 중 오류 발생: {e}")
                        
                        elif st.session_state.admin_view != 'users':
                            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_other")
                            if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                                try:
                                    save_df = edited_df.copy()
                                    if set(original_cols) == set(save_df.columns):
                                        save_df = save_df[original_cols]
                                    edited_df_safe = save_df.fillna("")
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=edited_df_safe)
                                    st.cache_data.clear()
                                    st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e:
                                    st.error(f"저장 중 오류 발생: {e}")
                except Exception as e:
                    err_msg = str(e)
                    if "Quota exceeded" in err_msg or "429" in err_msg or "RATE_LIMIT_EXCEEDED" in err_msg:
                        st.error("⚠️ 구글 시트 API 분당 요청 한도(60회)를 초과했습니다. 약 1분 후 다시 시도해주세요.")
                    else:
                        st.error(f"데이터를 불러올 수 없습니다. (상세 오류 내역: {err_msg})")
                
                st.markdown("---")
                st.markdown('<p class="sub-header-bold">👁️ 하단 시뮬레이터 테스트 (VIP 시점)</p>', unsafe_allow_html=True)
                st.caption("ℹ️ 위에서 수정한 DB가 하단의 시뮬레이터에 잘 적용되었는지 특정 VIP의 시점으로 테스트할 수 있습니다.")
                vip_opts = ["material_overall", "material_list"] + get_vip_list_exact()
                sel_ws = st.selectbox("**🔒 테스트 워크스페이스 선택**", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
                if sel_ws != st.session_state.workspace:
                    st.session_state.workspace = sel_ws
                    st.session_state.history = load_user_history(st.session_state.user_email, sel_ws)
                    st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문
# -----------------------------------------------------------------------------
if st.session_state.get('show_bot', True):
    col_left, col_main, col_bot = st.columns([0.02, 0.70, 0.28], gap="small")
else:
    col_left, col_main = st.columns([0.02, 0.98], gap="small")
    col_bot = None

with col_left:
    st.empty() 

with col_main:
    if st.session_state.show_reg and not st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">📝 계정 가입 (Pro Mode) <span style="font-size:15px; color:#666; font-weight:normal; letter-spacing:0px; margin-left:10px;">아래 사항 모두 기입해 주시면 감사하겠습니다.</span></p>', unsafe_allow_html=True)
            
            if st.session_state.reg_stage == 0:
                with st.form("form_reg_email", border=False):
                    e_in = st.text_input("1. 회사 이메일 주소")
                    submit_email = st.form_submit_button("인증번호 발송", use_container_width=True)
                    if submit_email:
                        if not e_in or "@" not in e_in: 
                            st.error("올바른 이메일 주소를 입력해주세요.")
                        else:
                            v_code = str(random.randint(100000, 999999))
                            with st.spinner("📧 이메일을 발송 중입니다... (최대 10초 소요)"):
                                if send_verification_email(e_in, v_code):
                                    st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1})
                                    st.rerun()
                                else: 
                                    st.error("이메일 발송 실패. 관리자에게 문의하세요.")
                                    
            elif st.session_state.reg_stage == 1:
                st.info(f"📧 [{st.session_state.temp_email}]로 인증번호가 발송되었습니다.")
                with st.form("form_reg_code", border=False):
                    v_in = st.text_input("인증번호 6자리 입력")
                    submit_code = st.form_submit_button("인증 확인", use_container_width=True)
                    if submit_code:
                        if v_in == st.session_state.v_code: 
                            st.session_state.reg_stage = 2
                            st.rerun()
                        else: 
                            st.error("인증번호가 일치하지 않습니다.")
                            
            elif st.session_state.reg_stage == 2:
                p1, p2 = st.columns(2)
                pw1 = p1.text_input("2. Password", type="password")
                pw2 = p2.text_input("Password 확인", type="password") 
                
                c1, c2 = st.columns(2)
                n_name = c1.text_input("3. 이름")
                n_comp = c2.text_input("4. Company (회사명)")
                
                c3, c4 = st.columns(2)
                n_dept = c3.text_input("5. 부서")
                n_job = c4.text_input("6. 직책/담당업무")
                
                c5, c6 = st.columns(2)
                n_phone = c5.text_input("7. 연락처")
                n_purpose = c6.text_input("8. 사용용도", placeholder="시뮬레이션, 교육 및 정보습득 등 사용목적 기입")

                st.markdown("---")
                st.markdown("""
                <div style='background-color: #e8f4f8; padding: 15px; border-radius: 5px; border: 1px solid #b8dae6; margin-bottom: 10px;'>
                    <span style='font-size:15px; font-weight:bold; color:#1A729A;'>📝 VIP 가입 (Pro Max Mode)</span><br>
                    <span style='font-size:13px; color:#555;'>VIP 가입을 통해 나의 회사 단독 DB를 보관하고 관리할 수 있습니다. 소재 및 조건 등을 입력하고 그에 맞는 시뮬레이션과 데이터 관리가 가능합니다.</span>
                </div>
                """, unsafe_allow_html=True)
                
                is_vip_request = st.checkbox(":red[Pro Max Mode] 가입합니다.")

                st.markdown("---")
                st.markdown("""
                <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; margin-bottom: 15px;'>
                    <span style='font-size:14px; font-weight:bold; color:#D35400;'>[보안 및 개인정보 처리 방침 동의]</span><br>
                    <ul style='font-size:13px; color:#555; margin-top:5px; padding-left:20px; margin-bottom:0px;'>
                        <li>본 플랫폼의 시뮬레이션 결과는 R&D 참조용으로만 제공되며, 실제 양산 기대값 및 상세 스펙은 당사 전문가와의 별도 협의가 필요합니다.</li>
                        <li>본 플랫폼 내의 모든 데이터, 연산 알고리즘 및 도출된 시뮬레이션 결과는 당사의 엄격한 대외비 및 영업비밀에 해당합니다.</li>
                        <li>본 플랫폼에서 도출된 결과값을 바탕으로 한 의사결정에 대하여 당사는 법적 책임을 지지 않습니다.</li>
                        <li>소재 특성의 최대 활용 지원, 테스트 피드백 및 원활한 플랫폼 사용 안내를 위해 가입 시 등록된 계정 연락처로 당사 담당자가 연락을 취할 수 있습니다.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                agree_sec = st.checkbox("위 보안 및 개인정보 처리 사항에 동의합니다.")

                if st.button("가입신청", disabled=not (pw1 and pw1==pw2 and n_name and agree_sec), use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    new_user = pd.DataFrame([{
                        "Email": st.session_state.temp_email, 
                        "Password": hash_password(pw1), 
                        "Name": n_name, 
                        "Company": n_comp, 
                        "Dept": n_dept,
                        "Job": n_job,
                        "Phone": n_phone,
                        "Purpose": n_purpose,
                        "ProMax_Req": "Y" if is_vip_request else "N",
                        "RegDate": (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")
                    }])
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                    st.cache_data.clear() 
                    
                    send_welcome_email(st.session_state.temp_email, n_name)
                    
                    st.success("가입신청 완료! 환영 이메일이 발송되었습니다. 로그인 해주세요.")
                    st.session_state.show_reg = False
                    st.session_state.reg_stage = 0
                    st.rerun()

    if st.session_state.get('show_profile') and st.session_state.logged_in:
        with st.container(border=True):
            st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
            if st.session_state.get('is_admin', False): st.info("관리자 계정입니다.")
            else:
                df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
                st.markdown(f"**이메일(ID):** {st.session_state.user_email} (변경 불가)")
                
                c1, c2 = st.columns([1, 1])
                m_pw = c1.text_input("새 Password (변경 시에만 입력)", type="password")
                
                current_tier = "Pro Max" if u_row.get('ProMax_Req', 'N') == 'Y' else "Pro"
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
                
                if st.button("개인정보 수정 완료"):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                    idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                    if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                    
                    df_update.at[idx, 'Name'] = m_name
                    df_update.at[idx, 'Company'] = m_comp
                    df_update.at[idx, 'Dept'] = m_dept
                    df_update.at[idx, 'Job'] = m_job
                    df_update.at[idx, 'Phone'] = m_phone
                    df_update.at[idx, 'Purpose'] = m_purpose
                    df_update.at[idx, 'ProMax_Req'] = 'Y' if m_tier == "Pro Max" else 'N'
                    
                    conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); 
                    st.cache_data.clear() 
                    
                    st.session_state.user_name = m_name
                    st.session_state.user_tier = m_tier
                    st.session_state.show_profile = False
                    st.success("수정 완료!"); st.rerun()

    with st.container(height=900, border=False):
        st.markdown("<div id='main-scroll-anchor'></div>", unsafe_allow_html=True) 
        
        with st.container(border=True):
            ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
            st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
            sp1, c_1 = st.columns([0.02, 0.98])
            with c_1:
                if is_pro and st.session_state.workspace == "material_overall":
                    vips = get_vip_list_exact()
                    dfs = []
                    for v in vips:
                        tmp = load_cloud_data(URL_MATS, v)
                        if not tmp.empty: 
                            tmp['Is_VIP'] = True
                            dfs.append(tmp.iloc[::-1]) 
                    if not mat_df_public.empty: 
                        tmp_pub = mat_df_public.copy()
                        tmp_pub['Is_VIP'] = False
                        dfs.append(tmp_pub)
                    
                    mat_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                    mat_df = mat_df.drop_duplicates(subset=['Name'], keep='first') if not mat_df.empty else pd.DataFrame()
                    df_vip = pd.DataFrame()
                else:
                    df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame()
                    
                    _dfs = []
                    if not df_vip.empty:
                        tmp_vip = df_vip.copy()
                        tmp_vip['Is_VIP'] = True
                        _dfs.append(tmp_vip.iloc[::-1])
                    if not mat_df_public.empty:
                        tmp_pub = mat_df_public.copy()
                        tmp_pub['Is_VIP'] = False
                        _dfs.append(tmp_pub)
                    
                    mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

                m1, m2, m3, m4 = st.columns(4)
                if not mat_df.empty and 'Category' in mat_df.columns:
                    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
                    ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
                    ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist()
                    sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
                    
                    vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist()
                    def format_mat_name(name):
                        return f"💎 {name}" if name in vip_names else name
                    
                    with m1:
                        cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], format_func=format_mat_name, key="sel_cat_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 양극재 추가"):
                                n_cat = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Cat_01")
                                c_cat = st.number_input("용량 (mAh/g)", value=160.0, key="n_cat_c")
                                v_cat = st.number_input("전압 (V)", value=3.2, key="n_cat_v")
                                
                                if st.button("저장", key="btn_save_cat", use_container_width=True):
                                    try:
                                        new_row = pd.DataFrame([{"Name": n_cat, "Category": "Cathode", "Cap_Def": c_cat, "Volt_Def": v_cat, "Den_Def": 2.2}])
                                        conn = st.connection("gsheets", type=GSheetsConnection)
                                        updated_data = pd.concat([df_vip, new_row], ignore_index=True).fillna("")
                                        conn.update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=updated_data)
                                        st.cache_data.clear() 
                                        st.success("소재가 저장되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error("DB 업데이트 오류. 구글 시트 권한을 확인하세요.")

                    with m2:
                        ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], format_func=format_mat_name, key="sel_ano_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 음극재 추가"):
                                n_ano = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Ano_01")
                                c_ano = st.number_input("용량 (mAh/g)", value=360.0, key="n_ano_c")
                                v_ano = st.number_input("전압 (V)", value=0.1, key="n_ano_v")
                                
                                if st.button("저장", key="btn_save_ano", use_container_width=True):
                                    try:
                                        new_row = pd.DataFrame([{"Name": n_ano, "Category": "Anode", "Cap_Def": c_ano, "Volt_Def": v_ano, "Den_Def": 1.1}])
                                        conn = st.connection("gsheets", type=GSheetsConnection)
                                        updated_data = pd.concat([df_vip, new_row], ignore_index=True).fillna("")
                                        conn.update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=updated_data)
                                        st.cache_data.clear() 
                                        st.success("소재가 저장되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error("DB 업데이트 오류. 구글 시트 권한을 확인하세요.")

                    with m3:
                        st.selectbox("**Electrolyte**", ele_list if ele_list else ["Sample Elec"], format_func=format_mat_name, key="sel_ele_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 전해액 추가"):
                                n_ele = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Elec_01")
                                d_ele = st.number_input("밀도 (g/cc)", value=1.2, key="n_ele_d")
                                
                                if st.button("저장", key="btn_save_ele", use_container_width=True):
                                    try:
                                        new_row = pd.DataFrame([{"Name": n_ele, "Category": "Electrolyte", "Den_Def": d_ele}])
                                        conn = st.connection("gsheets", type=GSheetsConnection)
                                        updated_data = pd.concat([df_vip, new_row], ignore_index=True).fillna("")
                                        conn.update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=updated_data)
                                        st.cache_data.clear() 
                                        st.success("소재가 저장되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error("DB 업데이트 오류. 구글 시트 권한을 확인하세요.")

                    with m4:
                        st.selectbox("**Separator**", sep_list if sep_list else ["Sample Sep"], format_func=format_mat_name, key="sel_sep_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 분리막 추가"):
                                n_sep = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Sep_01")
                                t_sep = st.number_input("두께 (μm)", value=16.0, key="n_sep_t") 
                                
                                if st.button("저장", key="btn_save_sep", use_container_width=True):
                                    try:
                                        new_row = pd.DataFrame([{"Name": n_sep, "Category": "Separator", "Load_Def": t_sep}])
                                        conn = st.connection("gsheets", type=GSheetsConnection)
                                        updated_data = pd.concat([df_vip, new_row], ignore_index=True).fillna("")
                                        conn.update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=updated_data)
                                        st.cache_data.clear() 
                                        st.success("소재가 저장되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error("DB 업데이트 오류. 구글 시트 권한을 확인하세요.")
                    
                    if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                        st.markdown(
                            "<div style='text-align: left; margin-top: 15px; color: #666; font-size: 14px; font-weight: bold;'>"
                            "🔒 위 추가하는 소재는 귀사의 전용 데이터로만 저장되며, 철저히 보안 관리됩니다."
                            "</div><br>", 
                            unsafe_allow_html=True
                        )
                    
                    row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
                    def_cap_min = safe_float(row.get('Cap_Min'), 100.0)
                    def_cap_max = safe_float(row.get('Cap_Max'), 250.0)
                    def_cap_val = safe_float(row.get('Cap_Def'), 160.0)
                    
                    def_vlt_min = safe_float(row.get('Volt_Min'), 2.0)
                    def_vlt_max = safe_float(row.get('Volt_Max'), 4.5)
                    def_vlt_val = safe_float(row.get('Volt_Def'), 3.05)
                    
                    def_den_min = safe_float(row.get('Den_Min'), 1.0)
                    def_den_max = safe_float(row.get('Den_Max'), 5.0)
                    def_den_val = safe_float(row.get('Den_Def'), 4.5)
                    
                    def_lif_min = safe_int(row.get('Life_Min'), 500)
                    def_lif_max = safe_int(row.get('Life_Max'), 10000)
                    def_lif_val = safe_int(row.get('Life_Def'), 4000)
                    
                    def_lod_min = safe_float(row.get('Load_Min'), 5.0)
                    def_lod_max = safe_float(row.get('Load_Max'), 45.0)
                    def_lod_val = safe_float(row.get('Load_Def'), 14.0)
                else:
                    st.warning("Cloud에서 소재 리스트를 불러오지 못했습니다. 앱이 기본값으로 작동합니다.")
                    cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
                    def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, 160.0; def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05; def_den_min, def_den_max, def_den_val = 1.0, 5.0, 4.5; def_lif_min, def_lif_max, def_lif_val = 500, 10000, 4000; def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
            sp2, c_2 = st.columns([0.03, 0.97])
            with c_2:
                expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True)
                
                s1, s2, s3, s4 = st.columns(4)
                v_cap = s1.slider("**Capacity (mAh/g)**", min_value=def_cap_min, max_value=def_cap_max, value=def_cap_val, key=f"cap_{cat_sel}")
                v_volt = s2.slider("**Voltage (V)**", min_value=def_vlt_min, max_value=def_vlt_max, value=def_vlt_val, key=f"volt_{cat_sel}")
                v_den = s3.slider("**True Density (g/cc)**", min_value=def_den_min, max_value=def_den_max, value=def_den_val, key=f"dens_{cat_sel}", disabled=not expert)
                v_life = s4.slider("**Base Life (Cycles)**", min_value=def_lif_min, max_value=def_lif_max, value=def_lif_val, key=f"life_{cat_sel}", disabled=not expert)
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
            sp3, c_3 = st.columns([0.03, 0.97])
            with c_3:
                show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True)
                
                p1, p2, p3 = st.columns(3)
                with p1:
                    st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
                    v_load = st.slider("**Cathode Areal Loading (mg/cm2)**", min_value=def_lod_min, max_value=def_lod_max, value=def_lod_val, key=f"load_{cat_sel}")
                    v_press = st.slider("**Cathode Press Density**", 1.5, 4.0, 2.5, key="ad_c_den_m", disabled=not show_adv)
                    st.slider("**Conductive Agent %**", 0.5, 10.0, 2.0, key="ad_c_con_m", disabled=not show_adv)
                    st.slider("**Binder %**", 0.5, 10.0, 3.0, key="ad_c_bin_m", disabled=not show_adv)
                    
                    porosity = max(0.0, (1 - (v_press / v_den)) * 100) if v_den > 0 else 0
                        
                with p2:
                    st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
                    v_np = st.slider("**N/P Ratio**", 0.95, 1.50, 1.10, step=0.01, key="sl_np_m")
                    st.slider("**Anode Press Density**", 0.8, 2.0, 1.1, key="ad_a_den_m", disabled=not show_adv)
                    st.slider("**Anode Active %**", 80.0, 98.0, 95.0, key="ad_a_act_m", disabled=not show_adv)
                    
                with p3:
                    st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
                    v_act = st.slider("**Active Ratio (%)**", 80.0, 99.0, 92.0, key="sl_act_m")
                    v_ec = st.slider("**E/C Ratio (g/Ah)**", 1.0, 8.0, 3.5, key="ad_ec_m", disabled=not show_adv)
                    st.slider("**Separator Thick (μm)**", 5, 50, 16, key="ad_sep_m", disabled=not show_adv)
                    
                info1, info2 = st.columns([1, 2])
                with info1:
                    st.caption(f"**예상 공극률 (Porosity): {porosity:.1f}%**")

                w1, w2, w3 = st.columns(3)
                with w1:
                    if porosity < 20.0: st.error("⚠️ 공극률 부족: 전해액 침투 불량 위험!")
                with w2:
                    if v_np < 1.05:
                        st.error("⚠️ N/P Ratio 위험: 나트륨 석출(Na-Plating) 및 단락 위험!")
                    elif v_np >= 1.15:
                        st.warning("⚠️ N/P Ratio 과다: 잉여 음극 설계로 인한 초기 비가역 용량 증가 및 에너지 밀도 하락!")
                with w3:
                    if show_adv and v_ec < 2.0:
                        st.error("⚠️ E/C Ratio 부족: 전해액 고갈(Depletion)에 따른 수명 급감 위험!")
                        
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
            sp4, c_4 = st.columns([0.03, 0.97])
            with c_4:
                t1, t2, t3 = st.columns(3)
                with t1:
                    st.markdown('<p class="sub-header-bold">Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
                    v_te = st.slider("Energy Density", 100, 350, 250, label_visibility="collapsed")
                with t2:
                    st.markdown('<p class="sub-header-bold">Simulation C-rate</p>', unsafe_allow_html=True)
                    v_tc = st.slider("C-rate", 0.1, 10.0, 1.0, label_visibility="collapsed")
                with t3:
                    st.markdown('<p class="sub-header-bold">Cycle Life Goal</p>', unsafe_allow_html=True)
                    v_tl = st.slider("Cycle Goal", 500, 10000, 2000, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
            sp5, c_5 = st.columns([0.03, 0.97])
            with c_5:
                btn_text = "🚀 RUN SIMULATION" if st.session_state.history else "🚀 RUN SIMULATION ㅡ 아직 시뮬레이션 이력이 없습니다. 실행 버튼을 눌러 주세요."
                run_clicked = st.button(btn_text, key="btn_run_m", use_container_width=True)
                        
                if run_clicked:
                    ir_drop = 0.1 + (v_tc * 0.02)
                    cell_v = max(0.1, v_volt - ir_drop)
                    efficiency = max(0.5, 1.0 - (v_tc * 0.015))
                    res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
                    whl = res_whkg * v_press * 0.8  
                    life_cyc = int(v_life * (0.95 ** v_tc))
                    
                    cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
                    v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                    
                    log_data = {
                        "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
                        "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1),
                        "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
                        "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc,
                        "dq_x": v_axis, "dq_y": dqdv
                    }
                    
                    is_dup = False
                    if st.session_state.history:
                        last_run = st.session_state.history[0]
                        keys_to_check = ["Cathode", "Anode", "Cap(mAh/g)", "Volt(V)", "Load(mg)", "N/P Ratio", "Active(%)", "C-rate"]
                        if all(log_data[k] == last_run.get(k) for k in keys_to_check):
                            is_dup = True

                    if is_dup:
                        st.warning("⚠️ 이전 실행과 동일한 파라미터 조건입니다. (중복 저장 방지)")
                    else:
                        with st.spinner("🚀 물리 엔진 연산 및 시뮬레이션 진행 중..."):
                            time.sleep(0.6) 
                            st.session_state.history.insert(0, log_data)
                            st.session_state.sim_result = log_data
                            st.session_state.trigger_auto_bot = True 
                            st.rerun()

                if st.session_state.history:
                    st.markdown("---")
                    st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록</p>', unsafe_allow_html=True)
                    
                    log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Life(Cyc)']} Cyc" for h in st.session_state.history]
                    sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")
                    res = st.session_state.history[sel_idx]
                    
                    st.markdown("---")
                    
                    r1, r2, r3, r4 = st.columns(4)
                    delta_e = round(res['Wh/kg'] - v_te, 1)
                    r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{delta_e:+} Wh/kg (vs Target)")
                    r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off")
                    delta_v = round(res['Cell_V'] - v_volt, 2)
                    r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{delta_v:+} V (IR Drop)", delta_color="inverse")
                    delta_l = res['Life(Cyc)'] - v_tl
                    r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{delta_l:+} Cyc (vs Target)")
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">Discharge Profile</p>', unsafe_allow_html=True)
                        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                        fig1.update_layout(
                            height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white",
                            plot_bgcolor="#f4f6f9", xaxis_title="DOD (%)", yaxis_title="Voltage (V)"
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                        st.markdown("""
                        <div style='display:flex; align-items:flex-start; color:#666; font-size:13px; margin-top:5px;'>
                            <span style='margin-right:5px;'>💡</span>
                            <span style='line-height:1.4;'>고율 방전 시 분극(Polarization) 및 IR Drop에 의한 초기 과전압(Overpotential) 크기를 나타내며, Plateau 구간의 기울기가 실가용 에너지의 품질을 결정합니다.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with g2:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">dQ/dV Profile</p>', unsafe_allow_html=True)
                        fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                        fig2.update_layout(
                            height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white",
                            plot_bgcolor="#f4f6f9", xaxis_title="Voltage (V)", yaxis_title="dQ/dV"
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                        st.markdown("""
                        <div style='display:flex; align-items:flex-start; color:#666; font-size:13px; margin-top:5px;'>
                            <span style='margin-right:5px;'>💡</span>
                            <span style='line-height:1.4;'>주요 상전이(Phase transition) 구간의 가역성을 진단합니다. 피크의 브로드닝(Broadening) 및 전압 Shift 현상은 활물질의 구조적 열화나 저항 증가를 암시합니다.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with g3:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">Cell Performance</p>', unsafe_allow_html=True)
                        categories = ['Energy(Wh/kg)', 'Power(C-rate)', 'Life(Cycle)', 'Voltage(V)', 'Loading(mg)']
                        r_vals = [
                            min(100, res.get('Wh/kg', 0) / 250 * 100),
                            min(100, res.get('C-rate', 1) / 5.0 * 100),
                            min(100, res.get('Life(Cyc)', 0) / 5000 * 100),
                            min(100, res.get('Cell_V', 0) / 4.0 * 100),
                            min(100, res.get('Load(mg)', 0) / 25.0 * 100)
                        ]
                        fig3 = go.Figure()
                        fig3.add_trace(go.Scatterpolar(
                            r=r_vals, theta=categories, fill='toself', line=dict(color='#E4B526', width=2)
                        ))
                        fig3.update_layout(
                            polar=dict(
                                bgcolor="#f4f6f9", 
                                radialaxis=dict(visible=True, range=[0, 100])
                            ),
                            showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10), template="plotly_white"
                        )
                        st.plotly_chart(fig3, use_container_width=True)
                        st.markdown("""
                        <div style='display:flex; align-items:flex-start; color:#666; font-size:13px; margin-top:5px;'>
                            <span style='margin-right:5px;'>💡</span>
                            <span style='line-height:1.4;'>5대 핵심 설계 지표의 Trade-off 밸런스입니다. 특정 축의 극단적 돌출 설계는 폼팩터 패키징 한계 및 양산성 병목(Bottle-neck)의 주요 원인이 됩니다.</span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
                    df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    if not df_history.empty and 'Time' in df_history.columns:
                        df_history['Time'] = df_history['Time'].astype(str)
                    
                    st.dataframe(df_history, use_container_width=True, column_config={"Time": st.column_config.TextColumn("Time")})
            st.markdown("<br>", unsafe_allow_html=True)

        if is_pro and st.session_state.history:
            with st.container(border=True):
                st.markdown('<p class="main-header">6. Data Management & Past Records (Pro)</p>', unsafe_allow_html=True)
                sp6, c_6 = st.columns([0.03, 0.97])
                with c_6:
                    
                    db_df_all = pd.DataFrame()
                    selected_times = []
                    
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        db_df_all = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                        
                        if not db_df_all.empty and 'Email' in db_df_all.columns:
                            
                            today_str = (datetime.utcnow() + timedelta(hours=9)).strftime("%m-%d %H:%M")
                            if 'Time' in db_df_all.columns:
                                db_df_all['Time'] = db_df_all['Time'].replace("", today_str).fillna(today_str)
                                
                            my_saved_data = db_df_all[(db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace)]
                            
                            if not my_saved_data.empty:
                                my_saved_data = my_saved_data.sort_values(by='Time', ascending=False)
                                
                                df_display = my_saved_data.drop(columns=['Email', 'Workspace', 'dq_x', 'dq_y'], errors='ignore').copy()
                                if 'User Comment' not in df_display.columns:
                                    df_display['User Comment'] = ""
                                df_display['User Comment'] = df_display['User Comment'].fillna("")
                                df_display['Time'] = df_display['Time'].astype(str)
                                
                                core_cols = ['Time', 'User Comment', 'Cathode', 'Anode']
                                other_cols = [c for c in df_display.columns if c not in core_cols]
                                df_display = df_display[core_cols + other_cols]
                                df_display.insert(0, "선택", False)
                                
                                original_comments = df_display['User Comment'].tolist()
                                disabled_cols = [col for col in df_display.columns if col not in ["선택", "User Comment"]]
                                
                                st.caption("💡 **Tip:** 아래 테이블의 `📝 코멘트 입력` 열을 더블클릭하여 메모를 남기고 `Enter`를 누르면 클라우드에 자동 저장됩니다.")
                                
                                edited_df = st.data_editor(
                                    df_display, 
                                    use_container_width=True, 
                                    hide_index=True,
                                    disabled=disabled_cols,
                                    column_config={
                                        "Time": st.column_config.TextColumn("Time", disabled=True),
                                        "User Comment": st.column_config.TextColumn(
                                            "📝 코멘트 입력 (더블클릭)", 
                                            help="실제 실험 결과(Real Wh/kg)나 개선사항 등을 자유롭게 기재하여 데이터 품질을 높여주세요.",
                                            width="large",
                                            required=False
                                        )
                                    }
                                )
                                
                                current_comments = edited_df['User Comment'].tolist()
                                if current_comments != original_comments:
                                    if 'User Comment' not in db_df_all.columns:
                                        db_df_all['User Comment'] = ""
                                    
                                    for idx, row in edited_df.iterrows():
                                        mask = (db_df_all['Email'] == st.session_state.user_email) & \
                                               (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & \
                                               (db_df_all['Time'] == row['Time'])
                                        if mask.any():
                                            db_df_all.loc[mask, 'User Comment'] = row['User Comment']
                                    
                                    conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all)
                                    st.cache_data.clear()
                                
                                selected_times = edited_df[edited_df["선택"] == True]["Time"].tolist()
                            else:
                                st.info("클라우드 DB에 이전에 저장된 시뮬레이션 데이터가 없습니다.")
                    except Exception as e:
                        err_msg = str(e)
                        if "Quota exceeded" in err_msg or "429" in err_msg or "RATE_LIMIT_EXCEEDED" in err_msg:
                            st.error("⚠️ 구글 시트 API 분당 요청 한도(60회)를 초과했습니다. 약 1분 후 다시 시도해주세요.")
                        else:
                            st.warning("데이터베이스 연결에 실패하여 과거 이력을 불러오지 못했습니다.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    btn1, btn2, btn3, btn4 = st.columns(4)
                    
                    if btn1.button("💾 계정에 저장", key="btn_save_my", use_container_width=True):
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                            is_duplicate = False
                            
                            if not db_df.empty and 'Email' in db_df.columns and 'Time' in db_df.columns:
                                if not db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                                    is_duplicate = True
                                    
                            if not is_duplicate:
                                save_record = res.copy()
                                save_record['Email'] = st.session_state.user_email
                                save_record['Workspace'] = st.session_state.workspace
                                save_record['User Comment'] = "" 
                                save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True))
                            
                            if is_duplicate:
                                st.warning("이미 저장된 시뮬레이션 결과입니다.")
                            else:
                                st.cache_data.clear() 
                                st.success("내 계정에 저장하기가 완료되었습니다.")
                                st.rerun() 
                        except Exception as e: 
                            st.error(f"저장 오류: {e}")

                    if btn2.button("🗑️ 선택 삭제", key="btn_del_sel", use_container_width=True):
                        if not selected_times:
                            st.warning("삭제할 항목을 체크해 주세요.")
                        elif not db_df_all.empty:
                            try:
                                mask = ~((db_df_all['Email'] == st.session_state.user_email) & \
                                         (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & \
                                         (db_df_all['Time'].isin(selected_times)))
                                updated_db = db_df_all[mask]
                                
                                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=updated_db)
                                st.cache_data.clear() 
                                st.success(f"총 {len(selected_times)}건의 이력이 삭제되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 오류: {e}")

                    df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    buffer = io.BytesIO()
                    try:
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_export.to_excel(writer, index=False, sheet_name='Simulation_Logs')
                        file_data = buffer.getvalue()
                        file_name = f"SynoCore_Logs_{(datetime.utcnow() + timedelta(hours=9)).strftime('%m%d_%H%M')}.xlsx"
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    except ImportError:
                        file_data = df_export.to_csv(index=False).encode('utf-8-sig')
                        file_name = f"SynoCore_Logs_{(datetime.utcnow() + timedelta(hours=9)).strftime('%m%d_%H%M')}.csv"
                        mime_type = "text/csv"

                    btn3.download_button(label="📥 엑셀 다운로드", data=file_data, file_name=file_name, mime=mime_type, key="btn_excel", use_container_width=True)

                    print_clicked = btn4.button("📄 화면 PDF 인쇄", key="btn_print_pdf", use_container_width=True)
                    if print_clicked:
                        components.html("<script>window.parent.print();</script>", height=0)

# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot) AI 패널 
# -----------------------------------------------------------------------------
SYSTEM_KNOWLEDGE = """
You are 'SynoBot', an expert Sodium-Ion Battery (SIB) R&D engineer powered by OpenAI.
Answer questions accurately and professionally in Korean based on the following SIB knowledge:
- Active Ratio (%): Trade-off between energy (requires 96-98%) and power (requires <90% with more conductive agent).
- Anode: SIB uses Hard Carbon instead of Graphite due to larger Na+ size. Storage involves sloping and plateau regions.
- Anode Press Density: Hard carbon is fragile; limit is 1.0~1.2 g/cc. Higher causes particle cracking, lower reduces cycle life.
- C-rate: Speed of charge/discharge. High C-rate causes overpotential (IR drop) reducing actual capacity.
- Capacity (mAh/g): Specific capacity. SIB layered oxides typically have 120~160 mAh/g.
- Cathode Press Density: Compressing cathode reduces volume for higher Wh/L. Too high causes zero porosity (dead cell) and particle cracking.
- Cycle Life: Degrades due to SEI growth, phase transition, and micro-cracking.
- E/C Ratio (g/Ah): High ratio improves cycle life but drops Wh/kg. Low ratio (<2.0) risks sudden death by electrolyte depletion.
- N/P Ratio: Must be > 1.05 to prevent Na-Plating (dendrite short-circuit). >1.15 lowers energy density.
- Porosity: Formula is (1 - Press Density / True Density) * 100. <20% causes poor wetting.

[응답 스타일 필수 지침]
- 반드시 SIB 수석 연구원(엔지니어)의 브리핑 스타일로 작성하십시오.
- 서술형, 만연체 문장(~~습니다, ~~합니다)의 사용을 피하십시오.
- 모든 답변은 도트 블릿('- ')을 사용하여 핵심만 명확히 나열하십시오.
- 블릿 기호와 텍스트가 떨어지지 않도록 바로 붙여서 작성하십시오. (예시: - 나트륨 석출(Na-Plating) 위험 감지)
"""

GREETING_MSG = "- 안녕하세요. 배터리 설계 전문 AI 시노봇입니다.\n- 좌측의 시뮬레이터 결과 또는 SIB 설계 지식에 대해 질문해 주십시오."

if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (Beta)")
        
        with st.form("chat_input_form", clear_on_submit=True):
            c_in1, c_in2 = st.columns([0.75, 0.25])
            user_q = c_in1.text_input("질문입력", label_visibility="collapsed", placeholder="시노봇에게 질문하기...")
            if c_in2.form_submit_button("전송", use_container_width=True) and user_q:
                st.session_state.chat_messages.append({"role": "user", "content": user_q})
                st.session_state.trigger_bot_reply = True
                st.rerun()
        
        chat_container = st.container(height=730, border=True) 
        
        with chat_container:
            # 🔥 [핵심 수정] 첫 줄 가림 방지 15px Spacer 공간 확보 🔥
            st.markdown("<div id='chat-top-anchor' style='height: 15px; width: 100%;'></div>", unsafe_allow_html=True)
            
            if OpenAI is None:
                st.error("⚠️ `openai` 라이브러리 설치가 필요합니다. `requirements.txt`에 `openai`를 추가 후 앱을 재시작 해주세요.")
            elif "OPENAI_API_KEY" not in st.secrets:
                st.warning("⚠️ Streamlit Secrets에 `OPENAI_API_KEY`가 설정되지 않아 대기 중입니다.")
            else:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                
                if not st.session_state.chat_messages:
                    st.session_state.chat_messages = [{"role": "assistant", "content": GREETING_MSG}]

                if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                    st.session_state.trigger_auto_bot = False 
                    
                    auto_prompt = "방금 사용자가 새로운 파라미터로 시뮬레이션을 실행했습니다. 제공된 데이터를 분석하여 잘된 점, 개선점, 위험 요소를 도트 블릿('- ') 형태로 3~4줄 이내로 짧고 명확하게 브리핑해 주십시오."
                    sys_prompt = SYSTEM_KNOWLEDGE + f"\n\n[Current User's Simulation State]\n{st.session_state.sim_result}"
                    
                    api_messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": auto_prompt}]
                    
                    with st.chat_message("assistant"):
                        with st.spinner("📊 실시간 데이터 분석 중..."):
                            try:
                                response = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)
                                bot_reply = "📊 **[실시간 AI 진단]**\n\n" + response.choices[0].message.content
                                st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                            except Exception as e:
                                st.error(f"자동 분석 오류: {str(e)}")
                    st.rerun()

                if st.session_state.get('trigger_bot_reply'):
                    st.session_state.trigger_bot_reply = False
                    
                    sys_prompt = SYSTEM_KNOWLEDGE
                    if st.session_state.sim_result:
                        sys_prompt += f"\n\n[Current User's Simulation State]\n{st.session_state.sim_result}"
                    
                    api_messages = [{"role": "system", "content": sys_prompt}]
                    for msg in st.session_state.chat_messages:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    with st.chat_message("assistant"):
                        with st.spinner("분석 답변 작성 중..."):
                            try:
                                response = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)
                                bot_reply = response.choices[0].message.content
                                st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                            except Exception as e:
                                st.error(f"AI 연산 오류: {str(e)}")
                    st.rerun()

                for message in reversed(st.session_state.chat_messages):
                    with st.chat_message(message["role"]):
                        display_content = message["content"].replace("\n- ", "\n\n\- ")
                        if display_content.startswith("- "): 
                            display_content = "\- " + display_content[2:]
                        st.markdown(display_content)
            
            # 🔥 [핵심 수정] 채팅 메시지 렌더링 직후 스크롤을 무조건 최상단으로 끌어올리는 JS 강제 주입 🔥
            components.html("""
                <script>
                    setTimeout(function() {
                        const doc = window.parent.document;
                        const anchor = doc.getElementById('chat-top-anchor');
                        if (anchor) {
                            let parent = anchor.parentElement;
                            while (parent) {
                                const style = window.parent.getComputedStyle(parent);
                                if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                                    parent.scrollTop = 0;
                                    break;
                                }
                                parent = parent.parentElement;
                            }
                        }
                    }, 100);
                </script>
            """, height=0)

# 7. 푸터 
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)