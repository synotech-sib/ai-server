import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 고도화된 커스텀 CSS (로그인 높이 정밀 조정 및 섹션 박스화)
st.markdown("""
    <style>
    /* 메뉴 및 헤더 가림 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 상단 로고 스타일: SynoCore와 V1.4 Pro를 한 줄에 */
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 10px; }

    /* 로그인 버튼 높이 조절 (입력창 42px와 동기화) */
    div[data-testid="stButton"] > button {
        height: 42px !important;
        margin-top: 0px !important;
        background-color: #003366 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        border: none !important;
        width: 100%;
    }

    /* 1-5번 섹션 박스 스타일: 내용 전체를 포함 */
    .section-container {
        background-color: #f7f7f7;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }

    /* 제목 스타일 (26px 볼드) */
    .main-header {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #333;
        margin-bottom: 15px;
        display: block;
    }

    /* 결과창 하단 텍스트 (하나 작게: 20px 볼드) */
    .result-sub-header {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #444;
        margin-top: 10px;
    }
    
    /* 입력창 레이블 간격 조정 */
    .stTextInput > label, .stSelectbox > label, .stSlider > label {
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 로드 (파일 체크)
@st.cache_data
def load_data():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        return mat_df
    except:
        return pd.DataFrame()

mat_df = load_data()

# -----------------------------------------------------------------------------
# [상단] 헤더 (좌우 50:50 배치)
# -----------------------------------------------------------------------------
head_l, head_r = st.columns([1, 1])

with head_l:
    st.markdown(f"""
        <div class="header-container">
            <span class="syno-title">SynoCore</span>
            <span class="syno-subtitle">V1.4 Pro</span>
        </div>
    """, unsafe_allow_html=True)

with head_r:
    # 로그인 폼 구성 (높이 정렬을 위해 padding 제거)
    login_col1, login_col2, login_col3 = st.columns([2, 2, 1])
    with login_col1:
        u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
    with login_col2:
        u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
    with login_col3:
        if st.button("Login"):
            # 관리자 계정 예시
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
    
    # 계정 생성 및 무료 시도 정보 (로그인 박스 바로 아래)
    link_col1, link_col2 = st.columns([1, 1])
    with link_col1:
        st.markdown('<div style="font-size:12px; color:#003366; font-weight:bold; cursor:pointer;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
    with link_col2:
        st.markdown('<div style="text-align:right; font-size:12px; color:gray;">무료 시도 0/3</div>', unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# [본문] 1~5번 섹션 (박스 내부에 내용 포함)
# -----------------------------------------------------------------------------

# 1. Material Selection
with st.container():
    st.markdown('<div class="section-container"><p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.selectbox("Cathode", ["Prussian White", "Layered Oxide", "Polyanion"])
    with m2: st.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    with m3: st.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    with m4: st.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown('</div>', unsafe_allow_html=True)

# 2. Material Specs Expert Mode
with st.container():
    st.markdown('<div class="section-container"><p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        s1.slider("Capacity (mAh/g)", 100, 200, 160)
        s2.slider("Voltage (V)", 2.0, 4.5, 3.05)
        s3.slider("Density (g/cc)", 1.5, 4.0, 2.2)
        s4.slider("Life (Cycles)", 500, 5000, 3000)
    else:
        s1.markdown('<p class="result-sub-header">Capacity</p><b>162 mAh/g</b>', unsafe_allow_html=True)
        s2.markdown('<p class="result-sub-header">Voltage</p><b>3.05 V</b>', unsafe_allow_html=True)
        s3.markdown('<p class="result-sub-header">Density</p><b>2.2 g/cc</b>', unsafe_allow_html=True)
        s4.markdown('<p class="result-sub-header">Life</p><b>4000 Cyc</b>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 3. Process Parameters
with st.container():
    st.markdown('<div class="section-container"><p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1: 
        st.markdown('<p class="result-sub-header">(A) Cathode Settings</p>', unsafe_allow_html=True)
        st.slider("Loading (mg/cm2)", 5.0, 40.0, 14.0)
    with p2:
        st.markdown('<p class="result-sub-header">(B) Anode Settings</p>', unsafe_allow_html=True)
        st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p3:
        st.markdown('<p class="result-sub-header">(C) Electrolyte Settings</p>', unsafe_allow_html=True)
        st.slider("Active Ratio (%)", 85.0, 98.0, 92.0)
    st.markdown('</div>', unsafe_allow_html=True)

# 4. Target Configuration
with st.container():
    st.markdown('<div class="section-container"><p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: 
        st.markdown('<p class="result-sub-header">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
        st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<p class="result-sub-header">Target C-rate (C)</p>', unsafe_allow_html=True)
        st.slider("C-rate Goal", 0.1, 10.0, 1.0, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# 5. Simulation History & Run
with st.container():
    st.markdown('<div class="section-container"><p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        st.session_state.sim_run = True
    
    if st.session_state.get('sim_run'):
        st.markdown("---")
        st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
        
        # 결과 대시보드
        res_c1, res_c2, res_c3 = st.columns(3)
        with res_c1: 
            st.markdown('<p class="result-sub-header">Energy Density</p>', unsafe_allow_html=True)
            st.write("## 158.4 Wh/kg")
        with res_c2: 
            st.markdown('<p class="result-sub-header">Cell Voltage</p>', unsafe_allow_html=True)
            st.write("## 2.95 V")
        with res_c3: 
            st.markdown('<p class="result-sub-header">Expected Life</p>', unsafe_allow_html=True)
            st.write("## 2,850 Cycles")

        st.markdown("---")
        # 그래프 30% 배치 및 확대 기능
        g_col1, g_col2 = st.columns([3, 7])
        with g_col1:
            st.markdown('<p class="result-sub-header">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100)
            y = 3.05 - (x/100)**2
            fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("🔍 그래프 크게 보기"):
                st.plotly_chart(fig, use_container_width=True) # 확대 시 container 너비에 맞게 출력

        with g_col2:
            st.markdown('<p class="result-sub-header">Detailed Design Parameters</p>', unsafe_allow_html=True)
            # 엔지니어용 상세 테이블
            detail_table = pd.DataFrame({
                "Parameters": ["Cathode Loading", "Anode Loading", "Electrolyte Vol.", "Separator Thick.", "N/P Ratio"],
                "Values": ["14.2", "12.8", "3.5", "16.0", "1.15"],
                "Units": ["mg/cm2", "mg/cm2", "ml/Ah", "μm", "Ratio"]
            })
            st.table(detail_table)
    st.markdown('</div>', unsafe_allow_html=True)