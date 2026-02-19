import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (박스 내부 배경색 및 로그인/무료시도 버튼 정밀 조정)
st.markdown("""
    <style>
    /* 메뉴 및 헤더 가림 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 상단 로고 스타일 */
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 8px; }

    /* 로그인 버튼 높이 및 입력창 정렬 */
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
        font-size: 24px; /* 더 크게 수정 */
        font-weight: bold;
        margin-top: 10px;
    }

    /* [핵심] 모든 컨테이너(박스)에 회색 배경 적용 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
    }

    /* 제목 스타일 (26px 볼드) */
    .main-header {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #003366;
        margin-bottom: 10px;
        display: block;
    }

    /* 결과/소제목 스타일 (20px 볼드) */
    .sub-header-bold {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [상단] 헤더 (좌우 50:50 배치)
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])

with head_l:
    st.markdown(f"""
        <div class="header-container">
            <span class="syno-title">SynoCore</span>
            <span class="syno-subtitle">V1.4 Pro</span>
        </div>
    """, unsafe_allow_html=True)

with head_r:
    # 로그인 행 (높이 일치)
    log_c1, log_c2, log_c3 = st.columns([2, 2, 1])
    with log_c1:
        u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
    with log_c2:
        u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
    with log_c3:
        st.button("Login")
    
    # 계정 생성 및 무료 시도 (강조)
    st.markdown('<div style="text-align:right; font-size:14px; color:#003366; font-weight:bold; margin-top:5px; cursor:pointer;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
    st.markdown('<div class="trial-highlight">💡 무료 시도 가능 횟수: 3 / 3</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [본문] 1~5번 섹션 (박스 내부에 제목+내용 완전 수납)
# -----------------------------------------------------------------------------

# 1. Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.selectbox("Cathode", ["Prussian White", "Layered Oxide", "Polyanion"])
    with m2: st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    with m3: st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    with m4: st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])

# 2. Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        s1.slider("Capacity (mAh/g)", 100, 200, 162)
        s2.slider("Voltage (V)", 2.5, 4.5, 3.05)
        s3.slider("Density (g/cc)", 1.5, 4.0, 2.2)
        s4.slider("Life (Cycles)", 500, 10000, 4000)
    else:
        s1.markdown('<p class="sub-header-bold">Capacity</p>162 mAh/g', unsafe_allow_html=True)
        s2.markdown('<p class="sub-header-bold">Voltage</p>3.05 V', unsafe_allow_html=True)
        s3.markdown('<p class="sub-header-bold">Density</p>2.2 g/cc', unsafe_allow_html=True)
        s4.markdown('<p class="sub-header-bold">Base Life</p>4000 Cycles', unsafe_allow_html=True)

# 3. Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: 
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        st.slider("Loading (mg/cm2)", 5.0, 40.0, 14.0)
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Change</p>', unsafe_allow_html=True)
        st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)

# 4. Target Configuration
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: 
        st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
        st.slider("C-rate Goal", 0.1, 20.0, 1.0, label_visibility="collapsed")

# 5. Simulation History & Run
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        st.session_state.sim_run = True

    if st.session_state.get('sim_run'):
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        
        r1, r2, r3 = st.columns(3)
        with r1: 
            st.markdown('<p class="sub-header-bold">Energy Density</p>', unsafe_allow_html=True)
            st.write("## 158.4 Wh/kg")
        with r2: 
            st.markdown('<p class="sub-header-bold">Cell Voltage</p>', unsafe_allow_html=True)
            st.write("## 2.95 V")
        with r3: 
            st.markdown('<p class="sub-header-bold">Estimated Life</p>', unsafe_allow_html=True)
            st.write("## 3,120 Cycles")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 그래프 30% 배치
        g_col1, g_col2 = st.columns([3, 7])
        with g_col1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100)
            y = 3.05 - (x/100)**2
            fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🔍 그래프 상세 확대 분석"):
                st.plotly_chart(fig, use_container_width=True)

        with g_col2:
            st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            detail_table = pd.DataFrame({
                "Parameters": ["Cathode Loading", "Anode Loading", "Electrolyte Weight", "N/P Ratio"],
                "Values": ["14.0 mg/cm²", "12.5 mg/cm²", "3.2 g/Ah", "1.15"],
                "Note": ["Optimal", "Balanced", "Standard", "Safety"]
            })
            st.table(detail_table)