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

# [라이브러리 예외 처리]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 전역 디자인 (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore Pro Max 1.7 (beta)", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@900&display=swap');
    
    /* 기본 요소 및 스트림릿 로고 숨김 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stLogo"] {display: none !important;}
    .viewerBadge_container__1JCIV {display: none !important;} 
    
    /* 전역 스크롤바 투명화 (휠은 작동) */
    ::-webkit-scrollbar { width: 0px !important; height: 0px !important; background: transparent !important; }
    * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
    
    /* 대시보드 최대폭 (10:65:25 비율 대응) */
    .main .block-container { max-width: 1550px !important; padding-top: 1.5rem; padding-bottom: 2rem; margin: auto; }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 60px; }
    .syno-title { color: #1A729A; font-size: 42px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #D35400; font-size: 18px; font-weight: bold; padding-top: 14px; }
    
    /* 🔥 지표 박스: 굵은 제목 & 글자/숫자 완벽 중앙 정렬 🔥 */
    div[data-testid="stMetric"] { 
        background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; 
        padding: 15px !important; height: 130px; display: flex; flex-direction: column; 
        justify-content: center !important; align-items: center !important; text-align: center !important;
    }
    div[data-testid="stMetricLabel"] { display: flex; justify-content: center !important; width: 100%; }
    div[data-testid="stMetricLabel"] > div { font-weight: 800 !important; font-size: 16px !important; color: #333 !important; text-align: center !important; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; font-weight: 900 !important; text-align: center !important; width: 100%; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; justify-content: center !important; width: 100%; }
    
    /* 🔥 실행 버튼 높이 20% 증가 🔥 */
    div.st-key-btn_run_m > button {
        height: 60px !important; background-color: #1A729A !important; color: white !important; 
        font-weight: bold !important; font-size: 18px !important; border-radius: 8px !important; width: 100%; border: none !important;
    }
    
    /* 일반 버튼 디자인 */
    div[data-testid="stButton"] > button { height: 42px !important; background-color: #1A729A !important; color: white !important; font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100%; border: none !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 20px !important; }
    
    .main-header { font-size: 24px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 15px; padding-right: 15px; }
    
    /* 토글 디자인 */
    div[data-testid="stToggle"] { background-color: #F4CE14; border: 1px solid #D4AC0D; padding: 0px 15px; border-radius: 4px; height: 40px; display: flex; align-items: center; justify-content: center; margin-top: 10px; }
    div[data-testid="stToggle"] > label { margin-bottom: 0px !important; font-size: 15px !important; color: #333 !important; width: 100%; display: flex; justify-content: center; }
    
    /* 시노봇 들여쓰기 제거 및 세로 배치 */
    div[data-testid="stChatMessage"] {
        display: flex !important; flex-direction: column !important; align-items: flex-start !important;
        gap: 5px !important; padding: 15px 10px !important; background-color: #ffffff;
        border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; box-shadow: 0px 2px 5px rgba(0,0,0,0.02);
    }
    div[data-testid="stChatMessage"] > div:first-child { margin-bottom: 5px !important; }
    div[data-testid="stChatMessageContent"] { margin-left: 0px !important; padding-left: 0px !important; width: 100% !important; }
    div[data-testid="stTextInput"] input { height: 45px !important; font-size: 15px !important; border: 2px solid #1A729A !important; border-radius: 6px; }
    
    /* 🔥 사용자 코멘트 셀 배경색 & 헤더 검정색 🔥 */
    th[data-testid="stTableColumnHeader"] { color: #000000 !important; font-weight: bold !important; }
    td[data-testid="stTableCell"]:nth-child(3) { background-color: #F3F0F4 !important; color: black !important; }

    /* PDF 인쇄 버튼 */
    .print-btn {
        display: flex; justify-content: center; align-items: center; height: 42px; background-color: #FFCA28; color: #222 !important; 
        font-weight: bold; font-size: 15px; border-radius: 4px; border: 1px solid #E4B526; text-decoration: none; width: 100%; cursor: pointer; transition: 0.2s;
    }
    .print-btn:hover { background-color: #FFB300; }
    
    /* 🔥 S & C 로고 애니메이션 🔥 */
    .anim-logo-container { display: flex; justify-content: center; align-items: center; height: 100px; padding-top: 15px; overflow: hidden; }
    .logo-s { font-family: 'Noto Sans KR', sans-serif; font-weight: 900; font-size: 70px; color: #BFBFBF; display: inline-block; animation: spin-s 1.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }
    .logo-c { font-family: 'Noto Sans KR', sans-serif; font-weight: 900; font-size: 70px; color: #BFBFBF; display: inline-block; margin-left: -20px; animation: spin-c 1.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }
    @keyframes spin-s { 0% { transform: translateX(-150px) rotate(-360deg); opacity: 0; } 100% { transform: translateX(0) rotate(0deg); opacity: 1; } }
    @keyframes spin-c { 0% { transform: translateX(150px) rotate(360deg); opacity: 0; } 100% { transform: translateX(0) rotate(0deg); opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 설정 및 유틸리티
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=600)
def load_cloud_data(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
    except Exception: pass
    return pd.DataFrame()

mat_df_public = load_cloud_data(URL_MATS, "material_list")

def get_vip_list_exact():
    df = load_cloud_data(URL_USERS, "VIPs")
    if not df.empty and 'Company' in df.columns:
        return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()]
    return []

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
    except Exception: return False

def get_dqdv(cat_sel, v_tc, m_df=None):
    v_axis = np.linspace(2.0, 4.2, 150)
    dqdv = np.zeros_like(v_axis)
    p1, p2 = 3.15, 0.0 
    if m_df is not None and not m_df.empty and 'Name' in m_df.columns:
        mat_row = m_df[m_df['Name'] == cat_sel]
        if not mat_row.empty:
            try:
                p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15))
                p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
            except: pass
    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]
    if not peaks: peaks = [3.15]
    for p in peaks:
        shifted_p = float(p) - (float(v_tc) * 0.015)
        dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
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
            row_dict = row.to_dict()
            row_dict.pop('Email', None)
            row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: 
                    row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'] = v_x
            row_dict['dq_y'] = v_y
            hist.append(row_dict)
        return hist[::-1] # 최신순 반환
    except: return []

# -----------------------------------------------------------------------------
# 3. 세션 초기화 및 전역 변수 설정
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'material_overall', 'user_vip_name': None, 'is_admin': False,
    'admin_view': None, 'admin_ws': None, 'chat_messages': [], 
    'show_bot': True, 'trigger_auto_bot': False, 'process_ai': False
}
for key, val in default_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

is_pro = st.session_state.logged_in

# -----------------------------------------------------------------------------
# 4. 헤더 영역 (🔥 0.08 : 0.67 : 0.25 상하단 완벽 동기화 🔥)
# -----------------------------------------------------------------------------
if st.session_state.show_bot:
    h_logo, h_main, h_bot = st.columns([0.08, 0.67, 0.25], gap="large")
else:
    h_logo, h_main = st.columns([0.08, 0.92], gap="large")
    h_bot = None

with h_main:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">1.7 (beta)</span></div>', unsafe_allow_html=True)

target_col = h_bot if st.session_state.show_bot else h_main

with target_col:
    if not is_pro:
        c1, c2 = st.columns([1, 1])
        with c1.popover("Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                if st.form_submit_button("로그인", use_container_width=True):
                    df_u = get_user_db()
                    u_id_clean = u_id.strip().lower()
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_overall'})
                        st.session_state.history = load_user_history(u_id_clean, 'material_overall')
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hash_password(u_pw))] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            domain = u_id_clean.split('@')[1].split('.')[0].lower()
                            vip_map = {v.lower(): v for v in get_vip_list_exact()}
                            st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list'})
                            st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                            st.rerun()
                        else: st.error("계정 정보를 확인해주세요.")
        
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): 
            st.session_state.show_reg = not st.session_state.show_reg
            st.session_state.show_profile = False
            st.rerun()
    else:
        r_info, r_btn = st.columns([2, 1])
        level_tag = "Pro Max User" if st.session_state.user_vip_name else "Pro User"
        r_info.markdown(f'<div class="user-greeting">{st.session_state.user_name} ({level_tag})</div>', unsafe_allow_html=True)
        if r_btn.button("Logout", key="btn_logout_m", use_container_width=True): 
            st.session_state.clear()
            st.rerun()

    st.columns([1, 1])[1].toggle("**💬 SynoBot 활성화**", value=st.session_state.show_bot, key="bot_toggle_ui")
    if st.session_state.bot_toggle_ui != st.session_state.show_bot:
        st.session_state.show_bot = st.session_state.bot_toggle_ui
        st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 👑 [최고 관리자 전용 대시보드] - 화면 전체 폭 사용
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    if st.session_state.admin_view is not None or st.session_state.show_profile is False:
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
            a1, a2, a3, a4, a5 = st.columns(5)
            
            if a1.button("👥 유저 관리 DB", use_container_width=True):
                st.session_state.admin_view = 'users' if st.session_state.admin_view != 'users' else None
                st.session_state.admin_ws = 'Users'
                st.rerun()
            if a2.button("🔋 소재 DB", use_container_width=True):
                st.session_state.admin_view = 'mats' if st.session_state.admin_view != 'mats' else None
                st.session_state.admin_ws = 'material_overall'
                st.rerun()
            if a3.button("⚙️ 파라미터 DB", use_container_width=True):
                st.session_state.admin_view = 'param' if st.session_state.admin_view != 'param' else None
                st.session_state.admin_ws = 'param_config'
                st.rerun()
            if a4.button("💾 로그 DB", use_container_width=True):
                st.session_state.admin_view = 'logs' if st.session_state.admin_view != 'logs' else None
                st.session_state.admin_ws = 'myData'
                st.rerun()
            if a5.button("🤖 챗봇 로그 DB", use_container_width=True):
                st.session_state.admin_view = 'bot_logs' if st.session_state.admin_view != 'bot_logs' else None
                st.rerun()

            if st.session_state.admin_view:
                st.markdown("---")
                if st.session_state.admin_view == 'bot_logs':
                    st.markdown('<p class="sub-header-bold">🤖 사용자별 시노봇 대화 이력 (현재 세션)</p>', unsafe_allow_html=True)
                    if st.session_state.chat_messages:
                        st.dataframe(pd.DataFrame(st.session_state.chat_messages), use_container_width=True)
                    else: st.info("기록된 대화가 없습니다.")
                else:
                    st.markdown('<p class="sub-header-bold">🛠️ 인라인 데이터베이스 편집기</p>', unsafe_allow_html=True)
                    if st.session_state.admin_view == 'users': target_url = URL_USERS; ws_options = ["Users", "VIPs"]
                    elif st.session_state.admin_view == 'mats': target_url = URL_MATS; ws_options = ["material_overall", "material_list"] + get_vip_list_exact()
                    elif st.session_state.admin_view == 'param': target_url = URL_PARAM; ws_options = ["param_config"]
                    elif st.session_state.admin_view == 'logs': target_url = URL_LOGS; ws_options = ["myData"]
                    
                    if len(ws_options) > 1:
                        sel_ws_admin = st.selectbox("📂 워크스페이스 선택", ws_options, index=ws_options.index(st.session_state.admin_ws) if st.session_state.admin_ws in ws_options else 0)
                        if sel_ws_admin != st.session_state.admin_ws:
                            st.session_state.admin_ws = sel_ws_admin; st.rerun()
                    
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'material_overall':
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
                            original_cols = df_admin.columns.tolist()
                            df_display = df_admin.copy()
                            is_log_view = (st.session_state.admin_view == 'logs')
                            
                            if is_log_view and not df_display.empty:
                                front_cols = [c for c in ['Workspace', 'Email', 'Time'] if c in original_cols]
                                other_cols = [c for c in original_cols if c not in front_cols]
                                df_display = df_display[front_cols + other_cols]
                                df_display = df_display.iloc[::-1].reset_index(drop=True)
                            
                            edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}")
                            
                            if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                                try:
                                    save_df = edited_df.copy()
                                    if is_log_view and not save_df.empty: save_df = save_df.iloc[::-1].reset_index(drop=True)
                                    if set(original_cols) == set(save_df.columns): save_df = save_df[original_cols]
                                    conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=save_df.fillna(""))
                                    st.cache_data.clear()
                                    st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                                except Exception as e:
                                    st.error(f"저장 오류: {e}")
                    except Exception as e:
                        st.error(f"데이터 로드 오류: {e}")

# -----------------------------------------------------------------------------
# 6. 메인 바디 (✅ 0.08 : 0.67 : 0.25 레이아웃 - 상단 라인과 일치)
# -----------------------------------------------------------------------------
if st.session_state.show_bot:
    col_logo, col_main, col_bot = st.columns([0.08, 0.67, 0.25], gap="large")
else:
    col_logo, col_main = st.columns([0.08, 0.92], gap="large")
    col_bot = None

# (A) 좌측 패널 - 로고 애니메이션 적용
with col_logo:
    st.markdown('<div class="logo-wrapper">', unsafe_allow_html=True)
    if os.path.exists("sc_logo.png"):
        st.image("sc_logo.png", use_container_width=True)
    elif os.path.exists("sc_logo.jpg"):
        st.image("sc_logo.jpg", use_container_width=True)
    else:
        st.markdown("""
            <div class="anim-logo-container">
                <div class="logo-s">S</div><div class="logo-c">C</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# (B) 중앙 패널 - 유저 폼 및 시뮬레이터 (메인 폭 안에서만 표시)
with col_main:
    # 계정 가입 폼
    if st.session_state.show_reg and not is_pro:
        with st.container(border=True):
            st.markdown('<p class="main-header">📝 계정 가입 (Pro Mode)</p>', unsafe_allow_html=True)
            col_reg1, col_reg2 = st.columns(2)
            reg_email = col_reg1.text_input("회사 이메일 주소")
            reg_name = col_reg2.text_input("성함")
            reg_pw = col_reg1.text_input("비밀번호 설정", type="password")
            reg_pw_chk = col_reg2.text_input("비밀번호 확인", type="password")
            reg_comp = col_reg1.text_input("회사명")
            reg_job = col_reg2.text_input("직책/담당업무")
            
            st.markdown("<div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; margin-bottom: 15px;'><span style='font-size:14px; font-weight:bold; color:#D35400;'>[보안 및 개인정보 처리 방침 동의]</span><br><ul style='font-size:13px; color:#555; margin-top:5px; padding-left:20px; margin-bottom:0px;'><li>본 플랫폼 내의 모든 데이터와 도출된 시뮬레이션 결과는 영업비밀에 해당합니다.</li></ul></div>", unsafe_allow_html=True)
            agree_sec = st.checkbox("위 보안 및 개인정보 처리 사항에 동의합니다.")
            
            if st.button("가입 신청서 제출", disabled=not (reg_pw and reg_pw==reg_pw_chk and agree_sec), use_container_width=True):
                conn = st.connection("gsheets", type=GSheetsConnection)
                df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                new_user = pd.DataFrame([{"Email": reg_email, "Password": hash_password(reg_pw), "Name": reg_name, "Company": reg_comp, "Job": reg_job, "ProMax_Req": "Y", "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                st.cache_data.clear() 
                st.success("가입신청 완료! 담당자 승인 후 로그인해 주세요.")
                st.session_state.show_reg = False
                st.rerun()

    # 정보 수정 폼
    if st.session_state.get('show_profile') and is_pro:
        with st.container(border=True):
            st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
            st.markdown(f"**이메일(ID):** {st.session_state.user_email}")
            p1, p2 = st.columns(2)
            m_pw = p1.text_input("새 Password (변경시에만 입력)", type="password")
            m_name = p2.text_input("이름", value=st.session_state.user_name)
            if st.button("개인정보 수정 완료", use_container_width=True):
                conn = st.connection("gsheets", type=GSheetsConnection)
                df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                df_update.at[idx, 'Name'] = m_name
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update)
                st.cache_data.clear()
                st.session_state.user_name = m_name
                st.session_state.show_profile = False
                st.success("수정 완료!")
                st.rerun()

    # 시뮬레이터 본문
    with st.container(border=False):
        with st.container(border=True):
            ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
            st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
            
            mat_df = pd.DataFrame()
            if is_pro and st.session_state.workspace == "material_overall":
                vips = get_vip_list_exact()
                dfs = []
                for v in vips:
                    tmp = load_cloud_data(URL_MATS, v)
                    if not tmp.empty: dfs.append(tmp.assign(Is_VIP=True).iloc[::-1])
                if not mat_df_public.empty: dfs.append(mat_df_public.copy().assign(Is_VIP=False))
                mat_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if dfs else pd.DataFrame()
                df_vip = pd.DataFrame()
            else:
                df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame()
                _dfs = []
                if not df_vip.empty: _dfs.append(df_vip.copy().assign(Is_VIP=True).iloc[::-1])
                if not mat_df_public.empty: _dfs.append(mat_df_public.copy().assign(Is_VIP=False))
                mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

            m1, m2, m3, m4 = st.columns(4)
            if not mat_df.empty and 'Category' in mat_df.columns:
                cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
                ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
                ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist()
                sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
                vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist()
                
                def format_mat_name(name): return f"💎 {name}" if name in vip_names else name
                
                with m1:
                    cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], format_func=format_mat_name)
                with m2:
                    ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], format_func=format_mat_name)
                with m3:
                    st.selectbox("**Electrolyte**", ele_list if ele_list else ["Sample Elec"], format_func=format_mat_name)
                with m4:
                    st.selectbox("**Separator**", sep_list if sep_list else ["Sample Sep"], format_func=format_mat_name)
                
                row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
                def_cap_val = safe_float(row.get('Cap_Def'), 160.0)
                def_vlt_val = safe_float(row.get('Volt_Def'), 3.05)
                def_den_val = safe_float(row.get('Den_Def'), 4.5)
                def_lif_val = safe_int(row.get('Life_Def'), 4000)
                def_lod_val = safe_float(row.get('Load_Def'), 14.0)
            else:
                cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
                def_cap_val, def_vlt_val, def_den_val, def_lif_val, def_lod_val = 160.0, 3.05, 4.5, 4000, 14.0

        with st.container(border=True):
            st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
            expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 (Pro Mode 전용)", disabled=True)
            s1, s2, s3, s4 = st.columns(4)
            # 모바일 튐 현상 방지: step 속성 명시
            v_cap = s1.slider("**Capacity (mAh/g)**", 100.0, 250.0, def_cap_val, step=1.0)
            v_volt = s2.slider("**Voltage (V)**", 2.0, 4.5, def_vlt_val, step=0.01)
            v_den = s3.slider("**True Density (g/cc)**", 1.0, 5.0, def_den_val, step=0.1, disabled=not expert)
            v_life = s4.slider("**Base Life (Cycles)**", 500, 10000, def_lif_val, step=100, disabled=not expert)

        with st.container(border=True):
            st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
            show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 (Pro Mode 전용)", disabled=True)
            p1, p2, p3 = st.columns(3)
            with p1:
                v_load = st.slider("**Cathode Loading (mg/cm2)**", 5.0, 45.0, def_lod_val, step=0.5)
                v_press = st.slider("**Cathode Press Density**", 1.5, 4.0, 2.5, step=0.1, disabled=not show_adv)
                porosity = max(0.0, (1 - (v_press / v_den)) * 100) if v_den > 0 else 0
            with p2:
                v_np = st.slider("**N/P Ratio**", 0.95, 1.50, 1.10, step=0.01)
                st.slider("**Anode Press Density**", 0.8, 2.0, 1.1, step=0.1, disabled=not show_adv)
            with p3:
                v_act = st.slider("**Active Ratio (%)**", 80.0, 99.0, 92.0, step=0.5)
                v_ec = st.slider("**E/C Ratio (g/Ah)**", 1.0, 8.0, 3.5, step=0.1, disabled=not show_adv)
            
            info_col, _ = st.columns([1, 2])
            with info_col: 
                st.caption(f"**예상 공극률 (Porosity): {porosity:.1f}%**")
            w1, w2, w3 = st.columns(3)
            if porosity < 20.0: w1.error("⚠️ 공극률 부족 위험!")
            if v_np < 1.05: w2.error("⚠️ N/P Ratio 위험: 나트륨 석출!")

        with st.container(border=True):
            st.markdown('<p class="main-header">4. Target Settings & Simulation</p>', unsafe_allow_html=True)
            t1, t2, t3 = st.columns(3)
            v_te = t1.slider("Energy Density Target", 100, 350, 250, step=5, label_visibility="collapsed")
            v_tc = t2.slider("C-rate Target", 0.1, 10.0, 1.0, step=0.1, label_visibility="collapsed")
            v_tl = t3.slider("Cycle Goal Target", 500, 10000, 2000, step=100, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 🔥 실행 버튼 (높이 20% 증가 적용)
            run_clicked = st.button("🚀 RUN SIMULATION", key="btn_run_m")
            
            if run_clicked:
                ir_drop = 0.1 + (v_tc * 0.02)
                cell_v = max(0.1, v_volt - ir_drop)
                efficiency = max(0.5, 1.0 - (v_tc * 0.015))
                res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
                whl = res_whkg * v_press * 0.8  
                life_cyc = int(v_life * (0.95 ** v_tc))
                v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                
                log_data = {
                    "Time": (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S"),
                    "Cathode": cat_sel, "Anode": ano_sel, "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1),
                    "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
                    "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc,
                    "dq_x": v_axis, "dq_y": dqdv
                }
                
                # 🔥 시뮬레이션 중복 실행(클릭) 방지 로직 
                is_dup = False
                if st.session_state.history:
                    last_run = st.session_state.history[0]
                    keys_check = ["Cathode", "Anode", "Cap(mAh/g)", "Volt(V)", "Load(mg)", "N/P Ratio", "Active(%)", "C-rate"]
                    if all(log_data[k] == last_run.get(k) for k in keys_check): 
                        is_dup = True

                if is_dup:
                    st.warning("⚠️ 이전 실행과 파라미터가 동일합니다. (중복 저장 방지)")
                else:
                    with st.spinner("🚀 물리 엔진 연산 진행 중..."):
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
                
                # ✅ 지표 제목 굵게, 내용 완벽 중앙 정렬 (CSS 반영)
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg'] - v_te, 1):+} Wh/kg (vs Target)")
                r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off")
                r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{round(res['Cell_V'] - v_volt, 2):+} V (IR Drop)", delta_color="inverse")
                r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{res['Life(Cyc)'] - v_tl:+} Cyc (vs Target)")
                
                # 🔥 그래프 하단 여유 공간 추가 🔥
                st.markdown("<br><br>", unsafe_allow_html=True)
                
                g1, g2, g3 = st.columns(3)
                with g1:
                    st.markdown('<p class="sub-header-bold" style="text-align: center;">Discharge Profile</p>', unsafe_allow_html=True)
                    fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                    fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
                    st.plotly_chart(fig1, use_container_width=True)
                with g2:
                    st.markdown('<p class="sub-header-bold" style="text-align: center;">dQ/dV Profile</p>', unsafe_allow_html=True)
                    fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                    fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
                    st.plotly_chart(fig2, use_container_width=True)
                with g3:
                    st.markdown('<p class="sub-header-bold" style="text-align: center;">Cell Performance</p>', unsafe_allow_html=True)
                    r_vals = [min(100, res.get('Wh/kg', 0)/250*100), min(100, res.get('C-rate', 1)/5.0*100), min(100, res.get('Life(Cyc)', 0)/5000*100), min(100, res.get('Cell_V', 0)/4.0*100), min(100, res.get('Load(mg)', 0)/25.0*100)]
                    fig3 = go.Figure(go.Scatterpolar(r=r_vals, theta=['Energy', 'Power', 'Life', 'Voltage', 'Load'], fill='toself', line=dict(color='#E4B526', width=2)))
                    fig3.update_layout(polar=dict(bgcolor="#f4f6f9", radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10), template="plotly_white")
                    st.plotly_chart(fig3, use_container_width=True)
                    
                st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
                
                # 표
                st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
                df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                st.dataframe(df_history, use_container_width=True)

        if is_pro and st.session_state.history:
            with st.container(border=True):
                st.markdown('<p class="main-header">6. Data Management & Past Records (Pro)</p>', unsafe_allow_html=True)
                btn1, btn2, btn3 = st.columns(3)
                
                if btn1.button("💾 계정에 현재 결과 저장", key="btn_save_my", use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                    save_rec = res.copy()
                    save_rec['Email'] = st.session_state.user_email
                    save_rec['Workspace'] = st.session_state.workspace
                    save_rec['User Comment'] = ""
                    save_rec.pop('dq_x', None); save_rec.pop('dq_y', None)
                    conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_rec])], ignore_index=True))
                    st.cache_data.clear()
                    st.success("저장 완료!")

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer: 
                    df_history.to_excel(writer, index=False)
                btn2.download_button(label="📥 엑셀 다운로드", data=buffer.getvalue(), file_name="SynoCore_Logs.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
                
                # 🔥 브라우저 기본 PDF 인쇄 (경고 문구 삭제) 🔥
                btn3.markdown('<a href="javascript:window.print()" class="print-btn">📄 화면 인쇄 (PDF 저장)</a>', unsafe_allow_html=True)

                st.markdown("---")
                
                # 클라우드 이력 (코멘트 자동저장 및 최신순 정렬)
                conn = st.connection("gsheets", type=GSheetsConnection)
                db_df_all = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                if not db_df_all.empty and 'Email' in db_df_all.columns:
                    my_saved_data = db_df_all[(db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace)]
                    if not my_saved_data.empty:
                        # 최신순 정렬 보장
                        my_saved_data = my_saved_data.sort_values(by='Time', ascending=False)
                        
                        col_title, col_btn_del = st.columns([0.8, 0.2])
                        with col_title:
                            st.markdown('<p class="sub-header-bold">🗄️ 내 클라우드 저장 이력</p>', unsafe_allow_html=True)
                        
                        df_display = my_saved_data.drop(columns=['Email', 'Workspace', 'dq_x', 'dq_y'], errors='ignore').copy()
                        if 'User Comment' not in df_display.columns: df_display['User Comment'] = ""
                        
                        core_cols = ['Time', 'User Comment', 'Cathode', 'Anode']
                        other_cols = [c for c in df_display.columns if c not in core_cols]
                        df_display = df_display[core_cols + other_cols]
                        df_display.insert(0, "선택", False)
                        
                        # 🔥 사용자 코멘트 더블클릭 자동 저장 로직 (저장 버튼 삭제 완료) 🔥
                        def on_editor_change():
                            if st.session_state.get('log_editor') and 'edited_rows' in st.session_state.log_editor:
                                changes = st.session_state.log_editor['edited_rows']
                                if changes:
                                    conn_u = st.connection("gsheets", type=GSheetsConnection)
                                    db_u = conn_u.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                                    for row_idx_str, col_updates in changes.items():
                                        row_idx = int(row_idx_str)
                                        target_time = df_display.iloc[row_idx]['Time']
                                        if "User Comment" in col_updates:
                                            new_comment = col_updates["User Comment"]
                                            mask = (db_u['Email'] == st.session_state.user_email) & (db_u.get('Workspace') == st.session_state.workspace) & (db_u['Time'] == target_time)
                                            if mask.any(): db_u.loc[mask, 'User Comment'] = new_comment
                                    conn_u.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_u)
                                    st.cache_data.clear()
                                    
                        edited_df = st.data_editor(
                            df_display, 
                            key="log_editor",
                            use_container_width=True, 
                            hide_index=True,
                            disabled=[c for c in df_display.columns if c not in ["선택", "User Comment"]],
                            on_change=on_editor_change,
                            column_config={
                                "User Comment": st.column_config.TextColumn("💬 사용자 코멘트 (더블클릭)", width="large")
                            }
                        )
                        st.caption("ℹ️ 셀 색상이 지정된 '사용자 코멘트' 칸을 더블클릭하여 내용을 입력하고 바깥 영역을 누르면 **자동으로 클라우드에 저장**됩니다.")

                        with col_btn_del:
                            selected_times = edited_df[edited_df["선택"] == True]["Time"].tolist()
                            if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
                                if not selected_times:
                                    st.warning("삭제할 항목을 체크해 주세요.")
                                else:
                                    mask = ~((db_df_all['Email'] == st.session_state.user_email) & \
                                             (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & \
                                             (db_df_all['Time'].isin(selected_times)))
                                    updated_db = db_df_all[mask]
                                    conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=updated_db)
                                    st.cache_data.clear() 
                                    st.success(f"총 {len(selected_times)}건의 이력이 삭제되었습니다.")
                                    st.rerun()

# -----------------------------------------------------------------------------
# (C) 우측 패널 - 🤖 시노봇 (SynoBot) AI 패널 
# -----------------------------------------------------------------------------
# 🔥 프롬프트: 부드러운 톤, 도트 블릿 강조, Pro Mode 영업 유도 추가 🔥
SYSTEM_KNOWLEDGE = """
You are 'SynoBot', an expert Sodium-Ion Battery (SIB) R&D engineer powered by OpenAI. Answer in Korean.
[Style Guide & Constraints]
1. Use a soft but professional engineering tone. (너무 딱딱하지 않게 자연스럽게)
2. IMPORTANT: Highlight key metrics, specs, and critical risks using ONLY dot bullets (- ).
3. DO NOT put a space between the bullet and the text (e.g., -에너지 밀도: 160Wh/kg).
4. If a user asks a general question, casually mention at the end: "\n\n💡 팁: Pro Mode로 전환하시면 귀사만의 단독 데이터 보안 관리 및 맞춤형 고급 시뮬레이션 정보를 제공받으실 수 있습니다."
"""

if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (Beta)")
        
        # 1. 채팅 입력창을 대화창 위에 배치 (역방향)
        def bot_submit():
            val = st.session_state.bot_input_field.strip()
            if val:
                st.session_state.chat_messages.append({"role": "user", "content": val})
                st.session_state.process_ai = True
                st.session_state.bot_input_field = ""

        st.text_input("질문을 입력하세요 (Enter)", key="bot_input_field", on_change=bot_submit, placeholder="시뮬레이션 분석 요청...")

        # 2. AI 연산
        if OpenAI and "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
            # 시뮬레이션 직후 자동 분석
            if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                st.session_state.trigger_auto_bot = False
                sys_msg = SYSTEM_KNOWLEDGE + f"\n\n[User's Current Simulation Result]\n{st.session_state.sim_result}"
                user_msg = "방금 시뮬레이션이 실행됨. 위 데이터를 분석해서 잘된 점과 위험 요소를 부드러운 엔지니어 관점에서 짧게 브리핑해. 핵심 수치와 위험요소는 무조건 도트 블릿(- )으로 강조할 것."
                with st.spinner("데이터 분석 중..."):
                    try:
                        resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}])
                        st.session_state.chat_messages.append({"role": "assistant", "content": "📊 **[AI 분석 리포트]**\n\n" + resp.choices[0].message.content})
                    except: pass

            # 일반 질문 답변
            elif st.session_state.process_ai:
                st.session_state.process_ai = False
                sys_msg = SYSTEM_KNOWLEDGE + (f"\n\n[User's Simulation Result]\n{st.session_state.sim_result}" if st.session_state.sim_result else "")
                msg_list = [{"role": "system", "content": sys_msg}] + st.session_state.chat_messages[-5:]
                with st.spinner("답변 작성 중..."):
                    try:
                        resp = client.chat.completions.create(model="gpt-4o-mini", messages=msg_list)
                        st.session_state.chat_messages.append({"role": "assistant", "content": resp.choices[0].message.content})
                    except: pass

        # 3. 최근 대화가 맨 위로 오는 역방향 컨테이너 (고정 높이 해제 -> 본문 길이에 맞춰 늘어남)
        with st.container(border=True):
            if not st.session_state.chat_messages:
                st.info("-안녕하세요. 배터리 설계 전문 시노봇입니다.\n-상단의 입력창에 분석 요청이나 기술 질문을 남겨주십시오.")
            
            for m in reversed(st.session_state.chat_messages):
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

# -----------------------------------------------------------------------------
# 7. 푸터 (기업 정보 및 카피라이트 중앙 정렬)
# -----------------------------------------------------------------------------
st.markdown("""
    <br><hr>
    <div style='text-align: center; color: #888; font-size: 13px; line-height: 1.6; margin-bottom: 20px;'>
        SynoTech Co., Ltd. l 687-88-01333<br>
        410, Industry-University Cooperation Building, Dankook University<br>
        152, Jukjeon-ro, Suji-gu, Yongin-si, Gyeonggi-do, South Korea<br>
        ☎️ +82 50 6020 8318 ㅣ 📧 cs@synotech.co.kr<br><br>
        ⓒ 2026. SynoTech. All rights reserved.
    </div>
""", unsafe_allow_html=True)