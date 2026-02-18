import streamlit as st
import pandas as pd
import numpy as np
import time

# --- [1. 시스템 초기화 및 다국어 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False

LANG_DICT = {
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 레시피 설계 플랫폼",
        "recipe_h": "🧪 소재 레시피 설정 (Material Recipe)",
        "param_h": "⚙️ 공정 설계 파라미터 (Process Parameters)",
        "target_h": "🎯 목표 설정 (Target Setting)",
        "btn_run": "🚀 레시피 분석 및 성능 보고서 생성",
        "report_title": "SIB 맞춤형 설계 및 기술 진단 보고서",
        "limit_title": "⚠️ 기술적 한계 및 제약 사항 (Technical Constraints)",
        "login_info": "Professional 사용자는 사이드바의 'Pro Login' 섹션을 통해 인증 후 전용 기능을 사용할 수 있습니다."
    },
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Recipe Design Platform",
        "recipe_h": "🧪 Material Recipe Settings",
        "param_h": "⚙️ Process Design Parameters",
        "target_h": "🎯 Target Setting",
        "btn_run": "🚀 Run Recipe Analysis & Generate Report",
        "report_title": "Custom SIB Design & Technical Diagnostic Report",
        "limit_title": "⚠️ Technical Limits & Constraints",
        "login_info": "Pro users can access exclusive features via the 'Pro Login' section in the sidebar."
    }
}

st.set_page_config(page_title="SynoCore V1.2 | Recipe Edition", layout="wide")

# --- [2. 전문 디자인 테마] ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .report-container { border: 2px solid #1A729A; padding: 40px; border-radius: 15px; background-color: #ffffff; margin-top: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .report-header { border-bottom: 3px double #1A729A; padding-bottom: 15px; margin-bottom: 25px; text-align: center; }
    .stat-card { background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }
    .limit-box { background-color: #fff4f4; border-left: 5px solid #dc3545; padding: 15px; margin-top: 15px; font-size: 0.9rem; }
    /* 고스트 슬라이더 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 통합 시뮬레이션 엔진] ---
def analyze_recipe_performance(cathode, anode, c_loading, a_loading, ice, np_ratio, v_window, c_rate):
    # 소재별 베이스 용량 매핑 (추정치)
    c_caps = {"프러시안 화이트 (PW)": 160, "층상산화물 (LO)": 135, "폴리음이온 (PA)": 110}
    a_caps = {"쿠라레 A": 340, "쿠라레 B": 320, "쿠라레 V": 300, "애경케미칼 D": 310, "애경케미칼 E": 290, "애경케미칼 F": 280}
    
    base_cap = c_caps.get(cathode, 140)
    # 전압 및 C-rate 감쇄 적용
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    rate_factor = np.exp(-0.2 * (c_rate - 0.1))
    
    # 실효 용량 (ICE 반영)
    eff_cap = base_cap * v_eff * rate_factor * (ice / 100.0)
    
    # 에너지 밀도 (Wh/kg) - 셀 중량 모델
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    return round(whkg, 1), round(eff_cap, 1)

# --- [4. 사이드바: 로그인 및 환경설정] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    sel_lang = st.selectbox("🌐 Language", ["한국어", "English"])
    T = LANG_DICT[sel_lang]
    
    st.divider()
    st.subheader("🔐 Pro Login")
    login_id = st.text_input("Professional ID")
    login_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_id == "energy11" and login_pw == "altris123":
            st.session_state.is_pro = True
            st.success("Professional 인증 완료")
        else:
            st.error("인증 정보가 일치하지 않습니다.")
    
    if st.session_state.is_pro:
        st.info("💡 전문가 기능: 데이터 내보내기 및 정밀 리포트 활성화")

# --- [5. 메인 레이아웃: 레시피 및 파라미터] ---
st.title(T["title"])
st.markdown("---")

# 레이아웃 구성: 왼쪽(레시피/파라미터), 오른쪽(목표설정)
col_main, col_target = st.columns([3, 1])

with col_main:
    # 5.1. 소재 레시피 설정
    st.subheader(T["recipe_h"])
    r1, r2, r3 = st.columns(3)
    cathode_type = r1.selectbox("양극재 (Cathode)", ["프러시안 화이트 (PW)", "층상산화물 (LO)", "폴리음이온 (PA)"])
    anode_type = r2.selectbox("음극재 (Anode)", ["쿠라레 A", "쿠라레 B", "쿠라레 V", "애경케미칼 D", "애경케미칼 E", "애경케미칼 F"])
    electrolyte = r3.selectbox("전해질 (Electrolyte)", ["G Type (표준)", "H Type (고온)", "I Type (저온)", "J Type (고출력)"])
    
    r4, r5, r6 = st.columns(3)
    additive = r4.multiselect("첨가제 & 도전재", ["VC", "FEC", "CNT", "Graphene", "Super P"])
    separator = r5.selectbox("분리막 (Separator)", ["PE (Polyethylene)", "PP (Polypropylene)", "Ceramic Coated"])
    v_window = r6.selectbox("전압 구간 (V)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])

    # 5.2. 공정 파라미터 설정
    st.subheader(T["param_h"])
    p1, p2, p3 = st.columns(3)
    c_loading = p1.slider("양극 로딩량 (mg/cm²)", 5.0, 30.0, 13.0)
    a_loading = p2.slider("음극 로딩량 (mg/cm²)", 5.0, 30.0, 8.0)
    ice_val = p3.slider("초기 효율 (ICE %)", 70.0, 95.0, 85.0)
    
    p4, p5 = st.columns(2)
    np_ratio = p4.slider("N/P Ratio", 1.0, 1.4, 1.15)
    c_rate = p5.slider("방전 속도 (C-rate)", 0.1, 5.0, 0.33)

with col_target:
    # 5.3. 목표 설정 (우측 배치)
    st.subheader(T["target_h"])
    target_whkg = st.number_input("Target Energy (Wh/kg)", value=160.0, step=1.0)
    st.divider()
    st.write("**Current Recipe Summary**")
    st.caption(f"Cathode: {cathode_type}")
    st.caption(f"Anode: {anode_type}")
    st.caption(f"Separator: {separator}")

# --- [6. 분석 실행 및 보고서 생성] ---
if st.button(T["btn_run"], use_container_width=True):
    whkg, eff_cap = analyze_recipe_performance(cathode_type, anode_type, c_loading, a_loading, ice_val, np_ratio, v_window, c_rate)
    
    # 리포트 섹션
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header"><h2 style="color:#1A729A;">{T["report_title"]}</h2></div>', unsafe_allow_html=True)
    
    # KPI 요약
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:{color}">{whkg} Wh/kg</div><div>{T["kpi_energy"]}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap} mAh/g</div><div>{T["kpi_cap"]}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{np_ratio}</div><div>N/P Ratio Balance</div></div>', unsafe_allow_html=True)

    # 기술적 코멘트 및 한계점
    st.subheader(T["limit_title"])
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown(f"**[{cathode_type} 특성 진단]**")
        if "프러시안" in cathode_type:
            st.write("- Prussian White는 고용량 구현에 유리하나 공정 중 수분 제어가 에너지 밀도 유지의 핵심 한계입니다.")
        elif "층상" in cathode_type:
            st.write("- 층상산화물은 구조적 안정성이 높으나 SIB 특유의 전압 강하(Voltage Slope)가 리튬 대비 급격합니다.")
            
    with col_r:
        st.markdown(f"**[기술적 제약 사항]**")
        if whkg < target_whkg:
            st.error(f"목표치 달성을 위해 로딩량을 최소 {c_loading * (target_whkg/whkg):.1f}mg 이상으로 설계하거나 ICE를 {ice_val + 5}% 이상 확보해야 합니다.")
        if c_rate > 1.0:
            st.warning("1.0C 이상의 고율 방전 시 분리막의 이온 전도도와 전해질 첨가제(FEC 등)의 계면 저항이 성능의 병목 현상이 될 수 있습니다.")

    st.markdown('</div>', unsafe_allow_html=True)

    # 히스토리 저장
    st.session_state.history.append({"Time": time.strftime("%H:%M:%S"), "Recipe": cathode_type, "Wh/kg": whkg, "Target": target_whkg})

# --- [7. 설계 히스토리] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 히스토리 (Design History)")
    st.table(pd.DataFrame(st.session_state.history).tail(5))