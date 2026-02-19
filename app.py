import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random
import io
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

st.markdown("""
    <style>
    /* 메뉴 가림 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* 헤더 50:50 레이아웃 */
    .header-left { display: flex; align-items: baseline; gap: 15px; }
    .syno-logo { color: #003366; font-size: 38px; font-weight: 900; }
    .syno-ver { color: #000000; font-size: 22px; font-weight: normal; }

    /* 로그인 버튼 높이 */
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border: none !important;
    }

    /* 무료 시도 강조 박스 */
    .trial-box {
        background-color: #003366; color: white; padding: 12px;
        border-radius: 8px; text-align: center; font-size: 22px; font-weight: bold; margin-top: 10px;
    }

    /* 섹션 박스 (제목+내용 수납) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px !important; margin-bottom: 45px !important;
    }

    /* 폰트 위계 */
    .section-title { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 15px; }
    .sub-title-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 엔진 및 세션 초기화
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("param_config.xlsx")
        # 컬럼 표준화 (단위 제거)
        mat_df.columns = [c.split('(')[0].strip() for c in mat_df.columns]
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except: return pd.DataFrame(), pd.DataFrame()

if not os.path.exists("users.xlsx"):
    pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Is_Pro"]).to_excel("users.xlsx", index=False)

mat_df, param_dict = load_data()

# 세션 초기화
for key, val in {'logged_in': False, 'is_pro': False, 'trial_count': 0, 'reg_step': 0, 'history': [], 'sim_count': 0}.items():
    if key not in st.session_state: st.session_state[key] = val

# -----------------------------------------------------------------------------
# 3. 상단 헤더 (50:50)
# -----------------------------------------------------------------------------
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
                st.session_state.logged_in, st.session_state.is_pro = True, True
                st.rerun()
        
        st.markdown('<div style="text-align:right; font-size:13px; color:#003366; font-weight:bold;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="trial-box">무료 시도 {st.session_state.trial_count}/3</div>', unsafe_allow_html=True)
        
        # 계정 가입 (인증 프로세스)
        with st.expander("계정 신청 및 6자리 인증"):
            if st.session_state.reg_step == 0:
                re_email = st.text_input("회사 이메일")
                if st.button("인증번호 발송"):
                    st.session_state.code = str(random.randint(100000, 999999))
                    st.session_state.reg_step = 1
                    st.info(f"인증번호: {st.session_state.code}"); st.rerun()
            elif st.session_state.reg_step == 1:
                if st.text_input("인증번호") == st.session_state.code and st.button("확인"):
                    st.session_state.reg_step = 2; st.rerun()
            elif st.session_state.reg_step == 2:
                with st.form("join"):
                    st.text_input("성함"); st.text_input("부서"); st.text_input("비번", type="password")
                    if st.form_submit_button("가입완료"): 
                        st.success("가입성공!"); st.session_state.reg_step = 0
    else:
        st.write(f"✅ **{u_id}** 접속 중")
        if st.button("나의 계정 및 데이터 관리"): pass
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 시뮬레이터 본문 (1~5번 완전 수납 박스)
# -----------------------------------------------------------------------------
# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="section-title">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: cat_sel = st.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist())
    with m2: ano_sel = st.selectbox("Anode", mat_df[mat_df['Category']=='Anode']['Name'].tolist())
    with m3: st.selectbox("Electrolyte", ["Standard", "High-Voltage"])
    with m4: st.selectbox("Separator", ["PE 16um", "PP 20um"])
    st.markdown("<br>", unsafe_allow_html=True)

cat_row = mat_df[mat_df['Name']==cat_sel].iloc[0]
ano_row = mat_df[mat_df['Name']==ano_sel].iloc[0]

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="section-title">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_m = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_m:
        c_cap = s1.slider("Capacity", 100, 200, int(cat_row['Base_Capacity']))
        c_v = s2.slider("Voltage", 2.5, 4.5, float(cat_row['Base_Avg_Voltage']))
    else:
        s1.markdown(f'<p class="sub-title-bold">Capacity</p> {cat_row["Base_Capacity"]} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-title-bold">Voltage</p> {cat_row["Base_Avg_Voltage"]} V', unsafe_allow_html=True)
        c_cap, c_v = cat_row['Base_Capacity'], cat_row['Base_Avg_Voltage']
    s3.markdown(f'<p class="sub-title-bold">Density</p> {cat_row["Base_True_Density"]} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-title-bold">Base Life</p> {cat_row["Base_Life"]} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="section-title">3. Process Parameters</p>', unsafe_allow_html=True)
    adv = st.checkbox("🔍 더 자세히 보기")
    p1, p2, p3 = st.columns(3)
    with p1: 
        st.markdown('<p class="sub-title-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        load = st.slider("Loading", 5.0, 40.0, float(cat_row['Rec_Loading']))
    with p2:
        st.markdown('<p class="sub-title-bold">(B) Anode Settings</p>', unsafe_allow_html=True)
        np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3:
        st.markdown('<p class="sub-title-bold">(C) Electrolyte Settings</p>', unsafe_allow_html=True)
        act = st.slider("Active Ratio", 85.0, 99.0, float(cat_row['Rec_Active']))
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Goals
with st.container(border=True):
    st.markdown('<p class="section-title">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: 
        st.markdown('<p class="sub-title-bold">Target Energy Density</p>', unsafe_allow_html=True)
        t_en = st.slider("Energy", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-title-bold">Target C-rate</p>', unsafe_allow_html=True)
        t_cr = st.slider("C-rate", 0.1, 10.0, 1.0, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation & Result
with st.container(border=True):
    st.markdown('<p class="section-title">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if not st.session_state.is_pro and st.session_state.trial_count >= 3:
            st.error("횟수 초과! Pro 가입 필요")
        else:
            st.session_state.sim_count += 1
            res_whkg = (c_cap * (act/100) * (c_v - 0.1)) / 2.5
            st.session_state.res = {"id": f"{st.session_state.sim_count:03d}", "whkg": res_whkg, "v": c_v - 0.1}
            st.session_state.history.insert(0, f"#{st.session_state.res['id']} | {cat_sel} | {res_whkg:.1f} Wh/kg")

    if st.session_state.history:
        st.markdown('<p class="sub-title-bold">과거 시뮬레이션 기록 선택</p>', unsafe_allow_html=True)
        st.selectbox("History", st.session_state.history, label_visibility="collapsed")

    if 'res' in st.session_state:
        st.markdown("---")
        st.markdown('<p class="section-title">Engineering Analysis Result</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        with r1: st.markdown('<p class="sub-title-bold">Energy Density</p>', unsafe_allow_html=True); st.write(f"## {st.session_state.res['whkg']:.1f} Wh/kg")
        with r2: st.markdown('<p class="sub-title-bold">Cell Voltage</p>', unsafe_allow_html=True); st.write(f"## {st.session_state.res['v']:.2f} V")
        with r3: st.markdown('<p class="sub-title-bold">Life Expectancy</p>', unsafe_allow_html=True); st.write(f"## {cat_row['Base_Life']} Cycles")

        st.markdown("---")
        g1, g2 = st.columns([3, 7])
        with g1:
            st.markdown('<p class="sub-title-bold">Discharge Profile</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_v-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🔍 그래프 상세 확대"): st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown('<p class="sub-title-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Parameter": ["Loading", "N/P", "Active%"], "Value": [load, np, act]}))
    st.markdown("<br>", unsafe_allow_html=True)