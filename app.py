import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (50:50 헤더, 박스 수납, 여백)
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
# 3. 데이터 및 세션 초기화 (users.xlsx 자동 생성 포함)
# -----------------------------------------------------------------------------
USER_DB = "users.xlsx"
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "RegDate"]).to_excel(USER_DB, index=False)

# 소재 DB
mat_db = {
    "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "load": 14.0, "active": 92.0},
    "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "load": 15.0, "active": 95.0},
    "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "load": 12.0, "active": 90.0}
}

# 세션 상태 강제 초기화 (에러 방지)
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'history' not in st.session_state: st.session_state.history = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_reg' not in st.session_state: st.session_state.show_reg = False
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0

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
                st.session_state.logged_in = True; st.rerun()
            else: st.error("Login Failed")
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            if st.button("계정생성 ㅣ Pro 회원가입"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            st.markdown(f'<div class="trial-highlight" style="font-size:16px; padding:5px; margin-top:0;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ **wschoi@synotech.co.kr** (Admin) 님 접속 중")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# 보안 가입 프로세스
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">계정 신청 및 보안 인증 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("회사 이메일 입력")
            if st.button("인증번호 발송"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in
                st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            st.write(f"인증번호 (테스트): {st.session_state.v_code}")
            v_in = st.text_input("6자리 번호 입력")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code:
                    st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            with st.form("reg_form"):
                st.text_input("이름"); st.text_input("부서"); st.text_input("비밀번호", type="password")
                if st.form_submit_button("가입 완료"):
                    st.success("가입 성공! 로그인을 시도하세요."); st.session_state.show_reg = False; st.session_state.reg_stage = 0
        st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 (소재 자동 연동 로직 적용)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_type = m1.selectbox("Cathode", list(mat_db.keys()))
    m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 선택 변화 시 세션값 강제 동기화
cur = mat_db[cat_type]
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_type:
    st.session_state.last_cat = cat_type
    st.session_state.c_cap = float(cur['cap'])
    st.session_state.c_volt = float(cur['volt'])
    st.session_state.c_dens = float(cur['dens'])
    st.session_state.c_life = int(cur['life'])
    st.session_state.loading = float(cur['load'])
    st.session_state.active = float(cur['active'])

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, st.session_state.c_cap)
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, st.session_state.c_volt)
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, st.session_state.c_dens)
        c_life = s4.slider("Life (Cycles)", 500, 10000, st.session_state.c_life)
    else:
        c_cap, c_volt, c_dens, c_life = st.session_state.c_cap, st.session_state.c_volt, st.session_state.c_dens, st.session_state.c_life
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        load = st.slider("Loading (mg/cm2)", 5.0, 40.0, st.session_state.loading)
        if show_adv:
            st.slider("Cathode Density", 1.5, 3.5, 2.5)
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0)
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
        if show_adv:
            st.slider("Anode Density", 0.8, 2.0, 1.1)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte & Cell</p>', unsafe_allow_html=True)
        act = st.slider("Active Ratio (%)", 85.0, 99.0, st.session_state.active)
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration (박스 분리)
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

# [5] Simulation & History (박스 분리 및 PC 시간 기록)
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            # 계산 로직
            res_whkg = (c_cap * (act/100) * (c_volt - 0.1)) / (2.4 + (load/35))
            cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log = {"time": cur_time, "whkg": res_whkg, "v": c_volt - 0.1, "life": c_life, "cat": cat_type}
            st.session_state.history.insert(0, log)
            st.session_state.res = log
        else: st.error("무료 횟수 초과!")

    if st.session_state.history:
        st.markdown('<p class="sub-header-bold">과거 시뮬레이션 기록 선택 (최근 순)</p>', unsafe_allow_html=True)
        h_list = [f"[{h['time']}] {h['cat']} | {h['whkg']:.1f} Wh/kg" for h in st.session_state.history]
        sel_h = st.selectbox("History", h_list, label_visibility="collapsed")
        # 선택된 기록 복원 (필요 시)

    if 'res' in st.session_state:
        st.markdown("---")
        st.markdown(f'<p class="main-header">Engineering Analysis Result ({st.session_state.res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{st.session_state.res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{st.session_state.res['v']:.2f} V")
        r3.metric("Expected Life", f"{st.session_state.res['life']:,} Cycles")
        
        g1, g2 = st.columns([3, 7])
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown('<p class="sub-header-bold">Design Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Param": ["Loading", "N/P", "Active%"], "Value": [load, np, act]}))
    st.markdown("<br>", unsafe_allow_html=True)