import streamlit as st
import pandas as pd
import numpy as np
import time

# [안전 장치] 모듈 임포트
try:
    from config.security_cfg import SECURITY_MODE, verify_admin_access
    from modules.engine import calculate_battery_specs
    from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
    REPORTER_READY = True
except Exception as e:
    st.error(f"⚠️ 시스템 구성 요소 로드 중 오류 발생: {e}")
    REPORTER_READY = False

# --- [1. 시스템 초기화 및 상태 관리] ---
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sidebar_state' not in st.session_state: st.session_state.sidebar_state = "expanded"
if 'history' not in st.session_state: st.session_state.history = []

st.set_page_config(
    page_title="SynoCore V1.2 | Energy11 Strategic Edition", 
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- [2. 에너지11 테마 및 UI 스타일링] ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .main h1 {{ 
        color: #000000 !important; font-weight: 700 !important; font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; padding-bottom: 5px; margin-bottom: 30px;
    }}
    h2, h3 {{ color: #1A729A !important; font-weight: 600 !important; }}
    
    /* 슬라이더 박스 제거 및 시노텍 블루 숫자 스타일 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div {{
        background-color: transparent !important; box-shadow: none !important; border: none !important;
    }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{
        color: #1A729A !important; font-weight: 800 !important; font-size: 1.1rem !important;
    }}
    
    /* 하단 최소/최대 수치 호버 효과 */
    div[data-testid="stSlider"] [data-baseweb="typography"] {{ color: black !important; opacity: 0; transition: opacity 0.3s; }}
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] {{ opacity: 1; }}

    [data-testid="stSidebar"] {{ background-color: #f1f6f9; border-right: 2px solid #1A729A; }}
    .stButton>button {{ background-color: #1A729A; color: white; border-radius: 6px; font-weight: bold; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 데이터 시트 기반 계산 보정 로직] ---
def get_adjusted_capacity(base_cap, v_window, c_rate):
    # 전압 구간별 용량 효율 (미팅자료 Page 4 참조)
    v_map = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.92, "3.8V-2.0V": 0.85}
    # C-rate별 용량 유지율 (미팅자료 Page 7 참조)
    c_retention = 1.0 if c_rate <= 0.1 else max(0.6, 1.0 - (c_rate * 0.08))
    return base_cap * v_map.get(v_window, 1.0) * c_retention

# --- [4. 사이드바: 에너지11 브랜드 로고 및 로그인] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption("Energy11 R&D Strategic Platform")
    
    st.divider()
    u_id = st.text_input("Admin ID")
    u_pw = st.text_input("Password", type="password")
    if verify_admin_access(u_id, u_pw):
        st.session_state.admin_mode = True
        st.success("✅ R&D MASTER AUTHORIZED")
    
    st.divider()
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [5. 메인 화면: 에너지11 테스트 파라미터 입력] ---
st.title("SynoCore V1.2: 전략적 SIB 설계 인텔리전스 (에너지11 전용)")
st.markdown("---")

# 입력 섹션 1: 물리적 설계
st.subheader("🛠️ 전극 물리 설계 (Electrode Design)")
in_c1, in_c2, in_c3, in_c4 = st.columns(4)
loading = in_c1.slider("Loading (mg/cm²)", 3.0, 30.0, 12.0, step=0.1, help="양극 활물질 로딩량")
density = in_c2.slider("Electrode Density (g/cc)", 1.0, 4.0, 2.5, step=0.1, help="압연 후 전극 합제 밀도")
area = in_c3.slider("Electrode Area (cm²)", 1.0, 50.0, 10.0, step=0.5)
np_ratio = in_c4.slider("N/P Ratio", 0.9, 1.5, 1.1, step=0.01)

# 입력 섹션 2: 테스트 조건 (미팅 자료 반영)
st.subheader("🧪 테스트 및 소재 변수 (Test Conditions)")
in_c5, in_c6, in_c7 = st.columns(3)
v_window = in_c5.selectbox("Voltage Window (V)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"], index=1)
c_rate = in_c6.slider("Discharge Rate (C-rate)", 0.1, 5.0, 0.2, step=0.1)
base_capacity = in_c7.number_input("Base Cap. (mAh/g)", value=140.0)

if st.button("🚀 전략적 분석 및 성능 시뮬레이션 실행"):
    try:
        # 보정된 용량 계산
        adjusted_cap = get_adjusted_capacity(base_capacity, v_window, c_rate)
        res = calculate_battery_specs(loading, adjusted_cap, area, np_ratio)
        
        # 추가 지표 계산
        thickness = (loading / 10) / density * 1000 # 전극 두께 (um)
        
        # --- 결과 출력 ---
        st.subheader("📊 설계 성능 핵심 지표 (Performance Metrics)")
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        m_c2.metric("Specific Energy", f"{res['specific_energy']} Wh/kg")
        m_c3.metric("Cathode Thick.", f"{thickness:.1f} μm")
        m_c4.metric("Anode Target", f"{res['required_anode']} mg/cm²")

        st.divider()
        
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("📈 로딩량 대비 에너지 밀도 민감도 (Sensitivity Analysis)")
            l_range = np.linspace(3, 30, 20)
            t_trend = [calculate_battery_specs(l, adjusted_cap, area, np_ratio)['specific_energy'] for l in l_range]
            st.line_chart(pd.DataFrame({'Loading': l_range, 'Wh/kg': t_trend}).set_index('Loading'))
        
        with col_right:
            st.subheader("🤖 AI Design Insight")
            score = 100
            if np_ratio < 1.05: score -= 30
            if thickness > 100: score -= 20
            st.metric("Design Stability", f"{score}/100")
            if score >= 80: st.success("✅ 양산 안정권 설계")
            else: st.warning("⚠️ 공정 개선 필요")
            st.info(f"선택 구간: {v_window}\n실효 용량: {adjusted_cap:.1f} mAh/g")

        # 히스토리 저장
        st.session_state.history.append({
            "Time": time.strftime("%H:%M:%S"), "Loading": loading, "Wh/kg": res['specific_energy'], "V_Window": v_window
        })

    except Exception as e:
        st.error(f"시뮬레이션 중 오류 발생: {e}")

# --- [6. 설계 히스토리 비교] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 비교 분석")
    st.table(pd.DataFrame(st.session_state.history).tail(5))