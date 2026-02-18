import streamlit as st
import pandas as pd
import numpy as np
import time

# [안전 장치] 모듈 임포트
try:
    from config.security_cfg import SECURITY_MODE, verify_admin_access
    from modules.engine import calculate_battery_specs
    from modules.database import init_db, save_lead, log_action
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
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800 !important; font-size: 1.1rem !important;
    }
    .report-box { border: 1px solid #1A729A; padding: 20px; border-radius: 10px; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 핵심 분석 로직] ---
def run_strategy_analysis(loading, base_cap, drying_quality, np_ratio, target_val=160.0):
    util_factor = drying_quality / 100.0
    effective_cap = base_cap * util_factor
    avg_v = 3.1 
    cell_factor = 0.38
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
    u_id = st.text_input("ID")
    u_pw = st.text_input("PW", type="password")

# --- [4. 메인 설계 및 공정 변수 입력] ---
st.title("SynoCore V1.2: 공정 품질 진단 및 160Wh/kg 달성 전략 시스템")

# [수정] col_input2 정의 오류 방지를 위해 명확히 선언
col_input1, col_input2 = st.columns([2, 1])

with col_input1:
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
    # [수정] image_76578c의 f-string 포맷팅 오류 교정
    st.info(f"**공정 반영 실효 용량**: {eff_c:.1f} mAh/g")
    st.info(f"**현재 설계 N/P 안정성**: {'매우 안전' if np_ratio > 1.1 else '안전'}")

# --- [5. 시뮬레이션 및 보고서 생성] ---
if st.button("🚀 성능 정밀 분석 및 전략 보고서 생성", use_container_width=True):
    whkg, eff_cap = run_strategy_analysis(loading, base_cap, drying_quality, np_ratio, target_whkg)
    
    st.divider()
    res_c1, res_c2, res_c3 = st.columns(3)
    diff = whkg - target_whkg
    res_c1.metric("예상 에너지 밀도", f"{whkg} Wh/kg", delta=f"{diff:+.1f} vs Target")
    res_c2.metric("보정 실효 용량", f"{eff_cap} mAh/g")
    res_c3.metric("공정 점수", f"{drying_quality} 점")

    st.markdown("<div class='report-box'>", unsafe_allow_html=True)
    st.subheader("📋 공정 진단 및 설계 최적화 제언 리포트")
    
    rep_left, rep_right = st.columns(2)
    with rep_left:
        st.markdown("### 🔍 상관관계 분석 결과")
        if whkg >= target_whkg:
            st.success(f"✅ **목표 달성:** {target_whkg}Wh/kg 달성이 가능합니다.")
        else:
            st.error(f"🚨 **목표 미달:** {abs(diff):.1f}Wh/kg의 추가 성능 확보가 필요합니다.")
            
        st.write(f"- 건조 품질 {drying_quality}% 기준, 용량 약 {base_cap - eff_cap:.1f}mAh/g 손실.")

    with rep_right:
        st.markdown("### 💡 전문가 조언 (Strategy)")
        if drying_quality < 95:
            st.warning("⚠️ 건조 공정 오류가 주요 하락 원인입니다.")
        st.markdown(f"- 160Wh/kg 달성 위해 로딩량을 약 **{loading * (target_whkg/whkg):.1f}mg**까지 상향 권장.")
    st.markdown("</div>", unsafe_allow_html=True)