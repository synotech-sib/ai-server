import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# [안전 장치] 모듈 임포트
try:
    from config.security_cfg import SECURITY_MODE, verify_admin_access
    from modules.engine import calculate_battery_specs
    from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
    from modules.reporter import generate_expert_report
    REPORTER_READY = True
except Exception as e:
    st.error(f"⚠️ 시스템 구성 요소 로드 중 오류 발생: {e}")
    REPORTER_READY = False

# --- [1. 시스템 초기화 및 상태 관리] ---
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sidebar_state' not in st.session_state: st.session_state.sidebar_state = "expanded"
if 'history' not in st.session_state: st.session_state.history = [] # Step 11: 히스토리 저장소

st.set_page_config(
    page_title="SynoCore V1.2 | SynoTech Strategic Platform", 
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- [2. 디자인 테마 및 고도화된 슬라이더 CSS] ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    
    /* 메인 타이틀: 로고(2.2rem)보다 작은 1.1rem, 검정색 */
    .main h1 {{ 
        color: #000000 !important; font-weight: 700 !important; font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; padding-bottom: 5px; margin-bottom: 30px;
    }}
    
    h2, h3 {{ color: #1A729A !important; font-weight: 600 !important; }}
    
    /* [슬라이더 디자인 최적화] */
    /* 1. 기본 바 및 핸들 */
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div {{ background-color: #e9ecef !important; }}
    div[data-testid="stSlider"] div[role="slider"] {{ background-color: #1A729A !important; border: 2px solid #ffffff !important; }}
    div[data-testid="stSlider"] div[data-baseweb="slider"] div div {{ background-color: #1A729A !important; }}

    /* 2. 상단 현재 수치: 박스 제거 및 시노텍 블루 플로팅 텍스트 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div {{
        background-color: transparent !important;
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
        color: #1A729A !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
    }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{
        color: #1A729A !important;
    }}

    /* 3. 하단 최소/최대 수치: 평소 투명 -> 호버 시 검정색 표시 */
    div[data-testid="stSlider"] [data-baseweb="typography"] {{
        color: black !important;
        font-weight: 500 !important;
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] {{
        opacity: 1;
    }}
    
    /* 사이드바 스타일 및 메뉴 버튼 유지 */
    [data-testid="stSidebar"] {{ background-color: #f1f6f9; border-right: 2px solid #1A729A; }}
    .stSidebarCollapseButton {{ color: #1A729A !important; }}
    
    /* 버튼 스타일 */
    .stButton>button {{
        background-color: #1A729A; color: white; border-radius: 6px; border: none; font-weight: bold;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    try:
        init_db()
        log_action("System", "SynoCore V1.2.11 Integrated Master Online")
        st.session_state.initialized = True
    except: pass

# --- [3. 다국어 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence Report (PDF)",
        "chart_h": "📈 Design Sensitivity Analysis",
        "hist_h": "🔄 Design History Comparison"
    },
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 설계 인텔리전스",
        "btn_run": "🚀 전략적 분석 실행",
        "res_h": "📊 설계 성능 핵심 지표",
        "pdf_btn": "📥 전문가용 인텔리전스 리포트 다운로드 (PDF)",
        "chart_h": "📈 설계 민감도 분석",
        "hist_h": "🔄 설계 이력 비교 분석"
    }
}

# --- [4. 사이드바 로직: 로고 및 로그인] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    u_id = st.text_input("Admin ID", key="admin_id")
    u_pw = st.text_input("Password", type="password", key="admin_pw")
    
    # 관리자 로그인 시 사이드바 자동 닫힘 제어
    if verify_admin_access(u_id, u_pw):
        if not st.session_state.admin_mode:
            st.session_state.admin_mode = True
            st.session_state.sidebar_state = "collapsed"
            st.rerun()
        st.success("✅ MASTER AUTHORIZED")
    else:
        if st.session_state.admin_mode:
            st.session_state.admin_mode = False
            st.session_state.sidebar_state = "expanded"
            st.rerun()

    st.divider()
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [5. 메인 화면: 설계 입력 인터페이스] ---
st.title(T["title"])
st.markdown("---")

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    loading = c1.slider("Loading (mg/cm²)", 5.0, 35.0, 12.0, step=0.1)
    capacity = c2.slider("Cap. (mAh/g)", 100.0, 250.0, 140.0, step=1.0)
    area = c3.slider("Area (cm²)", 1.0, 50.0, 10.0, step=0.5)
    np_ratio = c4.slider("N/P Ratio", 0.8, 1.5, 1.1, step=0.01)

if st.button(T["btn_run"], type="primary", use_container_width=True):
    try:
        # 5.1. 분석 실행
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        log_action("User", f"Run: {res['specific_energy']} Wh/kg")
        
        # [Step 11] 히스토리 데이터 누적
        history_entry = {
            "Time": time.strftime("%H:%M:%S"),
            "Loading": loading,
            "N/P Ratio": np_ratio,
            "Energy Density (Wh/kg)": res['specific_energy'],
            "Areal Cap (mAh/cm²)": res['areal_capacity']
        }
        st.session_state.history.append(history_entry)
        
        # 5.2. 지표 표시
        st.subheader(T["res_h"])
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        m_c2.metric("Specific Energy", f"{res['specific_energy']} Wh/kg")
        m_c3.metric("Total Capacity", f"{res['total_capacity']} mAh")
        m_c4.metric("Anode Target", f"{res['required_anode']} mg/cm²")

        st.divider()

        # 5.3. 시각화 및 인사이트
        col_chart, col_ai = st.columns([2, 1])
        with col_chart:
            st.subheader(T["chart_h"])
            load_range = np.linspace(5, 35, 20)
            trend = [calculate_battery_specs(l, capacity, area, np_ratio)['specific_energy'] for l in load_range]
            st.line_chart(pd.DataFrame({'Loading': load_range, 'Wh/kg': trend}).set_index('Loading'))

        with col_ai:
            st.subheader("🤖 AI Stability")
            score = 100
            if np_ratio < 1.05: score -= 30
            if loading > 22: score -= 20
            st.metric("Stability Score", f"{score}/100")
            if score >= 80: st.success("✅ 설계가 안정적입니다.")
            else: st.warning("⚠️ 보완이 권장됩니다.")

    except Exception as e:
        st.error(f"분석 오류: {e}")

# --- [6. Step 11: 설계 히스토리 비교 분석 (자동 확장 테이블)] ---
if st.session_state.history:
    st.divider()
    st.subheader(T["hist_h"])
    hist_df = pd.DataFrame(st.session_state.history)
    
    # 히스토리 테이블 표시
    st.dataframe(hist_df.iloc[::-1], use_container_width=True) # 최신 설계가 위로 오도록 역순 표시
    
    # 히스토리 추이 그래프
    if len(hist_df) > 1:
        st.caption("설계 시뮬레이션 간 에너지 밀도 변화 추이 (History Log)")
        st.line_chart(hist_df.set_index("Time")["Energy Density (Wh/kg)"])
    
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()

# --- [7. 관리자 대시보드 및 전문가 기능] ---
if st.session_state.admin_mode:
    st.markdown("---")
    st.header(f"🛡️ Intelligence Dashboard")
    tab1, tab2 = st.tabs(["📈 Lead Analytics", "📜 Audit Logs"])
    with tab1:
        leads = get_leads()
        if not leads.empty: st.bar_chart(leads['company'].value_counts())
    with tab2:
        st.dataframe(get_audit_logs(), use_container_width=True)