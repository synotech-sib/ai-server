import streamlit as st
import pandas as pd
import numpy as np
import time

# --- [1. 시스템 초기화 및 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
# Master V1.2 버전 정보 고정
st.session_state.model_version = "Master V1.2 (Energy11 x Altris Hybrid)"

# 다국어 사전
LANG_DICT = {
    "한국어": {
        "title": "SynoCore Master V1.2: SIB 레시피 설계 인텔리전스",
        "recipe_h": "🧪 소재 레시피 설정 (Material Recipe)",
        "param_h": "⚙️ 공정 설계 파라미터 (Process Params)",
        "target_h": "🎯 목표 설정 (Targeting)",
        "btn_run": "🚀 레시피 분석 및 기술 보고서 생성",
        "report_title": "SIB 맞춤형 설계 및 기술 진단 보고서",
        "limit_title": "⚠️ 기술적 제약 사항 및 엔지니어 코멘트",
        "hist_title": "🔄 설계 및 함수 진화 히스토리 (Versioning)"
    },
    "English": {
        "title": "SynoCore Master V1.2: Strategic SIB Recipe Design",
        "recipe_h": "🧪 Material Recipe Settings",
        "param_h": "⚙️ Process Design Parameters",
        "target_h": "🎯 Target Setting",
        "btn_run": "🚀 Run Recipe Analysis & Generate Report",
        "report_title": "SIB Custom Design & Diagnostic Report",
        "limit_title": "⚠️ Technical Constraints & Comments",
        "hist_title": "🔄 Design & Model Version History"
    }
}

st.set_page_config(page_title="SynoCore Master V1.2", layout="wide")

# --- [2. 고도화된 디자인 테마 및 고스트 슬라이더] ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .report-container { border: 2px solid #1A729A; padding: 40px; border-radius: 20px; background-color: #ffffff; margin-top: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .report-header { border-bottom: 3px double #1A729A; padding-bottom: 15px; margin-bottom: 25px; text-align: center; }
    .stat-card { background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }
    /* 고스트 슬라이더 (블루 숫자) */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="typography"] { color: black !important; opacity: 0; transition: opacity 0.3s; }
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 통합 시뮬레이션 엔진 (Altris Logic)] ---
def run_master_engine(c_type, a_type, c_loading, ice, np_ratio, v_window, c_rate):
    # 알트리스 소재 데이터 기준 용량 (mAh/g)
    # Prussian White(162), Layered(135), Polyanion(110) [cite: 213, 1226]
    c_base = {"프러시안 화이트 (PW)": 162.0, "층상산화물 (LO)": 135.0, "폴리음이온 (PA)": 110.0}.get(c_type, 140.0)
    
    # 전압 구간 보정 (알트리스 자료 Page 4 참조) [cite: 1226]
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    
    # C-rate 감쇄 (Rate Ladder 데이터 피팅) [cite: 134, 691]
    rate_factor = np.exp(-0.2 * (c_rate - 0.1))
    
    # 에너지11 풀셀 실효 용량 산출 (ICE 손실 포함) [cite: 1398, 1520]
    eff_cap = c_base * v_eff * rate_factor * (ice / 100.0)
    
    # 에너지 밀도 (Wh/kg) - 셀 레벨 중량 모델 적용
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    return round(whkg, 1), round(eff_cap, 1)

# --- [4. 사이드바: 마스터 로그인 및 다국어] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    sel_lang = st.selectbox("🌐 Language", ["한국어", "English"])
    T = LANG_DICT[sel_lang]
    
    st.divider()
    st.subheader("🔐 Professional Login")
    # [해결] 대표님 전용 마스터 계정 적용
    u_id = st.text_input("ID")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_id == "wschoi" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success("Master Authorized: wschoi")
        else:
            st.error("Invalid Credentials")
    
    if st.session_state.is_pro:
        st.info(f"Model: {st.session_state.model_version}")

# --- [5. 메인 레이아웃: 레시피 및 파라미터 통합 입력] ---
st.title(T["title"])
st.markdown("---")

col_left, col_right = st.columns([3, 1])

with col_left:
    # 5.1. 소재 레시피 (Recipe)
    st.subheader(T["recipe_h"])
    r1, r2, r3 = st.columns(3)
    c_type = r1.selectbox("양극재 (Cathode)", ["프러시안 화이트 (PW)", "층상산화물 (LO)", "폴리음이온 (PA)"])
    a_type = r2.selectbox("음극재 (Anode)", ["쿠라레 A", "쿠라레 B", "쿠라레 V", "애경케미칼 D", "애경케미칼 E", "애경케미칼 F"])
    electrolyte = r3.selectbox("전해질 (Electrolyte)", ["G Type (표준)", "H Type (고온)", "I Type (저온)", "J Type (고출력)"])
    
    r4, r5, r6 = st.columns(3)
    additives = r4.multiselect("첨가제 & 도전재", ["VC", "FEC", "CNT", "Graphene", "Super P"], default=["VC", "CNT"])
    separator = r5.selectbox("분리막 (Separator)", ["PE (Polyethylene)", "PP (Polypropylene)", "Ceramic Coated"])
    v_window = r6.selectbox("전압 구간 (Voltage Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])

    # 5.2. 공정 파라미터
    st.subheader(T["param_h"])
    p1, p2, p3 = st.columns(3)
    c_loading = p1.slider("양극 로딩량 (mg/cm²)", 5.0, 30.0, 13.0, step=0.1)
    ice_val = p2.slider("초기 효율 (ICE %)", 70.0, 95.0, 85.0, step=0.5)
    np_ratio = p3.slider("N/P Ratio (Safety)", 1.0, 1.4, 1.15, step=0.01)
    
    c_rate = st.slider("방전 속도 (C-rate)", 0.1, 5.0, 0.33, step=0.1)

with col_right:
    # 5.3. 목표 설정 및 요약 (우측 배치)
    st.subheader(T["target_h"])
    target_whkg = st.number_input("Target Energy (Wh/kg)", value=160.0, step=1.0)
    st.divider()
    st.write("**Current Recipe**")
    st.caption(f"Cathode: {c_type}")
    st.caption(f"Anode: {a_type}")
    st.caption(f"Electrolyte: {electrolyte}")
    st.caption(f"Separator: {separator}")

# --- [6. 분석 실행 및 보고서 렌더링] ---
if st.button(T["btn_run"], use_container_width=True):
    whkg, eff_cap = run_master_engine(c_type, a_type, c_loading, ice_val, np_ratio, v_window, c_rate)
    
    # 히스토리 저장 (버전 정보 포함)
    st.session_state.history.append({
        "Date": time.strftime("%Y-%m-%d %H:%M"),
        "Wh/kg": whkg,
        "Recipe": c_type,
        "Version": st.session_state.model_version
    })

    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header"><h2 style="color:#1A729A; margin:0;">{T["report_title"]}</h2><p style="color:#666; font-size:0.8rem;">Ref: Altris Pathfinder Data | Manufacturing: Energy11</p></div>', unsafe_allow_html=True)
    
    # KPI 섹션
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold; color:{color};">{whkg} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{eff_cap} mAh/g</div><div>실효 가역 용량 (@{c_rate}C)</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{np_ratio}</div><div>설계 N/P Ratio 마진</div></div>', unsafe_allow_html=True)

    st.divider()

    # 제약 사항 및 엔지니어 코멘트
    st.subheader(T["limit_title"])
    l_col, r_col = st.columns(2)
    with l_col:
        st.markdown(f"**[{c_type} 기술 분석]**")
        if "프러시안" in c_type:
            st.warning("- **수분 민감도**: 알트리스 가이드(Page 4)에 따라 170°C 이상의 진공 건조가 필수적이며, 수분 재흡수 시 용량 급락의 핵심 원인이 됩니다[cite: 29, 32].")
        st.write(f"- **소재 특성**: {a_type} 음극과의 매칭 시 초기 Sodiation 과정에서 12~15%의 비가역 손실이 발생함을 고려해야 합니다[cite: 234].")
    with r_col:
        st.markdown("**[설계 최적화 제언]**")
        if whkg < target_whkg:
            st.error(f"- **목표 미달**: 160Wh/kg 달성을 위해 로딩량을 현재 {c_loading}mg → **{c_loading * (target_whkg/whkg):.1f}mg/cm²**로 상향하거나 ICE 개선이 필요합니다.")
        st.info(f"- **안전 마진**: {a_type} 사용 시 Sodium Plating 방지를 위해 N/P Ratio를 알트리스 권고치인 **1.15** 이상으로 유지하십시오[cite: 231, 244].")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [7. 설계 히스토리 및 함수 진화 (Step 11)] ---
if st.session_state.history:
    st.divider()
    st.subheader(T["hist_title"])
    h_df = pd.DataFrame(st.session_state.history)
    st.table(h_df.iloc[::-1].head(5))
    if len(h_df) > 1:
        st.line_chart(h_df.set_index("Date")["Wh/kg"])