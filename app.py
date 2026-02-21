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

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
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
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

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

def get_user_db(): return load_cloud_data(URL_USERS, "Users")

def get_vip_list_exact():
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_USERS, worksheet="VIPs", ttl=0)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            if 'Company' in df.columns: return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()]
    except Exception: pass
    return []

# -----------------------------------------------------------------------------
# 3. 이메일 및 유틸리티 엔진
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
        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
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
        r1_c1, r1_c2 = st.columns(2); u_id = r1_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed"); u_pw = r1_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed", on_change=process_login)
        r2_c1, r2_c2 = st.columns(2); login_btn = r2_c1.button("Login", key="btn_login_m", use_container_width=True); reg_btn = r2_c2.button("계정신청 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True)
        if login_btn or st.session_state.pop('trigger_login', False):
            df_u = get_user_db(); u_id_clean = u_id.strip().lower(); hashed_pw = hash_password(u_pw) if u_pw else ""
            if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_list'})
                st.session_state.history = load_user_history(u_id_clean, 'material_list'); st.rerun()
            else:
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                if not valid.empty:
                    domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_exact_list = get_vip_list_exact(); vip_map = {v.lower(): v for v in vip_exact_list}
                    user_vip = vip_map.get(domain)
                    st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': u_id_clean, 'is_admin': False, 'user_vip_name': user_vip, 'workspace': 'material_list'})
                    st.session_state.history = load_user_history(u_id_clean, 'material_list'); st.rerun()
                else: st.error("ID/PW 확인 필요")
        if reg_btn: st.session_state.show_reg = not st.session_state.show_reg; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1]); r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if r_my.button("My 계정", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if r_out.button("Logout", use_container_width=True): 
            for k in default_session_vars: st.session_state[k] = default_session_vars[k]
            st.rerun()

# -----------------------------------------------------------------------------
# 관리자 및 VIP 전용 패널
# -----------------------------------------------------------------------------
if st.session_state.logged_in and st.session_state.is_admin:
    with st.container(border=True):
        st.markdown('<p class="main-header" style="color:#D35400;">👑 Admin Panel</p>', unsafe_allow_html=True)
        a1, a2, a3, a4 = st.columns(4)
        a1.link_button("👥 Users DB", URL_USERS, use_container_width=True); a2.link_button("🔋 Materials DB", URL_MATS, use_container_width=True); a3.link_button("⚙️ Parameters DB", URL_PARAM, use_container_width=True); a4.link_button("💾 Simulation Logs", URL_LOGS, use_container_width=True)
        vip_opts = ["material_list"] + get_vip_list_exact()
        sel_ws = st.selectbox("Workspace Switch (Admin Only)", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
        if sel_ws != st.session_state.workspace: st.session_state.workspace = sel_ws; st.session_state.history = load_user_history(st.session_state.user_email, sel_ws); st.rerun()

if st.session_state.logged_in and st.session_state.user_vip_name and not st.session_state.is_admin:
    with st.container(border=True):
        st.markdown(f'<p class="sub-header-bold" style="color:#00509E;">🏢 {st.session_state.user_vip_name.upper()} Workspace</p>', unsafe_allow_html=True)
        mode_opts = ["material_list (Public Mode)", f"{st.session_state.user_vip_name} (Private Mode)"]
        sel_mode = st.radio("Environment Selection", mode_opts, index=1 if st.session_state.workspace == st.session_state.user_vip_name else 0, horizontal=True)
        new_ws = "material_list" if "material_list" in sel_mode else st.session_state.user_vip_name
        if new_ws != st.session_state.workspace: st.session_state.workspace = new_ws; st.session_state.history = load_user_history(st.session_state.user_email, new_ws); st.rerun()

ws_tab = st.session_state.workspace
mat_df = load_cloud_data(URL_MATS, ws_tab)

# -----------------------------------------------------------------------------
# [가입신청 섹션]
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 Account Application</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("Company Email");
            if st.button("Send Verification Code"):
                if "@" not in e_in: st.error("Invalid email")
                else:
                    v_code = str(random.randint(100000, 999999))
                    if send_verification_email(e_in, v_code): st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
        elif st.session_state.reg_stage == 1:
            v_in = st.text_input(f"Enter code sent to {st.session_state.temp_email}");
            if st.button("Verify"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
                else: st.error("Mismatch")
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2); pw1 = p1.text_input("PW", type="password"); pw2 = p2.text_input("Confirm PW", type="password")
            c1, c2 = st.columns(2); n_name = c1.text_input("Name"); n_comp = c2.text_input("Company")
            c3, c4 = st.columns(2); n_dept = c3.text_input("Dept"); n_job = c4.text_input("Job")
            c5, c6 = st.columns(2); n_phone = c5.text_input("Phone"); n_purp = c6.text_input("Purpose")
            with st.expander("⚖️ Legal Disclaimer"): st.markdown("<div style='font-size:13px;'>Simulation results are for reference only. SynoTech is not liable for commercial decisions based on this data.</div>", unsafe_allow_html=True)
            if st.checkbox("I agree to the disclaimer"):
                if st.button("Submit", use_container_width=True):
                    conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=5)
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "Dept": n_dept, "Job": n_job, "Phone": n_phone, "Purpose": n_purp, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                    _ = conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                    st.success("Done! Please login."); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 UI (✅ 부제목 복구 완료)
# -----------------------------------------------------------------------------
is_pro = st.session_state.logged_in

with st.container(border=True):
    ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
    st.markdown(f'<p class="main-header">1. Material Selection <span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
    if not mat_df.empty:
        c1, c2, c3, c4 = st.columns(4); cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist(); cat_sel = c1.selectbox("Cathode", cat_list, key="scat")
        ano_sel = c2.selectbox("Anode", mat_df[mat_df['Category']=='Anode']['Name'].tolist(), key="sano"); ele_sel = c3.selectbox("Electrolyte", mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist(), key="sele"); sep_sel = c4.selectbox("Separator", mat_df[mat_df['Category']=='Separator']['Name'].tolist(), key="ssep")
        row = mat_df[mat_df['Name']==cat_sel].iloc[0]; d_cap = float(row.get('Cap_Def', 160)); d_vlt = float(row.get('Volt_Def', 3.05)); d_den = float(row.get('Den_Def', 2.2)); d_lif = int(row.get('Life_Def', 4000)); d_lod = float(row.get('Load_Def', 14.0))
    else: st.error("Materials Load Error"); d_cap, d_vlt, d_den, d_lif, d_lod = 160, 3.05, 2.2, 4000, 14

with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = True if is_pro else st.checkbox("Expert Mode (Pro Only)", disabled=True)
    s1, s2, s3, s4 = st.columns(4); v_cap = s1.slider("Capacity (mAh/g)", 100.0, 300.0, d_cap); v_vlt = s2.slider("Voltage (V)", 2.0, 5.0, d_vlt); v_den = s3.slider("Density (g/cc)", 1.0, 5.0, d_den, disabled=not expert); v_lif = s4.slider("Base Life", 500, 10000, d_lif, disabled=not expert)

with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    adv = True if is_pro else st.checkbox("Adv Mode (Pro Only)", disabled=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True) # ✅ 부제목 복구
        v_load = st.slider("Loading (mg/cm2)", 5.0, 50.0, d_lod); st.slider("Press Density", 1.5, 4.0, 2.5, disabled=not adv)
        st.slider("Conductive Agent %", 0.5, 10.0, 2.0, disabled=not adv); st.slider("Binder %", 0.5, 10.0, 3.0, disabled=not adv)
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True) # ✅ 부제목 복구
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, step=0.01); st.slider("Anode Press", 0.5, 2.5, 1.1, disabled=not adv)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True) # ✅ 부제목 복구
        v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0); st.slider("E/C Ratio", 1.0, 8.0, 3.5, disabled=not adv)

with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2); v_te = t1.slider("Energy Goal (Wh/kg)", 100, 300, 160); v_tc = t2.slider("Simulation C-rate", 0.1, 10.0, 1.0)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        cell_v = max(0.1, v_vlt - (0.1 + v_tc*0.02)); whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * max(0.5, 1.0 - (v_tc*0.015))
        res = {"Time": (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S"), "Cathode": cat_sel, "Wh/kg": round(whkg, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": int(v_lif * (0.95 ** v_tc))}
        v_ax, dq = get_dqdv(cat_sel, v_tc, mat_df); res.update({"dq_x": v_ax, "dq_y": dq, "Cap(mAh/g)": v_cap, "Anode": ano_sel, "Volt(V)": v_vlt, "Load(mg)": v_load, "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc})
        st.session_state.history.insert(0, res); st.rerun()
    if st.session_state.history:
        curr = st.session_state.history[st.selectbox("Select Record", range(len(st.session_state.history)), format_func=lambda x: f"[{st.session_state.history[x]['Time']}] {st.session_state.history[x]['Cathode']}") ]
        r1, r2, r3 = st.columns(3); r1.metric("Energy Density", f"{curr['Wh/kg']} Wh/kg", delta=round(curr['Wh/kg']-v_te, 1)); r2.metric("Cell V", f"{curr['Cell_V']} V"); r3.metric("Life", f"{curr['Life(Cyc)']:,} Cyc")
        g1, g2 = st.columns(2)
        g1.plotly_chart(go.Figure(go.Scatter(x=np.linspace(0,100,100), y=curr['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A'))).update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="DOD%"), use_container_width=True)
        g2.plotly_chart(go.Figure(go.Scatter(x=curr['dq_x'], y=curr['dq_y'], fill='tozeroy', line=dict(color='#e63946'))).update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="Voltage"), use_container_width=True)
        st.dataframe(pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore'), use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 데이터 관리
# -----------------------------------------------------------------------------
if is_pro and st.session_state.history:
    with st.container(border=True):
        st.markdown(f'<p class="main-header">6. Data Management ({st.session_state.workspace})</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("💾 Save to Cloud", use_container_width=True):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
                save_rec = curr.copy(); save_rec.update({'Email': st.session_state.user_email, 'Workspace': st.session_state.workspace}); save_rec.pop('dq_x', None); save_rec.pop('dq_y', None)
                _ = conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_rec])], ignore_index=True))
                st.success("Saved!")
            except: st.error("Save Failed")
        if c2.button("🗑️ Delete Record", use_container_width=True):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
                _ = conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df[~((db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == curr['Time']))])
                st.session_state.history = [h for h in st.session_state.history if h['Time'] != curr['Time']]; st.rerun()
            except: st.error("Delete Failed")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as wr: pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore').to_excel(wr, index=False)
        st.download_button("📥 Download Excel", buf.getvalue(), "SynoCore_Logs.xlsx", use_container_width=True)

st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)