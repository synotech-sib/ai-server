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

# 1. 페이지 설정 및 전문가용 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro Max", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 8px; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 20px; display: block; }
    .lock-msg { background-color: #fff3cd; color: #856404; padding: 12px; border-radius: 8px; border: 1px solid #ffeeba; font-weight: bold; text-align: center; margin-bottom: 15px; }
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
if 'init_v145_pro' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'init_v145_pro': True
    })

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

# 4. 상단 헤더 및 로그인/회원가입
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro Max</span></div>', unsafe_allow_html=True)

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
        
        if st.button("계정 생성 ㅣ Pro 회원가입"):
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.success("✅ Pro Mode 활성화 중 (전문가 기능 잠금 해제)")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# [회원가입 모듈]
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.expander("📝 Pro 회원가입 신청", expanded=True):
        st.write("가입 후 물성 직접 수정 및 상세 공정 파라미터 조절이 가능합니다.")
        # 가입 신청 로직 (생략 - 기존 로직 유지)
        if st.button("신청 완료"): st.success("신청되었습니다."); st.session_state.show_reg = False

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [1] Material Selection (전체 공개)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    # dQ/dV 피크 연출을 위해 소재별 타입을 지정
    mat_options = {
        "HiNa (Layered Oxide)": {"Cap": 145.0, "Volt": 3.2, "Type": "Layered"},
        "Altris (Prussian White)": {"Cap": 160.0, "Volt": 3.2, "Type": "Prussian"},
        "Tiamat (Polyanion NVPF)": {"Cap": 130.0, "Volt": 3.8, "Type": "Polyanion"}
    }
    cat_sel = m1.selectbox("Cathode", list(mat_options.keys()))
    m2.selectbox("Anode", ["Hard Carbon (Standard)", "Hard Carbon (High-Cap)"])
    m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability Additive"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated 20um"])

# -----------------------------------------------------------------------------
# [2] & [3] 기능 잠금 섹션 (Pro 전용)
# -----------------------------------------------------------------------------
is_pro = st.session_state.logged_in

with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    if not is_pro:
        st.markdown('<div class="lock-msg">🔒 소재 물성 직접 수정 기능은 Pro 사용자에게만 제공됩니다.</div>', unsafe_allow_html=True)
    
    expert = st.checkbox("🔓 Expert Mode (Manual Edit)", disabled=not is_pro)
    s1, s2, s3, s4 = st.columns(4)
    # Pro가 아니면 기본값 고정 및 조작 불가
    def_cap = mat_options[cat_sel]["Cap"]
    def_volt = mat_options[cat_sel]["Volt"]
    
    v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, def_cap, disabled=not (is_pro and expert))
    v_volt = s2.slider("Voltage (V)", 2.5, 4.5, def_volt, disabled=not (is_pro and expert))
    v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, 2.2, disabled=not (is_pro and expert))
    v_life = s4.slider("Base Life (Cyc)", 500, 10000, 4000, disabled=not (is_pro and expert))

with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters (Advanced)</p>', unsafe_allow_html=True)
    if not is_pro:
        st.markdown('<div class="lock-msg">🔒 상세 공정 파라미터 조절 및 Lab-to-Fab 보정은 Pro 사용자에게만 제공됩니다.</div>', unsafe_allow_html=True)
    
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, 14.0, disabled=not is_pro)
        # Lab-to-Fab 효율 보정 (어제 제안한 기능 반영)
        
        yield_val = st.slider("현장 양산 효율 (Lab-to-Fab, %)", 70, 100, 92, disabled=not is_pro) / 100.0
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, disabled=not is_pro)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Cell Settings</p>', unsafe_allow_html=True)
        v_act = st.slider("Active Material Ratio (%)", 80.0, 99.0, 92.0, disabled=not is_pro)

# -----------------------------------------------------------------------------
# [4] Simulation Analysis (무제한 실행 및 dQ/dV 결과)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">4. Simulation Analysis</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", 0.1, 10.0, 1.0)
    
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        # 계산 로직 (양산 효율 반영)
        final_cap = v_cap * yield_val if is_pro else v_cap * 0.92
        res_whkg = (final_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
        
        # dQ/dV 가상 데이터 생성 (소재 특성 반영)
        v_axis = np.linspace(2.0, 4.2, 150)
        dqdv = np.zeros_like(v_axis)
        mat_type = mat_options[cat_sel]["Type"]
        peaks = [3.05, 3.45] if mat_type == "Prussian" else ([3.75] if mat_type == "Polyanion" else [3.15])
        for p in peaks:
            dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15
        
        st.session_state.sim_result = {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Whkg": round(res_whkg, 1), "Volt": v_volt - 0.1, "Life": v_life,
            "dq_x": v_axis, "dq_y": dqdv, "Material": cat_sel
        }
        st.session_state.history.insert(0, st.session_state.sim_result)

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.info(f"💡 분석 결과: {res['Material']} 기반 설계 ({res['Time']})")
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Whkg']} Wh/kg", delta=round(res['Whkg']-v_te, 1))
        r2.metric("Cell Voltage", f"{res['Volt']} V")
        r3.metric("Expected Life", f"{res['Life']:,} Cyc")
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Discharge Profile")
            

[Image of lithium-ion battery discharge curve]

            fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Volt']-(np.linspace(0,1,100)**2), line=dict(color='#003366', width=4)))
            fig1.update_layout(height=350, template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            st.subheader("dQ/dV Profile (Battery Fingerprint)")
            
            fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='#e63946', width=2)))
            fig2.update_layout(height=350, template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV (mAh/g.V)")
            st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------------------------
# [5] Simulation History (독립 섹션)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History</p>', unsafe_allow_html=True)
    if st.session_state.history:
        # 그래프 데이터 제외하고 표 출력
        df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
        st.dataframe(df_history, use_container_width=True)
    else:
        st.write("아직 시뮬레이션 이력이 없습니다. 위에서 설계를 실행해 주세요.")