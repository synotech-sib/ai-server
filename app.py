import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# [안정화] 라이브러리 체크
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 전문가용 UI
st.set_page_config(page_title="SynoCore V1.5 Pro Max", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 20px; font-weight: normal; }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 유틸리티 함수 (보안 및 에러 방어)
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

# [안정화] 이미지 2번의 PyArrow 에러를 잡기 위한 데이터 로드 함수
def get_user_db(url):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet="Sheet1", ttl=5)
        # [핵심] 모든 컬럼을 강제로 문자로 변환하여 타입 충돌(ArrowTypeError) 방지
        return df.astype(str)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# 3. 세션 상태 및 마스터 데이터
# -----------------------------------------------------------------------------
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'trial_count': 0, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'init_master': True
    })

# 글로벌 3사 데이터 (내장)
MASTER_MATS = [
    {"Name": "HiNa Battery (Layered Oxide)", "Cap": 145.0, "Volt": 3.2, "Type": "Layered", "Life": 3000},
    {"Name": "Altris (Prussian White)", "Cap": 160.0, "Volt": 3.2, "Type": "Prussian", "Life": 4000},
    {"Name": "Tiamat (Polyanion NVPF)", "Cap": 130.0, "Volt": 3.8, "Type": "Polyanion", "Life": 5000}
]

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인/회원가입
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div style="display: flex; align-items: center;"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.5 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed").strip().lower()
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        
        if l_c3.button("Login", key="btn_login_m"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            else:
                df_u = get_user_db(SHEET_URL)
                hashed_pw = hash_password(u_pw) if u_pw else ""
                # [안정화] 공백 제거 대조
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id) & (df_u['Password'] == hashed_pw)]
                if not valid.empty:
                    st.session_state.logged_in = True; st.rerun()
                else: st.error("정보 확인 필요")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정 생성 ㅣ Pro 회원가입", key="btn_go_reg_m"): 
                st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info("✅ 접속 중: Authorized Member")
        if st.button("Logout", key="btn_logout_m"): st.session_state.logged_in = False; st.rerun()

# [회원가입 모듈 - 요청 문구 반영]
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소", key="r_email_m")
            if st.button("인증번호 발송", key="r_v_send_m"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in; st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력", key="r_v_in_m")
            if st.button("인증 확인", key="r_v_chk_m"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2)
            pw1 = p1.text_input("2. Password", type="password", key="r_p1_m")
            pw2 = p2.text_input("2-1. Password 확인", type="password", key="r_p2_m")
            n_name = st.text_input("3. 이름", key="r_n_m")
            if st.button("가입신청", disabled=not (pw1==pw2 and n_name), key="r_fin_m"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df_u = get_user_db(SHEET_URL)
                    new_user = pd.DataFrame([{
                        "Email": st.session_state.temp_email, "Password": hash_password(pw1), 
                        "Name": n_name, "RegDate": datetime.now().strftime("%Y-%m-%d")
                    }])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    # [요청 문구 반영]
                    st.success("가입신청이 완료되었습니다. 개인정보는 암호화되어 보관되므로 안심하셔도 됩니다.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except: st.error("시트 연결 오류")

# -----------------------------------------------------------------------------
# 5. 시뮬레이션 본문 (dQ/dV 및 효율 보정 추가)
# -----------------------------------------------------------------------------
st.markdown("---")
col_s1, col_s2 = st.columns([1, 3])

with col_s1:
    st.markdown('<p class="main-header">Parameters</p>', unsafe_allow_html=True)
    sel_mat = st.selectbox("Cathode Selection", MASTER_MATS, format_func=lambda x: x['Name'])
    
    # [신기능] Lab-to-Fab 효율 보정 슬라이더
    yield_val = st.slider("양산 공정 효율 (%)", 70, 100, 92) / 100.0
    
    expert = st.toggle("🔓 Expert Mode")
    v_cap = st.number_input("Capacity (mAh/g)", value=sel_mat['Cap']) if expert else sel_mat['Cap']
    v_volt = st.number_input("Voltage (V)", value=sel_mat['Volt']) if expert else sel_mat['Volt']
    v_act = st.slider("Active Ratio (%)", 85.0, 98.0, 92.0)

with col_s2:
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        final_cap = v_cap * yield_val * (v_act/100)
        res_whkg = (final_cap * (v_volt - 0.1)) / 2.5
        
        # dQ/dV 그래프용 가상 데이터 (소재 타입별 피크 연출)
        v_axis = np.linspace(2.0, 4.2, 150)
        dqdv = np.zeros_like(v_axis)
        peaks = [3.05, 3.45] if sel_mat['Type']=="Prussian" else ([3.75] if sel_mat['Type']=="Polyanion" else [3.15])
        for p in peaks:
            dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15
        
        st.session_state.sim_result = {
            "whkg": round(res_whkg, 1), "v": v_volt, "cap": round(final_cap, 1),
            "dq_x": v_axis, "dq_y": dqdv, "life": sel_mat['Life'],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        m1, m2, m3 = st.columns(3)
        m1.metric("Energy Density", f"{res['whkg']} Wh/kg")
        m2.metric("Final Capacity", f"{res['cap']} mAh/g")
        m3.metric("Expected Life", f"{res['life']:,} Cyc")
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Discharge Curve")
                        fig1 = go.Figure(go.Scatter(x=np.linspace(0, 100, 100), y=res['v'] - (np.linspace(0, 1, 100)**2.5), line=dict(color='#003366', width=3)))
            fig1.update_layout(height=350, template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            st.subheader("dQ/dV Profile")
                        fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='red')))
            fig2.update_layout(height=350, template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
            st.plotly_chart(fig2, use_container_width=True)