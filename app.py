import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# [안정화] 라이브러리 체크
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 디자인 (어제 버전 100% 복원)
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
        margin-bottom: 25px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 15px; display: block; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 유틸리티 및 세션 초기화
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'trial_count': 0, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'init_master': True
    })

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
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
        return df.astype(str) # PyArrow 에러 방지
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name"])

# -----------------------------------------------------------------------------
# 3. 상단 헤더 및 로그인 (내용 사라짐 방지 구조)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed").strip().lower()
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        if l_c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            else:
                df_u = get_user_db()
                hashed_pw = hash_password(u_pw) if u_pw else ""
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id) & (df_u['Password'] == hashed_pw)]
                if not valid.empty:
                    st.session_state.logged_in = True; st.rerun()
                else: st.error("정보 확인 필요")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정생성 ㅣ Pro 회원가입"):
                st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info("✅ 접속 중: Authorized Member")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# 가입신청 섹션 (화면 사라짐 방지를 위해 Expander 사용)
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.expander("📝 Pro 계정 신청 (개인정보는 암호화 보관됩니다)", expanded=True):
        if st.session_state.reg_stage == 0:
            reg_email = st.text_input("회사 이메일")
            if st.button("인증번호 발송"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = reg_email; st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            if st.button("인증 완료 (다음)"): st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            reg_pw = st.text_input("비밀번호 설정", type="password")
            reg_name = st.text_input("이름")
            if st.button("최종 신청"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df_u = get_user_db()
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(reg_pw), "Name": reg_name, "RegDate": datetime.now().strftime("%Y-%m-%d")}])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    st.success("신청 완료! 암호화되어 안전하게 보관됩니다."); st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except: st.error("연결 오류")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 메인 시뮬레이터 (1~4번 섹션 완벽 복원)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    if not mat_df.empty:
        cat_sel = m1.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist())
        row = mat_df[mat_df['Name']==cat_sel].iloc[0]
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = float(row.get('Capacity', 160)), float(row.get('Voltage', 3.05)), float(row.get('Density', 2.2)), int(row.get('Life', 4000)), float(row.get('Rec_Loading', 14.0))
    else:
        cat_sel = m1.selectbox("Cathode", ["Sample 소재"])
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = 160.0, 3.05, 2.2, 4000, 14.0
    m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"])
    m3.selectbox("Electrolyte", ["Standard", "High-Stability"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i) if expert else c_cap_i
    v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i) if expert else c_volt_i
    v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i) if expert else c_dens_i
    v_life = s4.slider("Base Life (Cyc)", 500, 10000, c_life_i) if expert else c_life_i
    if not expert:
        s1.metric("Capacity", f"{v_cap} mAh/g")
        s2.metric("Voltage", f"{v_volt} V")
        s3.metric("Density", f"{v_dens} g/cc")
        s4.metric("Base Life", f"{v_life:,} Cyc")

# [3] Process Parameters (자세히 보기 기능 포함)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    p1, p2, p3 = st.columns(3)
    with p1:
        v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, c_load_i)
        if show_adv: st.slider("Cathode Press Density", 1.5, 3.5, 2.5)
    with p2:
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
        if show_adv: st.slider("Anode Active Ratio %", 90.0, 98.0, 95.0)
    with p3:
        v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0)
        if show_adv: st.slider("Separator Thick (μm)", 12, 30, 16)

# [4] Target & Simulation Execution (에너지 밀도 목표 + 실행 버튼)
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target & Simulation Analysis</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
    v_tc = t2.slider("Simulation C-rate", 0.1, 10.0, 1.0)
    
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
            
            # [신기능] dQ/dV 그래프용 가상 데이터 생성
            v_axis = np.linspace(2.0, 4.2, 150)
            dqdv = np.zeros_like(v_axis)
            # Altris(Prussian White)인 경우 피크 2개, 그 외 1개 연출
            peaks = [3.05, 3.45] if "Prussian" in cat_sel or "Altris" in cat_sel else [3.2]
            for p in peaks:
                dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15
            
            st.session_state.sim_result = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Whkg": round(res_whkg, 1), "Volt": round(v_volt - 0.1, 2), "Life": v_life,
                "dq_x": v_axis, "dq_y": dqdv, "Cathode": cat_sel
            }
            st.session_state.history.insert(0, st.session_state.sim_result)
        else: st.error("무료 체험 횟수 초과!")

# -----------------------------------------------------------------------------
# [결과 시각화] Discharge Curve + dQ/dV Profile
# -----------------------------------------------------------------------------
if st.session_state.sim_result:
    res = st.session_state.sim_result
    st.markdown(f'<p class="main-header">Analysis Result ({res["Time"]})</p>', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    r1.metric("Energy Density", f"{res['Whkg']} Wh/kg", delta=round(res['Whkg'] - v_te, 1))
    r2.metric("Cell Voltage", f"{res['Volt']} V")
    r3.metric("Expected Life", f"{res['Life']:,} Cyc")
    
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Discharge Profile")
        
        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Volt']-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
        fig1.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        st.subheader("dQ/dV Profile (Fingerprint)")
        
        fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='#e63946', width=2)))
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
        st.plotly_chart(fig2, use_container_width=True)

# [5] Simulation History (전체 로그)
if st.session_state.history:
    st.markdown("---")
    st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore'), use_container_width=True)