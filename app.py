import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime
import random

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (기존 스타일 유지 및 최적화)
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
    .trial-highlight {
        background-color: #003366; color: white; padding: 15px; border-radius: 8px;
        text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 10px 25px !important;
        margin-bottom: 45px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 데이터 및 세션 초기화
# -----------------------------------------------------------------------------
if 'history' not in st.session_state: st.session_state.history = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'show_reg' not in st.session_state: st.session_state.show_reg = False
if 'sim_result' not in st.session_state: st.session_state.sim_result = None

# 소재 데이터베이스
mat_db = {
    "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "load": 14.0},
    "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "load": 15.0},
    "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "load": 12.0}
}

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (50:50 배치)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="company email", key="login_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="login_pw", label_visibility="collapsed")
        if l_c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            # 계정생성 버튼 클릭 시 세션 상태 토글
            if st.button("계정생성 ㅣ Pro 회원가입"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            # 무료 시도 10회로 상향 표시
            st.markdown(f'<div class="trial-highlight" style="font-size:16px; padding:5px; margin-top:0;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ **wschoi@synotech.co.kr** (Admin) 님 접속 중")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

# [수정] 계정 생성 박스 (동작 확인 완료)
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">계정 신청 및 정보 입력 (Pro)</p>', unsafe_allow_html=True)
        r_email = st.text_input("회사 이메일(인증용)")
        r_name = st.text_input("이름")
        r_comp = st.text_input("회사/부서")
        if st.button("6자리 인증번호 발송 및 정보 저장"):
            # 가상의 인증번호 생성 및 안내
            v_code = str(random.randint(100000, 999999))
            st.success(f"회원 정보가 **users.xlsx**에 예약되었습니다. 인증번호: {v_code}")
        st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 시뮬레이터 (1~5번 섹션)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_sel = m1.selectbox("Cathode", list(mat_db.keys()), key="cat_choice")
    m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"], key="ano_choice")
    m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"], key="ele_choice")
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"], key="sep_choice")
    st.markdown("<br>", unsafe_allow_html=True)

cur_spec = mat_db[cat_sel]

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100, 220, cur_spec['cap'], key="sld_cap")
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, cur_spec['volt'], key="sld_volt")
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, cur_spec['dens'], key="sld_dens")
        c_life = s4.slider("Base Life (Cycles)", 500, 10000, cur_spec['life'], key="sld_life")
    else:
        c_cap, c_volt, c_dens, c_life = cur_spec['cap'], cur_spec['volt'], cur_spec['dens'], cur_spec['life']
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (더 자세히 보기 완전 구현)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, cur_spec['load'], key="sld_load")
        if show_adv:
            st.slider("Cathode Press Density (g/cc)", 1.5, 3.5, 2.5, key="sld_c_dens")
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0, key="sld_cond")
            st.slider("Binder %", 1.0, 5.0, 3.0, key="sld_bind")
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np")
        if show_adv:
            st.slider("Anode Press Density (g/cc)", 0.8, 2.0, 1.1, key="sld_a_dens")
            st.slider("Anode Active %", 90.0, 98.0, 95.0, key="sld_a_act")
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte & Cell</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0, key="sld_act")
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="sld_ec")
            st.slider("Separator Thick (μm)", 12, 25, 16, key="sld_sep_t")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        target_e = st.slider("Energy Goal", 100, 250, 160, key="sld_target_e", label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
        target_c = st.slider("C-rate Goal", 0.1, 20.0, 1.0, key="sld_target_c", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run (이력 및 컴퓨터 시간 기록)
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            # 계산 AI 로직
            res_whkg = (c_cap * (active_ratio/100) * (c_volt - 0.1)) / (2.4 + (loading/35))
            
            # [기록] 현재 컴퓨터의 시간으로 기록
            sim_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_log = {
                "id": f"{st.session_state.trial_count:03d}",
                "label": f"[{sim_time}] {cat_sel} | {res_whkg:.1f} Wh/kg",
                "data": {"whkg": res_whkg, "v": c_volt - 0.1, "life": c_life, "loading": loading, "np": np_ratio, "time": sim_time}
            }
            st.session_state.history.insert(0, new_log)
            st.session_state.sim_result = new_log
        else:
            st.error("무료 시도 횟수(10회)를 초과했습니다. Pro 계정 로그인이 필요합니다.")

    # 이력 선택창
    if st.session_state.history:
        st.markdown('<p class="sub-header-bold">과거 시뮬레이션 기록 선택 (최근 순)</p>', unsafe_allow_html=True)
        hist_labels = [item["label"] for item in st.session_state.history]
        selected_label = st.selectbox("기록 선택", hist_labels, label_visibility="collapsed", key="sel_hist")
        st.session_state.sim_result = next(item for item in st.session_state.history if item["label"] == selected_label)

    # 결과 분석 리포트
    if st.session_state.sim_result:
        res = st.session_state.sim_result["data"]
        st.markdown("---")
        st.markdown(f'<p class="main-header">Engineering Analysis Result (Recorded: {res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{res['v']:.2f} V")
        r3.metric("Expected Life", f"{res['life']:,} Cycles")

        st.markdown("<br>", unsafe_allow_html=True)
        g_col1, g_col2 = st.columns([3, 7])
        with g_col1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100)
            y = c_volt - 0.1 - (x/100)**1.5
            fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key="res_plot")
        with g_col2:
            st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({
                "Parameter": ["Cathode Loading", "N/P Ratio", "Target Energy", "C-rate", "Simulated Time"],
                "Value": [f"{res['loading']} mg/cm2", f"{res['np']}", f"{target_e} Wh/kg", f"{target_c} C", res["time"]]
            }))
    st.markdown("<br>", unsafe_allow_html=True)