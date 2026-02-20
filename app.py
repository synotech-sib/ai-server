import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# [안정화] 구글 시트 라이브러리 체크
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.5 Pro Max", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 8px; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 20px; display: block; }
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

def get_user_db(url):
    """[안정화] ArrowTypeError 방지를 위해 모든 데이터를 문자열로 변환"""
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet="Sheet1", ttl=5)
        return df.astype(str)  # 전체 데이터를 문자열로 변환하여 에러 방지
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "RegDate"])

# -----------------------------------------------------------------------------
# 3. 세션 상태 및 마스터 데이터
# -----------------------------------------------------------------------------
if 'init_v15_fixed' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'init_v15_fixed': True
    })

MASTER_MATS = [
    {"Name": "HiNa Battery (Layered Oxide)", "Cap": 145.0, "Volt": 3.2, "Type": "Layered", "Life": 3000},
    {"Name": "Altris (Prussian White)", "Cap": 160.0, "Volt": 3.2, "Type": "Prussian", "Life": 4000},
    {"Name": "Tiamat (Polyanion NVPF)", "Cap": 130.0, "Volt": 3.8, "Type": "Polyanion", "Life": 5000}
]

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인/가입
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div style="display: flex; align-items: center;"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.5 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("email", placeholder="email", key="id_login", label_visibility="collapsed").strip().lower()
        u_pw = l_c2.text_input("password", type="password", placeholder="password", key="pw_login", label_visibility="collapsed")
        
        if l_c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            else:
                df_u = get_user_db(SHEET_URL)
                hashed_pw = hash_password(u_pw) if u_pw else ""
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id) & (df_u['Password'] == hashed_pw)]
                if not valid.empty:
                    st.session_state.logged_in = True; st.rerun()
                else: st.error("정보 확인 필요")
        
        if st.button("계정 생성 ㅣ Pro 회원가입"):
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.success("✅ 접속 중: Authorized Member")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이션 본문
# -----------------------------------------------------------------------------
st.markdown("---")
col_sidebar, col_main = st.columns([1, 3])

with col_sidebar:
    st.markdown('<p class="main-header">Parameters</p>', unsafe_allow_html=True)
    sel_mat = st.selectbox("Cathode Selection", MASTER_MATS, format_func=lambda x: x['Name'])
    yield_val = st.slider("양산 공정 효율 (%)", 70, 100, 92) / 100.0
    expert = st.toggle("🔓 Expert Mode")
    v_cap = st.number_input("Capacity (mAh/g)", value=sel_mat['Cap']) if expert else sel_mat['Cap']
    v_volt = st.number_input("Voltage (V)", value=sel_mat['Volt']) if expert else sel_mat['Volt']
    v_act = st.slider("Active Ratio (%)", 85.0, 98.0, 92.0)

with col_main:
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        final_cap = v_cap * yield_val * (v_act/100)
        res_whkg = (final_cap * (v_volt - 0.1)) / 2.5
        
        v_axis = np.linspace(2.0, 4.2, 150)
        dqdv = np.zeros_like(v_axis)
        peaks = [3.05, 3.45] if sel_mat['Type']=="Prussian" else ([3.75] if sel_mat['Type']=="Polyanion" else [3.15])
        for p in peaks:
            dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15
        
        st.session_state.sim_result = {
            "whkg": round(res_whkg, 1), "v": v_volt, "cap": round(final_cap, 1),
            "dq_x": v_axis, "dq_y": dqdv, "life": sel_mat['Life']
        }

    # [중요] 결과 출력 블록 - 들여쓰기 교정 완료
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        m1, m2, m3 = st.columns(3)
        m1.metric("Energy Density", f"{res['whkg']} Wh/kg")
        m2.metric("Applied Capacity", f"{res['cap']} mAh/g")
        m3.metric("Expected Life", f"{res['life']:,} Cyc")
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Discharge Profile")
            
            # 라인 175: 들여쓰기 오류 수정 지점
            fig1 = go.Figure(go.Scatter(x=np.linspace(0, 100, 100), y=res['v'] - (np.linspace(0, 1, 100)**2.5), line=dict(color='#003366', width=4)))
            fig1.update_layout(height=400, template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
            st.plotly_chart(fig1, use_container_width=True)
            
        with g2:
            st.subheader("dQ/dV Profile")
            
            fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='#e63946', width=2)))
            fig2.update_layout(height=400, template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
            st.plotly_chart(fig2, use_container_width=True)