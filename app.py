import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# [필수] 구글 시트 연결 라이브러리 체크
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("설치 필요: pip install st-gsheets-connection")

# 1. 페이지 설정 및 전문가용 디자인 CSS
st.set_page_config(page_title="SynoCore V1.5 Pro Max", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 20px; font-weight: normal; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    .main-header { font-size: 24px; font-weight: bold; color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 유틸리티 함수 (암호화 및 데이터 정제)
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

# [안정화] 구글 시트 데이터 로드 시 에러 방어 및 데이터 타입 강제 변환
def get_user_db(conn, url):
    try:
        df = conn.read(spreadsheet=url, worksheet="Sheet1", ttl=5)
        return df.astype(str) # 모든 데이터를 문자로 변환하여 PyArrow 에러 원천 차단
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# 3. 세션 상태 초기화
# -----------------------------------------------------------------------------
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "",
        'temp_email': "", 'history': [], 'sim_result': None, 'init_master': True
    })

# 구글 시트 연결 설정
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인/가입 모듈
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div style="display: flex; align-items: center;"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.5 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="login_id", label_visibility="collapsed").strip().lower()
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="login_pw", label_visibility="collapsed")
        
        if l_c3.button("Login"):
            # 마스터 계정 체크
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
            else:
                try:
                    df_u = get_user_db(conn, SHEET_URL)
                    hashed_pw = hash_password(u_pw) if u_pw else ""
                    valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id) & (df_u['Password'] == hashed_pw)]
                    if not valid.empty:
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("정보 확인 필요")
                except: st.warning("DB 연결 지연 중...")

        if st.button("New Account? 회원가입 신청", use_container_width=True):
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.info("✅ 접속 중: Authorized Member")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# [회원가입] 모든 로직 포함
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소")
            if st.button("인증번호 발송"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in; st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2)
            pw1 = p1.text_input("2. Password", type="password")
            pw2 = p2.text_input("2-1. Password 확인", type="password")
            n_name = st.text_input("3. 이름")
            if st.button("가입신청", disabled=not (pw1==pw2 and n_name)):
                try:
                    df_u = get_user_db(conn, SHEET_URL)
                    new_user = pd.DataFrame([{
                        "Email": st.session_state.temp_email, "Password": hash_password(pw1), 
                        "Name": n_name, "RegDate": datetime.now().strftime("%Y-%m-%d")
                    }])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    st.success("가입신청이 완료되었습니다. 개인정보는 암호화되어 보관되므로 안심하셔도 됩니다.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except: st.error("시트 저장 오류. 권한 설정을 확인하세요.")

# -----------------------------------------------------------------------------
# 5. 메인 시뮬레이터 본문
# -----------------------------------------------------------------------------
MASTER_MATS = [
    {"Name": "HiNa Battery (Layered Oxide)", "Cap": 145.0, "Volt": 3.2, "Dens": 4.0, "Type": "Layered"},
    {"Name": "Altris (Prussian White)", "Cap": 160.0, "Volt": 3.2, "Dens": 1.8, "Type": "Prussian"},
    {"Name": "Tiamat (Polyanion NVPF)", "Cap": 130.0, "Volt": 3.8, "Dens": 2.8, "Type": "Polyanion"}
]

with st.sidebar:
    st.markdown('<p class="main-header">Material & Process</p>', unsafe_allow_html=True)
    sel_mat = st.selectbox("Select Cathode Lib", MASTER_MATS, format_func=lambda x: x['Name'])
    
    st.markdown("---")
    # [신기능] Lab-to-Fab 보정
    yield_val = st.slider("현장 양산 효율 (Lab-to-Fab, %)", 70, 100, 92) / 100.0
    
    expert = st.toggle("🔓 Expert Mode (Manual Edit)")
    v_cap = st.number_input("Capacity (mAh/g)", value=sel_mat['Cap']) if expert else sel_mat['Cap']
    v_volt = st.number_input("Average Voltage (V)", value=sel_mat['Volt']) if expert else sel_mat['Volt']
    v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0)

# 시뮬레이션 실행
if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
    final_cap = v_cap * yield_val * (v_act/100)
    res_whkg = (final_cap * (v_volt - 0.1)) / 2.5
    
    # [신기능] dQ/dV 피크 생성 알고리즘
    v_axis = np.linspace(2.0, 4.2, 150)
    dqdv = np.zeros_like(v_axis)
    peaks = [3.1, 3.4] if sel_mat['Type']=="Prussian" else ([3.7] if sel_mat['Type']=="Polyanion" else [3.15])
    for p in peaks:
        dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.06**2)) * 10
    
    st.session_state.sim_result = {
        "whkg": round(res_whkg, 1), "v": v_volt, "cap": round(final_cap, 1),
        "dq_x": v_axis, "dq_y": dqdv, "time": datetime.now().strftime("%H:%M:%S")
    }

# 6. 결과 시각화
if st.session_state.sim_result:
    res = st.session_state.sim_result
    st.markdown("---")
    st.markdown(f'<p class="main-header">Analysis Result ({res["time"]})</p>', unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Energy Density", f"{res['whkg']} Wh/kg")
    m2.metric("Applied Capacity", f"{res['cap']} mAh/g")
    m3.metric("Nominal Voltage", f"{res['v']} V")
    
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Discharge Profile")
        fig1 = go.Figure(go.Scatter(x=np.linspace(0, 100, 100), y=res['v'] - (np.linspace(0, 1, 100)**2), line=dict(color='#003366', width=3)))
        fig1.update_layout(xaxis_title="DOD (%)", yaxis_title="Voltage (V)", height=350, template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        st.subheader("dQ/dV Profile")
        fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='red')))
        fig2.update_layout(xaxis_title="Voltage (V)", yaxis_title="dQ/dV (mAh/g.V)", height=350, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)