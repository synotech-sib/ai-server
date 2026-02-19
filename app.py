import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (박스 디자인, 여백, 헤더 정밀 조정)
st.markdown("""
    <style>
    /* 메뉴 및 헤더 가림 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* 상단 헤더 50:50 배치 */
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000000; font-size: 22px; font-weight: normal; padding-top: 8px; }

    /* 로그인 버튼 및 입력창 수평 정렬 */
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important;
        border-radius: 4px !important; width: 100%; border: none !important;
    }

    /* 무료 시도 강조 박스 */
    .trial-highlight {
        background-color: #003366; color: white; padding: 15px;
        border-radius: 8px; text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;
    }

    /* [박스 수납 스타일] 제목과 내용이 모두 들어가는 회색 박스 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 10px 25px !important;
        margin-bottom: 45px !important; /* 박스 사이 간격 확보 */
    }

    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 세션 상태 관리 (버튼 작동 및 페이지 유지용)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_reg' not in st.session_state: st.session_state.show_reg = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'sim_result' not in st.session_state: st.session_state.sim_result = None

# 소재 데이터베이스
mat_db = {
    "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "rec_load": 14.0, "rec_dens": 2.5},
    "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "rec_load": 15.0, "rec_dens": 2.8},
    "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "rec_load": 12.0, "rec_dens": 2.1}
}

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (좌우 50:50 배치)
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])

with head_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with head_r:
    if not st.session_state.logged_in:
        log_c1, log_c2, log_c3 = st.columns([2, 2, 1])
        with log_c1: u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
        with log_c2: u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
        with log_c3: 
            if st.button("Login", key="login_main"):
                if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                    st.session_state.logged_in = True
                    st.rerun()
        
        # 계정생성 섹션
        reg_col1, reg_col2 = st.columns([1, 1])
        with reg_col1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="reg_toggle"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_col2:
            st.markdown(f'<div class="trial-highlight" style="font-size:16px; padding:5px; margin-top:0;">무료 시도 {st.session_state.trial_count}/3</div>', unsafe_allow_html=True)
    else:
        st.write(f"✅ **wschoi@synotech.co.kr** (Admin) 님 접속 중")
        if st.button("나의 계정 및 데이터 관리"): pass
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

# 계정 생성 폼 (세션 활성화 시)
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">계정생성 ㅣ Pro 회원가입</p>', unsafe_allow_html=True)
        st.text_input("회사 이메일")
        if st.button("6자리 인증번호 발송"):
            st.info("인증번호가 발송되었습니다. (Simulation)")
        st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 시뮬레이터 (각 번호별 완전 수납 박스)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: cat_type = st.selectbox("Cathode", list(mat_db.keys()))
    with m2: ano_type = st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    with m3: elec_type = st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    with m4: sep_type = st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown("<br>", unsafe_allow_html=True) # 박스 하단 여백 확보

cur_spec = mat_db[cat_type]

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100, 220, cur_spec['cap'])
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, cur_spec['volt'])
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, cur_spec['dens'])
        c_life = s4.slider("Life (Cycles)", 500, 10000, cur_spec['life'])
    else:
        c_cap, c_volt, c_dens, c_life = cur_spec['cap'], cur_spec['volt'], cur_spec['dens'], cur_spec['life']
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (자세히 보기 기능 대폭 강화)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, cur_spec['rec_load'])
        if show_adv:
            st.slider("Cathode Press Density (g/cc)", 1.5, 3.5, 2.5)
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0)
            st.slider("Binder %", 1.0, 5.0, 3.0)
            st.caption(f"Estimated Thickness: {loading/2.5*10:.1f} μm")

    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
        if show_adv:
            st.slider("Anode Press Density (g/cc)", 0.8, 2.0, 1.1)
            st.slider("Anode Active Material %", 90.0, 98.0, 95.0)
            st.caption(f"Target Anode Loading: {loading*1.15:.1f} mg/cm2")

    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte & Cell</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
            st.slider("Separator Thickness (μm)", 12, 25, 16)
            st.slider("Electrolyte Density", 1.0, 1.5, 1.2)
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration (별도 박스로 분리 및 C-rate 복구)
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: 
        st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        target_e = st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
        target_c = st.slider("C-rate Goal", 0.1, 20.0, 1.0, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run (별도 박스로 분리)
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if st.session_state.trial_count < 3 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            # 계산 로직
            cell_v = c_volt - 0.1
            wh_kg = (c_cap * (active_ratio/100) * cell_v) / (2.4 + (loading/35))
            st.session_state.sim_result = {"whkg": wh_kg, "v": cell_v, "life": c_life}
        else:
            st.error("무료 시도 횟수를 초과했습니다. Pro 가입이 필요합니다.")
    
    if st.session_state.sim_result:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        
        # 결과 대시보드 (20px 볼드 헤더 적용)
        res1, res2, res3 = st.columns(3)
        with res1:
            st.markdown('<p class="sub-header-bold">Energy Density</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['whkg']:.1f} Wh/kg")
        with res2:
            st.markdown('<p class="sub-header-bold">Cell Voltage</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['v']:.2f} V")
        with res3:
            st.markdown('<p class="sub-header-bold">Expected Life</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['life']:,} Cycles")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 그래프 및 상세 데이터 (30% 너비 유지)
        g_col1, g_col2 = st.columns([3, 7])
        with g_col1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100)
            y = c_volt - 0.1 - (x/100)**1.5
            fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🔍 그래프 상세 확대 분석"):
                st.plotly_chart(fig, use_container_width=True)

        with g_col2:
            st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({
                "Parameters": ["Cathode Loading", "N/P Ratio", "Active Ratio", "Test C-rate"],
                "Values": [f"{loading} mg/cm2", f"{np_ratio}", f"{active_ratio} %", f"{target_c} C"],
                "Note": ["Optimal", "Balanced", "High-Active", "Applied"]
            }))
    st.markdown("<br>", unsafe_allow_html=True)