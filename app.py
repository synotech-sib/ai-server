import streamlit as st
import pandas as pd
import numpy as np

# --- [시스템 설정] ---
st.set_page_config(page_title="SynoCore V1.2 | Altris Professional", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main h1 { color: #000000 !important; font-size: 1.2rem !important; border-bottom: 2px solid #1A729A; padding-bottom: 10px; }
    /* 고스트 슬라이더 스타일 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    .recommendation-box { background-color: #e3f2fd; border-left: 5px solid #1A729A; padding: 15px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- [알트리스 기반 엔진] ---
def get_altris_metrics(base_cap, v_window, c_rate, drying):
    # 전압 보정 계수 (알트리스 자료 기준)
    v_map = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.75}
    # C-rate 감쇄 (Rate Capability 지수 모델)
    c_factor = np.exp(-0.15 * (c_rate - 0.1))
    # 풀셀 효율 및 공정 품질
    eff = 0.85 * (drying / 100.0)
    
    final_cap = base_cap * v_map[v_window] * c_factor * eff
    return round(final_cap, 2)

# --- [메인 레이아웃] ---
st.title("SynoCore V1.2: 알트리스 데이터 기반 전략적 설계 가이드")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🛠️ 설계 파라미터")
    c_a, c_b = st.columns(2)
    loading = c_a.slider("Loading (mg/cm²)", 5.0, 25.0, 13.0, step=0.1)
    base_cap = c_b.slider("양극재 기본 용량 (mAh/g)", 100, 170, 160)
    
    c_c, c_d = st.columns(2)
    drying = c_c.slider("건조 품질 (Drying Quality %)", 50, 100, 100)
    np_ratio = c_d.slider("N/P Ratio", 1.0, 1.3, 1.15)

with col2:
    st.subheader("🧪 테스트 조건")
    # 전압은 선택 박스로 제안 (엔지니어 신뢰도 상승)
    v_window = st.selectbox("전압 구간 (Voltage Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])
    # C-rate는 슬라이더로 제안
    c_rate = st.slider("C-rate (방전 속도)", 0.1, 5.0, 0.5, step=0.1)
    
    # --- [AI 동적 제안 기능 추가] ---
    st.markdown("#### 🤖 AI 설계 제언")
    if c_rate >= 2.0:
        st.error("고출력 설계 감지: 로딩량을 10mg/cm² 이하로 낮추고 전극 밀도를 조정하세요.")
    elif loading >= 20.0:
        st.warning("고로딩 설계 감지: 건조 시간을 24시간 이상으로 늘리고 탈리 방지 바인더를 추가하세요.")
    else:
        st.success("균형 잡힌 설계입니다. 알트리스 표준 공정(170°C 건조)을 준수하세요.")

# --- [결과 계산 및 그래프] ---
if st.button("🚀 알트리스 성능 분석 실행", use_container_width=True):
    full_cap = get_altris_metrics(base_cap, v_window, c_rate, drying)
    whkg = (full_cap * 3.1 * 0.38 * (loading / (loading + 4.8))) * 10
    
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("예상 에너지 밀도", f"{whkg:.1f} Wh/kg", delta=f"{whkg-160:.1f} to Target")
    res2.metric("풀셀 예상 용량", f"{full_cap} mAh/g")
    res3.metric("필요 음극 로딩량", f"{(loading * full_cap * np_ratio / 280):.2f} mg/cm²")

    # C-rate 성능 곡선 그래프
    rates = [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]
    full_data = [get_altris_metrics(base_cap, v_window, r, drying) for r in rates]
    st.line_chart(pd.DataFrame({"C-rate": rates, "Full-cell Capacity": full_data}).set_index("C-rate"))