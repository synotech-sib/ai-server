import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random

# 1. 페이지 설정 및 커스텀 CSS
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

st.markdown("""
    <style>
    /* 메뉴 및 헤더 가림 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* 상단 로고 스타일: SynoCore(네이비) V1.4 Pro(블랙) 한 줄 배치 */
    .header-left { display: flex; align-items: baseline; gap: 10px; }
    .syno-logo { color: #003366; font-size: 38px; font-weight: 900; }
    .syno-ver { color: #000000; font-size: 22px; font-weight: normal; }

    /* 로그인 버튼 높이 조절 (입력창 42px와 동기화) */
    div[data-testid="stButton"] > button {
        height: 42px !important;
        background-color: #003366 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        width: 100%;
        border: none !important;
    }

    /* 무료 시도 강조 박스 (딥블루, 큰 글씨) */
    .trial-highlight {
        background-color: #003366;
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-top: 10px;
    }

    /* [핵심] 섹션 박스 스타일: 내용 전체를 회색 박스 안에 수납 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 12px !important;
        padding: 25px !important;
        margin-bottom: 45px !important; /* 박스 하단 여유 공간 */
    }

    /* 제목 스타일 (26px 볼드) */
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 15px; display: block; }
    
    /* 소제목 스타일 (20px 볼드) */
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; display: block; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태 관리 (로그인, 시뮬레이션 기록 등)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'sim_result' not in st.session_state: st.session_state.sim_result = None

# 소재 데이터베이스
mat_db = {
    "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "load": 14.0},
    "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "load": 15.0},
    "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "load": 12.0}
}

# -----------------------------------------------------------------------------
# 3. 상단 헤더 (좌우 50:50 배치)
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])

with head_l:
    st.markdown("""
        <div class="header-left">
            <span class="syno-logo">SynoCore</span>
            <span class="syno-ver">V1.4 Pro</span>
        </div>
    """, unsafe_allow_html=True)

with head_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="company email", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
        if l_c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
        
        st.markdown('<div style="text-align:right; font-size:13px; color:#003366; font-weight:bold; cursor:pointer;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="trial-highlight">💡 무료 시도 가능 횟수: {3 - st.session_state.trial_count} / 3</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ **{u_id}** (Admin) 님 접속 중")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 본문 1~5번 섹션 (완전 수납 박스)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_type = m1.selectbox("Cathode", list(mat_db.keys()))
    ano_type = m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    elec_type = m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    sep_type = m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown("<br>", unsafe_allow_html=True)

cur_spec = mat_db[cat_type]

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        st.markdown('<p class="sub-header-bold">Tuning Properties</p>', unsafe_allow_html=True)
        c_cap = s1.slider("Capacity (mAh/g)", 100, 220, cur_spec['cap'])
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, cur_spec['volt'])
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, cur_spec['dens'])
        c_life = s4.slider("Life (Cycles)", 500, 10000, cur_spec['life'])
    else:
        c_cap, c_volt, c_dens, c_life = cur_spec['cap'], cur_spec['volt'], cur_spec['dens'], cur_spec['life']
        s1.markdown(f'<p class="sub-header-bold">Capacity</p> {c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p> {c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p> {c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p> {c_life} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (더 자세히 보기 기능 수정 완료)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    # "더 자세히 보기" 체크박스 (섹션 상단 배치)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    
    # 컬럼 생성
    p1, p2, p3 = st.columns(3)
    
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, cur_spec['load'])
        # [핵심] 체크박스 상태에 따라 추가 파라미터 노출
        if show_adv:
            st.slider("Cathode Press Density (g/cc)", 1.5, 3.5, 2.5)
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0)
            st.slider("Binder %", 1.0, 5.0, 3.0)

    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
        if show_adv:
            st.slider("Anode Press Density (g/cc)", 0.8, 2.0, 1.1)
            st.slider("Anode Active Material %", 90.0, 98.0, 95.0)

    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Change</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
            st.slider("Separator Thickness (μm)", 12, 25, 16)
            
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration
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

# [5] Simulation History & Run
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        # 계산 로직
        cell_v = c_volt - 0.1
        res_whkg = (c_cap * (active_ratio/100) * cell_v) / (2.4 + (loading/35))
        st.session_state.sim_result = {"whkg": res_whkg, "v": cell_v, "life": c_life}

    # 결과 분석 리포트 (시뮬레이션 후 나타남)
    if st.session_state.sim_result:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        
        r1, r2, r3 = st.columns(3)
        with r1: 
            st.markdown('<p class="sub-header-bold">Energy Density</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['whkg']:.1f} Wh/kg")
        with r2: 
            st.markdown('<p class="sub-header-bold">Cell Voltage</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['v']:.2f} V")
        with r3: 
            st.markdown('<p class="sub-header-bold">Estimated Life</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['life']:,} Cycles")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 그래프 30% 배치
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
            detail_table = pd.DataFrame({
                "Parameters": ["Cathode Loading", "Anode Loading", "Electrolyte Weight", "N/P Ratio"],
                "Values": [f"{loading} mg/cm²", f"{loading*1.1:.2f} mg/cm²", "3.5 g/Ah", f"{np_ratio}"],
                "Status": ["Optimal", "Balanced", "Standard", "Safety"]
            })
            st.table(detail_table)
    st.markdown("<br>", unsafe_allow_html=True)