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
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 20px; font-weight: normal; padding-top: 8px; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 8px; }
    .pro-lock-text { color: #d9534f; font-weight: bold; font-size: 14px; }
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 유틸리티 함수
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

def get_user_db(url):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet="Sheet1", ttl=5)
        return df.astype(str)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name"])

# 3. 세션 상태 초기화
if 'init_v145' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'trial_count': 0, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'init_v145': True
    })

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

# 4. 상단 헤더 및 로그인
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div style="display: flex; align-items: center;"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login").strip().lower()
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login")
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
        if st.button("계정 생성 ㅣ Pro 회원가입"): st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.success("✅ Pro Mode 접속 중")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 권한 체크 변수
is_pro = st.session_state.logged_in

# -----------------------------------------------------------------------------
# [1] Material Selection (전체 공개)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_sel = m1.selectbox("Cathode", ["HiNa (Layered)", "Altris (Prussian White)", "Tiamat (Polyanion)"])
    m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"])
    m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])

# -----------------------------------------------------------------------------
# [2] Material Specs (조건부 자물쇠)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    
    # [요청 반영] 로그인 전후 텍스트 및 활성화 변경
    lock_suffix = " :red-bold[(Pro Mode 전용)]" if not is_pro else ""
    expert = st.checkbox(f"🔓 물성 직접 수정 활성화 {lock_suffix}", key="chk_exp_m", disabled=not is_pro)
    
    s1, s2, s3, s4 = st.columns(4)
    v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, 160.0, disabled=not (is_pro and expert))
    v_volt = s2.slider("Voltage (V)", 2.5, 4.5, 3.2, disabled=not (is_pro and expert))
    v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, 2.2, disabled=not (is_pro and expert))
    v_life = s4.slider("Base Life (Cycles)", 500, 10000, 4000, disabled=not (is_pro and expert))

# -----------------------------------------------------------------------------
# [3] Process Parameters (조건부 자물쇠)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    # [요청 반영] 로그인 전후 텍스트 및 활성화 변경
    adv_lock_suffix = " :red-bold[(Pro Mode 전용)]" if not is_pro else ""
    show_adv = st.checkbox(f"🔍 더 자세히 보기 (Advanced Settings) {adv_lock_suffix}", key="chk_adv_m", disabled=not is_pro)
    
    p1, p2, p3 = st.columns(3)
    with p1: 
        v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, 14.0, disabled=not is_pro)
        if show_adv and is_pro: st.slider("Cathode Press Density", 1.5, 3.5, 2.5)
    with p2: 
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, disabled=not is_pro)
        if show_adv and is_pro: st.slider("Anode Active %", 90.0, 98.0, 95.0)
    with p3: 
        v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, disabled=not is_pro)
        if show_adv and is_pro: st.slider("Separator Thick (μm)", 12, 30, 16)

# -----------------------------------------------------------------------------
# [4] Simulation Analysis (실행 및 실시간 결과)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">4. Simulation Analysis</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", 0.1, 10.0, 1.0)
    
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        st.session_state.trial_count += 1
        res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
        cur_time = datetime.now().strftime("%H:%M:%S")
        
        # dQ/dV 가상 데이터 생성
        v_axis = np.linspace(2.0, 4.2, 150)
        dqdv = np.zeros_like(v_axis)
        peaks = [3.05, 3.45] if "Prussian" in cat_sel else [3.2]
        for p in peaks: dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15
        
        st.session_state.sim_result = {
            "Time": cur_time, "Whkg": round(res_whkg, 1), "Volt": v_volt - 0.1, 
            "Life": v_life, "dq_x": v_axis, "dq_y": dqdv, "Material": cat_sel
        }
        st.session_state.history.insert(0, st.session_state.sim_result)

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Whkg']} Wh/kg", delta=round(res['Whkg']-v_te, 1))
        r2.metric("Cell Voltage", f"{res['Volt']} V")
        r3.metric("Expected Life", f"{res['Life']:,} Cyc")
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Discharge Profile")
            fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Volt']-(np.linspace(0,1,100)**2), line=dict(color='#003366', width=4)))
            fig1.update_layout(height=350, template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            st.subheader("dQ/dV Profile")
            fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='#e63946', width=2)))
            fig2.update_layout(height=350, template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
            st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------------------------
# [5] Simulation History (이전 로직 유지: 기록 보기 및 선택복원)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History</p>', unsafe_allow_html=True)
    
    if st.session_state.history:
        # [이전 로직] 과거 기록 불러오기 선택기
        log_opts = [f"[{h['Time']}] {h['Material']} | {h['Whkg']} Wh/kg" for h in st.session_state.history]
        sel_idx = st.selectbox("🔍 과거 기록 불러오기 (선택 시 상단 결과창에 복원됩니다)", range(len(log_opts)), format_func=lambda x: log_opts[x])
        
        if st.button("⏪ 선택 기록 복원"):
            st.session_state.sim_result = st.session_state.history[sel_idx]
            st.rerun()

        st.markdown("---")
        # [이전 로직] 전체 이력 테이블 출력
        df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
        st.dataframe(df_history, use_container_width=True)
    else:
        st.write("아직 시뮬레이션 이력이 없습니다.")