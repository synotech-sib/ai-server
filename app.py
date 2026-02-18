import streamlit as st
import pandas as pd
import numpy as np
import time

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
if 'history' not in st.session_state: st.session_state.history = []

st.set_page_config(
    page_title="SynoCore V1.2 | Energy11 Intelligence", 
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- [2. 디자인 및 슬라이더 스타일링 (고스트 넘버)] ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main h1 { 
        color: #000000 !important; font-weight: 700 !important; font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; padding-bottom: 5px; margin-bottom: 30px;
    }
    h2, h3 { color: #1A729A !important; font-weight: 600 !important; }
    
    /* 슬라이더 숫자 스타일 최적화 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div {
        background-color: transparent !important; box-shadow: none !important; border: none !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800 !important; font-size: 1.1rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="typography"] { color: black !important; opacity: 0; transition: opacity 0.3s; }
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] { opacity: 1; }

    [data-testid="stSidebar"] { background-color: #f1f6f9; border-right: 2px solid #1A729A; }
    .stButton>button { background-color: #1A729A; color: white; border-radius: 6px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 보정 및 상관관계 분석 엔진] ---
def analyze_design_strategy(loading, base_cap, drying_quality, target=160.0):
    # 건조 품질에 따른 실효 용량 저하 반영
    utilization = drying_quality / 100.0
    effective_cap = base_cap * utilization
    
    # 에너지 밀도 추정 (SIB 전용 보정 계수 포함)
    avg_v = 3.1 # Prussian Blue 평균 전압
    cell_overhead_factor = 0.38 # 셀 중량 내 활물질 비중 효율
    energy_density = (effective_cap * avg_v * cell_overhead_factor) * (loading / (loading + 4.5)) * 10
    
    return round(energy_density, 1), round(effective_cap, 1)

# --- [4. 사이드바 및 로그인 로직] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption("Energy11 R&D Strategic Platform")
    
    st.divider()
    selected_lang = st.selectbox("🌐 Language", ["한국어", "English"])
    u_id = st.text_input("Admin ID")
    u_pw = st.text_input("Password", type="password")
    if verify_admin_access(u_id, u_pw):
        st.session_state.admin_mode = True
        st.success("✅ R&D MASTER AUTHORIZED")
    
    st.divider()
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")

# --- [5. 메인 화면: 공정/설계 변수 입력] ---
st.title("SynoCore V1.2: 공정 최적화 및 목표(160Wh/kg) 분석 시스템")
st.markdown("---")

col_input1, col_input2 = st.columns([2, 1])

with col_input1:
    st.subheader("🛠️ 전극 및 공정 파라미터 설정")
    c1, c2 = st.columns(2)
    loading = c1.slider("양극 Loading량 (mg/cm²)", 5.0, 30.0, 15.0, step=0.1)
    np_ratio = c2.slider("N/P Ratio (Stability)", 0.9, 1.5, 1.1, step=0.01)
    
    c3, c4 = st.columns(2)
    base_cap = c3.slider("활물질 이론 용량 (mAh/g)", 100, 160, 140)
    drying_quality = c4.slider("건조 공정 품질 (Drying Quality %)", 50, 100, 100, help="건조 오류 시 수치를 낮추세요")

with col_input2:
    st.subheader("🎯 Target Specs")
    target_whkg = st.number_input("목표 에너지 밀도 (Wh/kg)", value=160.0)
    st.info(f"건조 오류 반영 시 예상 실효 용량: **{base_cap * (drying_quality/100):.1;1} mAh/g**")

if st.button("🚀 성능 분석 및 전략 리포트 생성", use_container_width=True):
    whkg, eff_cap = analyze_design_strategy(loading, base_cap, drying_quality, target_whkg)
    
    # 결과 요약
    st.divider()
    res_c1, res_c2, res_c3 = st.columns(3)
    diff = whkg - target_whkg
    res_c1.metric("예상 에너지 밀도", f"{whkg} Wh/kg", delta=f"{diff:.1f} vs Target")
    res_c2.metric("실효 용량", f"{eff_cap} mAh/g")
    res_c3.metric("안정성 점수", f"{100 if drying_quality > 90 else 100 - (100-drying_quality)} 점")

    # --- [상관관계 및 제안 보고서 섹션] ---
    st.subheader("📋 설계 전략 및 상관관계 분석 보고서")
    rep_l, rep_r = st.columns(2)
    
    with rep_l:
        st.markdown(f"### 🔍 분석 결과 요약")
        if whkg >= target_whkg:
            st.success(f"🎉 **목표 달성 가능:** 현재 설계로 {target_whkg}Wh/kg 달성이 가능합니다.")
        else:
            st.error(f"🚨 **목표 미달:** 현재 설계로는 목표치에 {abs(diff):.1f}Wh/kg 부족합니다.")
        
        st.markdown(f"""
        **핵심 파라미터 상관관계 가이드:**
        1. **로딩량 vs 에너지:** 목표치 도달을 위해 로딩량을 {loading * 1.2:.1f}mg 이상으로 상향 검토가 필요합니다.
        2. **건조 품질 영향:** 건조 품질이 10% 하락할 때마다 전체 에너지 밀도는 약 {whkg * 0.1:.1f}Wh/kg씩 선형적으로 감소합니다.
        3. **N/P Ratio 최적화:** 현재 {np_ratio}에서 1.05 수준으로 타이트하게 가져갈 시 중량 절감이 가능합니다.
        """)

    with rep_r:
        st.markdown("### 💡 전문가 제언 (Recommendations)")
        if drying_quality < 95:
            st.warning("⚠️ **공정 긴급 진단:** 현재 건조 공정 오류가 실효 용량 저하의 주원인입니다. 온도 프로파일 재검토가 시급합니다.")
        
        st.info(f"""
        **160Wh/kg 달성을 위한 최적화 경로:**
        - 활물질 용량 **{base_cap}mAh/g** 유지 시, 로딩량을 최소 **18.5mg/cm²**까지 증대해야 함.
        - 건조 품질을 **98% 이상**으로 회복시켜 용량 발현율을 극대화할 것.
        - 고로딩 시 전극 탈리 방지를 위한 바인더 조성 최적화 병행 필요.
        """)

    # 히스토리 저장
    st.session_state.history.append({"Time": time.strftime("%H:%M:%S"), "Loading": loading, "Wh/kg": whkg, "Quality": drying_quality})

# --- [6. 설계 히스토리 비교] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 및 공정 변화 추이")
    st.dataframe(pd.DataFrame(st.session_state.history).tail(5), use_container_width=True)