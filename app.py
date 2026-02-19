import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (UI/UX 정밀 조정)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 8px; }

    /* 로그인 버튼 높이 및 입력창 수평 정렬 */
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important;
        border-radius: 4px !important; width: 100%; border: none !important;
    }

    /* 무료 시도 강조 박스 */
    .trial-highlight {
        background-color: #003366; color: white; padding: 12px;
        border-radius: 8px; text-align: center; font-size: 22px; font-weight: bold; margin-top: 5px;
    }

    /* 섹션 박스 스타일 (제목+내용 완전 수납) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 40px !important;
    }

    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 세션 상태 및 데이터 초기화 (버튼 작동의 핵심)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_reg' not in st.session_state: st.session_state.show_reg = False
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'sim_result' not in st.session_state: st.session_state.sim_result = None

# 가상 소재 데이터베이스
mat_db = {
    "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "rec_load": 14.0, "rec_dens": 2.5},
    "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "rec_load": 15.0, "rec_dens": 2.8},
    "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "rec_load": 12.0, "rec_dens": 2.1}
}

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (50:50 배치 & 로그인 로직)
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])

with head_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with head_r:
    if not st.session_state.logged_in:
        log_c1, log_c2, log_c3 = st.columns([2, 2, 1])
        u_id = log_c1.text_input("ID", placeholder="company email", label_visibility="collapsed")
        u_pw = log_c2.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
        if log_c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Login Error")
        
        # 계정생성 ㅣ Pro 회원가입 (클릭 시 세션 변경)
        if st.button("계정생성 ㅣ Pro 회원가입", key="reg_btn", help="회원가입 절차 시작"):
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.write(f"✅ **wschoi@synotech.co.kr** (Admin) 접속 중")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # 무료 시도 강조
    st.markdown(f'<div class="trial-highlight">💡 무료 시도 가능 횟수: {3 - st.session_state.trial_count} / 3</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. [신규] 계정 생성 로직 (로그인 하단 섹션)
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">계정생성 ㅣ Pro 회원가입</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            reg_email = st.text_input("회사 이메일 입력")
            if st.button("6자리 인증숫자 발송 (Simulation)"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.reg_stage = 1
                st.info(f"인증번호가 발송되었습니다: {st.session_state.v_code}")
                st.rerun()
        elif st.session_state.reg_stage == 1:
            v_input = st.text_input("인증번호 입력")
            if st.button("인증 확인"):
                if v_input == st.session_state.v_code:
                    st.success("인증 성공! 정보를 입력하세요.")
                    st.session_state.reg_stage = 2
                    st.rerun()
        elif st.session_state.reg_stage == 2:
            with st.form("reg_form"):
                st.text_input("성함")
                st.text_input("회사/부서")
                st.text_input("비밀번호", type="password")
                if st.form_submit_button("가입 완료"):
                    st.success("가입이 완료되었습니다. 로그인 해주세요.")
                    st.session_state.show_reg = False
                    st.session_state.reg_stage = 0

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 본문 시뮬레이터 (1~5번 섹션)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: cat_type = st.selectbox("Cathode", list(mat_db.keys()))
    with m2: ano_type = st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    with m3: elec_type = st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    with m4: sep_type = st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 변경 시 슬라이더 값 동기화
cur_spec = mat_db[cat_type]
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_type:
    st.session_state.last_cat = cat_type
    st.session_state.loading_val = cur_spec['rec_load']
    st.session_state.dens_val = cur_spec['rec_dens']

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100, 200, cur_spec['cap'])
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, cur_spec['volt'])
    else:
        c_cap, c_volt = cur_spec['cap'], cur_spec['volt']
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
    s3.markdown(f'<p class="sub-header-bold">Density</p>{cur_spec["dens"]} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-header-bold">Base Life</p>{cur_spec["life"]} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, st.session_state.loading_val)
        if show_adv: st.slider("Binder %", 1.0, 5.0, 3.0)
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Change</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: t_en = st.slider("Target Energy Density (Wh/kg)", 100, 250, 160)
    with t2: t_cr = st.slider("Target C-rate", 0.1, 10.0, 1.0)
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", type="primary"):
        if st.session_state.trial_count < 3 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            # 실제 계산 로직
            res_whkg = (c_cap * (active_ratio/100) * (c_volt - 0.1)) / 2.5
            st.session_state.sim_result = {"whkg": res_whkg, "v": c_volt - 0.1, "life": cur_spec['life']}
        else:
            st.error("무료 시도 횟수를 초과했습니다. 로그인 하세요.")

    # 결과 출력 (세션 데이터가 있을 때만)
    if st.session_state.sim_result:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{st.session_state.sim_result['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{st.session_state.sim_result['v']:.2f} V")
        r3.metric("Expected Life", f"{st.session_state.sim_result['life']:,} Cycles")

        # 그래프 (30% 너비 및 확대)
        g1, g2 = st.columns([3, 7])
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100)
            y = c_volt - (x/100)**1.5
            fig = go.Figure(go.Scatter(x=x, y=y, name="Full-Cell", line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🔍 그래프 상세 확대 분석"):
                st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown('<p class="sub-header-bold">Detailed Design Table</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Param": ["N/P", "Loading", "C-rate"], "Val": [np_ratio, loading, t_cr]}))
    st.markdown("<br>", unsafe_allow_html=True)