import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import random

# 1. 페이지 설정 및 디자인 (기본 틀 유지)
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
# 2. [핵심] 엑셀 자료 불러오기 (Hardcoding 제거)
# -----------------------------------------------------------------------------
@st.cache_data
def load_excel_materials():
    file_path = "material_list.xlsx" # 대표님의 엑셀 파일명
    try:
        df = pd.read_excel(file_path)
        # 에러 방지용 전처리: 컬럼명의 공백 제거 및 소문자화(옵션)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"엑셀 파일을 읽을 수 없습니다: {e}")
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# 3. [에러 해결] 세션 상태 초기화 (AttributeError 방지)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'show_reg' not in st.session_state: st.session_state.show_reg = False
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0
if 'v_code' not in st.session_state: st.session_state.v_code = ""
if 'temp_email' not in st.session_state: st.session_state.temp_email = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'sim_result' not in st.session_state: st.session_state.sim_result = None
if 'loading_val' not in st.session_state: st.session_state.loading_val = 14.0

# -----------------------------------------------------------------------------
# 4. 헤더 및 로그인 (50:50)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

# 구글 시트 연결 (가입자 DB용)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.warning("GSheets 연결을 위해 라이브러리 설치가 필요할 수 있습니다.")

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="main_login_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="main_login_pw", label_visibility="collapsed")
        if l_c3.button("Login", key="btn_login_top"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            else: st.error("계정 확인 필요")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_reg_start"):
                st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ 접속 중: Admin")
        if st.button("Logout", key="btn_logout_top"): st.session_state.logged_in = False; st.rerun()

# -----------------------------------------------------------------------------
# 5. [1번 섹션] Material Selection (엑셀 연동)
# -----------------------------------------------------------------------------
mat_df = load_excel_materials()

with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        # 엑셀의 'Name' 컬럼을 기반으로 선택 리스트 생성
        cat_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
        cat_type = m1.selectbox("Cathode", cat_list, key="sel_cathode")
        
        ano_list = mat_df[mat_df['Category'] == 'Anode']['Name'].tolist()
        m2.selectbox("Anode", ano_list if ano_list else ["Sample Anode"], key="sel_anode")
        
        m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"], key="sel_elec")
        m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"], key="sel_sep")
        
        # [에러 해결] 선택된 소재의 수치를 세션에 즉시 반영 (Sync)
        selected_row = mat_df[mat_df['Name'] == cat_type].iloc[0]
        st.session_state.c_cap = float(selected_row.get('Capacity', 160))
        st.session_state.c_volt = float(selected_row.get('Voltage', 3.05))
        st.session_state.c_dens = float(selected_row.get('Density', 2.2))
        st.session_state.c_life = int(selected_row.get('Life', 4000))
        st.session_state.loading_val = float(selected_row.get('Rec_Loading', 14.0))
    else:
        st.warning("material_list.xlsx 파일을 찾을 수 없어 기본값을 사용합니다.")
    st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. [2번 섹션] Material Specs (KeyError 해결)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert_mode")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, st.session_state.get('c_cap', 160.0), key="sld_cap")
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, st.session_state.get('c_volt', 3.05), key="sld_volt")
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, st.session_state.get('c_dens', 2.2), key="sld_dens")
        c_life = s4.slider("Life (Cycles)", 500, 10000, st.session_state.get('c_life', 4000), key="sld_life")
    else:
        c_cap, c_volt = st.session_state.get('c_cap', 160.0), st.session_state.get('c_volt', 3.05)
        c_dens, c_life = st.session_state.get('c_dens', 2.2), st.session_state.get('c_life', 4000)
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. [3번~5번 섹션] (Duplicate ID 및 여백 해결)
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv_settings")
    p1, p2, p3 = st.columns(3)
    with p1:
        load = st.slider("Loading (mg/cm2)", 5.0, 45.0, st.session_state.loading_val, key="sld_main_loading")
        if show_adv:
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="sld_adv_dens")
            st.slider("Conductive Agent %", 0.5, 5.0, 2.0, key="sld_adv_cond")
    with p2:
        np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_main_np")
    with p3:
        act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sld_main_active")
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    target_e = t1.slider("Energy Density Goal (Wh/kg)", 100, 250, 160, key="sld_target_energy")
    target_c = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0, key="sld_target_crate")
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_sim"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (c_cap * (act/100) * (c_volt - 0.1)) / (2.4 + (load/35))
            cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.sim_result = {"time": cur_time, "whkg": res_whkg, "v": c_volt - 0.1, "life": c_life}
            st.session_state.history.insert(0, f"[{cur_time}] {res_whkg:.1f} Wh/kg")
        else: st.error("무료 횟수 초과!")

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Engineering Analysis Result ({res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{res['v']:.2f} V")
        r3.metric("Expected Life", f"{res['life']:,} Cycles")
        
        g1, g2 = st.columns([3, 7])
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            # [에러 해결] DuplicateElementId 방지용 고유 key 부여
            st.plotly_chart(fig, use_container_width=True, key="fig_main_result")
        with g2:
            st.table(pd.DataFrame({"Parameter": ["Loading", "N/P", "Active%", "C-rate"], "Value": [f"{load} mg", f"{np}", f"{act}%", f"{target_c}C"]}))
    st.markdown("<br>", unsafe_allow_html=True)