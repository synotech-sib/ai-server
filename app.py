import streamlit as st
import pandas as pd
import numpy as np
import time

# --- [1. 시스템 초기화 및 다국어 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'model_version' not in st.session_state: st.session_state.model_version = "V1.2.27 (Hybrid Empirical)"

LANG_DICT = {
    "한국어": {
        "title": "SynoCore V1.2: 에너지11 x 알트리스 전략 플랫폼",
        "recipe_h": "🧪 소재 레시피 (Material Recipe)",
        "param_h": "⚙️ 공정 설계 변수",
        "target_h": "🎯 목표 에너지 밀도",
        "btn_run": "🚀 레시피 분석 및 보고서 생성",
        "report_title": "SIB 맞춤형 설계 및 기술 진단 보고서",
        "limit_title": "⚠️ 기술적 제약 사항 및 코멘트",
        "hist_title": "🔄 설계 및 함수 진화 히스토리 (Model Versioning)"
    },
    "English": {
        "title": "SynoCore V1.2: Energy11 x Altris Strategic Platform",
        "recipe_h": "🧪 Material Recipe",
        "param_h": "⚙️ Process Design Parameters",
        "target_h": "🎯 Target Energy Density",
        "btn_run": "🚀 Run Recipe Analysis & Report",
        "report_title": "Custom SIB Design & Technical Diagnostic Report",
        "limit_title": "⚠️ Technical Constraints & Comments",
        "hist_title": "🔄 Design & Model Version History"
    }
}

st.set_page_config(page_title="SynoCore V1.2 | Master Recipe", layout="wide")

# --- [2. 전문 디자인 테마 및 고도화된 슬라이더] ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .report-container { border: 2px solid #1A729A; padding: 35px; border-radius: 15px; background-color: #ffffff; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .stat-card { background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }
    /* 고스트 슬라이더 (블루 숫자) */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="typography"] { color: black !important; opacity: 0; transition: opacity 0.3s; }
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 통합 시뮬레이션 및 N/P 밸런싱 엔진] ---
def run_recipe_engine(c_type, a_type, c_loading, ice, np_ratio, v_window, c_rate):
    # 알트리스 소재 데이터 기준 (mAh/g)
    c_base = {"프러시안 화이트 (PW)": 162, "층상산화물 (LO)": 135, "폴리음이온 (PA)": 110}.get(c_type, 140)
    # 알트리스 C-rate 및 전압 감쇄 적용
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    rate_factor = np.exp(-0.2 * (c_rate - 0.1))
    
    # 에너지11 풀셀 실효 용량 및 ICE 손실 (ICE 85% 기준 보정)
    eff_cap = c_base * v_eff * rate_factor * (ice / 100.0)
    
    # 에너지 밀도 (Wh/kg) - 셀 중량 모델 (효율 0.38)
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    return round(whkg, 1), round(eff_cap, 1)

# --- [4. 사이드바: Pro Login 및 다국어] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    sel_lang = st.selectbox("🌐 Language", ["한국어", "English"])
    T = LANG_DICT[sel_lang]
    
    st.divider()
    st.subheader("🔐 Pro Login")
    login_id = st.text_input("ID (User/Admin)")
    login_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_id == "energy11" and login_pw == "altris123":
            st.session_state.is_pro = True
            st.success("Professional 인증 완료")
        else:
            st.error("인증 실패")
    
    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()

# --- [5. 메인 레이아웃: 설계 및 레시피] ---
st.title(T["title"])
st.markdown("---")

col_left, col_right = st.columns([3, 1])

with col_left:
    # 5.1. 소재 레시피 설정
    st.subheader(T["recipe_h"])
    r1, r2, r3 = st.columns(3)
    cathode = r1.selectbox("양극재 (Cathode)", ["프러시안 화이트 (PW)", "층상산화물 (LO)", "폴리음이온 (PA)"])
    anode = r2.selectbox("음극재 (Anode)", ["쿠라레 A", "쿠라레 B", "쿠라레 V", "애경케미칼 D", "애경케미칼 E", "애경케미칼 F"])
    electrolyte = r3.selectbox("전해질 (Electrolyte)", ["G Type (표준)", "H Type (고온)", "I Type (저온)", "J Type (고출력)"])
    
    r4, r5, r6 = st.columns(3)
    additives = r4.multiselect("첨가제 & 도전재", ["VC", "FEC", "CNT", "Graphene", "Super P"], default=["VC", "CNT"])
    separator = r5.selectbox("분리막 (Separator)", ["PE (Polyethylene)", "PP (Polypropylene)", "Ceramic Coated"])
    v_window = r6.selectbox("전압 구간 (V Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])

    # 5.2. 공정 파라미터 설정
    st.subheader(T["param_h"])
    p1, p2, p3 = st.columns(3)
    c_loading = p1.slider("양극 로딩량 (mg/cm²)", 5.0, 30.0, 13.0, step=0.1)
    ice_val = p2.slider("초기 효율 (ICE %)", 70.0, 95.0, 85.0, step=0.5)
    np_ratio = p3.slider("N/P Ratio", 1.0, 1.4, 1.15, step=0.01)
    
    c_rate = st.slider("방전 속도 (C-rate)", 0.1, 5.0, 0.33, step=0.1)

with col_right:
    # 5.3. 목표 설정 및 요약 (우측 배치)
    st.subheader(T["target_h"])
    target_whkg = st.number_input("Target Energy Density (Wh/kg)", value=160.0, step=1.0)
    st.divider()
    st.write("**Current Recipe**")
    st.caption(f"C: {cathode}")
    st.caption(f"A: {anode}")
    st.caption(f"E: {electrolyte}")
    st.caption(f"S: {separator}")

# --- [6. 분석 실행 및 보고서 렌더링] ---
if st.button(T["btn_run"], use_container_width=True):
    whkg, eff_cap = run_recipe_engine(cathode, anode, c_loading, ice_val, np_ratio, v_window, c_rate)
    
    # 히스토리 저장 (함수 버전 포함)
    st.session_state.history.append({
        "Time": time.strftime("%H:%M:%S"),
        "Recipe": cathode,
        "Wh/kg": whkg,
        "Version": st.session_state.model_version
    })

    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; border-bottom:2px solid #1A729A; padding-bottom:10px; margin-bottom:20px;"><h2 style="color:#1A729A; margin:0;">{T["report_title"]}</h2><p style="color:#666; font-size:0.8rem;">Ref: Altris Pathfinder Data | User: Energy11</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    # [수정] image_77bcfc의 f-string 괄호 중첩 오류 해결
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:{color};">{whkg} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{np_ratio}</div><div>설계 N/P Ratio</div></div>', unsafe_allow_html=True)

    st.divider()

    # 6.1. 제약 사항 및 기술 코멘트
    st.subheader(T["limit_title"])
    l_col, r_col = st.columns(2)
    
    with l_col:
        st.markdown(f"**[{cathode} 기술 분석]**")
        if "프러시안" in cathode:
            st.warning("- **수분 민감도**: Prussian White는 고용량 구현에 유리하나, 공정 내 잔류 수분이 10ppm 이상일 경우 전압 불안정 및 사이클 급락의 핵심 원인이 됩니다.")
        elif "층상" in cathode:
            st.info("- **전압 거동**: 층상산화물은 초기 효율이 우수하나 SIB 특유의 급격한 Voltage Slope로 인해 시스템 BMS 가용 범위가 좁아질 수 있습니다.")
            
    with r_col:
        st.markdown("**[설계 최적화 제언]**")
        if whkg < target_whkg:
            st.error(f"- **목표 미달**: 160Wh/kg 달성을 위해 로딩량을 현재 {c_loading}mg → **{c_loading * (target_whkg/whkg):.1f}mg/cm²**로 상향하거나, {v_window}를 4.2V 구간으로 확장해야 합니다.")
        if c_rate > 1.0:
            st.warning(f"- **고율 방전 제약**: {c_rate}C 환경에서는 {separator}의 이온 전도도가 병목이 될 수 있습니다. 저항 감소를 위해 CNT 도전재 비중 확대를 제언합니다.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- [7. Step 11: 진화 히스토리 시각화] ---
if st.session_state.history:
    st.divider()
    st.subheader(T["hist_title"])
    h_df = pd.DataFrame(st.session_state.history)
    st.table(h_df.iloc[::-1].head(5))
    
    if len(h_df) > 1:
        st.line_chart(h_df.set_index("Time")["Wh/kg"])