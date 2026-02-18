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
st.set_page_config(page_title="SynoCore V1.2 | Energy11 Cell Intelligence", layout="wide")

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

# --- [2. 정밀 추정 엔진: 전압, C-rate, 하프/풀셀 매칭] ---
def estimate_performance(base_cap, v_window, c_rate, quality, is_full_cell=True):
    # 2.1. 전압 구간 보정 (자료 Page 4 기반)
    v_factor = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.92, "3.8V-2.0V": 0.84}.get(v_window, 1.0)
    
    # 2.2. C-rate 성능 저하 모델 (자료 Page 7 기반 - 비선형 감쇄)
    # 0.1C를 100%로 기준, C-rate가 높을수록 내부 저항 증가 반영
    rate_factor = np.exp(-0.12 * (c_rate - 0.1)) if c_rate > 0.1 else 1.0
    
    # 2.3. 하프셀 vs 풀셀 변환 (ICE 및 매칭 손실 약 12% 반영)
    cell_conversion = 0.88 if is_full_cell else 1.0
    
    # 2.4. 공정 품질(건조 등) 반영
    q_factor = quality / 100.0
    
    final_cap = base_cap * v_factor * rate_factor * cell_conversion * q_factor
    return round(final_cap, 2)

# --- [3. 사이드바 및 환경 설정] ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption("Energy11 R&D Strategic Platform")
    st.divider()
    target_whkg = st.number_input("Target Energy Density (Wh/kg)", value=160.0)
    st.divider()
    with st.expander("System Auth"):
        u_id = st.text_input("ID")
        u_pw = st.text_input("PW", type="password")

# --- [4. 메인 화면: 설계 및 테스트 파라미터 입력] ---
st.title("SynoCore V1.2: 전압/C-rate 추정 및 하프-풀셀 비교 시스템")

col_in1, col_in2 = st.columns([2, 1])

with col_in1:
    st.subheader("🛠️ 설계 및 공정 파라미터")
    c1, c2 = st.columns(2)
    loading = c1.slider("양극 Loading량 (mg/cm²)", 5.0, 30.0, 15.3, step=0.1)
    np_ratio = c2.slider("N/P Ratio", 0.9, 1.5, 1.1, step=0.01)
    
    c3, c4 = st.columns(2)
    base_cap = c3.slider("하프셀 기준 용량 (mAh/g)", 100.0, 160.0, 140.0)
    drying_quality = c4.slider("건조 공정 품질 (%)", 50, 100, 100)

with col_in2:
    st.subheader("🧪 테스트 조건 설정")
    v_window = st.selectbox("전압 조건 (Voltage Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])
    c_rate_target = st.slider("평가 속도 (C-rate)", 0.1, 5.0, 0.2, step=0.1)
    st.info(f"💡 **분석 포인트**: {v_window} 구간에서 {c_rate_target}C 방전 시의 성능을 추정합니다.")

# --- [5. 시뮬레이션 및 데이터 시각화] ---
if st.button("🚀 성능 정밀 분석 및 비교 그래프 생성", use_container_width=True):
    # 5.1. 현재 조건 계산
    full_cap = estimate_performance(base_cap, v_window, c_rate_target, drying_quality, is_full_cell=True)
    half_cap = estimate_performance(base_cap, v_window, c_rate_target, drying_quality, is_full_cell=False)
    
    # 에너지 밀도 산출 (Full-cell 기준)
    avg_v = 3.1 if "4.2V" in v_window else 2.9
    whkg = (full_cap * avg_v * 0.38 * (loading / (loading + 4.8))) * 10
    
    # 5.2. 핵심 지표 출력
    st.divider()
    m1, m2, m3 = st.columns(3)
    diff = whkg - target_whkg
    m1.metric("예상 에너지 밀도", f"{whkg:.1} Wh/kg", delta=f"{diff:.1f} vs Target")
    m2.metric("풀셀 예상 용량", f"{full_cap} mAh/g")
    m3.metric("하프셀 대비 유지율", f"{(full_cap/half_cap)*100:.1f} %")

    # 5.3. 하프셀 vs 풀셀 C-rate 비교 그래프 (핵심 추가 기능)
    st.subheader("📈 C-rate별 예상 성능 비교 (Half-cell vs Full-cell)")
    
    rates = [0.1, 0.2, 0.5, 1.0, 2.0, 3.0, 5.0]
    half_data = [estimate_performance(base_cap, v_window, r, drying_quality, False) for r in rates]
    full_data = [estimate_performance(base_cap, v_window, r, drying_quality, True) for r in rates]
    
    chart_df = pd.DataFrame({
        "C-rate": rates,
        "Half-cell (Ideal)": half_data,
        "Full-cell (Actual)": full_data
    }).set_index("C-rate")
    
    st.line_chart(chart_df)
    st.caption("※ 위 그래프는 에너지11 미팅 자료의 Rate Capability 데이터를 기반으로 추정된 모델입니다.")

    # 5.4. 전략 분석 보고서
    st.markdown("<div class='report-box'>", unsafe_allow_html=True)
    st.subheader("📋 공정 진단 및 최적화 전략 리포트")
    
    rep_l, rep_r = st.columns(2)
    with rep_l:
        st.markdown("### 🔍 성능 분석 결과")
        st.write(f"- **전압 영향**: {v_window} 구간 선택으로 하프셀 대비 용량이 약 {base_cap * (1-0.92) if '4.0V' in v_window else 0:.1f}mAh/g 변동되었습니다.")
        st.write(f"- **Rate 특성**: {c_rate_target}C 방전 시, 저항 성분에 의해 용량 발현율이 약 {(full_cap/full_data[0])*100:.1f}%로 제한됩니다.")
        if whkg < target_whkg:
            st.error(f"🚨 목표 {target_whkg}Wh/kg 달성을 위해 {abs(diff):.1f}Wh/kg의 추가 확보가 필요합니다.")

    with rep_r:
        st.markdown("### 💡 전문가 제언")
        st.info(f"""
        1. **설계 변경**: 목표 에너지 달성을 위해 로딩량을 현재 {loading}mg에서 **{loading * (target_whkg/whkg):.1f}mg**으로 상향 검토하십시오.
        2. **공정 최적화**: 건조 품질이 성능 저하의 원인일 경우, 전극 내 잔류 수분이 하프/풀셀 간극을 더욱 벌릴 수 있습니다.
        3. **N/P 조절**: 고속 방전({c_rate_target}C)이 주 목적이라면 N/P Ratio를 1.15 이상으로 높여 안전 마진을 확보하십시오.
        """)
    st.markdown("</div>", unsafe_allow_html=True)