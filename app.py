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
# 2. [중요] 세션 상태 초기화 (AttributeError 방지)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'sim_result' not in st.session_state: st.session_state.sim_result = None
if 'loading_val' not in st.session_state: st.session_state.loading_val = 14.0
if 'show_reg' not in st.session_state: st.session_state.show_reg = False

# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 표준화 (KeyError & Length Mismatch 방지)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    file = "material_list.xlsx"
    if not os.path.exists(file): return pd.DataFrame()
    df = pd.read_excel(file)
    # 컬럼명에서 괄호 및 단위 제거하여 표준화 (예: 'Base_Capacity (mAh/g)' -> 'Base_Capacity')
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_data()

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
        if l_c3.button("Login", key="btn_login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_reg"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            st.markdown(f'<div class="trial-highlight" style="font-size:16px; padding:5px; margin-top:0;">무료 시도 {st.session_state.trial_count}/3</div>', unsafe_allow_html=True)
    else:
        st.write(f"✅ **wschoi@synotech.co.kr** (Admin) 님 접속 중")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 시뮬레이터 (1~5번 완전 수납 박스)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["PW", "LO"]
    cat_sel = m1.selectbox("Cathode", cat_list, key="sel_cat")
    ano_sel = m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"], key="sel_ano")
    m3.selectbox("Electrolyte", ["Standard NaPF6"], key="sel_elec")
    m4.selectbox("Separator", ["PE 16um"], key="sel_sep")
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 연동 (Sync)
if not mat_df.empty:
    cat_row = mat_df[mat_df['Name'] == cat_sel].iloc[0]
    # KeyError 방지를 위해 get() 메서드 사용 및 표준화된 이름 사용
    c_cap_base = cat_row.get('Base_Capacity', 162)
    c_volt_base = cat_row.get('Base_Avg_Voltage', 3.05)
    c_dens_base = cat_row.get('Base_True_Density', cat_row.get('Base_True Density', 2.2))
    c_life_base = cat_row.get('Base_Life', 4000)
    st.session_state.loading_val = float(cat_row.get('Rec_Loading', 14.0))

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert_spec")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100, 220, int(c_cap_base), key="sld_cap")
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, float(c_volt_base), key="sld_volt")
    else:
        c_cap, c_volt = c_cap_base, c_volt_base
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
    s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens_base} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life_base} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, st.session_state.loading_val, key="sld_load")
        if show_adv:
            st.slider("Cathode Press Density (g/cc)", 1.5, 3.5, 2.5, key="sld_cat_dens")
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0, key="sld_cond")

    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np")
        if show_adv:
            st.slider("Anode Press Density (g/cc)", 0.8, 2.0, 1.1, key="sld_ano_dens")

    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte & Cell</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0, key="sld_active")
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="sld_ec")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        target_e = st.slider("Energy Goal", 100, 250, 160, key="sld_t_e", label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
        target_c = st.slider("C-rate Goal", 0.1, 20.0, 1.0, key="sld_t_c", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run"):
        if st.session_state.trial_count < 3 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            cell_v = c_volt - 0.1
            wh_kg = (c_cap * (active_ratio/100) * cell_v) / (2.4 + (loading/35))
            st.session_state.sim_result = {"whkg": wh_kg, "v": cell_v, "life": c_life_base}
        else:
            st.error("무료 시도 횟수를 초과했습니다.")

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
            st.markdown('<p class="sub-header-bold">Expected Life</p>', unsafe_allow_html=True)
            st.write(f"## {st.session_state.sim_result['life']:,} Cycles")

        st.markdown("<br>", unsafe_allow_html=True)
        g_col1, g_col2 = st.columns([3, 7])
        with g_col1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100)
            y = c_volt - 0.1 - (x/100)**1.5
            fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key="chart_discharge")
        with g_col2:
            st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Parameter": ["Loading", "N/P", "C-rate"], "Value": [f"{loading}", f"{np_ratio}", f"{target_c}C"]}))
    st.markdown("<br>", unsafe_allow_html=True)