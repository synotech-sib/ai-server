import streamlit as st
import pandas as pd
import numpy as np
import time

# [안전 장치] 모듈 임포트
try:
    from config.security_cfg import SECURITY_MODE, verify_admin_access
    from modules.engine import calculate_battery_specs
    from modules.database import init_db, save_lead, log_action
    # 보고서 모듈 (필요시 활성화)
    REPORTER_READY = True
except Exception as e:
    st.error(f"⚠️ 시스템 구성 요소 로드 중 오류 발생: {e}")
    REPORTER_READY = False

# --- [1. 시스템 초기화 및 테마 설정] ---
st.set_page_config(page_title="SynoCore V1.2 | Energy11 R&D", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main h1 { color: #000000 !important; font-size: 1.2rem !important; border-bottom: 2px solid #1A729A; padding-bottom: 10px; }
    h3 { color: #1A729A !important; }
    /* 슬라이더 숫자 강조 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800 !important; font-size: 1.1rem !important;
    }
    .report-box { border: 1px solid #1A729A; padding: 20px; border-radius: 10px; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 핵심 분석 로직] ---
def run_strategy_analysis(loading, base_cap, drying_quality, np_ratio, target_val=160.0):
    # 건조 품질에 따른 실효 용량 보정 (Utilization 계수)
    util_factor = drying_quality / 100.0
    effective_cap = base_cap * util_factor
    
    # 에너지 밀도 산출 (SIB Full-cell 보정 계수 0.38 적용)
    avg_v = 3.1 # Prussian Blue 평균 전압
    cell_factor = 0.38
    # 로딩량에 따른 중량 효율 가중치 곡선
    weight_eff = loading / (loading + 4.8)
    whkg = (effective_cap * avg_v * cell_factor * weight_eff) * 10
    
    return round(whkg, 1), round(effective_cap, 1)

# --- [3. 사이드바 및 언어 설정] ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption("Energy11 R&D Strategic Platform")
    st.divider()
    target_whkg = st.number_input("목표 에너지 밀도 (Wh/kg)", value=160.0)
    st.divider()
    with st.expander("Admin Login"):
        u_id = st.text_input("ID")
        u_pw = st.text_input("PW", type="password")

# --- [4. 메인 설계 및 공정 변수 입력] ---
st.title("SynoCore V1.2: 공정 품질 진단 및 160Wh/kg 달성 전략 시스템")

col_in1, col_in2 = st.columns([2, 1])

with col_in1:
    st.subheader("🛠️ 전극 설계 및 공정 품질 설정")
    c1, c2 = st.columns(2)
    loading = c1.slider("양극 Loading량 (mg/cm²)", 5.0, 30.0, 15.3, step=0.1)
    np_ratio = c2.slider("N/P Ratio (Stability)", 0.9, 1.5, 1.1, step=0.01)
    
    c3, c4 = st.columns(2)
    base_cap = c3.slider("양극재 이론 용량 (mAh/g)", 100.0, 160.0, 140.0)
    drying_quality = c4.slider("건조 공정 품질 (Drying Quality %)", 50, 100, 100)

with col_input2:
    st.subheader("💡 실시간 보정 데이터")
    eff_c = base_cap * (drying_quality/100)
    st.info(f"**공정 반영 실효 용량**: {eff_c:.1f} mAh/g")
    st.info(f"**현재 설계 N/P 안정성**: {'매우 안전' if np_ratio > 1.1 else '안전'}")

# --- [5. 시뮬레이션 및 보고서 생성] ---
if st.button("🚀 성능 정밀 분석 및 전략 보고서 생성", use_container_width=True):
    whkg, eff_cap = run_strategy_analysis(loading, base_cap, drying_quality, np_ratio, target_whkg)
    
    # 5.1. 핵심 지표 출력
    st.divider()
    res_c1, res_c2, res_c3 = st.columns(3)
    diff = whkg - target_whkg
    res_c1.metric("예상 에너지 밀도", f"{whkg} Wh/kg", delta=f"{diff:+.1f} vs Target")
    res_c2.metric("보정 실효 용량", f"{eff_cap} mAh/g")
    res_c3.metric("안정성 점수", f"{drying_quality if drying_quality < 90 else 100} 점")

    # 5.2. 전문가 분석 보고서 (상관관계 및 제언)
    st.markdown("<div class='report-box'>", unsafe_allow_html=True)
    st.subheader("📋 공정 진단 및 설계 최적화 제언 리포트")
    
    rep_left, rep_right = st.columns(2)
    
    with rep_left:
        st.markdown("### 🔍 상관관계 분석 결과")
        if whkg >= target_whkg:
            st.success(f"✅ **목표 달성:** 현재 공정 품질 유지 시 {target_whkg}Wh/kg 달성이 가능합니다.")
        else:
            st.error(f"🚨 **목표 미달:** 목표치 도달을 위해 {abs(diff):.1f}Wh/kg의 추가 성능 확보가 필요합니다.")
            
        st.write(f"""
        - **공정 결함 영향**: 건조 품질 {drying_quality}% 기준, 활물질 용량이 약 {base_cap - eff_cap:.1f}mAh/g 손실되었습니다.
        - **로딩량 감도**: 로딩량을 1mg 증대할 때마다 에너지 밀도는 약 {whkg/loading:.1f}Wh/kg 증가하는 관계를 보입니다.
        - **중량 효율**: 현재 로딩({loading}mg)에서의 활물질 중량 비중은 목표 대비 개선 여지가 있습니다.
        """)

    with rep_right:
        st.markdown("### 💡 전문가 조언 (Strategy)")
        if drying_quality < 95:
            st.warning("⚠️ **공정 개선 제언**: 건조 공정 오류가 전체 에너지 밀도 하락의 주범입니다. 용량 발현율 회복이 최우선입니다.")
        
        st.markdown(f"""
        **160Wh/kg 달성을 위한 최적 경로:**
        1. **로딩 상향**: 현재 용량 수준에서 로딩량을 최소 **{loading * (target_whkg/whkg):.1f}mg/cm²**까지 높여야 함.
        2. **N/P 최적화**: {np_ratio} 수준을 유지하되, 음극 로딩 정밀 제어로 불용량을 최소화할 것.
        3. **소재 개선**: 미팅 자료의 PB-A 수준인 **147mAh/g** 이상의 초기 용량 확보가 병행되어야 함.
        """)
    st.markdown("</div>", unsafe_allow_html=True)