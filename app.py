import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 2. 고도화된 커스텀 CSS (박스 완전 수납 및 무료 시도 강조)
st.markdown("""
    <style>
    /* 메뉴 및 헤더 가림 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 상단 로고 스타일: SynoCore와 V1.4 Pro 한 줄 배치 */
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 22px; font-weight: normal; padding-top: 8px; }

    /* 로그인 버튼 높이 조절 (입력창과 완벽 일치) */
    div[data-testid="stButton"] > button {
        height: 42px !important;
        background-color: #003366 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        width: 100%;
        border: none !important;
    }

    /* 무료 시도 강조 박스 (큰 글씨) */
    .trial-highlight {
        background-color: #003366;
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* 1-5번 전체 수납 박스 스타일 */
    .section-wrapper {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #dee2e6;
        margin-bottom: 30px;
    }

    /* 제목 스타일 (26px 볼드) */
    .main-header {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #003366;
        margin-bottom: 20px;
        border-left: 5px solid #003366;
        padding-left: 15px;
    }

    /* 결과/소제목 스타일 (20px 볼드) */
    .sub-header-bold {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #333;
        margin-bottom: 10px;
    }

    /* 텍스트 가독성 강화 */
    .stMarkdown p { font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 로드
@st.cache_data
def load_data():
    try:
        return pd.read_excel("material_list.xlsx")
    except:
        return pd.DataFrame()

mat_df = load_data()

# -----------------------------------------------------------------------------
# [상단] 헤더 (50:50 배치)
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
    # 로그인 입력 및 버튼 (높이 일치)
    log_c1, log_c2, log_c3 = st.columns([2, 2, 1])
    with log_c1:
        u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
    with log_c2:
        u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
    with log_c3:
        st.button("Login")
    
    # 계정 생성 링크 및 무료 시도 강조
    st.markdown('<div style="text-align:right; font-size:14px; color:#003366; font-weight:bold; margin-bottom:5px;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
    st.markdown('<div class="trial-highlight">💡 무료 시도 가능 횟수: 3 / 3</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [본문] 1~5번 섹션 (박스 내부에 제목+내용 완전 수납)
# -----------------------------------------------------------------------------

# 1. Material Selection
st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
with m1: st.selectbox("Cathode (양극)", ["Prussian White", "Layered Oxide", "Polyanion"])
with m2: st.selectbox("Anode (음극)", ["Aekyung Chemical", "Kuraray HC"])
with m3: st.selectbox("Electrolyte (전해액)", ["Standard NaPF6", "High-Stability"])
with m4: st.selectbox("Separator (분리막)", ["PE 16um", "Ceramic Coated"])
st.markdown('</div>', unsafe_allow_html=True)

# 2. Material Specs
st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
expert_spec = st.checkbox("🔓 물성 직접 수정 활성화 (연구원 전용)")
s1, s2, s3, s4 = st.columns(4)
if expert_spec:
    s1.slider("Capacity (mAh/g)", 100, 250, 162)
    s2.slider("Voltage (V)", 2.5, 4.5, 3.05)
    s3.slider("Density (g/cc)", 1.5, 4.0, 2.2)
    s4.slider("Life (Cycles)", 500, 10000, 4000)
else:
    s1.markdown('<p class="sub-header-bold">Capacity</p>162 mAh/g', unsafe_allow_html=True)
    s2.markdown('<p class="sub-header-bold">Voltage</p>3.05 V', unsafe_allow_html=True)
    s3.markdown('<p class="sub-header-bold">Density</p>2.2 g/cc', unsafe_allow_html=True)
    s4.markdown('<p class="sub-header-bold">Base Life</p>4000 Cycles', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)



# 3. Process Parameters
st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
p1, p2, p3 = st.columns(3)
with p1: 
    st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
    st.slider("Loading Level (mg/cm2)", 5.0, 40.0, 14.0)
with p2:
    st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
    st.slider("N/P Ratio (용량 밸런스)", 1.0, 1.5, 1.15)
with p3:
    st.markdown('<p class="sub-header-bold">(C) Electrolyte Change</p>', unsafe_allow_html=True)
    st.slider("Active Ratio (%)", 85.0, 99.0, 92.0)
st.markdown('</div>', unsafe_allow_html=True)

# 4. Target Design Goals
st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
st.markdown('<p class="main-header">4. Target Design Goals</p>', unsafe_allow_html=True)
t1, t2 = st.columns(2)
with t1: 
    st.markdown('<p class="sub-header-bold">Target Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
    st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
with t2:
    st.markdown('<p class="sub-header-bold">Target C-rate (출력 조건)</p>', unsafe_allow_html=True)
    st.slider("C-rate Goal", 0.1, 20.0, 1.0, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. Simulation Execution
st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
if st.button("🚀 RUN DESIGN SIMULATION"):
    st.session_state.show_results = True

if st.session_state.get('show_results'):
    st.markdown("---")
    st.markdown('<p class="main-header">Engineering Analysis Result</p>', unsafe_allow_html=True)
    
    # 결과 요약 (20px 볼드 적용)
    r1, r2, r3 = st.columns(3)
    with r1: 
        st.markdown('<p class="sub-header-bold">Energy Density</p>', unsafe_allow_html=True)
        st.write("## 158.4 Wh/kg")
    with r2: 
        st.markdown('<p class="sub-header-bold">Cell Voltage</p>', unsafe_allow_html=True)
        st.write("## 2.95 V")
    with r3: 
        st.markdown('<p class="sub-header-bold">Estimated Life</p>', unsafe_allow_html=True)
        st.write("## 3,120 Cycles")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 그래프 및 표 레이아웃 (30% 너비 적용)
    g_col1, g_col2 = st.columns([3, 7])
    with g_col1:
        st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
        x = np.linspace(0, 100, 100)
        y = 3.05 - (x/100)**2
        fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("🔍 그래프 상세 확대 분석"):
            st.plotly_chart(fig, use_container_width=True)

    with g_col2:
        st.markdown('<p class="sub-header-bold">Detailed Design Parameters</p>', unsafe_allow_html=True)
        detail_data = pd.DataFrame({
            "Parameters": ["Cathode Loading", "Anode Loading", "Electrolyte Weight", "N/P Ratio", "Cell Thickness"],
            "Values": ["14.0 mg/cm²", "12.5 mg/cm²", "3.2 g/Ah", "1.15", "185 μm"],
            "Status": ["Optimal", "Balanced", "Standard", "Safety", "Target Met"]
        })
        st.table(detail_data)

st.markdown('</div>', unsafe_allow_html=True)