import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (박스 디자인 및 로그인 박스 높이 고정)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 8px; }

    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important;
        border-radius: 4px !important; width: 100%; border: none !important;
    }

    .trial-highlight {
        background-color: #003366; color: white; padding: 15px;
        border-radius: 8px; text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;
    }

    /* 박스 수납 및 하단 여백 설정 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 10px 25px !important;
        margin-bottom: 45px !important;
    }

    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. 가상 데이터베이스 (실제 엑셀 로드 권장)
def get_mat_data():
    return {
        "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "rec_load": 14.0, "rec_dens": 2.5, "rec_act": 92.0},
        "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "rec_load": 15.0, "rec_dens": 2.8, "rec_act": 95.0},
        "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "rec_load": 12.0, "rec_dens": 2.1, "rec_act": 90.0}
    }

mat_db = get_mat_data()

# -----------------------------------------------------------------------------
# [상단] 헤더 50:50 배치
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])
with head_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with head_r:
    log_c1, log_c2, log_c3 = st.columns([2, 2, 1])
    with log_c1: st.text_input("ID", placeholder="company email", label_visibility="collapsed")
    with log_c2: st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
    with log_c3: st.button("Login")
    st.markdown('<div style="text-align:right; font-size:14px; color:#003366; font-weight:bold; margin-top:5px; cursor:pointer;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
    st.markdown('<div class="trial-highlight">💡 무료 시도 가능 횟수: 3 / 3</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [본문] 1~5번 섹션 (박스 수납)
# -----------------------------------------------------------------------------

# 1. Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: cat_type = st.selectbox("Cathode", list(mat_db.keys()))
    with m2: ano_type = st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    with m3: elec_type = st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    with m4: sep_type = st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 변경 감지 및 세션 업데이트 (중요!)
cur_spec = mat_db[cat_type]
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_type:
    st.session_state.last_cat = cat_type
    st.session_state.loading = cur_spec['rec_load']
    st.session_state.cat_dens = cur_spec['rec_dens']
    st.session_state.active = cur_spec['rec_act']

# 2. Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100, 200, cur_spec['cap'])
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

# 3. Process Parameters (확장 기능 추가)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_more = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, st.session_state.loading)
        cat_dens_val = st.slider("Cathode Density (g/cc)", 1.5, 3.5, st.session_state.cat_dens)
        if show_more:
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0)
            st.slider("Binder %", 1.0, 5.0, 3.0)
            st.caption(f"Estimated Thickness: {loading/cat_dens_val*10:.1f} μm")

    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
        ano_dens_val = st.slider("Anode Density (g/cc)", 0.8, 2.0, 1.1)
        if show_more:
            st.slider("Anode Active %", 90.0, 98.0, 95.0)
            st.caption(f"Target Anode Loading: {loading*1.1:.1f} mg/cm2")

    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Change</p>', unsafe_allow_html=True)
        ec_ratio = st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, st.session_state.active)
        if show_more:
            st.slider("Separator Thick (μm)", 12, 25, 16)
            st.slider("Electrolyte Density", 1.0, 1.5, 1.2)
            
    st.markdown("<br>", unsafe_allow_html=True)

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
    st.markdown("<br>", unsafe_allow_html=True)

# 5. Simulation
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        cell_v = c_volt - 0.1
        wh_kg_res = (c_cap * (active_ratio/100) * cell_v) / (2.4 + (loading/35))
        st.session_state.result = {"wh_kg": wh_kg_res, "v": cell_v, "life": c_life}

    if 'result' in st.session_state:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{st.session_state.result['wh_kg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{st.session_state.result['v']:.2f} V")
        r3.metric("Expected Life", f"{st.session_state.result['life']:,} Cycles")
    st.markdown("<br>", unsafe_allow_html=True)