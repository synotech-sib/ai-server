import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 커스텀 CSS (디자인 디테일 반영)
st.markdown("""
    <style>
    /* 메뉴 및 헤더 가림 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 상단 로고 스타일 */
    .logo-container { display: flex; align-items: baseline; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #555; font-size: 22px; font-weight: normal; }

    /* 섹션 박스 스타일 (1~5번 구분) */
    .section-box {
        background-color: #f2f2f2;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 25px;
    }

    /* 제목 스타일 (1-5번 및 결과 타이틀) */
    .main-header {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #333;
        margin-bottom: 15px;
    }

    /* 결과창 하단 텍스트 (하나 작게 + 볼드) */
    .result-sub-header {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #444;
    }

    /* 버튼 스타일 */
    div.stButton > button:first-child {
        background-color: #003366; color: white; border-radius: 5px; height: 3.5em; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 및 세션 초기화
@st.cache_data
def load_data():
    # 실제 환경에서는 파일이 있어야 합니다. 여기서는 구조만 유지합니다.
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("param_config.xlsx")
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except:
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_data()

if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0

# -----------------------------------------------------------------------------
# [상단] 헤더 50:50 배치
# -----------------------------------------------------------------------------
header_l, header_r = st.columns([1, 1])

with header_l:
    st.markdown(f"""
        <div class="logo-container">
            <span class="syno-title">SynoCore</span>
            <span class="syno-subtitle">V1.4 Pro</span>
        </div>
    """, unsafe_allow_html=True)

with header_r:
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([2, 2, 1])
        u_id = c1.text_input("ID", placeholder="Email", label_visibility="collapsed")
        u_pw = c2.text_input("PW", type="password", placeholder="Password", label_visibility="collapsed")
        if c3.button("Login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
        
        # 계정생성 및 무료시도 정보
        st.markdown('<div style="text-align:right; font-size:12px; color:gray;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:5px; text-align:center; font-size:14px;">무료 시도 {st.session_state.trial_count}/3</div>', unsafe_allow_html=True)
    else:
        st.write(f"✅ **최우성 관리자님** 접속 중")
        if st.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 메인 섹션 (1~5번 박스 처리)
# -----------------------------------------------------------------------------

# 1번 섹션
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
with m1: cat = st.selectbox("Cathode", ["Prussian White", "Layered Oxide", "Polyanion"])
with m2: ano = st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
with m3: elec = st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
with m4: sep = st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
st.markdown('</div>', unsafe_allow_html=True)

# 2번 섹션
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
s1, s2, s3, s4 = st.columns(4)
if expert_spec:
    c_cap = s1.slider("Capacity", 100, 200, 160)
    c_vol = s2.slider("Voltage", 2.0, 4.5, 3.05)
    c_den = s3.slider("Density", 1.5, 4.0, 2.2)
    c_lif = s4.slider("Life", 500, 5000, 3000)
else:
    s1.markdown("**Capacity** \n### 160 mAh/g")
    s2.markdown("**Voltage** \n### 3.05 V")
    s3.markdown("**Density** \n### 2.2 g/cc")
    s4.markdown("**Life** \n### 3000 Cyc")
st.markdown('</div>', unsafe_allow_html=True)

# 3번 섹션
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
p1, p2, p3 = st.columns(3)
with p1: 
    st.markdown('<p class="result-sub-header">(A) Cathode Settings</p>', unsafe_allow_html=True)
    loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, 14.0)
with p2:
    st.markdown('<p class="result-sub-header">(B) Anode Settings</p>', unsafe_allow_html=True)
    np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
with p3:
    st.markdown('<p class="result-sub-header">(C) Electrolyte Settings</p>', unsafe_allow_html=True)
    active = st.slider("Active Ratio (%)", 85.0, 98.0, 92.0)
st.markdown('</div>', unsafe_allow_html=True)

# 4번 섹션
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
t1, t2 = st.columns(2)
with t1: 
    st.markdown('<p class="result-sub-header">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
    t_en = st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
with t2:
    st.markdown('<p class="result-sub-header">Target C-rate (C)</p>', unsafe_allow_html=True)
    t_cr = st.slider("C-rate Goal", 0.1, 10.0, 1.0, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5번 섹션 및 실행
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
if st.button("🚀 RUN DESIGN SIMULATION"):
    st.session_state.trial_count += 1
    st.session_state.result_ready = True
    st.success("Simulation Complete!")

if st.session_state.get('result_ready'):
    st.markdown("---")
    st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
    
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1: st.markdown('<p class="result-sub-header">Energy Density</p>', unsafe_allow_html=True); st.write("## 158.4 Wh/kg")
    with res_c2: st.markdown('<p class="result-sub-header">Cell Voltage</p>', unsafe_allow_html=True); st.write("## 2.95 V")
    with res_c3: st.markdown('<p class="result-sub-header">Expected Life</p>', unsafe_allow_html=True); st.write("## 2850 Cycles")

    # 그래프 레이아웃 (30% 너비 및 확대 기능)
    st.markdown("---")
    g_col1, g_col2 = st.columns([3, 7]) # 왼쪽 30% 영역 사용
    
    with g_col1:
        st.markdown('<p class="result-sub-header">Discharge Profile</p>', unsafe_allow_html=True)
        # 간단한 샘플 데이터
        x = np.linspace(0, 100, 100)
        y = 3.05 - (x/100)**2
        fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        # 확대 버튼 (Expander 활용)
        with st.expander("🔍 그래프 크게 보기"):
            fig_large = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=4)))
            fig_large.update_layout(title="Detailed Discharge Analysis", height=600)
            st.plotly_chart(fig_large, use_container_width=True)

    with g_col2:
        st.markdown('<p class="result-sub-header">Detailed Design Parameters</p>', unsafe_allow_html=True)
        detail_table = pd.DataFrame({
            "Parameters": ["Cathode Weight", "Anode Weight", "Electrolyte Vol.", "N/P Ratio"],
            "Values": ["14.2 g", "12.8 g", "3.5 ml", "1.15"],
            "Units": ["g", "g", "ml", "Ratio"]
        })
        st.table(detail_table)
st.markdown('</div>', unsafe_allow_html=True)