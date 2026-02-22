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

# [PDF 라이브러리 예외 처리]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

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
# 1. 페이지 설정 및 디자인 (스크롤바 숨김 + 챗봇 스타일링 + 로고 중앙 정렬)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore Pro Max 1.7 (beta)", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* 스크롤바 트랙 숨기기 */
    ::-webkit-scrollbar { width: 0px !important; height: 0px !important; background: transparent !important; }
    * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
    
    .main .block-container { max-width: 1400px !important; padding-top: 2rem; padding-bottom: 2rem; margin: auto; }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 60px; }
    .syno-title { color: #1A729A; font-size: 44px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #D35400; font-size: 20px; font-weight: bold; padding-top: 16px; }
    
    div.st-key-btn_home_overlay { margin-top: -60px !important; opacity: 0 !important; z-index: 999 !important; height: 60px !important; width: 350px !important; overflow: hidden !important; }
    div.st-key-btn_home_overlay button { height: 100% !important; width: 100% !important; cursor: pointer !important; }
    
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px 15px 10px 15px; height: 120px; display: flex; flex-direction: column; justify-content: flex-start; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; color: #1A729A !important; margin-top: 5px; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; margin-top: 3px; }
    
    div[data-testid="stButton"] > button { height: 40px !important; background-color: #1A729A !important; color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: none !important; }
    div[data-testid="stDownloadButton"] > button { height: 40px !important; background-color: #FFCA28 !important; color: #222 !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: 1px solid #E4B526 !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #FFB300 !important; border: 1px solid #DDA010 !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 20px !important; }
    
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    
    div[data-testid="stToggle"] { background-color: #F4CE14; border: 1px solid #D4AC0D; padding: 0px 15px; border-radius: 4px; height: 40px; display: flex; align-items: center; justify-content: center; margin-top: 10px; }
    div[data-testid="stToggle"] > label { margin-bottom: 0px !important; font-size: 15px !important; color: #333 !important; width: 100%; display: flex; justify-content: center; }
    
    /* 챗봇 메시지 스타일링 (들여쓰기 제거, 위아래 배치) */
    div[data-testid="stChatMessage"] { display: flex !important; flex-direction: column !important; align-items: flex-start !important; padding: 15px 10px !important; background-color: #ffffff; border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; box-shadow: 0px 2px 5px rgba(0,0,0,0.02); }
    div[data-testid="stChatMessage"] > div[data-testid="stChatMessageAvatar"] { margin-bottom: 8px !important; }
    div[data-testid="stChatMessageContent"] { width: 100% !important; margin-left: 0px !important; padding-left: 0px !important; }
    
    /* 질문 입력칸 디자인 */
    div[data-testid="stTextInput"] input { height: 45px !important; font-size: 15px !important; border-radius: 6px; border: 2px solid #1A729A !important; }
    
    /* 🔥 [추가] 왼쪽 패널 로고 중앙 정렬을 위한 CSS 🔥 */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 및 유틸리티 함수
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

def hash_password(password): return hashlib.sha256(password.strip().encode()).hexdigest()

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
if not param_df.empty and 'Parameter_ID' in param_df.columns: sys_params = param_df.set_index('Parameter_ID').to_dict('index')

def get_p(pid, prop, fallback):
    try: return float(sys_params[pid][prop])
    except: return fallback

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try: conn = st.connection("gsheets", type=GSheetsConnection); return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
    except Exception: return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default
def safe_int(val, default):
    try: return int(float(val)) if val != "" and not pd.isna(val) else default
    except: return default

def send_verification_email(to_email, code):
    sender_email = "wschoi@synotech.co.kr"; sender_password = "여기에_16자리_앱비밀번호를_입력하세요"
    try:
        if "EMAIL_PASSWORD" in st.secrets: sender_password = st.secrets["EMAIL_PASSWORD"]
    except: pass
    try:
        msg = MIMEMultipart(); msg['From'] = f"SynoCore Admin <{sender_email}>"; msg['To'] = to_email; msg['Subject'] = "[SynoCore Pro] 회원가입 인증번호 안내"
        body = f"안녕하세요. SynoCore Pro Max 플랫폼 회원가입을 위한 인증번호 안내입니다.\n\n▶ 인증번호 : {code}\n\n위 인증번호 6자리를 입력해 주시기 바랍니다.\n감사합니다."
        msg.attach(MIMEText(body, 'plain', 'utf-8')); server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(sender_email, sender_password.replace(" ", "")); server.send_message(msg); server.quit(); return True
    except Exception: return False

def get_dqdv(cat_sel, v_tc, m_df=None):
    v_axis = np.linspace(2.0, 4.2, 150); dqdv = np.zeros_like(v_axis); p1, p2 = 3.15, 0.0 
    if m_df is not None and not m_df.empty and 'Name' in m_df.columns:
        mat_row = m_df[m_df['Name'] == cat_sel]
        if not mat_row.empty:
            try: p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15)); p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
            except: pass
    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]; peaks = [3.15] if not peaks else peaks
    for p in peaks: shifted_p = float(p) - (float(v_tc) * 0.015); dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email, workspace="material_list"):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
        if db_df.empty or 'Email' not in db_df.columns: return []
        my_logs = db_df[(db_df['Email'] == email) & (db_df.get('Workspace', 'material_list') == workspace)]; hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None); row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame()); row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
        return hist[::-1]
    except: return []

def create_pdf(data_list, title="SynoCore Simulation Report"):
    if FPDF is None: return b""
    pdf = FPDF(orientation="L", unit="mm", format="A4"); pdf.add_page(); pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, title, ln=True, align="C"); pdf.set_font("Arial", "", 10); pdf.cell(0, 10, f"Generated: {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')} (KST)", ln=True, align="R"); pdf.ln(5)
    if not data_list: pdf.cell(0, 10, "No data available.", ln=True); return pdf.output(dest="S").encode("latin-1")
    headers = ["Time", "Cathode", "Cap(mAh)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life"]; col_widths = [25, 60, 25, 20, 25, 20, 25, 25, 25]
    pdf.set_font("Arial", "B", 10); [pdf.cell(col_widths[i], 10, head, border=1, align="C") for i, head in enumerate(headers)]; pdf.ln(); pdf.set_font("Arial", "", 10)
    for item in data_list:
        pdf.cell(col_widths[0], 10, str(item.get("Time", "")), border=1, align="C"); pdf.cell(col_widths[1], 10, str(item.get("Cathode", ""))[:30], border=1, align="L")
        [pdf.cell(col_widths[i+2], 10, str(item.get(k, "")), border=1, align="C") for i, k in enumerate(["Cap(mAh/g)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life(Cyc)"])]; pdf.ln()
    return pdf.output(dest="S").encode("latin-1")

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 모듈 (🔥 레이아웃 싱크 맞춤 🔥)
# -----------------------------------------------------------------------------
default_vars = {'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False, 'workspace': 'material_overall', 'user_vip_name': None, 'is_admin': False, 'admin_view': None, 'admin_ws': None, 'chat_messages': [], 'show_bot': True, 'trigger_auto_bot': False, 'process_ai': False}
for key, val in default_vars.items():
    if key not in st.session_state: st.session_state[key] = val

# ✅ [수정] 상단 헤더에도 gap="large"를 적용하여 하단과 동일한 간격을 유지합니다.
h_l, h_r = st.columns([1, 1], gap="large") 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">1.7 (beta)</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False; st.session_state.show_profile = False; st.session_state.admin_view = None; st.session_state.admin_ws = None; st.rerun()

with h_r:
    is_pro = st.session_state.logged_in
    if not is_pro:
        c1, c2 = st.columns([1, 1])
        with c1.popover("Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed"); u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed"); submit_login = st.form_submit_button("로그인", use_container_width=True)
                if submit_login:
                    df_u = get_user_db(); u_id_clean = u_id.strip().lower(); hashed_pw = hash_password(u_pw) if u_pw else ""
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_overall'}); st.session_state.history = load_user_history(u_id_clean, 'material_overall'); st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                            st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list'}); st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace); st.rerun()
                        else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): 
            st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1])
        r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if r_my.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if r_out.button("Logout", key="btn_logout_m", use_container_width=True): 
            for key, val in default_vars.items(): st.session_state[key] = val
            st.rerun()

    t1, t2 = st.columns([1, 1])
    with t2:
        bot_active = st.toggle("**💬 SynoBot 활성화**", value=st.session_state.show_bot, key="bot_toggle_ui")
        if bot_active != st.session_state.show_bot: st.session_state.show_bot = bot_active; st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드]
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    if st.session_state.admin_view is not None or st.session_state.show_profile is False:
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True); a1, a2, a3, a4 = st.columns(4)
            if a1.button("👥 유저 관리 DB", use_container_width=True): st.session_state.admin_view = 'users' if st.session_state.admin_view != 'users' else None; st.session_state.admin_ws = 'Users'; st.rerun()
            if a2.button("🔋 소재 DB", use_container_width=True): st.session_state.admin_view = 'mats' if st.session_state.admin_view != 'mats' else None; st.session_state.admin_ws = 'material_overall'; st.rerun()
            if a3.button("⚙️ 파라미터 DB", use_container_width=True): st.session_state.admin_view = 'param' if st.session_state.admin_view != 'param' else None; st.session_state.admin_ws = 'param_config'; st.rerun()
            if a4.button("💾 로그 DB", use_container_width=True): st.session_state.admin_view = 'logs' if st.session_state.admin_view != 'logs' else None; st.session_state.admin_ws = 'myData'; st.rerun()

            if st.session_state.admin_view:
                st.markdown("---"); st.markdown(f'<p class="sub-header-bold">🛠️ 인라인 데이터베이스 편집기</p>', unsafe_allow_html=True)
                if st.session_state.admin_view == 'users': target_url = URL_USERS; ws_options = ["Users", "VIPs"]
                elif st.session_state.admin_view == 'mats': target_url = URL_MATS; ws_options = ["material_overall", "material_list"] + get_vip_list_exact()
                elif st.session_state.admin_view == 'param': target_url = URL_PARAM; ws_options = ["param_config"]
                elif st.session_state.admin_view == 'logs': target_url = URL_LOGS; ws_options = ["myData"]
                
                if len(ws_options) > 1:
                    sel_ws_admin = st.selectbox("📂 편집할 워크스페이스(탭) 선택", ws_options, index=ws_options.index(st.session_state.admin_ws) if st.session_state.admin_ws in ws_options else 0)
                    if sel_ws_admin != st.session_state.admin_ws: st.session_state.admin_ws = sel_ws_admin; st.rerun()
                
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'material_overall':
                        st.caption("ℹ️ 'material_overall'은 공용 및 모든 VIP 데이터가 취합된 **읽기 전용(Read-only)** 통합 뷰입니다."); vips = get_vip_list_exact(); dfs = []
                        for v in vips: tmp = load_cloud_data(target_url, v); (dfs.append(tmp.iloc[::-1]) if not tmp.empty else None)
                        tmp_public = load_cloud_data(target_url, "material_list"); (dfs.append(tmp_public) if not tmp_public.empty else None)
                        df_admin = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(); df_admin = df_admin.drop_duplicates(subset=['Name'], keep='first') if not df_admin.empty else pd.DataFrame(); st.dataframe(df_admin, use_container_width=True)
                    else:
                        df_admin = conn.read(spreadsheet=target_url, worksheet=st.session_state.admin_ws, ttl=600); st.caption("ℹ️ 빈 행을 클릭하여 데이터를 추가하거나, 행을 선택해 `Delete` 키로 삭제할 수 있습니다.")
                        original_cols = df_admin.columns.tolist(); df_display = df_admin.copy(); is_log_view = (st.session_state.admin_view == 'logs')
                        if is_log_view and not df_display.empty: front_cols = [c for c in ['Workspace', 'Email', 'Time'] if c in original_cols]; other_cols = [c for c in original_cols if c not in front_cols]; df_display = df_display[front_cols + other_cols]; df_display = df_display.iloc[::-1].reset_index(drop=True)
                        edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}_{st.session_state.admin_ws}")
                        if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                            try:
                                save_df = edited_df.copy(); (save_df.iloc[::-1].reset_index(drop=True) if is_log_view and not save_df.empty else None); save_df = save_df[original_cols] if set(original_cols) == set(save_df.columns) else save_df
                                conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=save_df.fillna("")); st.cache_data.clear(); st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                            except Exception as e: st.error(f"저장 중 오류 발생: {e}")
                except Exception as e: st.error(f"데이터 로드 오류: {e}")
                
                st.markdown("---"); st.markdown('<p class="sub-header-bold">👁️ 하단 시뮬레이터 테스트 (VIP 시점)</p>', unsafe_allow_html=True); vip_opts = ["material_overall", "material_list"] + get_vip_list_exact()
                sel_ws = st.selectbox("**🔒 테스트 워크스페이스 선택**", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
                if sel_ws != st.session_state.workspace: st.session_state.workspace = sel_ws; st.session_state.history = load_user_history(st.session_state.user_email, sel_ws); st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 (✅ 5 : 70 : 25 비율)
# -----------------------------------------------------------------------------
if st.session_state.get('show_bot', True):
    col_left, col_main, col_bot = st.columns([0.05, 0.70, 0.25], gap="large")
else:
    col_left, col_main = st.columns([0.05, 0.95], gap="large")
    col_bot = None

with col_left:
    # 🔥 [수정] 왼쪽 패널에 로고 이미지 적용 (image_7.png 사용) 🔥
    # 주의: 실행되는 디렉토리에 image_7.png 파일이 있어야 합니다.
    # 만약 파일이 없다면 아래 st.image 줄을 주석 처리하고 기존 텍스트 코드를 주석 해제하세요.
    try:
        st.image("image_7.png", width=60)
    except Exception:
        st.markdown("<div style='text-align: center; color: #bbb; font-weight: bold; margin-top: 10px; font-size: 13px; letter-spacing: 1px;'>SC</div>", unsafe_allow_html=True)
    # st.markdown("<div style='text-align: center; color: #bbb; font-weight: bold; margin-top: 10px; font-size: 13px; letter-spacing: 1px;'>SynoCore</div>", unsafe_allow_html=True)

with col_main:
    with st.container(height=900, border=False):
        with st.container(border=True):
            ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""; st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True); sp1, c_1 = st.columns([0.02, 0.98])
            with c_1:
                if is_pro and st.session_state.workspace == "material_overall":
                    vips = get_vip_list_exact(); dfs = []; [dfs.append(load_cloud_data(URL_MATS, v).assign(Is_VIP=True).iloc[::-1]) for v in vips if not load_cloud_data(URL_MATS, v).empty]; (dfs.append(mat_df_public.copy().assign(Is_VIP=False)) if not mat_df_public.empty else None)
                    mat_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if dfs else pd.DataFrame(); df_vip = pd.DataFrame()
                else:
                    df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame(); _dfs = []; (_dfs.append(df_vip.copy().assign(Is_VIP=True).iloc[::-1]) if not df_vip.empty else None); (_dfs.append(mat_df_public.copy().assign(Is_VIP=False)) if not mat_df_public.empty else None)
                    mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

                m1, m2, m3, m4 = st.columns(4)
                if not mat_df.empty and 'Category' in mat_df.columns:
                    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist(); ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist(); ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist(); sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist(); vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist()
                    format_mat_name = lambda name: f"💎 {name}" if name in vip_names else name
                    
                    with m1:
                        cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], format_func=format_mat_name, key="sel_cat_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 양극재 추가"):
                                n_cat = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Cat_01"); c_cat = st.number_input("용량 (mAh/g)", value=160.0, key="n_cat_c"); v_cat = st.number_input("전압 (V)", value=3.2, key="n_cat_v")
                                if st.button("저장", key="btn_save_cat", use_container_width=True): (st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, pd.DataFrame([{"Name": n_cat, "Category": "Cathode", "Cap_Def": c_cat, "Volt_Def": v_cat, "Den_Def": 2.2}])], ignore_index=True).fillna("")), st.cache_data.clear(), st.success("소재가 저장되었습니다."), st.rerun())

                    with m2:
                        ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], format_func=format_mat_name, key="sel_ano_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 음극재 추가"):
                                n_ano = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Ano_01"); c_ano = st.number_input("용량 (mAh/g)", value=360.0, key="n_ano_c"); v_ano = st.number_input("전압 (V)", value=0.1, key="n_ano_v")
                                if st.button("저장", key="btn_save_ano", use_container_width=True): (st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, pd.DataFrame([{"Name": n_ano, "Category": "Anode", "Cap_Def": c_ano, "Volt_Def": v_ano, "Den_Def": 1.1}])], ignore_index=True).fillna("")), st.cache_data.clear(), st.success("소재가 저장되었습니다."), st.rerun())

                    with m3:
                        st.selectbox("**Electrolyte**", ele_list if ele_list else ["Sample Elec"], format_func=format_mat_name, key="sel_ele_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 전해액 추가"):
                                n_ele = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Elec_01"); d_ele = st.number_input("밀도 (g/cc)", value=1.2, key="n_ele_d")
                                if st.button("저장", key="btn_save_ele", use_container_width=True): (st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, pd.DataFrame([{"Name": n_ele, "Category": "Electrolyte", "Den_Def": d_ele}])], ignore_index=True).fillna("")), st.cache_data.clear(), st.success("소재가 저장되었습니다."), st.rerun())

                    with m4:
                        st.selectbox("**Separator**", sep_list if sep_list else ["Sample Sep"], format_func=format_mat_name, key="sel_sep_m")
                        if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                            with st.expander("➕ 분리막 추가"):
                                n_sep = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Sep_01"); t_sep = st.number_input("두께 (μm)", value=16.0, key="n_sep_t") 
                                if st.button("저장", key="btn_save_sep", use_container_width=True): (st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, pd.DataFrame([{"Name": n_sep, "Category": "Separator", "Load_Def": t_sep}])], ignore_index=True).fillna("")), st.cache_data.clear(), st.success("소재가 저장되었습니다."), st.rerun())
                    
                    (st.markdown("<div style='text-align: left; margin-top: 15px; color: #666; font-size: 14px; font-weight: bold;'>🔒 위 추가하는 소재는 귀사의 전용 데이터로만 저장되며, 철저히 보안 관리됩니다.</div><br>", unsafe_allow_html=True) if is_pro and st.session_state.workspace not in ["material_list", "material_overall"] else None)
                    row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series(); def_cap_min = safe_float(row.get('Cap_Min'), 100.0); def_cap_max = safe_float(row.get('Cap_Max'), 250.0); def_cap_val = safe_float(row.get('Cap_Def'), 160.0); def_vlt_min = safe_float(row.get('Volt_Min'), 2.0); def_vlt_max = safe_float(row.get('Volt_Max'), 4.5); def_vlt_val = safe_float(row.get('Volt_Def'), 3.05); def_den_min = safe_float(row.get('Den_Min'), 1.0); def_den_max = safe_float(row.get('Den_Max'), 5.0); def_den_val = safe_float(row.get('Den_Def'), 4.5); def_lif_min = safe_int(row.get('Life_Min'), 500); def_lif_max = safe_int(row.get('Life_Max'), 10000); def_lif_val = safe_int(row.get('Life_Def'), 4000); def_lod_min = safe_float(row.get('Load_Min'), 5.0); def_lod_max = safe_float(row.get('Load_Max'), 45.0); def_lod_val = safe_float(row.get('Load_Def'), 14.0)
                else:
                    st.warning("Cloud에서 소재 리스트를 불러오지 못했습니다. 앱이 기본값으로 작동합니다."); cat_sel, ano_sel = "Sample Cathode", "Sample Anode"; def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, 160.0; def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05; def_den_min, def_den_max, def_den_val = 1.0, 5.0, 4.5; def_lif_min, def_lif_max, def_lif_val = 500, 10000, 4000; def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True); sp2, c_2 = st.columns([0.03, 0.97])
            with c_2:
                expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True); s1, s2, s3, s4 = st.columns(4); v_cap = s1.slider("**Capacity (mAh/g)**", min_value=def_cap_min, max_value=def_cap_max, value=def_cap_val, key=f"cap_{cat_sel}"); v_volt = s2.slider("**Voltage (V)**", min_value=def_vlt_min, max_value=def_vlt_max, value=def_vlt_val, key=f"volt_{cat_sel}"); v_den = s3.slider("**True Density (g/cc)**", min_value=def_den_min, max_value=def_den_max, value=def_den_val, key=f"dens_{cat_sel}", disabled=not expert); v_life = s4.slider("**Base Life (Cycles)**", min_value=def_lif_min, max_value=def_lif_max, value=def_lif_val, key=f"life_{cat_sel}", disabled=not expert)
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True); sp3, c_3 = st.columns([0.03, 0.97])
            with c_3:
                show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True); p1, p2, p3 = st.columns(3)
                with p1: st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True); v_load = st.slider("**Cathode Areal Loading (mg/cm2)**", min_value=def_lod_min, max_value=def_lod_max, value=def_lod_val, key=f"load_{cat_sel}"); v_press = st.slider("**Cathode Press Density**", 1.5, 4.0, 2.5, key="ad_c_den_m", disabled=not show_adv); st.slider("**Conductive Agent %**", 0.5, 10.0, 2.0, key="ad_c_con_m", disabled=not show_adv); st.slider("**Binder %**", 0.5, 10.0, 3.0, key="ad_c_bin_m", disabled=not show_adv); porosity = max(0.0, (1 - (v_press / v_den)) * 100) if v_den > 0 else 0
                with p2: st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True); v_np = st.slider("**N/P Ratio**", 0.95, 1.50, 1.10, step=0.01, key="sl_np_m"); st.slider("**Anode Press Density**", 0.8, 2.0, 1.1, key="ad_a_den_m", disabled=not show_adv); st.slider("**Anode Active %**", 80.0, 98.0, 95.0, key="ad_a_act_m", disabled=not show_adv)
                with p3: st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True); v_act = st.slider("**Active Ratio (%)**", 80.0, 99.0, 92.0, key="sl_act_m"); v_ec = st.slider("**E/C Ratio (g/Ah)**", 1.0, 8.0, 3.5, key="ad_ec_m", disabled=not show_adv); st.slider("**Separator Thick (μm)**", 5, 50, 16, key="ad_sep_m", disabled=not show_adv)
                info1, info2 = st.columns([1, 2]); with info1: st.caption(f"**예상 공극률 (Porosity): {porosity:.1f}%**"); w1, w2, w3 = st.columns(3); (w1.error("⚠️ 공극률 부족: 전해액 침투 불량 위험!") if porosity < 20.0 else None); (w2.error("⚠️ N/P Ratio 위험: 나트륨 석출 및 단락 위험!") if v_np < 1.05 else (w2.warning("⚠️ N/P Ratio 과다: 에너지 밀도 하락 및 초기 비가역 증가!") if v_np >= 1.15 else None)); (w3.error("⚠️ E/C Ratio 부족: 전해액 고갈에 따른 수명 급감 위험!") if show_adv and v_ec < 2.0 else None)
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True); sp4, c_4 = st.columns([0.03, 0.97])
            with c_4: t1, t2, t3 = st.columns(3); v_te = t1.slider("Energy Density", 100, 350, 250, label_visibility="collapsed"); v_tc = t2.slider("C-rate", 0.1, 10.0, 1.0, label_visibility="collapsed"); v_tl = t3.slider("Cycle Goal", 500, 10000, 2000, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True); sp5, c_5 = st.columns([0.03, 0.97])
            with c_5:
                run_clicked = st.button("🚀 RUN SIMULATION" if st.session_state.history else "🚀 RUN SIMULATION ㅡ 아직 시뮬레이션 이력이 없습니다. 실행 버튼을 눌러 주세요.", key="btn_run_m", use_container_width=True)
                if run_clicked:
                    ir_drop = 0.1 + (v_tc * 0.02); cell_v = max(0.1, v_volt - ir_drop); efficiency = max(0.5, 1.0 - (v_tc * 0.015)); res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency; whl = res_whkg * v_press * 0.8; life_cyc = int(v_life * (0.95 ** v_tc)); cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S"); v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                    log_data = {"Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel, "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1), "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc, "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc, "dq_x": v_axis, "dq_y": dqdv}; is_dup = False
                    if st.session_state.history: last_run = st.session_state.history[0]; is_dup = all(log_data[k] == last_run.get(k) for k in ["Cathode", "Anode", "Cap(mAh/g)", "Volt(V)", "Load(mg)", "N/P Ratio", "Active(%)", "C-rate"])
                    (st.warning("⚠️ 이전 실행과 동일한 파라미터 조건입니다. (중복 저장 방지)") if is_dup else (time.sleep(0.6), st.session_state.history.insert(0, log_data), st.session_state.update({'sim_result': log_data, 'trigger_auto_bot': True}), st.rerun()))

                if st.session_state.history:
                    st.markdown("---"); st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록</p>', unsafe_allow_html=True); log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Life(Cyc)']} Cyc" for h in st.session_state.history]; sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed"); res = st.session_state.history[sel_idx]; st.markdown("---")
                    r1, r2, r3, r4 = st.columns(4); r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg'] - v_te, 1):+} Wh/kg (vs Target)"); r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off"); r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{round(res['Cell_V'] - v_volt, 2):+} V (IR Drop)", delta_color="inverse"); r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{res['Life(Cyc)'] - v_tl:+} Cyc (vs Target)"); st.markdown("<br><br>", unsafe_allow_html=True)
                    g1, g2, g3 = st.columns(3)
                    with g1: st.markdown('<p class="sub-header-bold" style="text-align: center;">Discharge Profile</p>', unsafe_allow_html=True); fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3))); fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9", xaxis_title="DOD (%)", yaxis_title="Voltage (V)"); st.plotly_chart(fig1, use_container_width=True); st.markdown("<div style='display:flex; align-items:flex-start; color:#666; font-size:13px; margin-top:5px;'><span style='margin-right:5px;'>💡</span><span style='line-height:1.4;'>고율 방전 시 분극(Polarization) 및 IR Drop에 의한 초기 과전압(Overpotential) 크기를 나타내며, Plateau 구간의 기울기가 실가용 에너지의 품질을 결정합니다.</span></div>", unsafe_allow_html=True)
                    with g2: st.markdown('<p class="sub-header-bold" style="text-align: center;">dQ/dV Profile</p>', unsafe_allow_html=True); fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2))); fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9", xaxis_title="Voltage (V)", yaxis_title="dQ/dV"); st.plotly_chart(fig2, use_container_width=True); st.markdown("<div style='display:flex; align-items:flex-start; color:#666; font-size:13px; margin-top:5px;'><span style='margin-right:5px;'>💡</span><span style='line-height:1.4;'>주요 상전이(Phase transition) 구간의 가역성을 진단합니다. 피크의 브로드닝(Broadening) 및 전압 Shift 현상은 활물질의 구조적 열화나 저항 증가를 암시합니다.</span></div>", unsafe_allow_html=True)
                    with g3: st.markdown('<p class="sub-header-bold" style="text-align: center;">Cell Performance</p>', unsafe_allow_html=True); categories = ['Energy(Wh/kg)', 'Power(C-rate)', 'Life(Cycle)', 'Voltage(V)', 'Loading(mg)']; r_vals = [min(100, res.get('Wh/kg', 0) / 250 * 100), min(100, res.get('C-rate', 1) / 5.0 * 100), min(100, res.get('Life(Cyc)', 0) / 5000 * 100), min(100, res.get('Cell_V', 0) / 4.0 * 100), min(100, res.get('Load(mg)', 0) / 25.0 * 100)]; fig3 = go.Figure(); fig3.add_trace(go.Scatterpolar(r=r_vals, theta=categories, fill='toself', line=dict(color='#E4B526', width=2))); fig3.update_layout(polar=dict(bgcolor="#f4f6f9", radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10), template="plotly_white"); st.plotly_chart(fig3, use_container_width=True); st.markdown("<div style='display:flex; align-items:flex-start; color:#666; font-size:13px; margin-top:5px;'><span style='margin-right:5px;'>💡</span><span style='line-height:1.4;'>5대 핵심 설계 지표의 Trade-off 밸런스입니다. 특정 축의 극단적 돌출 설계는 폼팩터 패키징 한계 및 양산성 병목(Bottle-neck)의 주요 원인이 됩니다.</span></div>", unsafe_allow_html=True)
                    st.markdown("---"); st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True); st.dataframe(pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore'), use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot) AI 패널 - 🔥 역방향(Reverse) 피드형 아키텍처 🔥
# -----------------------------------------------------------------------------
# ✅ [수정] 시스템 프롬프트: 서술형 허용하되 중요 내용은 블릿 강조
SYSTEM_KNOWLEDGE = """
You are 'SynoBot', an expert Sodium-Ion Battery (SIB) R&D engineer powered by OpenAI.
Answer questions accurately and professionally in Korean.

[응답 스타일 필수 지침]
- SIB 수석 연구원(엔지니어)의 전문적인 브리핑 스타일로 답변하십시오.
- 핵심 데이터, 중요한 결론, 또는 나열이 필요한 정보는 반드시 도트 블릿('- ')을 사용하여 눈에 띄게 정리하십시오.
- 필요한 경우 간결한 서술형 문장을 포함할 수 있으나, 장황한 설명은 피하고 핵심 위주로 구성하십시오.
"""
GREETING_MSG = "-배터리 설계 전문 AI 시노봇 대기 중\n-좌측 시뮬레이터 결과 또는 SIB 설계 지식을 질문해 주십시오"

if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (Beta)")
        if OpenAI is None: st.error("⚠️ `openai` 라이브러리 미설치.")
        elif "OPENAI_API_KEY" not in st.secrets: st.warning("⚠️ API Key 미설정.")
        else:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            if not st.session_state.chat_messages: st.session_state.chat_messages = [{"role": "assistant", "content": GREETING_MSG}]
            def handle_bot_input():
                user_val = st.session_state.get("bot_user_input", "").strip()
                if user_val: st.session_state.chat_messages.append({"role": "user", "content": user_val}); st.session_state.process_ai = True; st.session_state.bot_user_input = "" 
            st.text_input("💬 시노봇에게 질문 (Enter로 전송)", key="bot_user_input", on_change=handle_bot_input, placeholder="시뮬레이션 결과를 분석해줘")

            if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                st.session_state.trigger_auto_bot = False 
                auto_prompt = "방금 시뮬레이션이 실행됨. 제공된 데이터를 분석하여 잘된 점, 개선점, 위험 요소를 엔지니어 관점에서 브리핑할 것. 중요 내용은 블릿으로 강조."
                sys_prompt = SYSTEM_KNOWLEDGE + f"\n\n[Current User's Simulation State]\n{st.session_state.sim_result}"
                with st.spinner("📊 실시간 데이터 분석 중..."):
                    try: response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": auto_prompt}]); st.session_state.chat_messages.append({"role": "assistant", "content": "📊 **[실시간 AI 진단]**\n" + response.choices[0].message.content})
                    except Exception as e: st.error(f"분석 오류: {str(e)}")
            elif st.session_state.get("process_ai", False):
                st.session_state.process_ai = False; sys_prompt = SYSTEM_KNOWLEDGE + (f"\n\n[Current User's Simulation State]\n{st.session_state.sim_result}" if st.session_state.sim_result else ""); api_messages = [{"role": "system", "content": sys_prompt}] + [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_messages]
                with st.spinner("답변 작성 중..."):
                    try: response = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages); st.session_state.chat_messages.append({"role": "assistant", "content": response.choices[0].message.content})
                    except Exception as e: st.error(f"연산 오류: {str(e)}")

            chat_container = st.container(height=750, border=True) 
            with chat_container:
                for message in reversed(st.session_state.chat_messages):
                    with st.chat_message(message["role"]): st.markdown(message["content"])

# 7. 푸터 
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)