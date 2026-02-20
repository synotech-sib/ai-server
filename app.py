import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 8px; }
    
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 35px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    
    /* 2번 항목 수치 강조 스타일 (글자 크기 복구) */
    .value-display { font-size: 22px !important; font-weight: bold !important; color: #003366; margin-bottom: 5px; }
    .unit-display { font-size: 14px; color: #666; font-weight: normal; }
    </style>
""", unsafe_allow_html=True)

# 2. 세션 상태 초기화 (로그인 및 로그 기록)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'history' not in st.session_state:
    st.session_state.history = []
if 'sim_result' not in st.session_state:
    st.session_state.sim_result = None

# 3. 로그인 로직 (안정성 강화)
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="login_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="login_pw", label_visibility="collapsed")
        if l_c3.button("Login", key="login_btn"):
            # 관리자 정보 확인
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun() # 로그인 즉시 화면 갱신
            else:
                st.error("ID 또는 PW가 일치하지 않습니다.")
    else:
        st.info("✅ Pro Mode 활성화됨")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 기초 데이터 초기값
c_cap_i, c_volt_i, v_load_i, v_np_i, v_act_i = 160.0, 3.05, 14.0, 1.15, 92.0

# -----------------------------------------------------------------------------
# 시뮬레이터 본문
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_sel = m1.selectbox("Cathode", ["Sample Cathode", "NCM-811", "LFP"])
    ano_sel = m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"])
    m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    
    # 레이블 구성: 로그인 전에는 빨간색 텍스트 추가
    exp_label = "🔓 물성 직접 수정 활성화"
    if not st.session_state.logged_in:
        exp_label += " :red[(Pro Mode 전용)]"
    
    expert = st.checkbox(exp_label, key="chk_exp", disabled=not st.session_state.logged_in)
    
    s1, s2, s3, s4 = st.columns(4)
    if expert and st.session_state.logged_in:
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i)
        v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i)
        v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, 2.2)
        v_life = s4.slider("Base Life (Cycles)", 500, 10000, 4000)
    else:
        v_cap, v_volt, v_dens, v_life = c_cap_i, c_volt_i, 2.2, 4000
        # 로그인 전에도 흐림 현상 없이 크게 표시
        s1.markdown(f'<p class="sub-header-bold">Capacity</p><p class="value-display">{v_cap} <span class="unit-display">mAh/g</span></p>', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p><p class="value-display">{v_volt} <span class="unit-display">V</span></p>', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p><p class="value-display">{v_dens} <span class="unit-display">g/cc</span></p>', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p><p class="value-display">{v_life:,} <span class="unit-display">Cyc</span></p>', unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    adv_label = "🔍 상세 설정(Advanced Settings) 활성화"
    if not st.session_state.logged_in:
        adv_label += " :red[(Pro Mode 전용)]"
        
    show_adv = st.checkbox(adv_label, key="chk_adv", disabled=not st.session_state.logged_in)
    
    p1, p2, p3 = st.columns(3)
    can_edit = st.session_state.logged_in and show_adv
    
    v_load = p1.slider("Loading (mg/cm2)", 5.0, 45.0, v_load_i, disabled=not can_edit)
    v_np = p2.slider("N/P Ratio", 1.0, 1.5, v_np_i, disabled=not can_edit)
    v_act = p3.slider("Active Ratio (%)", 80.0, 99.0, v_act_i, disabled=not can_edit)

# [4] Target
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0)

# [5] Simulation Run & Log
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Run & Log</p>', unsafe_allow_html=True)
    
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        # 계산 로직
        res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
        cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "Time": cur_time, "Cathode": cat_sel, "Wh/kg": round(res_whkg, 1),
            "Volt": v_volt, "Loading": v_load, "NP": v_np, "Life": v_life
        }
        st.session_state.history.insert(0, log_entry) # 최신 로그 상단 배치
        st.session_state.sim_result = log_entry

    if st.session_state.history:
        st.write("---")
        # 기록 선택 및 복원
        l_col1, l_col2 = st.columns([3, 1])
        with l_col1:
            opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg" for h in st.session_state.history]
            selected_idx = st.selectbox("과거 로그 선택", range(len(opts)), format_func=lambda x: opts[x])
        with l_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("결과값 불러오기"):
                st.session_state.sim_result = st.session_state.history[selected_idx]
                st.success("로그 기록을 불러왔습니다.")

        # 전체 로그 테이블
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

    # 시뮬레이션 결과 분석창
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown(f"### 📈 Result Analysis ({res['Time']})")
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg")
        r2.metric("Voltage", f"{res['Volt']} V")
        r3.metric("Life", f"{res['Life']:,} Cyc")
        
        # 그래프 생성
        fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Volt']-(np.linspace(0,1,100)**2), line=dict(color='#003366', width=3)))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)