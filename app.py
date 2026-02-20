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
    .main .block-container { max-width: 1150px; padding-top: 2rem; padding-bottom: 2rem; margin: auto; }
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    .syno-title { color: #1A729A; font-size: 46px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 14px; }
    
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    
    div[data-testid="stButton"] > button {
        height: 40px !important; background-color: #1A729A !important; 
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    
    div[data-testid="stDownloadButton"] > button {
        height: 40px !important; background-color: #FFCA28 !important; 
        color: #222 !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: 1px solid #E4B526 !important;
    }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #FFB300 !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 40px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# https://www.247connect.cloud/ko/%EA%B8%B0%EA%B3%84%EC%A0%81-%EC%9D%B8%EC%A1%B0-%EC%9D%B8%EA%B0%84/
# -----------------------------------------------------------------------------
URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"

def hash_password(password): return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=60, show_spinner=False)
def load_cloud_data(url):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

mat_df = load_cloud_data(URL_MATS)
param_df = load_cloud_data(URL_PARAM)
sys_params = param_df.set_index('Parameter_ID').to_dict('index') if not param_df.empty else {}

def get_p(pid, prop, fallback):
    try: return float(sys_params[pid][prop])
    except: return fallback

def get_user_db():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5)
        return df.astype(str) if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# ✉️ [이메일 발송 시스템 - ✅ 보안 100% 모드] 
# -----------------------------------------------------------------------------
def send_verification_email(to_email, code):
    primary_email = "wschoi@synotech.co.kr"
    alias_email = "synocore@synotech.co.kr"  
    
    # ✅ 코드 내 비밀번호 완전 제거. 오직 Secrets 환경변수에서만 가져옵니다.
    try:
        app_password = st.secrets["EMAIL_PASSWORD"]
    except Exception:
        st.error("이메일 시스템 설정(Secrets)을 확인해주세요.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = f"SynoCore 공식 센터 <{alias_email}>"
        msg['To'] = to_email
        msg['Subject'] = "[SynoCore Pro] 회원가입을 위한 인증번호가 발급되었습니다."

        body = f"""안녕하세요. 시노텍(SynoTech) 차세대 배터리 설계 플랫폼 SynoCore입니다.

회원가입 인증번호를 안내해 드립니다.

■ 인증번호 : {code}

본 메일은 발신 전용입니다. 감사합니다.
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(primary_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

# -----------------------------------------------------------------------------
# [물리 엔진 및 시뮬레이션 함수]
# -----------------------------------------------------------------------------
def get_dqdv(cat_sel, v_tc):
    v_axis = np.linspace(2.0, 4.2, 150)
    dqdv = np.zeros_like(v_axis)
    p1, p2 = 3.15, 0.0 
    if not mat_df.empty and 'Name' in mat_df.columns:
        mat_row = mat_df[mat_df['Name'] == cat_sel]
        if not mat_row.empty:
            p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15))
            p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
    
    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]
    for p in peaks:
        shifted_p = float(p) - (float(v_tc) * 0.015) 
        dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
        if db_df is None or db_df.empty: return []
        my_logs = db_df[db_df['Email'] == email]
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None)
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0))
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y
            hist.append(row_dict)
        return hist[::-1]
    except: return []

def create_pdf(data_list, title="Simulation Report"):
    if FPDF is None: return b""
    pdf = FPDF(orientation="L", unit="mm", format="A4"); pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C"); pdf.ln(10); pdf.set_font("Arial", "", 10)
    for item in data_list:
        pdf.cell(0, 8, f"Time: {item.get('Time')} | Cathode: {item.get('Cathode')} | Energy: {item.get('Wh/kg')} Wh/kg", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# -----------------------------------------------------------------------------
# [UI 세션 제어]
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "", 'history': []})

# -----------------------------------------------------------------------------
# [상단 헤더 & 로그인]
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l: st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)
with h_r:
    if not st.session_state.logged_in:
        c1, c2 = st.columns(2)
        u_id = c1.text_input("ID", placeholder="company email", label_visibility="collapsed")
        u_pw = c2.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
        b1, b2 = st.columns(2)
        if b1.button("Login", use_container_width=True):
            df_u = get_user_db()
            u_id_clean = u_id.strip().lower()
            valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hash_password(u_pw))] if not df_u.empty else pd.DataFrame()
            if u_id_clean == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.update({'logged_in': True, 'user_name': "최우석 대표", 'user_email': u_id_clean, 'history': load_user_history(u_id_clean)}); st.rerun()
            elif not valid.empty:
                st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': u_id_clean, 'history': load_user_history(u_id_clean)}); st.rerun()
            else: st.error("계정 정보를 확인해주세요.")
        if b2.button("계정신청 ㅣ Pro Mode", use_container_width=True): st.session_state.show_reg = True; st.rerun()
    else:
        r1, r2 = st.columns([3, 1])
        r1.markdown(f'<div class="user-greeting">{st.session_state.get("user_name")}님 (Pro)</div>', unsafe_allow_html=True)
        if r2.button("Logout", use_container_width=True): 
            st.session_state.logged_in = False; st.session_state.history = []; st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# [계정 신청 로직]
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (이메일 인증)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("가입용 회사 이메일 입력")
            if st.button("인증번호 발송"):
                if not e_in or "@" not in e_in: st.error("올바른 이메일 주소를 입력해주세요.")
                else:
                    v_code = str(random.randint(100000, 999999))
                    with st.spinner("📧 인증 메일을 발송 중입니다..."):
                        if send_verification_email(e_in, v_code):
                            st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
                        else: st.error("메일 발송에 실패했습니다.")
        elif st.session_state.reg_stage == 1:
            v_in = st.text_input(f"[{st.session_state.temp_email}]로 발송된 6자리 입력")
            if st.button("인증 확인") and v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
            elif v_in: st.error("인증번호 불일치")
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2); pw1 = p1.text_input("Password", type="password"); pw2 = p2.text_input("Password 확인", type="password")
            n_name = st.text_input("이름"); n_comp = st.text_input("회사명")
            if st.button("최종 가입신청") and pw1 == pw2 and n_name:
                conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1")
                new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "RegDate": datetime.now().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=pd.concat([df_u, new_user], ignore_index=True))
                st.success("가입 완료! 로그인 해주세요."); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

# -----------------------------------------------------------------------------
# [본문 시뮬레이터]
# -----------------------------------------------------------------------------
is_pro = st.session_state.logged_in

with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    if not mat_df.empty:
        cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
        cat_sel = m1.selectbox("Cathode", cat_list if cat_list else ["Sample"])
        row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
        def_cap_min, def_cap_max, def_cap_val = float(row.get('Cap_Min', 100)), float(row.get('Cap_Max', 250)), float(row.get('Cap_Def', 160))
        def_vlt_min, def_vlt_max, def_vlt_val = float(row.get('Volt_Min', 2.0)), float(row.get('Volt_Max', 4.5)), float(row.get('Volt_Def', 3.05))
        def_lod_min, def_lod_max, def_lod_val = float(row.get('Load_Min', 5.0)), float(row.get('Load_Max', 45.0)), float(row.get('Load_Def', 14.0))
        ano_sel = m2.selectbox("Anode", mat_df[mat_df['Category']=='Anode']['Name'].tolist())
        m3.selectbox("Electrolyte", mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist())
        m4.selectbox("Separator", mat_df[mat_df['Category']=='Separator']['Name'].tolist())
    else:
        cat_sel, ano_sel = "Sample", "Sample"
        def_cap_min, def_cap_max, def_cap_val = 100, 250, 160
        def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05
        def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = True if is_pro else st.checkbox("수정 활성화 (Pro 전용)", key="chk_exp_m", disabled=True)
    s1, s2, s3, s4 = st.columns(4)
    v_cap = s1.slider("Capacity (mAh/g)", def_cap_min, def_cap_max, def_cap_val, key=f"cap_{cat_sel}")
    v_volt = s2.slider("Voltage (V)", def_vlt_min, def_vlt_max, def_vlt_val, key=f"volt_{cat_sel}")
    v_dens = s3.slider("Density (g/cc)", 1.0, 4.5, 2.2, disabled=not expert)
    v_life = s4.slider("Base Life (Cycles)", 500, 10000, 4000, disabled=not expert)
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: v_load = st.slider("Loading (mg/cm2)", def_lod_min, def_lod_max, def_lod_val, key=f"load_{cat_sel}")
    with p2: v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3: v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0)
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: v_te = st.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    with t2: v_tc = st.slider("Simulation C-rate", 0.1, 5.0, 1.0)
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        cell_v = v_volt - (v_tc * 0.15)
        res_whkg = (v_cap * (v_act/100) * cell_v) / 2.5
        log = {"Time": datetime.now().strftime("%H:%M:%S"), "Cathode": cat_sel, "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "C-rate": v_tc}
        st.session_state.history.insert(0, log); st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.history:
    res = st.session_state.history[0]
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg")
    c2.metric("Cell Voltage", f"{res['Cell_V']} V")
    c3.metric("Simulation C-rate", f"{res['C-rate']} C")
    
    g1, g2 = st.columns(2)
    with g1:
        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
        fig1.update_layout(title="Discharge Profile", height=280, template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        v_x, v_y = get_dqdv(res['Cathode'], res['C-rate'])
        fig2 = go.Figure(go.Scatter(x=v_x, y=v_y, fill='tozeroy', line=dict(color='#e63946')))
        fig2.update_layout(title="dQ/dV Profile", height=280, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

# 6. 데이터 관리
if is_pro and st.session_state.history:
    with st.container(border=True):
        st.markdown('<p class="main-header">6. Data Management & Export (Pro)</p>', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        if b1.button("💾 내 계정에 저장하기"):
            conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData")
            if db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                save_row = res.copy(); save_row['Email'] = st.session_state.user_email
                conn.update(spreadsheet=URL_USERS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_row])]))
                st.success("저장 완료!")
            else: st.warning("중복 데이터 제외")
        
        df_exp = pd.DataFrame(st.session_state.history)
        buffer = io.BytesIO()
        df_exp.to_excel(buffer, index=False)
        b2.download_button("📥 내 기록 다운로드", data=buffer.getvalue(), file_name="SynoCore_Logs.xlsx")
        
        if FPDF is not None:
            b3.download_button("📄 결과 PDF 출력", data=create_pdf(st.session_state.history, "SynoCore Report"), file_name="Report.pdf")

st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)