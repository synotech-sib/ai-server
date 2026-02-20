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
    /* Pro Mode 전용 글자 스타일 */
    .pro-text { color: #ff4b4b; font-weight: bold; margin-left: 5px; font-size: 14px; }
    
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 35px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 비밀번호 암호화
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2. 세션 상태 초기화
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'history': [], 'sim_result': None, 'init_master': True
    })

# 4. 상단 헤더 (로그인 모듈 - "무료 시도" 삭제됨)
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        if l_c3.button("Login"):
            # 관리자 및 간이 로그인 로직 (DB연동 부분은 기존과 동일하므로 생략/유지 가능)
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("정보 확인 필요")
    else:
        st.info("✅ Pro Mode 접속 중")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 기초 데이터 설정 (가상)
c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = 160.0, 3.05, 2.2, 4000, 14.0
cat_sel, ano_sel = "Standard Cathode", "Hard Carbon (A)"

# -----------------------------------------------------------------------------
# 시뮬레이터 본문
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    cat_sel = m1.selectbox("Cathode", ["LFP-Type", "NMC-Type", "Sodium-ion"])
    ano_sel = m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"])

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    
    # 체크박스 레이블 조건부 설정
    chk_label_2 = "🔓 물성 직접 수정 활성화"
    if not st.session_state.logged_in:
        chk_label_2 += " (Pro Mode 전용)"
        
    expert = st.checkbox(chk_label_2, key="chk_exp_m", disabled=not st.session_state.logged_in)
    
    s1, s2, s3, s4 = st.columns(4)
    if expert and st.session_state.logged_in:
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i)
        v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i)
        v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i)
        v_life = s4.slider("Base Life (Cycles)", 500, 10000, c_life_i)
    else:
        v_cap, v_volt, v_dens, v_life = c_cap_i, c_volt_i, c_dens_i, c_life_i
        s1.metric("Capacity", f"{v_cap}")
        s2.metric("Voltage", f"{v_volt}")
        s3.metric("Density", f"{v_dens}")
        s4.metric("Base Life", f"{v_life:,}")

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    # 체크박스 레이블 조건부 설정
    chk_label_3 = "🔍 더 자세히 보기 (Advanced Settings)"
    if not st.session_state.logged_in:
        chk_label_3 += " (Pro Mode 전용)"
        
    show_adv = st.checkbox(chk_label_3, key="chk_adv_m", disabled=not st.session_state.logged_in)
    
    p1, p2, p3 = st.columns(3)
    # 로그인 여부와 체크박스 여부에 따른 활성화 제어
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

# [5] Simulation Run & Log
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Run & Log</p>', unsafe_allow_html=True)
    
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
        cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "Time": cur_time, "Cathode": cat_sel, "Wh/kg": round(res_whkg, 1),
            "Volt": v_volt, "Load": v_load, "NP": v_np, "Life": v_life
        }
        st.session_state.history.insert(0, log_entry)
        st.session_state.sim_result = log_entry

    if st.session_state.history:
        st.write("---")
        # 로그 선택 및 다시 보기
        log_options = [f"[{h['Time']}] {h['Wh/kg']} Wh/kg" for h in st.session_state.history]
        selected_idx = st.selectbox("과거 시뮬레이션 기록 선택", range(len(log_options)), format_func=lambda x: log_options[x])
        
        if st.button("선택한 로그 데이터 적용"):
            st.session_state.sim_result = st.session_state.history[selected_idx]
            st.success("데이터를 불러왔습니다.")

        # 상세 로그 테이블
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

    # 결과 분석 창
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown(f"### Result: {res['Wh/kg']} Wh/kg")
        col_res = st.columns(3)
        col_res[0].metric("Energy", f"{res['Wh/kg']} Wh/kg")
        col_res[1].metric("Voltage", f"{res['Volt']} V")
        col_res[2].metric("Life", f"{res['Life']:,} Cyc")