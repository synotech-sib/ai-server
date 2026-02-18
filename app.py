import streamlit as st
import pandas as pd
import numpy as np
import time

# --- [1. 시스템 초기화 및 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
# [master v1.2] 버전 관리 정보
st.session_state.model_version = "master v1.2 (Energy11 x Altris Hybrid)"

LANG_DICT = {
    "한국어": {
        "title": "SynoCore Master V1.2: SIB 레시피 설계 인텔리전스",
        "recipe_h": "🧪 소재 레시피 설정 (Recipe)",
        "param_h": "⚙️ 공정 설계 파라미터",
        "target_h": "🎯 목표 설정",
        "btn_run": "🚀 마스터 분석 및 기술 보고서 생성",
        "report_title": "SIB 맞춤형 설계 및 정밀 진단 보고서",
        "limit_title": "⚠️ 기술적 제약 사항 및 엔지니어 코멘트",
        "hist_title": "🔄 설계 및 함수 진화 히스토리 (Versioning)"
    },
    "English": {
        "title": "SynoCore Master V1.2: SIB Recipe Intelligence",
        "recipe_h": "🧪 Material Recipe",
        "param_h": "⚙️ Process Design",
        "target_h": "🎯 Target Setting",
        "btn_run": "🚀 Run Master Analysis & Report",
        "report_title": "Custom SIB Design & Diagnostic Report",
        "limit_title": "⚠️ Technical Constraints & Comments",
        "hist_title": "🔄 Design & Model Version History"
    }
}

st.set_page_config(page_title="SynoCore Master V1.2", layout="wide")

# --- [2. 전문 디자인 테마 및 고스트 슬라이더] ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .report-container { border: 2px solid #1A729A; padding: 35px; border-radius: 15px; background-color: #ffffff; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .stat-card { background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="typography"] { color: black !important; opacity: 0; transition: opacity 0.3s; }
    div[data-testid="stSlider"]:hover [data-baseweb="typography"] { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 통합 연산 엔진] ---
def run_master_engine(cathode, anode, c_loading, ice, np_ratio, v_window, c_rate):
    # 알트리스 기반 소재 데이터
    c_base = {"프러시안 화이트 (PW)": 162, "층상산화물 (LO)": 135, "폴리음이온 (PA)": 110}.get(cathode, 140)
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    rate_factor = np.exp(-0.2 * (c_rate - 0.1))
    
    # 실효 용량 (ICE 보정 포함)
    eff_cap = c_base * v_eff * rate_factor * (ice / 100.0)
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    return round(whkg, 1), round(eff_cap, 1)

# --- [4. 사이드바: 마스터 계정 로그인 및 다국어] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    sel_lang = st.selectbox("🌐 Language", ["한국어", "English"])
    T = LANG_DICT[sel_lang]
    
    st.divider()
    st.subheader("🔐 Professional Login")
    # [수정] 대표님 전용 계정으로 업데이트
    login_id = st.text_input("ID")
    login_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_id == "wschoi" and login_pw == "snotech0773!":
            st.session_state.is_pro = True
            st.success("Master Authorized: wschoi")
        else:
            st.error("Invalid Credentials")
    
    if st.session_state.is_pro:
        st.info(f"Current Model: {st.session_state.model_version}")

# --- [5. 메인 레이아웃: 레시피 설계] ---
st.title(T["title"])
st.markdown("---")

col_main, col_target = st.columns([3, 1])

with col_main:
    st.subheader(T["recipe_h"])
    r1, r2, r3 = st.columns(3)
    cathode = r1.selectbox("양극재 (Cathode)", ["프러시안 화이트 (PW)", "층상산화물 (LO)", "폴리음이온 (PA)"])
    anode = r2.selectbox("음극재 (Anode)", ["쿠라레 A", "쿠라레 B", "쿠라레 V", "애경케미칼 D", "애경케미칼 E", "애경케미칼 F"])
    electrolyte = r3.selectbox("전해질 (Electrolyte)", ["G Type (표준)", "H Type (고온)", "I Type (저온)", "J Type (고출력)"])
    
    r4, r5, r6 = st.columns(3)
    additives = r4.multiselect("첨가제 & 도전재", ["VC", "FEC", "CNT", "Graphene", "Super P"], default=["VC", "CNT"])
    separator = r5.selectbox("분리막 (Separator)", ["PE (Polyethylene)", "PP (Polypropylene)", "Ceramic Coated"])
    v_window = r6.selectbox("전압 구간 (Voltage Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])

    st.subheader(T["param_h"])
    p1, p2, p3 = st.columns(3)
    c_loading = p1.slider("양극 로딩량 (mg/cm²)", 5.0, 30.0, 13.0, step=0.1)
    ice_val = p2.slider("초기 효율 (ICE %)", 70.0, 95.0, 85.0, step=0.5)
    np_ratio = p3.slider("N/P Ratio", 1.0, 1.4, 1.15, step=0.01)
    
    c_rate = st.slider("방전 속도 (C-rate)", 0.1, 5.0, 0.33, step=0.1)

with col_target:
    # 목표 설정 및 요약 정보
    st.subheader(T["target_h"])
    target_whkg = st.number_input("Target Energy (Wh/kg)", value=160.0, step=1.0)
    st.divider()
    st.write("**Design Summary**")
    st.caption(f"Cathode: {cathode}")
    st.caption(f"Anode: {anode}")
    st.caption(f"C-rate: {c_rate}C")

# --- [6. 분석 결과 및 보고서] ---
if st.button(T["btn_run"], use_container_width=True):
    whkg, eff_cap = run_master_engine(cathode, anode, c_loading, ice_val, np_ratio, v_window, c_rate)
    
    # 히스토리 저장 (버전 정보 포함)
    st.session_state.history.append({
        "Date": time.strftime("%Y-%m-%d %H:%M"),
        "Wh/kg": whkg,
        "Version": st.session_state.model_version,
        "Recipe": cathode
    })

    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; border-bottom:2px solid #1A729A; padding-bottom:15px; margin-bottom:25px;"><h2 style="color:#1A729A; margin:0;">{T["report_title"]}</h2></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:{color};">{whkg} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{np_ratio}</div><div>N/P Ratio</div></div>', unsafe_allow_html=True)

    st.subheader(T["limit_title"])
    l_col, r_col = st.columns(2)
    with l_col:
        st.markdown(f"**[{cathode} 소재 진단]**")
        if "프러시안" in cathode: st.warning("- 공정 중 수분 함량 10ppm 초과 시 에너지 밀도 및 수명 급락 위험.")
        st.write(f"- {anode} 음극 매칭 시 알트리스 권고 N/P Ratio 1.15를 준수하십시오.")
    with r_col:
        st.markdown("**[기술적 제언]**")
        if whkg < target_whkg: st.error(f"- 목표치 미달: 로딩량을 {c_loading * (target_whkg/whkg):.1f}mg 이상으로 설계하십시오.")
        st.info(f"- {separator} 사용 시 고출력 특성 보완을 위한 CNT 분산 공정 최적화가 필요합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [7. 설계 히스토리 및 모델 진화] ---
if st.session_state.history:
    st.divider()
    st.subheader(T["hist_title"])
    h_df = pd.DataFrame(st.session_state.history)
    st.table(h_df.iloc[::-1].head(5))
    if len(h_df) > 1: st.line_chart(h_df.set_index("Date")["Wh/kg"])