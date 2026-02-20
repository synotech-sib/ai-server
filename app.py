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

# [라이브러리 예외 처리]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

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
    
    /* 일반 실행/저장 버튼 (시노블루) */
    div[data-testid="stButton"] > button {
        height: 40px !important; background-color: #1A729A !important; 
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    
    /* 파일 다운로드/출력 버튼 (윈도우 폴더 색상) */
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
    except Exception: return pd.DataFrame()

mat_df = load_cloud_data(URL_MATS)
param_df = load_cloud_data(URL_PARAM)
sys_params = param_df.set_index('Parameter_ID').to_dict('index') if not param_df.empty else {}

def get_p(pid, prop, fallback):
    try: return float(sys_params[pid][prop])
    except: return fallback

# -----------------------------------------------------------------------------
# ✉️ [이메일 발송 시스템] 
# -----------------------------------------------------------------------------
def send_verification_email(to_email, code):
    primary_email = "wschoi@synotech.co.kr"
    alias_email = "synocore@synotech.co.kr"  
    try:
        app_password = st.secrets["EMAIL_PASSWORD"]
    except Exception: return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = f"SynoCore 공식 센터 <{alias_email}>"
        msg['To'] = to_email
        msg['Subject'] = "[SynoCore Pro] 회원가입을 위한 인증번호가 발급되었습니다."
        body = f"안녕하세요. SynoCore입니다.\n\n회원가입 인증번호 안내드립니다.\n■ 인증번호 : {code}\n\n감사합니다."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(primary_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

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
        return db_df[db_df['Email'] == email].to_dict('records')[::-1]
    except: return []

# -----------------------------------------------------------------------------
# [UI 세션 제어]
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "", 'history': []})

# -----------------------------------------------------------------------------
# [상단 헤더 & 로그인 - 1:1 비율 및 컴팩트 디자인]
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
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                df_u = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5)
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id.strip().lower()) & (df_u['Password'] == hash_password(u_pw))]
                if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                    st.session_state.update({'logged_in': True, 'user_name': "최우석 대표", 'user_email': u_id, 'history': load_user_history(u_id)}); st.rerun()
                elif not valid.empty:
                    st.session_state.update({'logged_in': True, 'user_name': valid.iloc[0]['Name'], 'user_email': u_id, 'history': load_user_history(u_id)}); st.rerun()
                else: st.error("계정 정보를 확인해주세요.")
            except: st.error("로그인 중 오류 발생")
        if b2.button("계정신청 ㅣ Pro Mode", use_container_width=True): st.session_state.show_reg = True; st.rerun()
    else:
        r1, r2 = st.columns([3, 1])
        r1.markdown(f'<div class="user-greeting">{st.session_state.get("user_name")}님 (Pro)</div>', unsafe_allow_html=True)
        if r2.button("Logout", use_container_width=True): st.session_state.logged_in = False; st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [계정 신청]
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (이메일 인증)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("가입용 회사 이메일 입력")
            if st.button("인증번호 발송"):
                if "@" in e_in:
                    v_code = str(random.randint(100000, 999999))
                    with st.spinner("📧 인증 메일을 발송 중입니다..."):
                        if send_verification_email(e_in, v_code):
                            st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
                else: st.error("이메일 주소를 확인해주세요.")
        elif st.session_state.reg_stage == 1:
            v_in = st.text_input(f"[{st.session_state.temp_email}]로 발송된 6자리 입력")
            if st.button("인증 확인") and v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2); pw1 = p1.text_input("PW", type="password"); pw2 = p2.text_input("PW 확인", type="password")
            n_name = st.text_input("이름"); n_comp = st.text_input("회사명")
            if st.button("최종 가입신청") and pw1 == pw2 and n_name:
                conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1")
                new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "RegDate": datetime.now().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=pd.concat([df_u, new_user])); st.session_state.show_reg = False; st.success("가입 완료!"); st.rerun()

# -----------------------------------------------------------------------------
# [1. Material Selection]
# -----------------------------------------------------------------------------
is_pro = st.session_state.logged_in

with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["Sample"]
    cat_sel = m1.selectbox("Cathode", cat_list)
    ano_sel = m2.selectbox("Anode", mat_df[mat_df['Category']=='Anode']['Name'].tolist() if not mat_df.empty else ["Sample"])
    m3.selectbox("Electrolyte", mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist() if not mat_df.empty else ["Sample"])
    m4.selectbox("Separator", mat_df[mat_df['Category']=='Separator']['Name'].tolist() if not mat_df.empty else ["Sample"])

    row = mat_df[mat_df['Name']==cat_sel].iloc[0] if not mat_df.empty else pd.Series()
    def_cap_min, def_cap_max, def_cap_val = float(row.get('Cap_Min', 100)), float(row.get('Cap_Max', 250)), float(row.get('Cap_Def', 160))
    def_vlt_min, def_vlt_max, def_vlt_val = float(row.get('Volt_Min', 2.0)), float(row.get('Volt_Max', 4.5)), float(row.get('Volt_Def', 3.05))
    def_lod_min, def_lod_max, def_lod_val = float(row.get('Load_Min', 5.0)), float(row.get('Load_Max', 45.0)), float(row.get('Load_Def', 14.0))
    st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [2. Material Specs & 3. Process]
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs & 3. Process Parameters</p>', unsafe_allow_html=True)
    expert = True if is_pro else st.checkbox("수정 활성화 (Pro)", disabled=True)
    s1, s2, s3, s4 = st.columns(4)
    v_cap = s1.slider("Capacity (mAh/g)", def_cap_min, def_cap_max, def_cap_val, key=f"cap_{cat_sel}")
    v_volt = s2.slider("Voltage (V)", def_vlt_min, def_vlt_max, def_vlt_val, key=f"volt_{cat_sel}")
    v_dens = s3.slider("Density (g/cc)", 1.0, 4.5, 2.2, disabled=not expert)
    v_life = s4.slider("Base Life (Cycles)", 500, 10000, 4000, disabled=not expert)
    
    p1, p2, p3, p4 = st.columns(4)
    v_load = p1.slider("Loading (mg/cm2)", def_lod_min, def_lod_max, def_lod_val, key=f"load_{cat_sel}")
    v_np = p2.slider("N/P Ratio", 1.0, 1.5, 1.15)
    v_act = p3.slider("Active Ratio (%)", 80.0, 99.0, 92.0)
    v_crate_p = p4.slider("Process Rate (C)", 0.1, 5.0, 0.5, disabled=not expert)
    st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [4. Target Settings]
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Density Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", get_p('target_crate', 'Min', 0.1), get_p('target_crate', 'Max', 5.0), get_p('target_crate', 'Default', 1.0))
    st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [5. Simulation Control]
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        cell_v = v_volt - (v_tc * 0.12)
        res_whkg = (v_cap * (v_act/100) * cell_v) / 2.4
        log = {"Time": datetime.now().strftime("%H:%M:%S"), "Cathode": cat_sel, "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "C-rate": v_tc}
        st.session_state.history.insert(0, log); st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.history:
    res = st.session_state.history[0]
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=round(res['Wh/kg'] - v_te, 1))
    c2.metric("Cell Voltage", f"{res['Cell_V']} V")
    c3.metric("Simulation C-rate", f"{res['C-rate']} C")
    
    g1, g2 = st.columns(2)
    with g1:
        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
        fig1.update_layout(title="Discharge Profile", height=280, template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        v_x, v_y = get_dqdv(res['Cathode'], res['C-rate'])
        fig2 = go.Figure(go.Scatter(x=v_x, y=v_y, fill='tozeroy', line=dict(color='#e63946')))
        fig2.update_layout(title="dQ/dV Fingerprint", height=280, template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
        st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------------------------
# [6. Data Management]
# -----------------------------------------------------------------------------
if is_pro and st.session_state.history:
    with st.container(border=True):
        st.markdown('<p class="main-header">6. Data Management & Export (Pro)</p>', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        if b1.button("💾 내 계정에 저장하기"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData")
                if db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                    save_row = res.copy(); save_row['Email'] = st.session_state.user_email
                    conn.update(spreadsheet=URL_USERS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_row])]))
                    st.success("내 계정에 저장하기가 완료되었습니다.")
                else: st.warning("중복 데이터 제외. 내 기록 다운로드를 실행해 주세요.")
            except: st.error("저장 중 오류 발생")
        
        df_exp = pd.DataFrame(st.session_state.history)
        buffer = io.BytesIO()
        df_exp.to_excel(buffer, index=False)
        b2.download_button("📥 내 기록 다운로드", data=buffer.getvalue(), file_name="SynoCore_Logs.xlsx")
        
        if FPDF is not None:
            # 간단 PDF 리포트 생성 예시
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 16); pdf.cell(40, 10, "SynoCore Report"); 
            b3.download_button("📄 결과 PDF 출력", data=pdf.output(dest="S").encode("latin-1"), file_name="Report.pdf")

st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)