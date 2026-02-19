import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (박스 간격 및 여유 공간 정밀 조정)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

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
        width: 100%; border: none !important;
    }

    /* 무료 시도 강조 박스 */
    .trial-highlight {
        background-color: #003366; color: white; padding: 15px;
        border-radius: 8px; text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;
    }

    /* [수정] 박스 상하 여유 공간 (margin-bottom 추가) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 12px !important;
        padding: 25px !important;
        margin-bottom: 40px !important; /* 박스 사이의 간격을 줄간격 하나 이상으로 확보 */
    }

    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 15px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [상단] 헤더 50:50
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])
with head_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with head_r:
    log_c1, log_c2, log_c3 = st.columns([2, 2, 1])
    with log_c1: u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
    with log_c2: u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
    with log_c3: st.button("Login")
    st.markdown('<div style="text-align:right; font-size:14px; color:#003366; font-weight:bold; margin-top:5px; cursor:pointer;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
    st.markdown('<div class="trial-highlight">💡 무료 시도 가능 횟수: 3 / 3</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [본문] 1~5번 섹션 (박스 수납 및 여백 적용)
# -----------------------------------------------------------------------------

# 1. Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: cat_type = st.selectbox("Cathode", ["Prussian White", "Layered Oxide", "Polyanion"])
    with m2: ano_type = st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    with m3: elec_type = st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    with m4: sep_type = st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])

# 2. Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100, 200, 162)
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, 3.05)
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, 2.2)
        c_life = s4.slider("Life (Cycles)", 500, 10000, 4000)
    else:
        c_cap, c_volt, c_dens, c_life = 162, 3.05, 2.2, 4000
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life} Cycles', unsafe_allow_html=True)

# 3. Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: 
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, 14.0)
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Change</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)

# 4. Target Configuration
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: 
        st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        target_e = st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
        target_c = st.slider("C-rate Goal", 0.1, 20.0, 1.0, label_visibility="collapsed")

# 5. Simulation History & Run
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        # [AI/Calculation Logic] 실제 변수들을 사용하여 계산 수행
        cell_v = c_volt - 0.1 # 음극 전압 차감
        total_energy = (c_cap * (active_ratio/100) * cell_v)
        # 무게 에너지 밀도 간이 계산식 (로딩 및 팩터 반영)
        wh_kg_res = total_energy / (2.5 + (loading/40)) 
        st.session_state.result = {"wh_kg": wh_kg_res, "v": cell_v, "life": c_life}

    if 'result' in st.session_state:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{st.session_state.result['wh_kg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{st.session_state.result['v']:.2f} V")
        r3.metric("Expected Life", f"{st.session_state.result['life']:,} Cycles")

        # 그래프 및 표 30% 레이아웃
        g_c1, g_c2 = st.columns([3, 7])
        with g_c1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt - (np.linspace(0,1,100)**2), line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with g_c2:
            st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Parameters": ["N/P Ratio", "Loading", "Active %"], "Values": [np_ratio, loading, active_ratio]}))