import streamlit as st
import pandas as pd
import numpy as np
import time

# --- [1. 시스템 설정 및 테마 정의] ---
st.set_page_config(page_title="SynoCore V1.2 | Energy11 x Altris Master", layout="wide")

# 세션 상태 초기화 (Step 11: 히스토리 관리)
if 'history' not in st.session_state: st.session_state.history = []
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* 전문 보고서 프레임 */
    .report-container { border: 2px solid #1A729A; padding: 35px; border-radius: 15px; background-color: #ffffff; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .report-header { border-bottom: 3px double #1A729A; padding-bottom: 15px; margin-bottom: 25px; text-align: center; }
    .report-title { color: #1A729A; font-size: 1.8rem; font-weight: 800; margin: 0; }
    
    /* KPI 박스 */
    .kpi-card { background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }
    .kpi-val { font-size: 1.6rem; font-weight: bold; color: #1A729A; }
    
    /* 슬라이더 고스트 넘버 스타일 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="typography"] { color: black !important; opacity: 0; transition: opacity 0.3s; }
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 통합 분석 엔진: 알트리스 데이터 + 에너지11 공정 모델] ---
def run_integrated_simulation(loading, base_cap, drying, v_window, c_rate, np_ratio):
    # 2.1. 알트리스 전압 및 C-rate 보정 (실험 데이터 피팅)
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    # Rate Capability: 고출력 시 용량 감쇄 (알트리스 Rate Ladder 기반)
    rate_factor = np.exp(-0.22 * (c_rate - 0.1)) if c_rate > 0.1 else 1.0
    
    # 2.2. 에너지11 공정 및 Full-cell 변환 (ICE 손실 반영)
    # 알트리스 자료 기준 Full-cell ICE 손실 약 15% 적용
    process_eff = (drying / 100.0) * 0.85 
    
    # 2.3. 실효 용량 및 에너지 밀도 산출
    effective_cap = base_cap * v_eff * rate_factor * process_eff
    # 셀 레벨 중량 모델: 활물질 비중 효율 0.38 및 로딩량 가중치 적용
    whkg = (effective_cap * 3.1 * 0.38 * (loading / (loading + 4.9))) * 10
    
    # 2.4. 음극 목표량 (Hard Carbon 기준)
    anode_target = (loading * effective_cap * np_ratio) / 295 # HC Rated 295mAh/g
    
    return {
        "whkg": round(whkg, 1),
        "eff_cap": round(effective_cap, 1),
        "anode_mass": round(anode_target, 3),
        "loss_summary": {
            "Voltage": round((1-v_eff)*100, 1),
            "C-rate": round((1-rate_factor)*100, 1),
            "Process": round((1-process_eff/0.85)*100, 1)
        }
    }

# --- [3. 사이드바: 목표 설정 및 시스템 제어] ---
with st.sidebar:
    st.markdown("<h1 style='color:#1A729A;'>SynoCore V1.2</h1>", unsafe_allow_html=True)
    st.caption("Strategic Cell Intelligence Platform")
    st.divider()
    target_whkg = st.number_input("목표 에너지 밀도 (Wh/kg)", value=160.0)
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [4. 메인 UI: 파라미터 입력 섹션] ---
st.title("에너지11 x 알트리스 통합 설계 시뮬레이션")
st.markdown("---")

col_in1, col_in2 = st.columns([1, 1])

with col_in1:
    st.subheader("🏭 에너지11: 공정 및 설계 변수")
    loading = st.slider("양극 로딩량 (mg/cm²)", 5.0, 30.0, 13.0, step=0.1)
    np_ratio = st.slider("N/P Ratio (알트리스 가이드 1.15)", 1.0, 1.4, 1.15, step=0.01)
    drying = st.slider("건조 공정 품질 (%)", 50, 100, 100)

with col_in2:
    st.subheader("🧪 알트리스: 소재 및 테스트 변수")
    base_cap = st.slider("양극재 기본 용량 (mAh/g)", 100, 175, 162)
    v_window = st.selectbox("전압 구간 (Voltage Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])
    c_rate = st.slider("테스트 속도 (C-rate)", 0.1, 5.0, 0.33, step=0.1)

# --- [5. 시뮬레이션 실행 및 결과 리포팅] ---
if st.button("🚀 정밀 시뮬레이션 및 전략 보고서 생성", use_container_width=True):
    res = run_integrated_simulation(loading, base_cap, drying, v_window, c_rate, np_ratio)
    
    # 히스토리 저장 (Step 11 기능)
    st.session_state.history.append({
        "Time": time.strftime("%H:%M:%S"),
        "Wh/kg": res['whkg'],
        "Loading": loading,
        "Capacity": res['eff_cap'],
        "Drying": drying
    })

    # --- 보고서 렌더링 ---
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    
    st.markdown(f'''
        <div class="report-header">
            <p class="report-title">SIB DESIGN STRATEGY REPORT</p>
            <p style="color:#666;">Energy11 Production Line | Material Ref: Altris Prussian White</p>
        </div>
    ''', unsafe_allow_html=True)

    # 5.1. 핵심 KPI 지표
    k1, k2, k3 = st.columns(3)
    diff = res['whkg'] - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:{color}">{res["whkg"]} Wh/kg</div><div style="font-size:0.9rem; color:#666;">예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val">{res["eff_cap"]} mAh/g</div><div style="font-size:0.9rem; color:#666;">풀셀 실효 용량</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-val">{res["anode_mass"]} mg</div><div style="font-size:0.9rem; color:#666;">목표 음극 로딩량</div></div>', unsafe_allow_html=True)

    st.divider()

    # 5.2. 분석 데이터 및 그래프
    g1, g2 = st.columns([3, 2])
    
    with g1:
        st.subheader("📈 Rate Capability 추정 곡선")
        rates = [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]
        curve = [run_integrated_simulation(loading, base_cap, drying, v_window, r, np_ratio)['eff_cap'] for r in rates]
        st.line_chart(pd.DataFrame({"C-rate": rates, "Capacity": curve}).set_index("C-rate"))
        st.caption("▲ 알트리스 Rate Ladder 데이터를 기반으로 한 방전 속도별 용량 유지율")

    with g2:
        st.subheader("💡 전문가 전략 제언")
        if res['whkg'] < target_whkg:
            st.error(f"🚨 **목표 미달 ({abs(diff):.1f} Wh/kg 부족)**")
            st.write(f"- **해결책 1**: 로딩량을 최소 **{loading * (target_whkg/res['whkg']):.1f}mg** 이상으로 상향하십시오.")
            st.write("- **해결책 2**: 건조 공정을 최적화하여 손실률을 0%로 회복하십시오.")
        else:
            st.success("🎉 **목표 달성 가능한 설계입니다.**")
            st.write("- 현재 설계는 알트리스 소재의 포텐셜을 충분히 활용하고 있습니다.")
        
        st.info(f"""
        **알트리스 핵심 가이드 준수 여부:**
        - N/P Ratio {np_ratio}: {'적정' if np_ratio >= 1.15 else '⚠️ 낮음 (Plating 위험)'}
        - 건조 품질 {drying}%: {'적정' if drying == 100 else '⚠️ 위험 (전압 불안정)'}
        """)

    st.markdown('</div>', unsafe_allow_html=True)

# --- [6. Step 11: 설계 히스토리 비교 섹션] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 및 비교 분석 (Step 11)")
    h_df = pd.DataFrame(st.session_state.history)
    st.table(h_df.iloc[::-1].head(5)) # 최근 5개 항목 표시
    
    if len(h_df) > 1:
        st.caption("설계 변경에 따른 에너지 밀도 변화 추이")
        st.line_chart(h_df.set_index("Time")["Wh/kg"])