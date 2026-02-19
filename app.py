import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import random
import os

# 1. 페이지 설정 및 디자인
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
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 45px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. [에러 해결] 세션 상태 초기화 (AttributeError 방지)
# -----------------------------------------------------------------------------
session_defaults = {
    'logged_in': False, 'trial_count': 0, 'show_reg': False, 'reg_stage': 0,
    'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
    'loading_val': 14.0, 'c_cap': 160.0, 'c_volt': 3.05, 'c_dens': 2.2, 'c_life': 4000
}
for key, val in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# -----------------------------------------------------------------------------
# 3. [에러 해결] 엑셀 데이터 로드 및 전처리 (KeyError 방지)
# -----------------------------------------------------------------------------
@st.cache_data
def load_materials():
    file_path = "material_list.xlsx"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    df = pd.read_excel(file_path)
    # 컬럼명 전처리: 공백 제거 및 단위(괄호) 제거하여 코드와 일치시킴
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_materials()

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (50:50 배치)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="top_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="top_pw", label_visibility="collapsed")
        if l_c3.button("Login", key="top_login_btn"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="top_reg_btn"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ 접속 중: Admin")
        if st.button("Logout", key="top_logout_btn"): st.session_state.logged_in = False; st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 시뮬레이터 (박스 수납 및 데이터 연동)
# -----------------------------------------------------------------------------

# [1] Material Selection (엑셀 데이터 연동)
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        cat_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
        cat_sel = m1.selectbox("Cathode", cat_list, key="sel_cat")
        
        # 선택된 소재 수치 자동 업데이트 (Sync)
        sel_row = mat_df[mat_df['Name'] == cat_sel].iloc[0]
        st.session_state.c_cap = float(sel_row.get('Capacity', 160))
        st.session_state.c_volt = float(sel_row.get('Voltage', 3.05))
        st.session_state.c_dens = float(sel_row.get('Density', 2.2))
        st.session_state.c_life = int(sel_row.get('Life', 4000))
        st.session_state.loading_val = float(sel_row.get('Rec_Loading', 14.0))

        m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"], key="sel_ano")
        m3.selectbox("Electrolyte", ["Standard NaPF6"], key="sel_ele")
        m4.selectbox("Separator", ["PE 16um"], key="sel_sep")
    else:
        st.error("material_list.xlsx 파일을 불러올 수 없습니다.")
    st.markdown("<br>", unsafe_allow_html=True)

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert")
    s1, s2, s3, s4 = st.columns(4)
    if expert:
        c_cap = s1.slider("Capacity", 100.0, 220.0, st.session_state.c_cap, key="sld_cap")
        c_volt = s2.slider("Voltage", 2.5, 4.5, st.session_state.c_volt, key="sld_volt")
    else:
        c_cap, c_volt = st.session_state.c_cap, st.session_state.c_volt
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
    s3.markdown(f'<p class="sub-header-bold">Density</p>{st.session_state.c_dens} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-header-bold">Base Life</p>{st.session_state.c_life} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv")
    p1, p2, p3 = st.columns(3)
    with p1:
        load = st.slider("Loading (mg/cm2)", 5.0, 45.0, st.session_state.loading_val, key="sld_load")
        if show_adv: 
            st.slider("Cathode Density", 1.5, 3.5, 2.5, key="sld_cat_dens")
            st.slider("Conductive Agent %", 0.5, 5.0, 2.0, key="sld_cond")
            st.slider("Binder %", 0.5, 5.0, 3.0, key="sld_bind")
    with p2:
        np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np")
        if show_adv: st.slider("Anode Density", 0.8, 2.0, 1.1, key="sld_ano_dens")
    with p3:
        act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sld_act")
        if show_adv: st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="sld_ec")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target & [5] Simulation (Duplicate ID 해결)
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    t_en = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160, key="sld_target_e")
    t_cr = t2.slider("Target C-rate", 0.1, 20.0, 1.0, key="sld_target_c")
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (c_cap * (act/100) * (c_volt - 0.1)) / 2.5
            st.session_state.sim_result = {"whkg": res_whkg, "v": c_volt - 0.1, "time": datetime.now().strftime("%H:%M:%S")}
        else: st.error("횟수 초과!")

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Analysis Result ({res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{res['v']:.2f} V")
        r3.metric("Expected Life", f"{st.session_state.c_life:,} Cyc")
        
        g1, g2 = st.columns([3, 7])
        with g1:
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            # [에러 해결] 고유 key 부여하여 DuplicateElementId 방지
            st.plotly_chart(fig, use_container_width=True, key="plot_res_main")
        with g2:
            st.table(pd.DataFrame({"Param": ["Loading", "N/P", "C-rate"], "Value": [load, np, t_cr]}))
    st.markdown("<br>", unsafe_allow_html=True)