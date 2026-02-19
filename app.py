import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random

# 1. 페이지 설정 및 디자인 CSS
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-left { display: flex; align-items: baseline; gap: 10px; }
    .syno-logo { color: #003366; font-size: 38px; font-weight: 900; }
    .syno-ver { color: #000000; font-size: 22px; font-weight: normal; }
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
        border-radius: 12px !important; padding: 25px !important; margin-bottom: 45px !important;
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 15px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 및 전처리 (KeyError & Length Mismatch 해결)
@st.cache_data
def load_data():
    mat_file = "material_list.xlsx"
    if not os.path.exists(mat_file): return pd.DataFrame()
    df = pd.read_excel(mat_file)
    # 컬럼명에서 괄호 및 단위 제거하여 표준화 (예: 'Capacity (mAh/g)' -> 'Capacity')
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_data()

# 3. 세션 상태 초기화 (AttributeError 해결)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'sim_result' not in st.session_state: st.session_state.sim_result = None
if 'loading_val' not in st.session_state: st.session_state.loading_val = 14.0

# 4. 상단 헤더 (50:50)
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-left"><span class="syno-logo">SynoCore</span><span class="syno-ver">V1.4 Pro</span></div>', unsafe_allow_html=True)
with h_r:
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([2, 2, 1])
        u_id = c1.text_input("ID", placeholder="company email", label_visibility="collapsed")
        u_pw = c2.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
        if c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
        st.markdown('<div style="text-align:right; font-size:13px; color:#003366; font-weight:bold;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="trial-highlight">💡 무료 시도 가능 횟수: {3 - st.session_state.trial_count} / 3</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ **wschoi@synotech.co.kr** (Admin) 접속 중")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 5. 본문 시뮬레이터 (박스 수납)
# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["PW", "LO"]
    cat_sel = m1.selectbox("Cathode", cat_list)
    ano_sel = m2.selectbox("Anode", ["Kurarey A", "Aekyung D"])
    m3.selectbox("Electrolyte", ["Standard", "High-V"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic"])

# 데이터 연동 로직
if not mat_df.empty:
    cat_row = mat_df[mat_df['Name']==cat_sel].iloc[0]
    # 'Base_Capacity' 또는 'Capacity' 컬럼 유연하게 대응
    c_cap_base = cat_row.get('Base_Capacity', cat_row.get('Capacity', 160))
    c_volt_base = cat_row.get('Base_Avg_Voltage', cat_row.get('Base_Avg.Voltage', 3.05))
    c_dens_base = cat_row.get('Base_True_Density', cat_row.get('Base_True Density', 2.2))
    c_life_base = cat_row.get('Base_Life', 4000)
    st.session_state.loading_val = float(cat_row.get('Rec_Loading', 14.0))

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity", 100, 220, int(c_cap_base))
        c_v = s2.slider("Voltage", 2.5, 4.5, float(c_volt_base))
    else:
        s1.markdown(f'<p class="sub-header-bold">Capacity</p> {c_cap_base} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p> {c_volt_base} V', unsafe_allow_html=True)
        c_cap, c_v = c_cap_base, c_volt_base
    s3.markdown(f'<p class="sub-header-bold">Density</p> {c_dens_base} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-header-bold">Base Life</p> {c_life_base} Cyc', unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, st.session_state.loading_val, key="load_slider")
        if show_adv: st.slider("Conductive Agent %", 1.0, 5.0, 2.0, key="cond_slider")
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode Settings</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="np_slider")
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Settings</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0, key="act_slider")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Goals & [5] Simulation
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target & 5. Run</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    t_en = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if not st.session_state.logged_in and st.session_state.trial_count >= 3:
            st.error("무료 횟수 초과!")
        else:
            st.session_state.trial_count += 1
            st.session_state.sim_result = {"whkg": (c_cap * (active_ratio/100) * (c_v-0.1)) / 2.5, "v": c_v-0.1, "life": c_life_base}

    if st.session_state.sim_result:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"#### **Energy Density**\n## {st.session_state.sim_result['whkg']:.1f} Wh/kg")
        r2.markdown(f"#### **Cell Voltage**\n## {st.session_state.sim_result['v']:.2f} V")
        r3.markdown(f"#### **Life Expectancy**\n## {st.session_state.sim_result['life']} Cyc")
        
        st.markdown("---")
        g1, g2 = st.columns([3, 7])
        with g1:
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_v-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key="res_plot")
        with g2:
            st.table(pd.DataFrame({"Param": ["Loading", "N/P", "Active%"], "Value": [loading, np_ratio, active_ratio]}))