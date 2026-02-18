import streamlit as st
import pandas as pd
import numpy as np
import time

# --- [1. 시스템 초기화 및 다국어 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

LANG_DICT = {
    "한국어": {
        "title": "SynoCore V1.2: 에너지11 x 알트리스 전략 플랫폼",
        "sidebar_title": "시노코어 V1.2",
        "input_section1": "🏭 에너지11: 공정 및 설계 변수",
        "input_section2": "🧪 알트리스: 소재 및 테스트 변수",
        "btn_run": "🚀 정밀 시뮬레이션 및 전략 보고서 생성",
        "report_title": "SIB 설계 및 성능 검증 보고서",
        "kpi_energy": "예상 에너지 밀도",
        "kpi_cap": "풀셀 실효 용량",
        "kpi_anode": "목표 음극 로딩량",
        "hist_title": "🔄 설계 이력 및 비교 분석 (Step 11)",
        "target_label": "목표 에너지 밀도",
        "guide_title": "💡 전문가 전략 제언"
    },
    "English": {
        "title": "SynoCore V1.2: Energy11 x Altris Strategic Platform",
        "sidebar_title": "SynoCore V1.2",
        "input_section1": "🏭 Energy11: Process & Design",
        "input_section2": "🧪 Altris: Material & Test",
        "btn_run": "🚀 Run Simulation & Generate Report",
        "report_title": "SIB DESIGN & PERFORMANCE REPORT",
        "kpi_energy": "Est. Energy Density",
        "kpi_cap": "Full-cell Eff. Capacity",
        "kpi_anode": "Anode Loading Target",
        "hist_title": "🔄 Design History & Comparison (Step 11)",
        "target_label": "Target Energy Density",
        "guide_title": "💡 Expert Strategic Strategy"
    }
}

st.set_page_config(page_title="SynoCore V1.2 | Master Edition", layout="wide")

# --- [2. 고도화된 디자인 테마 (고스트 슬라이더 포함)] ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* 보고서 컨테이너 */
    .report-container { border: 2px solid #1A729A; padding: 35px; border-radius: 15px; background-color: #ffffff; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .report-header { border-bottom: 3px double #1A729A; padding-bottom: 15px; margin-bottom: 25px; text-align: center; }
    
    /* KPI 카드 */
    .kpi-card { background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }
    .kpi-val { font-size: 1.6rem; font-weight: bold; color: #1A729A; }
    
    /* 슬라이더 고스트 스타일 (박스 제거, 블루 숫자) */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="typography"] { color: black !important; opacity: 0; transition: opacity 0.3s; }
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 알트리스 x 에너지11 통합 엔진] ---
def run_master_simulation(loading, base_cap, drying, v_window, c_rate, np_ratio):
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    rate_factor = np.exp(-0.22 * (c_rate - 0.1)) if c_rate > 0.1 else 1.0
    process_eff = (drying / 100.0) * 0.85 
    effective_cap = base_cap * v_eff * rate_factor * process_eff
    whkg = (effective_cap * 3.1 * 0.38 * (loading / (loading + 4.9))) * 10
    anode_target = (loading * effective_cap * np_ratio) / 295 
    
    return {
        "whkg": round(whkg, 1),
        "eff_cap": round(effective_cap, 1),
        "anode_mass": round(anode_target, 3),
        "loss_summary": {"V": round((1-v_eff)*100, 1), "C": round((1-rate_factor)*100, 1), "P": round((1-process_eff/0.85)*100, 1)}
    }

# --- [4. 사이드바: 로고, 언어, 관리자 모드] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem;'>SynoCore</h1>", unsafe_allow_html=True)
    
    # 언어 선택 기능 복구
    sel_lang = st.selectbox("🌐 Language", ["한국어", "English"])
    T = LANG_DICT[sel_lang]
    
    st.divider()
    target_whkg = st.number_input(T["target_label"], value=160.0)
    
    st.divider()
    # 관리자 로그인 기능 유지
    with st.expander("Admin Access"):
        u_id = st.text_input("ID")
        u_pw = st.text_input("PW", type="password")
        if u_id == "admin" and u_pw == "syno123": # 예시 계정
            st.session_state.admin_mode = True
            st.success("Authorized")
    
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [5. 메인 UI 및 입력] ---
st.title(T["title"])
st.markdown("---")

col_in1, col_in2 = st.columns([1, 1])

with col_in1:
    st.subheader(T["input_section1"])
    loading = st.slider("Cathode Loading (mg/cm²)", 5.0, 30.0, 13.0, step=0.1)
    np_ratio = st.slider("N/P Ratio", 1.0, 1.4, 1.15, step=0.01)
    drying = st.slider("Drying Quality (%)", 50, 100, 100)

with col_in2:
    st.subheader(T["input_section2"])
    base_cap = st.slider("Base Capacity (mAh/g)", 100, 175, 162)
    v_window = st.selectbox("Voltage Window", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])
    c_rate = st.slider("C-rate", 0.1, 5.0, 0.33, step=0.1)

# --- [6. 시뮬레이션 및 결과 리포트] ---
if st.button(T["btn_run"], use_container_width=True):
    res = run_master_simulation(loading, base_cap, drying, v_window, c_rate, np_ratio)
    
    # 히스토리 누적 (Step 11 기능 복구)
    st.session_state.history.append({
        "Time": time.strftime("%H:%M:%S"), "Wh/kg": res['whkg'], "Loading": loading, "V_Window": v_window
    })

    # 전문 보고서 생성
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header"><h2 style="color:#1A729A;">{T["report_title"]}</h2></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    diff = res['whkg'] - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    k1.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:{color}">{res["whkg"]} Wh/kg</div><div>{T["kpi_energy"]}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi-card"><div class="kpi-val">{res["eff_cap"]} mAh/g</div><div>{T["kpi_cap"]}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-card"><div class="kpi-val">{res["anode_mass"]} mg</div><div>{T["kpi_anode"]}</div></div>', unsafe_allow_html=True)

    st.divider()
    
    g1, g2 = st.columns([3, 2])
    with g1:
        st.subheader("📈 Rate Capability Curve")
        rates = [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]
        curve = [run_master_simulation(loading, base_cap, drying, v_window, r, np_ratio)['eff_cap'] for r in rates]
        st.line_chart(pd.DataFrame({"C-rate": rates, "Capacity": curve}).set_index("C-rate"))
    
    with g2:
        st.subheader(T["guide_title"])
        if diff < 0:
            st.error(f"🚨 목표치 미달: {abs(diff):.1f} Wh/kg 보완 필요")
            st.write(f"추천 로딩량: **{loading * (target_whkg/res['whkg']):.1f}mg**")
        else:
            st.success("🎉 설계가 목표치를 충족합니다.")
        st.info(f"알트리스 가이드 기준 N/P {np_ratio} 및 건조 품질 {drying}% 확인됨.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- [7. 설계 히스토리 비교 섹션 (Step 11)] ---
if st.session_state.history:
    st.divider()
    st.subheader(T["hist_title"])
    h_df = pd.DataFrame(st.session_state.history)
    st.table(h_df.iloc[::-1].head(5))
    if len(h_df) > 1:
        st.line_chart(h_df.set_index("Time")["Wh/kg"])