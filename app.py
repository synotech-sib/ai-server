import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# 구글 시트 라이브러리 예외 처리
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 8px; }
    .pro-badge { color: #d63384; font-size: 14px; font-weight: bold; margin-left: 10px; }
    
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2. 세션 상태 초기화
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'show_reg': False,
        'reg_stage': 0,
        'v_code': "",
        'temp_email': "",
        'history': [],
        'sim_result': None,
        'init_master': True
    })

# 3. 데이터 로드
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

@st.cache_data
def load_materials():
    if not os.path.exists("material_list.xlsx"): return pd.DataFrame()
    df = pd.read_excel("material_list.xlsx")
    df.columns = [str(c).split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_materials()

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# 4. 상단 헤더 (로그인 모듈)
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        if l_c3.button("Login"):
            df_u = get_user_db()
            hashed_pw = hash_password(u_pw) if u_pw else ""
            valid = df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == hashed_pw)] if not df_u.empty else pd.DataFrame()
            
            if (u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!") or not valid.empty:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("정보 확인 필요")
        
        if st.button("계정생성 ㅣ Pro 회원가입"): 
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.info(f"✅ 접속 중: {st.session_state.get('temp_email', 'Admin')}")
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

# 가입신청 섹션 (생략 가능하나 구조 유지)
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        # ... (기존 가입 로직 동일) ...
        e_in = st.text_input("1. 회사 이메일 주소", key="r_email_m")
        if st.button("인증번호 발송"):
            st.session_state.v_code = str(random.randint(100000, 999999))
            st.session_state.temp_email = e_in
            st.session_state.reg_stage = 1
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문
# -----------------------------------------------------------------------------

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
    pro_label = "" if st.session_state.logged_in else " <span class='pro-badge'>(Pro Mode 전용)</span>"
    st.markdown(f'<p class="main-header">2. Material Specs Expert Mode{pro_label}</p>', unsafe_allow_html=True)
    
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_exp_m", disabled=not st.session_state.logged_in)
    
    s1, s2, s3, s4 = st.columns(4)
    if expert and st.session_state.logged_in:
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i)
        v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i)
        v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i)
        v_life = s4.slider("Base Life (Cycles)", 500, 10000, c_life_i)
    else:
        v_cap, v_volt, v_dens, v_life = c_cap_i, c_volt_i, c_dens_i, c_life_i
        s1.metric("Capacity", f"{v_cap} mAh/g")
        s2.metric("Voltage", f"{v_volt} V")
        s3.metric("Density", f"{v_dens} g/cc")
        s4.metric("Base Life", f"{v_life:,} Cyc")

# [3] Process Parameters
with st.container(border=True):
    st.markdown(f'<p class="main-header">3. Process Parameters{pro_label}</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 상세 공정 변수 활성화", key="chk_adv_m", disabled=not st.session_state.logged_in)
    
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">Cathode Settings</p>', unsafe_allow_html=True)
        v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, c_load_i, disabled=not st.session_state.logged_in if show_adv else True)
    with p2:
        st.markdown('<p class="sub-header-bold">Anode & Balance</p>', unsafe_allow_html=True)
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, disabled=not st.session_state.logged_in if show_adv else True)
    with p3:
        st.markdown('<p class="sub-header-bold">Cell Efficiency</p>', unsafe_allow_html=True)
        v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, disabled=not st.session_state.logged_in if show_adv else True)

# [4] Target Selection
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Selection</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0)

# [5] Simulation Run & Log
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Run & Log</p>', unsafe_allow_html=True)
    
    if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
        # 계산 로직
        res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
        cell_v = v_volt - 0.1
        cur_time = datetime.now().strftime("%H:%M:%S")
        
        log_data = {
            "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
            "Cap": v_cap, "Volt": v_volt, "Load": v_load,
            "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "Life": v_life
        }
        st.session_state.history.insert(0, log_data)
        st.session_state.sim_result = log_data

    # 로그 기록 및 복원
    if st.session_state.history:
        st.write("---")
        cols = st.columns([2, 1])
        with cols[0]:
            log_df = pd.DataFrame(st.session_state.history)
            st.dataframe(log_df, use_container_width=True, height=200)
        with cols[1]:
            st.markdown("**기록 복원**")
            log_opts = [f"{h['Time']} | {h['Wh/kg']}Wh" for h in st.session_state.history]
            sel_log = st.selectbox("다시 볼 기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x])
            if st.button("내용 불러오기"):
                st.session_state.sim_result = st.session_state.history[sel_log]

    # 결과 디스플레이
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.success(f"불러온 결과: {res['Wh/kg']} Wh/kg (설계 시간: {res['Time']})")
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg")
        r2.metric("Cell Voltage", f"{res['Cell_V']} V")
        r3.metric("Expected Life", f"{res['Life']:,} Cyc")
        
        # 그래프 예시
        fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**2), line=dict(color='#003366')))
        fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("SynoCore V1.45 Pro Mode - Authorized Personnel Only")