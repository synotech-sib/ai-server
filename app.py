import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 8px; }
    
    /* 빨간색 Pro Mode 전용 문구 스타일 */
    .pro-tag { color: #ff0000; font-weight: bold; font-size: 14px; margin-left: 10px; }
    
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
    /* 수치 글자 크기 복구 (기존 데모 스타일) */
    .value-large { font-size: 22px !important; font-weight: bold !important; color: #003366; }
    </style>
""", unsafe_allow_html=True)

# 비밀번호 암호화 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2. 세션 상태 초기화 (Trial 관련 삭제)
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
        'init_master': True
    })

# 3. 데이터 로드 (원본 코드 유지)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

@st.cache_data
def load_materials():
    if not os.path.exists("material_list.xlsx"): return pd.DataFrame()
    df = pd.read_excel("material_list.xlsx")
    df.columns = [str(c).split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_materials()

# 4. 상단 헤더 및 로그인 (무료 시도 부분 삭제)
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        if l_c3.button("Login"):
            # 관리자 계정 예외 처리
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("정보 확인 필요")
        
        if st.button("계정생성 ㅣ Pro 회원가입"):
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.info("✅ Pro Mode 접속 중")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 5. 시뮬레이터 본문
# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        cat_sel = m1.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist())
        row = mat_df[mat_df['Name']==cat_sel].iloc[0]
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = float(row.get('Capacity', 160)), float(row.get('Voltage', 3.05)), float(row.get('Density', 2.2)), int(row.get('Life', 4000)), float(row.get('Rec_Loading', 14.0))
        ano_sel = m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"])
        m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
        m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    else:
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = 160.0, 3.05, 2.2, 4000, 14.0
        cat_sel, ano_sel = "Sample Cathode", "Sample Anode"

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    
    # 체크박스 및 Pro 전용 문구
    c_col1, c_col2 = st.columns([0.3, 0.7])
    with c_col1:
        expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_exp_m", disabled=not st.session_state.logged_in)
    with c_col2:
        if not st.session_state.logged_in:
            st.markdown('<p class="pro-tag">(Pro Mode 전용)</p>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    if expert and st.session_state.logged_in:
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i)
        v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i)
        v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i)
        v_life = s4.slider("Base Life (Cycles)", 500, 10000, c_life_i)
    else:
        v_cap, v_volt, v_dens, v_life = c_cap_i, c_volt_i, c_dens_i, c_life_i
        s1.markdown(f'<p class="sub-header-bold">Capacity</p><p class="value-large">{v_cap} <span style="font-size:14px">mAh/g</span></p>', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p><p class="value-large">{v_volt} <span style="font-size:14px">V</span></p>', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p><p class="value-large">{v_dens} <span style="font-size:14px">g/cc</span></p>', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p><p class="value-large">{v_life:,} <span style="font-size:14px">Cyc</span></p>', unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    c_col1, c_col2 = st.columns([0.35, 0.65])
    with c_col1:
        show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv_m", disabled=not st.session_state.logged_in)
    with c_col2:
        if not st.session_state.logged_in:
            st.markdown('<p class="pro-tag">(Pro Mode 전용)</p>', unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)
    # 로그인 여부에 따라 슬라이더 활성화 제어
    can_edit = st.session_state.logged_in and show_adv
    v_load = p1.slider("Loading (mg/cm2)", 5.0, 45.0, c_load_i, disabled=not can_edit)
    v_np = p2.slider("N/P Ratio", 1.0, 1.5, 1.15, disabled=not can_edit)
    v_act = p3.slider("Active Ratio (%)", 80.0, 99.0, 92.0, disabled=not can_edit)

# [4] Target
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0)

# [5] Simulation Run & Log (신규 항목)
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Run & Log</p>', unsafe_allow_html=True)
    
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        # 시뮬레이션 계산 로직
        res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
        cell_v = v_volt - 0.1
        cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
            "Wh/kg": round(res_whkg, 1), "Volt": round(cell_v, 2), "Life": v_life,
            "Loading": v_load, "NP_Ratio": v_np, "Active": v_act
        }
        st.session_state.history.insert(0, log_entry)
        st.session_state.sim_result = log_entry

    if st.session_state.history:
        st.markdown("---")
        # 로그 기록 복원 선택기
        l_col1, l_col2 = st.columns([3, 1])
        with l_col1:
            log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg" for h in st.session_state.history]
            selected_idx = st.selectbox("과거 시뮬레이션 기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x])
        with l_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("불러오기", use_container_width=True):
                st.session_state.sim_result = st.session_state.history[selected_idx]

        # 로그 데이터프레임 표시
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

    # 결과 분석 표시 (불러온 데이터 포함)
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown(f"### Analysis Result ({res['Time']})")
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg")
        r2.metric("Cell Voltage", f"{res['Volt']} V")
        r3.metric("Expected Life", f"{res['Life']:,} Cyc")
        
        # 그래프 출력
        fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Volt']-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)