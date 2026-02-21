import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import hashlib
import io
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

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.7 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    /* 가로폭 컴팩트 제어 */
    .main .block-container {
        max-width: 1150px; 
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: auto; 
    }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    .syno-title { color: #1A729A; font-size: 46px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 14px; }
    
    /* 지표 박스(stMetric) 높이 통일 */
    div[data-testid="stMetric"] { 
        background-color: #f8f9fa; 
        border: 1px solid #dee2e6; 
        border-radius: 10px; 
        padding: 15px; 
        height: 125px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; }
    
    div[data-testid="stTextInput"] input { height: 40px !important; font-size: 16px !important; }
    
    div[data-testid="stButton"] > button {
        height: 40px !important; background-color: #1A729A !important; 
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important; margin-top: 0px !important;
    }
    
    /* PDF 다운로드 버튼 색상 */
    div[data-testid="stDownloadButton"] > button {
        height: 40px !important; background-color: #FFCA28 !important; 
        color: #222 !important; 
        font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: 1px solid #E4B526 !important; margin-top: 0px !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #FFB300 !important;
        border: 1px solid #DDA010 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 40px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    
    div[data-testid="stSlider"] { padding-bottom: 10px; }
    
    /* 상단 기술 가이드 토글 */
    div[data-testid="stToggle"] {
        background-color: #F4CE14; border: 1px solid #D4AC0D; padding: 0px 15px;
        border-radius: 4px; height: 40px; display: flex; align-items: center; justify-content: center; margin-top: 10px;
    }
    div[data-testid="stToggle"] > label {
        margin-bottom: 0px !important; font-size: 15px !important; color: #333 !important; width: 100%; display: flex; justify-content: center;
    }

    /* ==============================================================
       ✅ 신규 추가: Glossary(용어 사전) 및 Details 디자인 커스텀 CSS
       ============================================================== */
    /* 1. 용어사전 박스 (회색 배경) */
    div[data-testid="stExpander"] {
        background-color: #f0f2f6 !important; 
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
    }
    /* 2. 용어사전 제목 (14px 볼드, 왼쪽 정렬) */
    div[data-testid="stExpander"] summary p {
        font-size: 14px !important;
        font-weight: bold !important;
        text-align: left !important;
        color: #333 !important;
    }
    /* 3. 용어사전 내용 (14px 노멀) */
    div[data-testid="stExpanderDetails"] p {
        font-size: 14px !important;
        font-weight: normal !important;
        color: #333 !important;
    }
    /* 4. "더 자세히" 버튼을 텍스트 링크형으로 변환 */
    div[data-testid="stExpanderDetails"] div[data-testid="stButton"] > button {
        background: transparent !important;
        border: none !important;
        color: #1A729A !important;
        text-decoration: underline !important;
        padding: 0 !important;
        font-size: 14px !important;
        font-weight: bold !important;
        box-shadow: none !important;
        height: auto !important;
        min-height: 0 !important;
        width: auto !important;
        justify-content: flex-start !important;
        margin-top: 5px !important;
    }
    div[data-testid="stExpanderDetails"] div[data-testid="stButton"] > button:hover {
        color: #D35400 !important;
        background: transparent !important;
    }
    /* 5. 우측 Details(3번째 열) 글자체 동기화 (14px 노멀) */
    div[data-testid="column"]:nth-of-type(3) p, 
    div[data-testid="column"]:nth-of-type(3) li {
        font-size: 14px !important;
        font-weight: normal !important;
        color: #333 !important;
        line-height: 1.6 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 설정
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

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

def get_p(pid, prop, fallback):
    try: return float(sys_params[pid][prop])
    except: return fallback

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

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
        body = f"안녕하세요. SynoCore Pro 시뮬레이터 플랫폼 회원가입을 위한 인증번호 안내입니다.\n\n▶ 인증번호 : {code}\n\n위 인증번호 6자리를 회원가입 창에 입력해 주시기 바랍니다.\n감사합니다."
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
# 유틸리티 (물리 엔진 및 PDF)
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
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
        return hist[::-1]
    except: return []

def create_pdf(data_list, title="Simulation Report"):
    if FPDF is None: return b""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C"); pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated: {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')} (KST)", ln=True, align="R"); pdf.ln(5)

    if not data_list:
        pdf.cell(0, 10, "No data available.", ln=True); return pdf.output(dest="S").encode("latin-1")

    headers = ["Time", "Cathode", "Cap(mAh)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life"]
    col_widths = [25, 60, 25, 20, 25, 20, 25, 25, 25]
    
    pdf.set_font("Arial", "B", 10)
    for i, head in enumerate(headers): pdf.cell(col_widths[i], 10, head, border=1, align="C")
    pdf.ln(); pdf.set_font("Arial", "", 10)
    for item in data_list:
        pdf.cell(col_widths[0], 10, str(item.get("Time", "")), border=1, align="C")
        pdf.cell(col_widths[1], 10, str(item.get("Cathode", ""))[:30], border=1, align="L")
        for i, k in enumerate(["Cap(mAh/g)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life(Cyc)"]):
            pdf.cell(col_widths[i+2], 10, str(item.get(k, "")), border=1, align="C")
        pdf.ln()
    return pdf.output(dest="S").encode("latin-1")

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 모듈 
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'material_overall', 'user_vip_name': None, 'show_guide': False, 'is_admin': False,
    'admin_view': None, 'admin_ws': None, 'selected_term': None
}
for key, val in default_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

h_l, h_r = st.columns([1, 1]) 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.7 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    is_pro = st.session_state.logged_in
    
    if not is_pro:
        c1, c2 = st.columns([1, 1])
        with c1.popover("Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                submit_login = st.form_submit_button("로그인", use_container_width=True)
                
                if submit_login:
                    df_u = get_user_db()
                    u_id_clean = u_id.strip().lower()
                    hashed_pw = hash_password(u_pw) if u_pw else ""
                    
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'show_guide': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_overall'})
                        st.session_state.history = load_user_history(u_id_clean, 'material_overall')
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                            st.session_state.update({'logged_in': True, 'show_guide': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list'});
                            st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                            st.rerun()
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
        toggle_label = "**기술 가이드 보기**" if is_pro else "**기술 가이드 보기 (Pro Mode)**"
        st.toggle(
            toggle_label, 
            key="show_guide",
            disabled=not is_pro
        )

st.markdown("---")

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드] 인라인 에디터
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    with st.container(border=True):
        st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
        a1, a2, a3, a4 = st.columns(4)
        
        if a1.button("👥 유저 관리 DB", use_container_width=True):
            if st.session_state.admin_view == 'users': st.session_state.admin_view = None
            else: st.session_state.admin_view = 'users'; st.session_state.admin_ws = 'Users'
            st.rerun()
        if a2.button("🔋 소재 DB", use_container_width=True):
            if st.session_state.admin_view == 'mats': st.session_state.admin_view = None
            else: st.session_state.admin_view = 'mats'; st.session_state.admin_ws = 'material_list'
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
                    
                    if is_log_view and not df_display.empty:
                        front_cols = [c for c in ['Workspace', 'Email', 'Time'] if c in original_cols]
                        other_cols = [c for c in original_cols if c not in front_cols]
                        df_display = df_display[front_cols + other_cols]
                        df_display = df_display.iloc[::-1].reset_index(drop=True)
                    
                    edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}_{st.session_state.admin_ws}")
                    
                    if st.button("💾 변경사항 클라우드에 저장", type="primary"):
                        try:
                            save_df = edited_df.copy()
                            if is_log_view and not save_df.empty:
                                save_df = save_df.iloc[::-1].reset_index(drop=True)
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
                    st.info("💡 **해결 체크리스트**\n1. 해당 구글 시트 파일 우측 상단 [공유] 버튼을 눌러 서비스 계정 이메일이 **편집자**로 추가되어 있는지 확인하세요.\n2. 구글 시트 하단의 실제 탭(Worksheet) 이름이 코드상에 설정된 이름과 일치하는지 확인하세요.")
        
        st.markdown("---")
        vip_opts = ["material_overall", "material_list"] + get_vip_list_exact()
        sel_ws = st.selectbox("**🔒 관리자 접속 워크스페이스 선택**", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
        if sel_ws != st.session_state.workspace:
            st.session_state.workspace = sel_ws
            st.session_state.history = load_user_history(st.session_state.user_email, sel_ws)
            st.rerun()

# -----------------------------------------------------------------------------
# 계정 가입 및 My 계정 관리
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 가입 (Pro Mode)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소")
            if st.button("인증번호 발송"):
                if not e_in or "@" not in e_in: st.error("올바른 이메일 주소를 입력해주세요.")
                else:
                    v_code = str(random.randint(100000, 999999))
                    with st.spinner("📧 이메일을 발송 중입니다... (최대 10초 소요)"):
                        if send_verification_email(e_in, v_code):
                            st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
                        else: st.error("이메일 발송 실패. 관리자에게 문의하세요.")
        elif st.session_state.reg_stage == 1:
            st.info(f"📧 [{st.session_state.temp_email}]로 인증번호가 발송되었습니다.")
            v_in = st.text_input("인증번호 6자리 입력")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
                else: st.error("인증번호가 일치하지 않습니다.")
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2); pw1 = p1.text_input("2. Password", type="password"); pw2 = p2.text_input("2-1. Password 확인", type="password")
            n_name = st.text_input("3. 이름"); n_comp = st.text_input("4. Company")
            if st.button("최종 가입신청", disabled=not (pw1==pw2 and n_name)):
                conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                st.cache_data.clear() 
                st.success("가입신청 완료! 로그인 해주세요."); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

if st.session_state.get('show_profile') and st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
        if st.session_state.get('is_admin', False): st.info("관리자 계정입니다.")
        else:
            df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
            st.markdown(f"**이메일(ID):** {st.session_state.user_email} (변경 불가)")
            p1, p2 = st.columns(2)
            m_pw = p1.text_input("새 Password (변경 시에만 입력)", type="password"); m_name = p2.text_input("이름", value=u_row.get('Name', ''))
            m_comp = p1.text_input("Company", value=u_row.get('Company', '')); m_dept = p2.text_input("부서", value=u_row.get('Dept', ''))
            m_job = p1.text_input("담당업무", value=u_row.get('Job', '')); m_phone = p2.text_input("연락처", value=u_row.get('Phone', ''))
            if st.button("개인정보 수정 완료"):
                conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
                idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                df_update.at[idx, 'Name'] = m_name; df_update.at[idx, 'Company'] = m_comp; df_update.at[idx, 'Dept'] = m_dept; df_update.at[idx, 'Job'] = m_job; df_update.at[idx, 'Phone'] = m_phone
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); 
                st.cache_data.clear() 
                st.session_state.user_name = m_name; st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 (✅ 70:10:20 레이아웃 변경)
# -----------------------------------------------------------------------------
if st.session_state.get('show_guide', False):
    col_main, col_glossary, col_deep = st.columns([0.7, 0.1, 0.2])
else:
    col_main = st.container()
    col_glossary, col_deep = None, None

with col_main:
    with st.container(border=True):
        ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
        st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
        sp1, c_1 = st.columns([0.03, 0.97])
        with c_1:
            if is_pro and st.session_state.workspace == "material_overall":
                vips = get_vip_list_exact()
                dfs = []
                for v in vips:
                    tmp = load_cloud_data(URL_MATS, v)
                    if not tmp.empty: 
                        dfs.append(tmp.iloc[::-1]) 
                if not mat_df_public.empty: dfs.append(mat_df_public)
                mat_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                mat_df = mat_df.drop_duplicates(subset=['Name'], keep='first') if not mat_df.empty else pd.DataFrame()
                df_vip = pd.DataFrame()
            else:
                df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame()
                
                _dfs = []
                if not df_vip.empty:
                    _dfs.append(df_vip.iloc[::-1])
                if not mat_df_public.empty:
                    _dfs.append(mat_df_public)
                
                mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else pd.DataFrame()

            m1, m2, m3, m4 = st.columns(4)
            if not mat_df.empty and 'Category' in mat_df.columns:
                cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
                ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
                ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist()
                sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
                
                with m1:
                    cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], key="sel_cat_m")
                    if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                        with st.expander("➕ 양극재 추가"):
                            n_cat = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Cat_01")
                            c_cat = st.number_input("용량 (mAh/g)", value=160.0, key="n_cat_c")
                            v_cat = st.number_input("전압 (V)", value=3.2, key="n_cat_v")
                            
                            if st.button("저장", key="btn_save_cat"):
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
                    ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], key="sel_ano_m")
                    if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                        with st.expander("➕ 음극재 추가"):
                            n_ano = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Ano_01")
                            c_ano = st.number_input("용량 (mAh/g)", value=360.0, key="n_ano_c")
                            v_ano = st.number_input("전압 (V)", value=0.1, key="n_ano_v")
                            
                            if st.button("저장", key="btn_save_ano"):
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
                    st.selectbox("**Electrolyte**", ele_list if ele_list else ["Sample Elec"], key="sel_ele_m")
                    if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                        with st.expander("➕ 전해액 추가"):
                            n_ele = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Elec_01")
                            d_ele = st.number_input("밀도 (g/cc)", value=1.2, key="n_ele_d")
                            
                            if st.button("저장", key="btn_save_ele"):
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
                    st.selectbox("**Separator**", sep_list if sep_list else ["Sample Sep"], key="sel_sep_m")
                    if is_pro and st.session_state.workspace not in ["material_list", "material_overall"]:
                        with st.expander("➕ 분리막 추가"):
                            n_sep = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Sep_01")
                            t_sep = st.number_input("두께 (μm)", value=16.0, key="n_sep_t") 
                            
                            if st.button("저장", key="btn_save_sep"):
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
                        "🔒 위 추가하는 소재는 귀사의 전용 데이터로만 저장되며, 저장된 데이터는 철저히 보안 관리됩니다."
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
            with info2:
                st.markdown(
                    "<div style='text-align: center; color: #888; font-size: 13px; font-weight: bold; padding-top: 5px;'>"
                    "※ 자세한 사항은 로그인 밑의「기술 가이드 보기」에서 확인 하시기 바랍니다."
                    "</div>", unsafe_allow_html=True
                )

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
            col_btn, col_msg = st.columns([1, 3])
            with col_btn:
                run_clicked = st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_m", use_container_width=True)
            with col_msg:
                if not st.session_state.history:
                    st.markdown('<div style="padding-top: 12px; color: #666; font-weight: bold;">아직 시뮬레이션 이력이 없습니다. 좌측 실행 버튼을 눌러주세요.</div>', unsafe_allow_html=True)
                    
            if run_clicked:
                ir_drop = 0.1 + (v_tc * 0.02)
                cell_v = max(0.1, v_volt - ir_drop)
                efficiency = max(0.5, 1.0 - (v_tc * 0.015))
                res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
                whl = res_whkg * v_press * 0.8  
                life_cyc = int(v_life * (0.95 ** v_tc))
                
                cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S")
                v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                
                log_data = {
                    "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
                    "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1),
                    "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
                    "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc,
                    "dq_x": v_axis, "dq_y": dqdv
                }
                st.session_state.history.insert(0, log_data)
                st.session_state.sim_result = log_data
                st.rerun()

            if st.session_state.history:
                st.markdown("---")
                st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록</p>', unsafe_allow_html=True)
                
                log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Life(Cyc)']} Cyc" for h in st.session_state.history]
                sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")
                res = st.session_state.history[sel_idx]
                
                st.markdown("---")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=round(res['Wh/kg'] - v_te, 1))
                r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L")
                r3.metric("Cell Voltage", f"{res['Cell_V']} V")
                r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=res['Life(Cyc)'] - v_tl)
                
                g1, g2, g3 = st.columns(3)
                with g1:
                    st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
                    fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                    fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
                    st.plotly_chart(fig1, use_container_width=True)
                with g2:
                    st.markdown('<p class="sub-header-bold">dQ/dV Profile</p>', unsafe_allow_html=True)
                    fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                    fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
                    st.plotly_chart(fig2, use_container_width=True)
                with g3:
                    st.markdown('<p class="sub-header-bold">Cell Performance Radar</p>', unsafe_allow_html=True)
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
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10), template="plotly_white"
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                st.markdown("---")
                st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
                df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                st.dataframe(df_history, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # 6. 내 데이터 관리 및 클라우드 과거 이력 
    # -----------------------------------------------------------------------------
    if is_pro and st.session_state.history:
        with st.container(border=True):
            st.markdown('<p class="main-header">6. Data Management & Past Records (Pro)</p>', unsafe_allow_html=True)
            sp6, c_6 = st.columns([0.03, 0.97])
            with c_6:
                btn1, btn2, btn3, btn4 = st.columns(4)
                
                if btn1.button("💾 내 계정에 저장하기", key="btn_save_my"):
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
                            save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                            conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True))
                        
                        if is_duplicate:
                            st.warning("이미 저장된 시뮬레이션 결과입니다.")
                        else:
                            st.cache_data.clear() 
                            st.success("내 계정에 저장하기가 완료되었습니다.")
                    except Exception as e: 
                        st.error(f"저장 오류: {e}")

                df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                buffer = io.BytesIO()
                try:
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_export.to_excel(writer, index=False, sheet_name='Simulation_Logs')
                    file_data = buffer.getvalue()
                    file_name = f"SynoCore_Logs_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                except ImportError:
                    file_data = df_export.to_csv(index=False).encode('utf-8-sig')
                    file_name = f"SynoCore_Logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"
                    mime_type = "text/csv"

                btn2.download_button(label="📥 내 기록 다운로드", data=file_data, file_name=file_name, mime=mime_type)

                if FPDF is not None:
                    btn3.download_button(label="📄 선택 항목 PDF 출력", data=create_pdf([res], f"Result - {res['Cathode']}"), file_name=f"SynoCore_Result_{res['Time'].replace(':','')}.pdf", mime="application/pdf")
                    btn4.download_button(label="📑 전체 이력 PDF 출력", data=create_pdf(st.session_state.history, "SynoCore - All Logs"), file_name="SynoCore_All_Logs.pdf", mime="application/pdf")
                else:
                    btn3.warning("PDF 모듈 필요"); btn4.warning("PDF 모듈 필요")

                st.markdown("---")
                
                try:
                    db_df_all = st.connection("gsheets", type=GSheetsConnection).read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                    if not db_df_all.empty and 'Email' in db_df_all.columns:
                        my_saved_data = db_df_all[(db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace)]
                        
                        if not my_saved_data.empty:
                            col_title, col_btn_del = st.columns([0.8, 0.2])
                            with col_title:
                                st.markdown('<p class="sub-header-bold">🗄️ 내 클라우드 저장 이력</p>', unsafe_allow_html=True)
                            
                            df_display = my_saved_data.drop(columns=['Email', 'Workspace', 'dq_x', 'dq_y'], errors='ignore').copy()
                            df_display.insert(0, "선택", False)
                            
                            edited_df = st.data_editor(
                                df_display, 
                                use_container_width=True, 
                                hide_index=True,
                                disabled=[col for col in df_display.columns if col != "선택"]
                            )
                            
                            with col_btn_del:
                                selected_times = edited_df[edited_df["선택"] == True]["Time"].tolist()
                                if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
                                    if not selected_times:
                                        st.warning("삭제할 항목을 체크해 주세요.")
                                    else:
                                        mask = ~((db_df_all['Email'] == st.session_state.user_email) & 
                                                 (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & 
                                                 (db_df_all['Time'].isin(selected_times)))
                                        updated_db = db_df_all[mask]
                                        
                                        conn = st.connection("gsheets", type=GSheetsConnection)
                                        conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=updated_db)
                                        st.cache_data.clear() 
                                        st.success(f"총 {len(selected_times)}건의 이력이 삭제되었습니다.")
                                        st.rerun()
                        else:
                            st.markdown('<p class="sub-header-bold">🗄️ 내 클라우드 저장 이력</p>', unsafe_allow_html=True)
                            st.info("클라우드 DB에 이전에 저장된 시뮬레이션 데이터가 없습니다.")
                except Exception as e:
                    err_msg = str(e)
                    if "Quota exceeded" in err_msg or "429" in err_msg or "RATE_LIMIT_EXCEEDED" in err_msg:
                        st.error("⚠️ 구글 시트 API 분당 요청 한도(60회)를 초과했습니다. 약 1분 후 다시 시도해주세요.")
                    else:
                        st.warning("데이터베이스 연결에 실패하여 과거 이력을 불러오지 못했습니다.")

# -----------------------------------------------------------------------------
# 📖 7. 우측 가이드 패널 렌더링 (심층 지식 DB 보강 및 LaTeX 적용)
# -----------------------------------------------------------------------------
GLOSSARY_DB = {
    "Active Ratio (%)": {
        "brief": "셀 내 전체 소재 중 실제 용량을 발현하는 활물질(Active Material)의 비중을 의미합니다.", 
        "deep": """
**[Active Ratio 심층 분석]**

활물질 비중 설계는 배터리의 **에너지 밀도와 출력 성능 간의 가장 대표적인 Trade-off 관계**를 보여줍니다.

* **고에너지 셀 (High Energy):** 활물질 비중을 96%~98% 수준으로 극대화합니다. 그러나 상대적으로 도전재와 바인더가 부족해져 내부 저항이 증가하고, 충방전 시 전극 탈리 현상이 발생할 수 있습니다.
* **고출력 셀 (High Power):** 활물질을 90% 이하로 낮추고 도전재 비율을 높여 전자의 이동 속도(Electronic Conductivity)를 극대화합니다.

**[에너지 밀도(Wh/kg) 산출 공식에서의 역할]**
셀 단위의 중량당 에너지 밀도는 활물질 비중에 정비례하여 증가합니다.
$$ Energy\ Density\ (Wh/kg) = \frac{Capacity\ (mAh/g) \times Voltage\ (V) \times Active\ Ratio\ (\%)}{Cell\ Factor} $$
(단, Cell Factor는 패키징 부자재 무게 등을 반영한 보정 상수)
"""
    },
    "Anode (음극)": {
        "brief": "배터리 충전 시 양극에서 넘어온 나트륨(Na) 이온을 받아들여 저장하는 전극 소재입니다.", 
        "deep": """
**[Anode (음극) 심층 분석]**

리튬 이온 배터리(LIB)의 표준 음극재인 흑연(Graphite)은 층간 간격이 좁아 크기가 큰 나트륨 이온(Na+)이 층간 삽입(Intercalation)되기 어렵습니다. 따라서 SIB에서는 주로 닫힌 기공(Closed Pore) 구조를 갖는 **하드카본(Hard Carbon)**이 필수적으로 사용됩니다.

* **작동 원리 (Storage Mechanism):** 하드카본은 크게 두 단계로 이온을 저장합니다.
  1. 슬로핑 영역 (Sloping Region): 탄소 층(Graphene layer) 사이 결함 구조에 나트륨 이온이 흡착됩니다.
  2. 플래토 영역 (Plateau Region): 닫힌 기공 내부에 나트륨 이온이 금속 클러스터 형태로 채워집니다.

* **설계 시 주의사항:** 음극의 가역 용량이 양극에서 오는 이온을 모두 수용하지 못하면 **나트륨 금속 석출(Na-Plating)** 현상이 발생하여 열폭주 및 셀 단락(Short)의 원인이 됩니다. 이를 막기 위해 반드시 **N/P Ratio**를 1.05 이상으로 설계해야 합니다.
"""
    },
    "Anode Active %": {
        "brief": "음극 슬러리 전체 무게 중 순수 하드카본(음극 활물질)이 차지하는 중량 비율입니다.", 
        "deep": """
**[Anode Active % 심층 분석]**

음극 활물질 비중은 양극 활물질 비중(`Active Ratio`)과 동일한 개념이나, **수계 바인더 시스템(Aqueous Binder System)**을 사용하는 음극 공정의 특수성을 고려해야 합니다.

* **조성 특징:** 음극은 보통 SBR(Styrene-Butadiene Rubber) 바인더와 CMC(Carboxymethyl Cellulose) 증점제를 사용합니다. 이 시스템은 결착력이 매우 뛰어나 활물질 비중을 **95% ~ 98%까지 극단적으로 높일 수 있습니다.**
* **설계 최적화:** 음극 활물질 비율을 높이면 전체 음극 코팅층의 부피와 무게를 줄일 수 있어 셀 전체의 에너지 밀도(Wh/L, Wh/kg) 상승에 크게 기여합니다. 
* **Trade-off:** 하지만 98%를 초과하여 바인더가 너무 적어지면, 구리 집전체(Cu Foil)와의 접착력(Adhesion)이 떨어져 롤 프레스(Roll Press) 공정 중 음극 층이 벗겨지는 치명적 불량이 발생합니다.
"""
    },
    "Anode Press Density": {
        "brief": "코팅된 음극을 롤 프레스(Roll Press) 기계로 압축했을 때의 밀도(g/cc)를 나타냅니다.", 
        "deep": """
**[Anode Press Density 심층 분석]**

음극 합제 밀도는 하드카본 입자의 물리적 파괴 한계와 밀접한 연관이 있습니다. 

* **물리적 특성:** 하드카본은 구형 흑연과 달리 비정질(Amorphous) 탄소의 무질서한 덩어리 형태이므로 심하게 압축할 경우 입자가 깨지기(Particle Cracking) 쉽습니다.
* **밀도 한계 (Limits):** 일반적으로 LIB의 인조흑연은 1.6~1.7 g/cc까지 압축이 가능하지만, SIB용 **하드카본은 보통 1.0 ~ 1.2 g/cc 수준**이 한계치로 평가받습니다.
* **설계 Trade-off:**
  1. 합제 밀도를 한계 이상으로 높이면 체적 에너지 밀도(Wh/L)는 상승하지만, 입자가 깨지면서 새로운 SEI 층이 형성되어 초기 효율(ICE)이 급감합니다.
  2. 반대로 너무 낮게 설정하면 전자 전도 네트워크가 끊어지고 전해액만 과도하게 머금어 배터리 수명(Cycle Life)이 저하됩니다.

**[음극 공극률 (Porosity) 계산식]**
$$ Anode\ Porosity\ (\%) = \left( 1 - \frac{Anode\ Press\ Density}{Anode\ True\ Density} \right) \times 100 $$
"""
    },
    "Binder & Conductive Agent": {
        "brief": "바인더는 소재를 결착시키는 접착제이고, 도전재는 전자의 이동 통로를 제공하는 첨가제입니다.", 
        "deep": """
**[Binder & Conductive Agent 심층 분석]**

배터리가 장기간 안정적으로 구동하기 위해서는 활물질 입자들을 물리적, 전기적으로 하나로 묶어주는 첨가제가 필수적입니다.

* **도전재 (Conductive Agent):** 활물질 자체는 전기가 잘 통하지 않는 경우가 많습니다. 카본블랙(Carbon Black)이나 탄소나노튜브(CNT)를 소량(1~3%) 첨가하여 입자 사이사이에 **3차원 전자 이동 네트워크**를 형성합니다. 도전재가 부족하면 고속 방전(C-rate) 시 전압 강하(IR Drop)가 심하게 발생합니다.
* **바인더 (Binder):** 양극에는 주로 유기용매계인 PVDF를, 음극에는 수계인 SBR/CMC를 사용합니다. 충방전 시 발생하는 **활물질의 부피 팽창/수축을 기계적으로 잡아주어** 전극 붕괴를 막아줍니다.
* **비중 설계 한계:** 두 첨가제는 스스로 용량을 내지 못하는(Dead Weight) 물질이므로, 기술이 발전할수록 이들의 비중을 1% 단위로 줄여 에너지 밀도를 극대화하는 추세입니다.
"""
    },
    "C-rate": {
        "brief": "배터리의 충전 및 방전 속도를 나타내는 기준 단위입니다.", 
        "deep": """
**[C-rate 심층 분석]**

C-rate(Current Rate)는 배터리 설계에서 출력(Power) 성능을 평가하는 절대적인 지표입니다. 

* **기본 정의:** 1C는 해당 배터리 셀이 가진 전체 용량을 **정확히 1시간 만에 100% 충전(또는 방전)하는 전류의 크기**를 의미합니다.
  * 예시: 10Ah 용량의 배터리에서 1C는 10A의 전류, 2C는 20A(30분 완충), 0.5C는 5A(2시간 완충)를 의미합니다.

* **시뮬레이터 반영 원리 (Peukert's Law 적용):**
  방전 C-rate가 높아질수록 셀 내부의 저항(Ohmic, Charge Transfer, Diffusion)에 의해 **과전압(Overpotential)**이 발생합니다. 이는 실제 작동 전압(Cell Voltage)을 깎아내려 최종적으로 우리가 쓸 수 있는 에너지(Wh)를 극심하게 감소시킵니다.
  
**[효율 감소 연산 로직]**
$$ Actual\ Capacity\ \approx Nominal\ Capacity \times (1 - C\_rate \times Loss\_Factor) $$
"""
    },
    "Capacity (mAh/g)": {
        "brief": "소재 1g당 저장하고 외부로 내보낼 수 있는 전하량(용량)입니다.", 
        "deep": """
**[Capacity 심층 분석]**

비용량(Specific Capacity, mAh/g)은 소재 고유의 결정 구조와 전이 금속의 산화/환원(Redox) 반응 한계에 의해 결정되는 배터리 설계의 '절대값'입니다.

* **SIB 양극재의 한계:** 현재 SIB용 층상 산화물(Layered Oxides) 양극재는 주로 120 ~ 160 mAh/g 수준의 가역 용량을 보여줍니다. (리튬 이온 배터리의 NCM 양극재가 200 mAh/g 이상인 것에 비해 상대적으로 낮습니다.)
* **에너지 밀도와의 관계:** 배터리 산업에서 "더 멀리 가는(더 오래 쓰는)" 배터리를 만들려면 이 Capacity 값을 높이는 것이 1순위 과제입니다. 

**[Areal Capacity (면적당 용량) 계산식]**
실제 셀 설계 엔지니어는 1g당 용량을 집전체 면적 단위로 환산하여 N/P Ratio 밸런스를 맞춥니다.
$$ Areal\ Capacity\ (mAh/cm^2) = \frac{Capacity\ (mAh/g) \times Loading\ (mg/cm^2) \times Active\ \%}{1000} $$
"""
    },
    "Cathode (양극)": {
        "brief": "배터리의 작동 전압과 전체 에너지를 결정하는 핵심 이온 공급원(Source)입니다.", 
        "deep": """
**[Cathode (양극) 심층 분석]**

SIB의 에너지 밀도 한계를 돌파하기 위한 가장 중요한 열쇠가 바로 양극재의 혁신입니다. 배터리 원가의 약 40% 이상을 차지합니다.

* **SIB 주요 양극재 3대장:**
  1. **프러시안 블루 (Prussian Blue Analogues):** 합성이 쉽고 저렴하지만 수분 제어가 어렵고 수명이 짧은 단점이 있습니다.
  2. **층상 산화물 (Layered Oxides, O3/P2 Type):** 망간(Mn), 철(Fe), 니켈(Ni) 등을 섞어 층상 구조를 만듭니다. 가장 상용화에 가까우나 고전압에서 구조 붕괴가 일어납니다.
  3. **폴리음이온 (Polyanion):** 구조가 매우 단단하여 10,000회 이상의 초장수명을 자랑하지만 에너지 밀도가 다소 낮습니다.

* **설계 파라미터:** 양극의 작동 전압(Voltage)과 용량(Capacity)을 곱한 값이 곧 배터리 셀 전체의 총 에너지(Energy) 한계천장이 됩니다.
"""
    },
    "Cathode Areal Loading (mg/cm2)": {
        "brief": "전극 집전체(알루미늄 포일) 단위 면적(cm²) 당 코팅된 양극 슬러리의 무게입니다.", 
        "deep": """
**[Cathode Areal Loading 심층 분석]**

로딩(Loading)량은 셀 내부의 **활성 물질(에너지를 내는 물질)과 비활성 물질(분리막, 동박, 알루미늄박 등)의 비율을 결정하는 핵심 공정 설계 변수**입니다.

* **후막(Thick) 전극의 장점 (High Loading):** 로딩량을 30~40 mg/cm² 수준으로 극단적으로 높이면, 동일한 부피 내에 겹쳐 들어가는 분리막과 메탈 집전체의 장수가 줄어들어 **배터리의 부피당/무게당 에너지 밀도(Wh/L, Wh/kg)가 극대화**됩니다.
* **후막(Thick) 전극의 단점 (Trade-off):** 전극이 너무 두꺼워지면, 나트륨 이온이 전해액을 타고 전극 깊숙이 침투(Diffusion)하는 거리가 멀어져 **급속 충전(고속 C-rate)이 불가능해집니다.** 또한 건조 공정 시 표면과 내부의 용매 증발 속도 차이로 인해 표면에 바인더가 몰리는 결함(Binder Migration)이 발생합니다.
"""
    },
    "Cathode Press Density": {
        "brief": "코팅 건조를 마친 양극을 롤 프레스 기계로 강력하게 압축한 후의 밀도(g/cc)입니다.", 
        "deep": """
**[Cathode Press Density 심층 분석]**

양극 합제 밀도(Press Density 또는 Calendered Density)는 배터리의 **체적당 에너지 밀도(Wh/L)**를 끌어올리는 가장 직관적인 파라미터입니다.

* **최적 압연의 중요성:** 분말 가루 형태의 슬러리가 건조된 직후에는 내부에 50~60%의 텅 빈 공간이 존재합니다. 이를 롤 프레스로 강하게 눌러 빈 공간을 20~30% 수준으로 줄여주면, 입자 간의 전기적 접촉(Electrical Contact)이 극대화되고 부피가 획기적으로 줄어듭니다.
* **압축 과다 시 치명적 결함:** 하지만 수치를 극대화하기 위해 진밀도(True Density)에 가깝게 너무 꽉 눌러버리면 다음과 같은 현상이 일어납니다.
  1. **입자 파괴 (Particle Cracking):** 양극재 입자가 부서지며 새로운 표면이 드러나 부반응이 가속화됩니다.
  2. **전해액 함침 불가 (Zero Porosity):** 나트륨 이온이 헤엄쳐 다닐 전해액(수영장)이 들어갈 틈이 없어져, 셀 내부 저항이 무한대로 치솟아 배터리가 사망(Dead)합니다. (현재 시뮬레이터에 적용된 경고 로직의 핵심입니다.)

**[Volumetric Energy Density (부피당 에너지 밀도) 환산식]**
본 시뮬레이터는 합제 밀도를 바탕으로 부피당 에너지를 역산합니다.
$$ Energy\ Density\ (Wh/L) = Energy\ Density\ (Wh/kg) \times Press\ Density\ (g/cc) \times Packing\ Factor $$
"""
    },
    "Cycle Life": {
        "brief": "배터리를 100% 충전하고 0%까지 방전하는 과정을 1회(Cycle)로 보았을 때, 초기 용량의 80% 이하로 떨어지기 전까지 반복할 수 있는 횟수입니다.", 
        "deep": """
**[Cycle Life 심층 분석]**

수명(Cycle Life)은 배터리의 경제성과 지속 가능성을 평가하는 최종 품질 지표입니다.

* **열화(Degradation)의 근본 원인:** SIB의 수명은 여러 가지 화학적/물리적 요인에 의해 갉아먹힙니다.
  1. **SEI (고체전해질계면) 지속 성장:** 매 충방전마다 전해액이 음극 표면에서 미세하게 분해되며 찌꺼기 층을 형성하고, 이 과정에서 가용 나트륨 이온을 소모해 버립니다.
  2. **양극재 상전이 (Phase Transition):** 깊은 충방전 구간에서 층상 산화물 양극재의 결정 구조가 뒤틀려 다시 돌아오지 않는 비가역적 손상이 누적됩니다.
  3. **체적 팽창에 의한 미세 균열 (Micro-cracking):** 입자의 수축/팽창이 반복되며 입자가 깨지고 전해액과 부반응을 일으킵니다.

* **시뮬레이션 연산 한계:** 현재 시뮬레이터는 입력된 Base 수명에 가혹 조건(높은 C-rate) 패널티를 부여하는 물리 수식을 적용 중입니다.
$$ Expected\ Life = Base\ Life \times (0.95)^{C\_rate} $$
"""
    },
    "E/C Ratio (g/Ah)": {
        "brief": "셀 전체 용량(Ah) 대비 주입된 전해액(Electrolyte) 무게(g)의 비율입니다.", 
        "deep": """
**[E/C Ratio 심층 분석]**

E/C Ratio(Electrolyte-to-Capacity Ratio)는 셀의 **최종 에너지 밀도와 수명 사이의 딜레마(Trade-off)**를 결정짓는 핵심 공정 수치입니다.

* **E/C Ratio가 높을 때 (풍부한 전해액):** 배터리 수명(Cycle Life)이 압도적으로 길어집니다. 충방전을 거듭하며 SEI 층 형성으로 전해액이 소모되더라도 여유분이 충분하기 때문입니다. 하지만 전해액 자체가 매우 무거운 액체이므로 배터리 팩 전체가 무거워져 **에너지 밀도(Wh/kg)는 곤두박질**칩니다.
* **E/C Ratio가 낮을 때 (Lean Electrolyte, < 2.0):** 우주항공이나 드론 등 초경량 배터리를 설계할 때 사용합니다. 무게가 줄어 Wh/kg는 극대화되지만, 몇 백 번 충방전 후 전해액이 완전히 말라붙는 **'전해액 고갈(Electrolyte Depletion)'** 현상이 발생해 배터리가 급사(Sudden Death)하는 위험이 도사리고 있습니다.
"""
    },
    "N/P Ratio": {
        "brief": "충전 시 양극(Cathode)에서 나오는 이온의 양 대비 음극(Anode)이 수용할 수 있는 용량의 설계 비율입니다.", 
        "deep": """
**[N/P Ratio 심층 분석]**

N/P Ratio(Negative to Positive Capacity Ratio)는 배터리의 **안전성(Safety)을 지키는 최후의 방어선**이자 수명 설계의 척도입니다.

**[N/P Ratio 연산 공식]**
$$ N/P\ Ratio = \frac{Anode\ Areal\ Capacity\ (mAh/cm^2)}{Cathode\ Areal\ Capacity\ (mAh/cm^2)} $$

* **안전 마진 (일반적으로 1.05 ~ 1.15):** 음극 용량을 양극보다 약 5%~15% 더 크게(여유 있게) 설계합니다.
* **N/P < 1.05 일 때의 치명적 위험:** 충전 시 양극에서 100마리의 나트륨 이온이 넘어오는데, 음극의 방 크기가 95마리분밖에 안 된다면 남은 5마리는 음극 표면에 금속 형태로 뾰족하게 쌓입니다. 이를 **나트륨 석출(Na-Plating)**이라 부르며, 뾰족한 수지상(Dendrite)으로 자라나 분리막을 관통해 거대한 화재 폭발을 일으킵니다.
* **N/P >= 1.15 초과 시의 손실:** 너무 안전만 생각해서 음극을 과도하게 두껍게 바르면, 버려지는 잉여 음극 공간 때문에 전체 셀의 에너지 밀도(Wh/kg)가 떨어지고, 초기에 낭비되는 비가역 나트륨 이온이 많아져 효율이 급감합니다.
"""
    },
    "Porosity (공극률)": {
        "brief": "프레스 공정을 마친 전극 합제층 내부에 여전히 존재하는 빈 공간의 부피 비율(%)입니다.", 
        "deep": """
**[Porosity (공극률) 심층 분석]**

공극률은 배터리 내부에서 이온이 이동하는 고속도로(전해액 통로)의 폭을 의미합니다. 엔지니어는 이 수치를 조절하여 이온 전도도와 에너지 밀도를 최적화합니다.

**[공극률 도출 계산식]**
$$ Porosity\ (\%) = \left( 1 - \frac{Press\ Density\ (합제밀도)}{True\ Density\ (진밀도)} \right) \times 100 $$

* **공극률이 부족할 때 (< 20%):** 에너지 밀도를 높이려고 롤 프레스로 전극을 가혹하게 압착하면 빈 공간이 사라집니다. 빈 공간이 없으면 주액(Injection) 공정에서 전해액이 전극 내부로 스며들지 못하는 **함침(Wetting) 불량**이 발생하며, 이온이 이동할 길이 끊겨 배터리 저항이 치솟습니다.
* **공극률이 과도할 때 (> 40%):** 압착을 덜 하여 빈 공간이 너무 많아지면, 동일한 배터리 케이스(캔, 파우치) 안에 넣을 수 있는 전극의 길이가 짧아져 셀 단위의 체적당 에너지 밀도(Wh/L)가 급락하고 활물질 입자 간의 전기적 연결망이 약해집니다.
"""
    },
    "Separator Thick (μm)": {
        "brief": "양극과 음극의 물리적 접촉(쇼트)을 막고 이온만 통과시키는 다공성 폴리머 필름의 두께입니다.", 
        "deep": """
**[Separator Thick 심층 분석]**

분리막 두께 설계는 **배터리의 에너지 밀도와 관통 화재(안전성) 사이의 극단적인 줄타기**를 보여줍니다.

* **에너지 밀도 관점:** 16μm이던 분리막 두께를 최신 공법을 적용해 9μm, 심지어 5μm까지 줄이게 되면, 젤리롤(Jelly-roll)을 감을 때 생겨난 빈 공간만큼 양극/음극재를 한 바퀴라도 더 감아 넣을 수 있습니다. 이는 배터리 셀의 용량을 직접적으로 늘려줍니다.
* **안전성(Safety) 관점:** 분리막이 얇아질수록 제조 공정 중 유입된 미세한 금속 이물질이나 충전 중 자라나는 나트륨 덴드라이트(Na-Dendrite)에 의해 분리막이 뚫릴(Penetration) 확률이 급증합니다. 뚫리는 순간 양/음극이 직접 닿아 내부 단락(Short-circuit)이 발생하고 열폭주로 이어집니다.
"""
    },
    "True Density (진밀도)": {
        "brief": "소재 입자 자체의 내부 기공이나 입자 간 빈 공간을 완전히 제외한 뼈대 물질 고유의 밀도(g/cc)입니다.", 
        "deep": """
**[True Density (진밀도) 심층 분석]**

진밀도(True Density)는 소재를 합성할 때 결정되는 **불변의 물리 화학적 특성**이며, 엔지니어가 임의로 바꿀 수 없는 기준 상수(Constant) 역할을 합니다.

* **측정 및 활용:** 기체 비중병(Gas Pycnometer) 등을 이용하여 매우 정밀하게 측정합니다. 
* **공정 설계의 등대:** 엔지니어는 롤 프레스(Roll Press) 기계로 전극을 누를 때, "이 소재를 어디까지 세게 눌러도 될까?"를 고민합니다. 이때 절대 넘을 수 없는 최대 한계벽이 바로 진밀도 수치입니다. 합제 밀도(Press Density)가 이 진밀도에 도달한다는 것은 전극 내부에 빈 공간(공극률)이 0%가 됨을 의미하기 때문입니다.
"""
    },
    "Voltage (V)": {
        "brief": "배터리의 구동 전압으로, 양극(Cathode)과 음극(Anode) 소재 고유의 산화환원 전위차에 의해 결정됩니다.", 
        "deep": """
**[Voltage 심층 분석]**

작동 전압(Operating Voltage)은 배터리 셀 단위의 총 에너지 밀도(Energy)를 산출하는 가장 중요한 곱셈 인자 중 하나입니다.

**[에너지 밀도 지배 방정식]**
$$ Energy\ (Wh) = Capacity\ (Ah) \times Average\ Voltage\ (V) $$

* **양극재의 전위 한계:** 현재 SIB용 프러시안 블루나 층상 산화물은 평균 3.0V ~ 3.2V 사이의 작동 전압을 가집니다. 이를 4.0V 이상의 고전압(High-voltage) 영역까지 끌어올려 충전(Cut-off)하게 되면 Capacity(용량)가 늘어나 에너지가 폭발적으로 증가합니다.
* **고전압 충전의 부작용 (Trade-off):** 전압을 너무 높이면 일반적인 유기 액체 전해액의 전기화학적 안정창(Electrochemical Window)을 벗어나게 되어, 전해액이 산화(Oxidation) 분해되며 가스를 발생시킵니다. 이는 배터리가 부푸는 스웰링(Swelling) 현상과 급격한 수명 단축의 주원인입니다.
"""
    }
}

# 사용자 정의 아코디언 UI (Auto-Close 로직 적용)
if col_glossary and col_deep:
    with col_glossary:
        st.markdown(f"#### 📖 Glossary")
        sorted_terms = sorted(GLOSSARY_DB.keys())
        
        for term in sorted_terms:
            with st.expander(term):
                st.write(GLOSSARY_DB[term]["brief"])
                if st.button("더 자세히 〉", key=f"btn_deep_{term}"):
                    st.session_state.selected_term = term
                    st.rerun()
            
    with col_deep:
        st.markdown(f"#### 🎓 Details")
        
        if st.session_state.selected_term and st.session_state.selected_term in GLOSSARY_DB:
            current_term = st.session_state.selected_term
            with st.container(border=True):
                st.markdown(f"**[{current_term}]**")
                st.markdown(GLOSSARY_DB[current_term]["deep"])
        else:
            with st.container(border=True):
                st.markdown("👈 좌측 용어 사전에서 **'더 자세히 〉'** 버튼을 클릭하시면, 해당 파라미터가 배터리 설계에 미치는 심층 실무 지식과 계산 수식이 표출됩니다.")

# 7. 푸터 (저작권 표시)
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)