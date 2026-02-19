import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random
import io
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 커스텀 CSS (디자인 고정)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

st.markdown("""
    <style>
    /* 1. Streamlit 기본 메뉴 숨김 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* 2. 헤더 디자인: SynoCore(네이비) V1.4 Pro(블랙) 한 줄 배치 */
    .header-left { display: flex; align-items: baseline; gap: 10px; }
    .syno-logo { color: #003366; font-size: 38px; font-weight: 900; }
    .syno-ver { color: #000000; font-size: 18px; font-weight: normal; }

    /* 3. 로그인 버튼 높이 및 입력창 수평 정렬 */
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important;
        border-radius: 4px !important; width: 100%; border: none !important;
    }

    /* 4. 무료 시도 강조 박스 (딥블루) */
    .trial-box {
        background-color: #003366; color: white; padding: 12px;
        border-radius: 8px; text-align: center; font-size: 22px; font-weight: bold; margin-top: 8px;
    }

    /* 5. 섹션 박스 스타일 (제목+내용 완전 수납 및 하단 여백) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px !important;
        margin-bottom: 40px !important;
    }

    /* 6. 텍스트 크기 위계질서 */
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 15px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터베이스 및 세션 초기화 (에러 방지 핵심)
# -----------------------------------------------------------------------------
def init_db():
    if not os.path.exists("users.xlsx"):
        pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Is_Pro"]).to_excel("users.xlsx", index=False)
    if not os.path.exists("sim_logs.xlsx"):
        pd.DataFrame(columns=["ID", "User", "Summary", "Data"]).to_excel("sim_logs.xlsx", index=False)

@st.cache_data
def load_mat_data():
    try:
        df = pd.read_excel("material_list.xlsx")
        # KeyError 방지를 위한 컬럼명 표준화
        df.columns = [c.split('(')[0].strip() for c in df.columns] 
        return df
    except: return pd.DataFrame()

init_db()
mat_df = load_mat_data()

# 세션 상태 관리
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'reg_step' not in st.session_state: st.session_state.reg_step = 0
if 'sim_result' not in st.session_state: st.session_state.sim_result = None
if 'history' not in st.session_state: st.session_state.history = []

# -----------------------------------------------------------------------------
# 3. 상단 레이아웃 (좌우 50:50 고정)
# -----------------------------------------------------------------------------
top_l, top_r = st.columns([1, 1])

with top_l:
    st.markdown("""
        <div class="header-left">
            <span class="syno-logo">SynoCore</span>
            <span class="syno-ver">V1.4 Pro</span>
        </div>
    """, unsafe_allow_html=True)

with top_r:
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([2, 2, 1])
        u_id = c1.text_input("ID", placeholder="company email", label_visibility="collapsed")
        u_pw = c2.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
        if c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.session_state.user_info = {"Name": "관리자", "Email": u_id, "Is_Pro": True}
                st.rerun()
            # 일반 유저 체크 로직 추가 가능
        
        st.markdown('<div style="text-align:right; font-size:13px; color:#003366; font-weight:bold; cursor:pointer;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
        # 무료 시도 강조
        st.markdown(f'<div class="trial-box">무료 시도 {st.session_state.trial_count}/3</div>', unsafe_allow_html=True)
    else:
        st.write(f"✅ **{st.session_state.user_info['Name']}** 님 접속 중")
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("나의 계정 및 데이터 관리"): pass # 마이페이지 로직
        if btn_c2.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 본문 시뮬레이터 (1~5번 완전 수납 박스)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty else ["PW", "PI", "LO"]
    with m1: cat_sel = st.selectbox("Cathode", cat_list)
    with m2: ano_sel = st.selectbox("Anode", ["Kurarey A", "Aekyung Chemical D"])
    with m3: st.selectbox("Electrolyte", ["G Type", "A Type"])
    with m4: st.selectbox("Separator", ["PE", "PP"])
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 연동 (Sync)
if not mat_df.empty:
    cat_row = mat_df[mat_df['Name'] == cat_sel].iloc[0]
    if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_sel:
        st.session_state.last_cat = cat_sel
        st.session_state.load_val = float(cat_row['Rec_Loading'])
        st.session_state.dens_val = float(cat_row['Rec_Density'])
else:
    cat_row = {'Base_Capacity': 162, 'Base_Avg_Voltage': 3.05, 'Base_True Density': 2.2, 'Base_Life': 4000}
    if 'load_val' not in st.session_state: st.session_state.load_val = 14.0

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        st.markdown('<p class="sub-header-bold">Tuning Mode</p>', unsafe_allow_html=True)
        c_cap = s1.slider("Capacity", 100, 200, int(cat_row['Base_Capacity']))
        c_v = s2.slider("Voltage", 2.5, 4.5, float(cat_row['Base_Avg_Voltage']))
    else:
        s1.markdown(f'<p class="sub-header-bold">Capacity</p> {cat_row["Base_Capacity"]} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p> {cat_row["Base_Avg_Voltage"]} V', unsafe_allow_html=True)
        c_cap, c_v = cat_row['Base_Capacity'], cat_row['Base_Avg_Voltage']
    s3.markdown(f'<p class="sub-header-bold">Density</p> {cat_row["Base_True Density"]} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-header-bold">Life</p> {cat_row["Base_Life"]} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, st.session_state.load_val)
        if show_adv: st.slider("Density (g/cc)", 1.5, 3.5, 2.5)
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode Settings</p>', unsafe_allow_html=True)
        np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Settings</p>', unsafe_allow_html=True)
        act = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Goals
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: 
        st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        target_e = st.slider("Goal", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
        target_c = st.slider("C-rate", 0.1, 10.0, 1.0, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if not st.session_state.logged_in and st.session_state.trial_count >= 3:
            st.error("무료 시도 횟수를 초과했습니다. Pro 전환이 필요합니다.")
        else:
            st.session_state.trial_count += 1
            # 간이 계산 로직
            res_whkg = (c_cap * (act/100) * (c_v - 0.1)) / 2.6 
            st.session_state.sim_result = {"whkg": res_whkg, "v": c_v - 0.1, "id": f"{st.session_state.trial_count:03d}"}
            st.session_state.history.insert(0, f"#{st.session_state.sim_result['id']} | {cat_sel} | {res_whkg:.1f} Wh/kg")

    if st.session_state.history:
        st.markdown('<p class="sub-header-bold">과거 시뮬레이션 기록 선택 (최근 순)</p>', unsafe_allow_html=True)
        st.selectbox("History", st.session_state.history, label_visibility="collapsed")

    # 결과 대시보드
    if st.session_state.sim_result:
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        
        r1, r2, r3 = st.columns(3)
        with r1: st.markdown('<p class="sub-header-bold">Energy Density</p>', unsafe_allow_html=True); st.write(f"## {st.session_state.sim_result['whkg']:.1f} Wh/kg")
        with r2: st.markdown('<p class="sub-header-bold">Voltage Gap</p>', unsafe_allow_html=True); st.write(f"## {st.session_state.sim_result['v']:.2f} V")
        with r3: st.markdown('<p class="sub-header-bold">Target Achievement</p>', unsafe_allow_html=True); st.write(f"## {st.session_state.sim_result['whkg']/target_e*100:.1f} %")

        # 그래프 및 표 (30% 너비)
        st.markdown("---")
        g_c1, g_c2 = st.columns([3, 7])
        with g_c1:
            st.markdown('<p class="sub-header-bold">C-rate Retention Prediction</p>', unsafe_allow_html=True)
            x_c = np.linspace(0.1, 10, 50)
            y_r = np.exp(-0.1 * (x_c - 1)) * 100
            fig = go.Figure(go.Scatter(x=x_c, y=y_r, name="Retention", line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🔍 그래프 상세 확대 분석"):
                st.plotly_chart(fig, use_container_width=True)

        with g_c2:
            st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
            detail_df = pd.DataFrame({
                "Parameter": ["Cathode Loading", "N/P Ratio", "Cell Thickness", "Target C-rate"],
                "Value": [f"{loading} mg/cm2", f"{np}", f"{(loading/2.5)*10+30:.1f} um", f"{target_c} C"],
                "Status": ["Optimal", "Balanced", "Target Met", "Applied"]
            })
            st.table(detail_df)
    st.markdown("<br>", unsafe_allow_html=True)