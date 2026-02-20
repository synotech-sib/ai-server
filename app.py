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
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* 완벽한 중앙 정렬 및 최대 폭 1050px 고정 */
    [data-testid="stAppViewBlockContainer"] {
        max-width: 1050px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto !important;
    }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    .syno-title { color: #1A729A; font-size: 46px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 14px; }
    
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; }
    div[data-testid="stTextInput"] input { height: 40px !important; font-size: 16px !important; }
    
    div[data-testid="stButton"] > button { height: 40px !important; background-color: #1A729A !important; color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: none !important; margin-top: 0px !important; }
    div[data-testid="stDownloadButton"] > button { height: 40px !important; background-color: #FFCA28 !important; color: #222 !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: 1px solid #E4B526 !important; margin-top: 0px !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #FFB300 !important; border: 1px solid #DDA010 !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 40px !important; }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 연동 및 최고 관리자 세팅
# -----------------------------------------------------------------------------
ADMIN_USERS = {
    "wschoi@synotech.co.kr": "최우석",
    "seoyeon@synotech.co.kr": "최서연"
}
ADMIN_PW = "synotech0773!"

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"

def hash_password(password): return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=60)
def load_cloud_data(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception: return pd.DataFrame()

param_df = load_cloud_data(URL_PARAM)
sys_params = param_df.set_index('Parameter_ID').to_dict('index') if not param_df.empty and 'Parameter_ID' in param_df.columns else {}
def get_p(pid, prop, fallback): return float(sys_params[pid][prop]) if pid in sys_params else fallback

def get_user_db():
    return load_cloud_data(URL_USERS, "Sheet1")

# ✅ VIP 리스트 실시간 불러오기 (캐시 무시 ttl=0 적용!)
def get_vip_list():
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_USERS, worksheet="VIPs", ttl=0) # 즉각적인 반영을 위해 ttl=0 설정
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            if 'Company' in df.columns:
                return [str(x).strip().lower() for x in df['Company'].dropna().tolist() if str(x).strip()]
    except Exception:
        pass
    return []

# -----------------------------------------------------------------------------
# 3. 이메일 발송 및 물리 시뮬레이션 엔진
# -----------------------------------------------------------------------------
def send_verification_email(to_email, code):
    primary_email = "wschoi@synotech.co.kr"; alias_email = "synocore@synotech.co.kr"; app_password = None
    try:
        if "EMAIL_PASSWORD" in st.secrets: app_password = st.secrets["EMAIL_PASSWORD"]
        elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]: app_password = st.secrets["connections"]["gsheets"].get("EMAIL_PASSWORD")
        if not app_password: return False
    except Exception: return False
    
    try:
        msg = MIMEMultipart(); msg['From'] = f"SynoCore <{alias_email}>"; msg['To'] = to_email; msg['Subject'] = "[SynoCore Pro] 회원가입을 위한 인증번호가 발급되었습니다."
        msg.attach(MIMEText(f"안녕하세요. 시노텍 차세대 배터리 설계 플랫폼 SynoCore입니다.\n\n회원가입 인증번호 안내드립니다.\n■ 인증번호 : {code}\n\n감사합니다.\nⓒ SynoTech All rights reserved.", 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(primary_email, app_password); server.send_message(msg); server.quit()
        return True
    except Exception: return False

def get_dqdv(cat_sel, v_tc, m_df=None):
    v_axis = np.linspace(2.0, 4.2, 150); dqdv = np.zeros_like(v_axis); p1, p2 = 3.15, 0.0 
    if m_df is not None and not m_df.empty and 'Name' in m_df.columns:
        mat_row = m_df[m_df['Name'] == cat_sel]
        if not mat_row.empty:
            try:
                if 'Peak1_V' in m_df.columns: p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15))
                if 'Peak2_V' in m_df.columns: p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
            except: pass
    if p1 == 3.15 and p2 == 0.0:
        if "Prussian" in str(cat_sel) or "Altris" in str(cat_sel): p1, p2 = 3.05, 3.45
        elif "Polyanion" in str(cat_sel) or "NVPF" in str(cat_sel): p1, p2 = 3.75, 0.0
    for p in [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]:
        shifted_p = float(p) - (float(v_tc) * 0.015); dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email, workspace):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
        if db_df.empty or 'Email' not in db_df.columns: return []
        
        my_logs = db_df[(db_df['Email'] == email) & (db_df.get('Workspace', 'material_list') == workspace)]
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None); row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Cell_V']: row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y
            hist.append(row_dict)
        return hist[::-1]
    except: return []

def create_pdf(data_list, title="Simulation Report"):
    if FPDF is None: return b""
    pdf = FPDF(orientation="L", unit="mm", format="A4"); pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C"); pdf.set_font("Arial", "", 10); pdf.cell(0, 10, f"Generated: {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')} (KST)", ln=True, align="R"); pdf.ln(5)
    if not data_list: return pdf.output(dest="S").encode("latin-1")
    col_widths = [25, 60, 25, 20, 25, 20, 25, 25, 25]; pdf.set_font("Arial", "B", 10)
    for i, head in enumerate(["Time", "Cathode", "Cap(mAh)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life"]): pdf.cell(col_widths[i], 10, head, border=1, align="C")
    pdf.ln(); pdf.set_font("Arial", "", 10)
    for item in data_list:
        pdf.cell(col_widths[0], 10, str(item.get("Time", "")), border=1, align="C"); pdf.cell(col_widths[1], 10, str(item.get("Cathode", ""))[:30], border=1, align="L")
        for i, k in enumerate(["Cap(mAh/g)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life(Cyc)"]): pdf.cell(col_widths[i+2], 10, str(item.get(k, "")), border=1, align="C")
        pdf.ln()
    return pdf.output(dest="S").encode("latin-1")

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 로그인 UI
# -----------------------------------------------------------------------------
default_session_vars = { 'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'trigger_login': False, 'user_name': "", 'user_email': "", 'show_profile': False, 'is_admin': False, 'user_vip_name': None, 'workspace': 'material_list' }
for key, value in default_session_vars.items():
    if key not in st.session_state: st.session_state[key] = value

def process_login(): st.session_state.trigger_login = True

h_l, h_r = st.columns([1, 1])
with h_l: st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)
with h_r:
    if not st.session_state.logged_in:
        r1_c1, r1_c2 = st.columns(2); u_id = r1_c1.text_input("ID", placeholder="company email", key="id_login_m", label_visibility="collapsed"); u_pw = r1_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed", on_change=process_login)
        r2_c1, r2_c2 = st.columns(2); login_btn = r2_c1.button("Login", key="btn_login_m", use_container_width=True); reg_btn = r2_c2.button("계정신청 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True)
        
        if login_btn or st.session_state.pop('trigger_login', False):
            df_u = get_user_db(); u_id_clean = u_id.strip().lower(); hashed_pw = hash_password(u_pw) if u_pw else ""
            
            if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_list'})
                st.session_state.history = load_user_history(u_id_clean, 'material_list'); st.rerun()
            else:
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                if not valid.empty:
                    domain = u_id_clean.split('@')[1].split('.')[0].lower() if '@' in u_id_clean else ""
                    vip_list = get_vip_list()
                    user_vip = domain if domain in vip_list else None
                    
                    st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': u_id_clean, 'is_admin': False, 'user_vip_name': user_vip, 'workspace': 'material_list'})
                    st.session_state.history = load_user_history(u_id_clean, 'material_list'); st.rerun()
                else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        
        if reg_btn: st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1]); r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if r_my.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if r_out.button("Logout", key="btn_logout_m", use_container_width=True): 
            for k in default_session_vars: st.session_state[k] = default_session_vars[k]
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드 및 VIP 리스트 로딩 에러 체크]
# -----------------------------------------------------------------------------
if st.session_state.logged_in and st.session_state.is_admin:
    with st.container(border=True):
        st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
        
        a1, a2, a3 = st.columns(3)
        a1.link_button("👥 통합 회원/로그 DB (Users)", URL_USERS, use_container_width=True)
        a2.link_button("🔋 통합 소재 DB (Materials)", URL_MATS, use_container_width=True)
        a3.link_button("⚙️ 보정 계수 DB (Parameters)", URL_PARAM, use_container_width=True)
        
        st.markdown("---")
        st.markdown('<p class="sub-header-bold">🔒 워크스페이스 전환 (관리자 권한)</p>', unsafe_allow_html=True)
        
        vip_list_fetched = get_vip_list()
        vip_opts = ["material_list"] + vip_list_fetched
        
        # ✅ VIP 리스트를 못 불러왔을 경우 원인 파악을 위한 안내창
        if len(vip_opts) == 1:
            st.warning("⚠️ 현재 등록된 VIP 회사가 없습니다. '통합 회원 DB(Users)' 파일에 `VIPs` 탭을 만들고 A1 셀에 `Company`, A2 이하에 `altris`, `icloud` 등을 기입해주세요.")
            
        sel_ws = st.selectbox("접속할 워크스페이스(탭) 선택", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
        
        if sel_ws != st.session_state.workspace:
            st.session_state.workspace = sel_ws
            st.session_state.history = load_user_history(st.session_state.user_email, sel_ws)
            st.rerun()

# -----------------------------------------------------------------------------
# 🏢 [VIP 유저 전용 워크스페이스 선택]
# -----------------------------------------------------------------------------
if st.session_state.logged_in and st.session_state.user_vip_name and not st.session_state.is_admin:
    with st.container(border=True):
        st.markdown(f'<p class="sub-header-bold" style="color:#00509E;">🏢 {st.session_state.user_vip_name.upper()} 전용 워크스페이스</p>', unsafe_allow_html=True)
        
        mode_opts = ["material_list (일반 공용 모드)", f"{st.session_state.user_vip_name} 전용 모드"]
        sel_mode = st.radio("시뮬레이션 환경 선택", mode_opts, index=1 if st.session_state.workspace == st.session_state.user_vip_name else 0, horizontal=True)
        
        new_ws = "material_list" if "material_list" in sel_mode else st.session_state.user_vip_name
        if new_ws != st.session_state.workspace:
            st.session_state.workspace = new_ws
            st.session_state.history = load_user_history(st.session_state.user_email, new_ws)
            st.rerun()

# 현재 선택된 워크스페이스(탭 이름)로 소재 데이터 로드
ws_tab = st.session_state.workspace
mat_df = load_cloud_data(URL_MATS, ws_tab)

if mat_df.empty and st.session_state.workspace != "material_list":
    st.error(f"🚨 관리자 알림: Materials 스프레드시트 내에 '{ws_tab}' 이라는 이름의 탭(Worksheet)이 존재하지 않아 데이터를 불러올 수 없습니다. 탭을 생성해주세요!")

# -----------------------------------------------------------------------------
# [계정 신청 및 개인정보 수정]
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro Mode)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("가입용 회사 이메일 입력")
            if st.button("인증번호 발송"):
                if not e_in or "@" not in e_in: st.error("올바른 이메일 주소를 입력해주세요.")
                else:
                    v_code = str(random.randint(100000, 999999))
                    with st.spinner("📧 SynoCore에서 인증 메일을 발송 중입니다..."):
                        if send_verification_email(e_in, v_code): st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"📧 [{st.session_state.temp_email}]로 인증번호가 발송되었습니다.")
            v_in = st.text_input("인증번호 6자리 입력")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
                else: st.error("인증번호가 일치하지 않습니다.")
        elif st.session_state.reg_stage == 2:
            st.markdown('<p class="sub-header-bold">세부 정보 입력</p>', unsafe_allow_html=True)
            p1, p2 = st.columns(2); pw1 = p1.text_input("Password", type="password"); pw2 = p2.text_input("Password 확인", type="password")
            c1, c2 = st.columns(2); n_name = c1.text_input("이름"); n_comp = c2.text_input("회사명")
            c3, c4 = st.columns(2); n_dept = c3.text_input("부서"); n_job = c4.text_input("담당업무")
            c5, c6 = st.columns(2); n_phone = c5.text_input("전화번호"); n_purpose = c6.text_input("이 프로그램 사용목적 (간략히)")
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("⚖️ 보안 및 법적효력 관련 내용 보기"):
                st.markdown("""
                <div style='background-color: #f1f3f5; padding: 15px; border-radius: 5px; font-size: 14px;'>
                <b>[면책 조항 및 법적 고지]</b><br><br>
                1. 본 플랫폼의 시뮬레이션 데이터는 학술적/기술적 <b>참조용(Reference Only)</b>으로만 제공됩니다.<br>
                2. 본 결과물은 양산 적용 등 절대적 기준으로 사용될 수 없으며, (주)시노텍(SynoTech)은 어떠한 법적 책임도 지지 않습니다.<br>
                3. 상세 논의가 필요하신 경우 공식 미팅을 통해 진행하시기 바랍니다.<br>
                </div>
                """, unsafe_allow_html=True)
                
            agree_terms = st.checkbox("위 보안 및 법적효력 관련 내용에 동의합니다.")
            if st.button("가입신청", use_container_width=True, disabled=not bool(pw1 and (pw1 == pw2) and n_name and agree_terms)):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5)
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "Dept": n_dept, "Job": n_job, "Phone": n_phone, "Purpose": n_purpose, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                    _ = conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=pd.concat([df_u, new_user], ignore_index=True))
                    st.success("가입 완료! 로그인 해주세요."); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()
                except Exception as e: st.error(f"오류가 발생했습니다: {e}")

if st.session_state.get('show_profile') and st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
        if st.session_state.user_email in ADMIN_USERS: st.info("관리자(Admin) 계정의 정보 변경은 시트에서 직접 수행해야 합니다.")
        else:
            df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
            st.markdown(f"**이메일(ID):** {st.session_state.user_email} (변경 불가)")
            p1, p2 = st.columns(2); m_pw = p1.text_input("새 Password (변경 시에만 입력)", type="password"); m_name = p2.text_input("이름", value=u_row.get('Name', ''))
            m_comp = p1.text_input("Company", value=u_row.get('Company', '')); m_dept = p2.text_input("부서", value=u_row.get('Dept', ''))
            m_job = p1.text_input("담당업무", value=u_row.get('Job', '')); m_phone = p2.text_input("연락처", value=u_row.get('Phone', ''))
            if st.button("개인정보 수정 완료"):
                conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5)
                idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                df_update.at[idx, 'Name'] = m_name; df_update.at[idx, 'Company'] = m_comp; df_update.at[idx, 'Dept'] = m_dept
                df_update.at[idx, 'Job'] = m_job; df_update.at[idx, 'Phone'] = m_phone
                _ = conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=df_update)
                st.session_state.user_name = m_name; st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()

is_pro = st.session_state.logged_in

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 UI
# -----------------------------------------------------------------------------

with st.container(border=True):
    ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
    st.markdown(f'<p class="main-header">1. Material Selection <span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
    sp1, c_1 = st.columns([0.01, 0.99])
    with c_1:
        m1, m2, m3, m4 = st.columns(4)
        if not mat_df.empty and 'Category' in mat_df.columns:
            cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
            ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
            ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist()
            sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
            
            cat_sel = m1.selectbox("Cathode", cat_list if cat_list else ["Sample Cathode"], key="sel_cat_m")
            ano_sel = m2.selectbox("Anode", ano_list if ano_list else ["Sample Anode"], key="sel_ano_m")
            m3.selectbox("Electrolyte", ele_list if ele_list else ["Sample Elec"], key="sel_ele_m")
            m4.selectbox("Separator", sep_list if sep_list else ["Sample Sep"], key="sel_sep_m")
            
            row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
            def_cap_min, def_cap_max, def_cap_val = float(row.get('Cap_Min', 100)), float(row.get('Cap_Max', 250)), float(row.get('Cap_Def', 160))
            def_vlt_min, def_vlt_max, def_vlt_val = float(row.get('Volt_Min', 2.0)), float(row.get('Volt_Max', 4.5)), float(row.get('Volt_Def', 3.05))
            def_den_min, def_den_max, def_den_val = float(row.get('Den_Min', 1.0)), float(row.get('Den_Max', 4.5)), float(row.get('Den_Def', 2.2))
            def_lif_min, def_lif_max, def_lif_val = int(row.get('Life_Min', 500)), int(row.get('Life_Max', 10000)), int(row.get('Life_Def', 4000))
            def_lod_min, def_lod_max, def_lod_val = float(row.get('Load_Min', 5.0)), float(row.get('Load_Max', 45.0)), float(row.get('Load_Def', 14.0))
        else:
            cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
            def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, 160.0; def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05; def_den_min, def_den_max, def_den_val = 1.0, 4.0, 2.2; def_lif_min, def_lif_max, def_lif_val = 500, 10000, 4000; def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    sp2, c_2 = st.columns([0.01, 0.99])
    with c_2:
        expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True)
        s1, s2, s3, s4 = st.columns(4)
        v_cap = s1.slider("Capacity (mAh/g)", def_cap_min, def_cap_max, def_cap_val, key=f"cap_{cat_sel}")
        v_volt = s2.slider("Voltage (V)", def_vlt_min, def_vlt_max, def_vlt_val, key=f"volt_{cat_sel}")
        v_dens = s3.slider("Density (g/cc)", def_den_min, def_den_max, def_den_val, key=f"dens_{cat_sel}", disabled=not expert)
        v_life = s4.slider("Base Life (Cycles)", def_lif_min, def_lif_max, def_lif_val, key=f"life_{cat_sel}", disabled=not expert)
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    sp3, c_3 = st.columns([0.01, 0.99])
    with c_3:
        show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True)
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
            v_load = st.slider("Loading (mg/cm2)", def_lod_min, def_lod_max, def_lod_val, key=f"load_{cat_sel}")
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, disabled=not show_adv)
            st.slider("Conductive Agent %", get_p('cat_conductive', 'Min', 0.5), get_p('cat_conductive', 'Max', 10.0), get_p('cat_conductive', 'Default', 2.0), disabled=not show_adv)
        with p2:
            st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
            v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, step=0.01)
            st.slider("Anode Active %", 80.0, 98.0, 95.0, disabled=not show_adv)
        with p3:
            st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
            v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0)
            st.slider("E/C Ratio (g/Ah)", get_p('ec_ratio', 'Min', 1.0), get_p('ec_ratio', 'Max', 8.0), get_p('ec_ratio', 'Default', 3.5), disabled=not show_adv)
        st.markdown("<br>", unsafe_allow_html=True)

# ✅ 4번 항목명 복구 및 가시성 확보
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    sp4, c_4 = st.columns([0.01, 0.99])
    with c_4:
        t1, t2 = st.columns(2)
        with t1: 
            st.markdown('<p class="sub-header-bold">Energy Density Goal (Wh/kg)</p>', unsafe_allow_html=True)
            v_te = st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
        with t2: 
            st.markdown('<p class="sub-header-bold">Simulation C-rate</p>', unsafe_allow_html=True)
            v_tc = st.slider("C-rate", get_p('target_crate', 'Min', 0.1), get_p('target_crate', 'Max', 10.0), get_p('target_crate', 'Default', 1.0), label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    sp5, c_5 = st.columns([0.01, 0.99])
    with c_5:
        col_btn, col_msg = st.columns([1, 3])
        with col_btn:
            run_clicked = st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_m", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
        with col_msg:
            if not st.session_state.history: st.markdown('<div style="padding-top: 12px; color: #666; font-weight: bold;">아직 시뮬레이션 이력이 없습니다. 좌측 실행 버튼을 눌러주세요.</div>', unsafe_allow_html=True)
                
        if run_clicked:
            ir_drop = 0.1 + (v_tc * 0.02); cell_v = max(0.1, v_volt - ir_drop); efficiency = max(0.5, 1.0 - (v_tc * 0.015))
            res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency; life_cyc = int(v_life * (0.95 ** v_tc))
            cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S")
            v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
            
            log_data = {"Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel, "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1), "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc, "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc, "dq_x": v_axis, "dq_y": dqdv}
            st.session_state.history.insert(0, log_data); st.session_state.sim_result = log_data; st.rerun()

        if st.session_state.history:
            st.markdown("---"); st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록 (선택 시 아래 결과가 즉시 변경됩니다)</p>', unsafe_allow_html=True)
            log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Cell_V']} V" for h in st.session_state.history]
            sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")
            res = st.session_state.history[sel_idx]
            
            st.markdown("---"); r1, r2, r3 = st.columns(3)
            r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=round(res['Wh/kg'] - v_te, 1))
            r2.metric("Cell Voltage", f"{res['Cell_V']} V"); r3.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc")
            
            g1, g2 = st.columns([1, 1])
            with g1:
                st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
                fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                fig1.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)"); st.plotly_chart(fig1, use_container_width=True, key=f"plot_v_{res['Time']}")
            with g2:
                st.markdown('<p class="sub-header-bold">dQ/dV Profile (Fingerprint)</p>', unsafe_allow_html=True)
                fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                fig2.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV"); st.plotly_chart(fig2, use_container_width=True, key=f"plot_dq_{res['Time']}")

            st.markdown("---"); st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore'), use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 내 데이터 관리 (저장, 삭제, 다운로드)
# -----------------------------------------------------------------------------
if is_pro and st.session_state.history:
    with st.container(border=True):
        st.markdown(f'<p class="main-header">6. Data Management & Export ({st.session_state.workspace})</p>', unsafe_allow_html=True)
        sp6, c_6 = st.columns([0.01, 0.99])
        with c_6:
            r1_c1, r1_c2 = st.columns(2)
            
            if r1_c1.button("💾 내 계정에 저장하기", key="btn_save_my", use_container_width=True):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
                    is_duplicate = False
                    if not db_df.empty and 'Email' in db_df.columns and 'Time' in db_df.columns and 'Workspace' in db_df.columns:
                        if not db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time']) & (db_df['Workspace'] == st.session_state.workspace)].empty: 
                            is_duplicate = True
                            
                    if not is_duplicate:
                        save_record = res.copy(); save_record['Email'] = st.session_state.user_email; save_record['Workspace'] = st.session_state.workspace
                        save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                        _ = conn.update(spreadsheet=URL_USERS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True))
                    
                    if is_duplicate: st.warning("이미 저장된 결과와 중복되는 부분을 제외 하고 저장하였습니다.")
                    else: st.success(f"[{st.session_state.workspace}] 전용 데이터베이스에 성공적으로 저장되었습니다.")
                except Exception as e: st.error(f"저장 오류: {e}")

            if r1_c2.button("🗑️ 현재 기록 완전히 삭제", key="btn_del_my", use_container_width=True):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
                    if not db_df.empty:
                        new_df = db_df[~((db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time']) & (db_df.get('Workspace', 'material_list') == st.session_state.workspace))]
                        _ = conn.update(spreadsheet=URL_USERS, worksheet="myData", data=new_df)
                        
                        st.session_state.history = [h for h in st.session_state.history if h['Time'] != res['Time']]
                        st.success("클라우드에서 해당 기록이 영구적으로 삭제되었습니다.")
                        st.rerun()
                except Exception as e: st.error(f"삭제 중 오류가 발생했습니다: {e}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            r2_c1, r2_c2, r2_c3 = st.columns(3)
            
            df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
            buffer = io.BytesIO()
            try:
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_export.to_excel(writer, index=False, sheet_name='Logs')
                f_data = buffer.getvalue(); f_name = f"SynoCore_{st.session_state.workspace}_Logs_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"; m_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            except ImportError:
                f_data = df_export.to_csv(index=False).encode('utf-8-sig'); f_name = f"SynoCore_{st.session_state.workspace}_Logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"; m_type = "text/csv"

            r2_c1.download_button(label="📥 내 기록 엑셀 다운로드", data=f_data, file_name=f_name, mime=m_type, use_container_width=True)

            if FPDF is not None:
                r2_c2.download_button(label="📄 선택 항목 PDF 출력", data=create_pdf([res], f"Result - {res['Cathode']}"), file_name=f"SynoCore_{st.session_state.workspace}_{res['Time'].replace(':','')}.pdf", mime="application/pdf", use_container_width=True)
                r2_c3.download_button(label="📑 전체 이력 PDF 출력", data=create_pdf(st.session_state.history, "SynoCore - All Logs"), file_name=f"SynoCore_{st.session_state.workspace}_All_Logs.pdf", mime="application/pdf", use_container_width=True)
            else:
                r2_c2.warning("PDF 모듈 필요"); r2_c3.warning("PDF 모듈 필요")

# 7. 푸터 (저작권 표시)
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)