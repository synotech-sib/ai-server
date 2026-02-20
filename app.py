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

# 1. 페이지 설정 및 디자인 (어제 버전 유지)
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2. 세션 상태 초기화
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'trial_count': 0, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
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

# 4. 상단 헤더 및 가입 모듈 (어제와 동일)
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        if l_c3.button("Login", key="btn_login_m"):
            df_u = get_user_db()
            hashed_pw = hash_password(u_pw) if u_pw else ""
            valid = df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == hashed_pw)] if not df_u.empty else pd.DataFrame()
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            elif not valid.empty:
                st.session_state.logged_in = True; st.rerun()
            else: st.error("정보 확인 필요")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_go_reg_m"): st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info("✅ 접속 중: Admin")
        if st.button("Logout", key="btn_logout_m"): st.session_state.logged_in = False; st.rerun()

# 가입신청 섹션 (생략 - 어제 코드 유지)
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        # ... (이전 가입 로직 코드와 동일)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        cat_sel = m1.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist(), key="sel_cat_m")
        row = mat_df[mat_df['Name']==cat_sel].iloc[0]
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = float(row.get('Capacity', 160)), float(row.get('Voltage', 3.05)), float(row.get('Density', 2.2)), int(row.get('Life', 4000)), float(row.get('Rec_Loading', 14.0))
        ano_sel = m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"], key="sel_ano_m")
        m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"], key="sel_ele_m")
        m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"], key="sel_sep_m")
    else:
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = 160.0, 3.05, 2.2, 4000, 14.0
        cat_sel, ano_sel = "Sample Cathode", "Sample Anode"

# [2] & [3] 섹션 (어제 코드 유지)
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_exp_m")
    s1, s2, s3, s4 = st.columns(4)
    v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i, key="sl_cap_m") if expert else c_cap_i
    v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i, key="sl_volt_m") if expert else c_volt_i
    v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i, key="sl_dens_m") if expert else c_dens_i
    v_life = s4.slider("Base Life (Cycles)", 500, 10000, c_life_i, key="sl_life_m") if expert else c_life_i
    if not expert:
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{v_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{v_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{v_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{v_life:,} Cyc', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, c_load_i, key="sl_load_m")
    with p2: v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sl_np_m")
    with p3: v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sl_act_m")

# [4] Target & 시뮬레이션 버튼 로직 (dQ/dV 추가)
with st.container(border=True):
    st.markdown('<p class="main-header">4. Simulation Analysis</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_tc = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0, key="sl_tc_m")
    
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_m"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
            cell_v = v_volt - 0.1
            
            # [dQ/dV 생성 로직 추가]
            v_axis = np.linspace(2.0, 4.2, 150)
            dqdv = np.zeros_like(v_axis)
            # 소재 키워드별 피크 위치 설정 (예시)
            peaks = [3.1, 3.45] if "Prussian" in cat_sel or "Altris" in cat_sel else [3.2]
            for p in peaks:
                dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15 # 가우시안 피크
            
            st.session_state.sim_result = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "Life": v_life,
                "dq_x": v_axis, "dq_y": dqdv, "Cathode": cat_sel, "Anode": ano_sel
            }
            st.session_state.history.insert(0, st.session_state.sim_result)

    # 분석 결과 창 (Discharge Curve + dQ/dV 그래프 나란히 배치)
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Analysis Result ({res["Time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg")
        r2.metric("Cell Voltage", f"{res['Cell_V']} V")
        r3.metric("Expected Life", f"{res['Life']:,} Cyc")
        
        g1, g2 = st.columns(2)
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            
            fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig1.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
            st.plotly_chart(fig1, use_container_width=True, key=f"v_plot_{random.randint(1,9999)}")
        
        with g2:
            st.markdown('<p class="sub-header-bold">dQ/dV Profile (Fingerprint)</p>', unsafe_allow_html=True)
            
            fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='red', width=2)))
            fig2.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
            st.plotly_chart(fig2, use_container_width=True, key=f"dq_plot_{random.randint(1,9999)}")

    # 시뮬레이션 상세 이력 (데이터프레임 출력 유지)
    if st.session_state.history:
        st.markdown("---")
        st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs (전체 이력)</p>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore'), use_container_width=True)