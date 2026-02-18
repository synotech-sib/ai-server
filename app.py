import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# [안전 장치] 모듈 임포트
try:
    from config.security_cfg import SECURITY_MODE, verify_admin_access
    from modules.engine import calculate_battery_specs
    from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
    from modules.reporter import generate_expert_report
    REPORTER_READY = True
except Exception as e:
    st.error(f"⚠️ 시스템 구성 요소 로드 중 오류 발생: {e}")
    REPORTER_READY = False

# --- [1. 시스템 초기화 및 사이드바 상태 제어] ---
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'sidebar_state' not in st.session_state: st.session_state.sidebar_state = "expanded"

# 설정: 로그인 여부에 따라 사이드바 초기 상태 결정
st.set_page_config(
    page_title="SynoCore V1.2 | SynoTech Strategic Platform", 
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- [2. 디자인 테마 및 색상 오류 교정 CSS] ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    
    /* [교정] 메인 타이틀: 로고(2.2rem)보다 작은 1.1rem, 검정색 */
    .main h1 {{ 
        color: #000000 !important; font-weight: 700 !important; font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; padding-bottom: 5px; margin-bottom: 30px;
    }}
    
    /* [해결] 슬라이더 색상 겹침 문제: 트랙과 핸들을 구분하여 가독성 확보 */
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div {{ background-color: #e9ecef !important; }} /* 트랙 배경 */
    div[data-testid="stSlider"] div[role="slider"] {{ background-color: #1A729A !important; border: 2px solid #ffffff !important; }} /* 핸들 */
    div[data-testid="stSlider"] div[data-baseweb="slider"] div div {{ background-color: #1A729A !important; }} /* 활성화 바 */
    
    /* 사이드바 스타일 및 메뉴 버튼(header) 가시성 유지 */
    [data-testid="stSidebar"] {{ background-color: #f1f6f9; border-right: 2px solid #1A729A; }}
    .stSidebarCollapseButton {{ color: #1A729A !important; }} /* 열기/닫기 버튼 강조 */
    
    /* 하단 크레딧 폰트 설정 */
    .streamlit-expanderHeader p {{ font-size: 0.8rem !important; color: #1A729A !important; }}
    .streamlit-expanderContent {{ font-size: 0.7rem !important; color: #555555; }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    /* header {{visibility: visible;}} <- 사이드바 버튼 유지를 위해 절대 숨기지 않음 */
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    try:
        init_db()
        log_action("System", "SynoCore V1.2.12 UI & Sidebar Logic Applied")
        st.session_state.initialized = True
    except: pass

# --- [3. 다국어 및 세션 관리] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence Report (PDF)",
        "chart_h": "📈 Design Sensitivity Analysis (Loading vs Wh/kg)"
    },
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 설계 인텔리전스",
        "btn_run": "🚀 전략적 분석 실행",
        "res_h": "📊 설계 성능 핵심 지표",
        "pdf_btn": "📥 전문가용 인텔리전스 리포트 다운로드 (PDF)",
        "chart_h": "📈 설계 민감도 분석 (로딩량 vs 에너지 밀도)"
    }
}

if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}
if 'last_res' not in st.session_state: st.session_state.last_res = None

# --- [4. 사이드바: 브랜드 로고 및 로그인 로직] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    u_id = st.text_input("Admin ID", key="admin_id")
    u_pw = st.text_input("Password", type="password", key="admin_pw")
    
    # [요청 반영] 로그인 시 사이드바 자동 닫기 로직
    if verify_admin_access(u_id, u_pw):
        if not st.session_state.admin_mode:
            st.session_state.admin_mode = True
            st.session_state.sidebar_state = "collapsed" # 로그인 시 닫힘 모드로 변경
            st.rerun() # 설정을 적용하기 위해 재실행
        st.success("✅ MASTER AUTHORIZED")
    else:
        # 로그인 정보가 틀리거나 비어있으면 일반 유저 모드
        if st.session_state.admin_mode:
            st.session_state.admin_mode = False
            st.session_state.sidebar_state = "expanded"
            st.rerun()

    st.divider()
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [5. 메인 화면: 슬라이더 분석 인터페이스] ---
st.title(T["title"])
st.markdown("---")

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    # 슬라이더 색상 겹침 해결: CSS 수정을 통해 가독성 확보
    loading = c1.slider("Loading (mg/cm²)", 5.0, 35.0, 12.0, step=0.1)
    capacity = c2.slider("Cap. (mAh/g)", 100.0, 250.0, 140.0, step=1.0)
    area = c3.slider("Area (cm²)", 1.0, 50.0, 10.0, step=0.5)
    np_ratio = c4.slider("N/P Ratio", 0.8, 1.5, 1.1, step=0.01)

if st.button(T["btn_run"], type="primary", use_container_width=True):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        try:
            res = calculate_battery_specs(loading, capacity, area, np_ratio)
            log_action("User", f"Run: {res['specific_energy']} Wh/kg")
            
            st.subheader(T["res_h"])
            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            m_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
            
            delta_val = None
            if st.session_state.last_res:
                delta_val = f"{res['specific_energy'] - st.session_state.last_res['specific_energy']:+.1f} Wh/kg"
            m_c2.metric("Specific Energy", f"{res['specific_energy']} Wh/kg", delta=delta_val)
            
            m_c3.metric("Total Capacity", f"{res['total_capacity']} mAh")
            m_c4.metric("Anode Target", f"{res['required_anode']} mg/cm²")

            st.divider()
            st.subheader(T["chart_h"])
            load_range = np.linspace(5, 35, 30)
            energy_trend = [calculate_battery_specs(l, capacity, area, np_ratio)['specific_energy'] for l in load_range]
            st.line_chart(pd.DataFrame({'Loading': load_range, 'Energy': energy_trend}).set_index('Loading'))

            st.divider()
            st.subheader("🤖 SynoCore AI Design Insight")
            s_c1, s_c2 = st.columns([1, 2])
            with s_c1:
                score = 100
                if np_ratio < 1.05: score -= 30
                if loading > 22: score -= 20
                st.metric("Design Stability Score", f"{score} / 100")
                if score >= 80: st.success("✅ 안정 범위")
                else: st.warning("⚠️ 보완 권장")
            with s_c2:
                if np_ratio < 1.05: st.write("🚨 **Danger:** 전극 표면 리튬 석출 위험")
                if loading > 22: st.write("⚠️ **Warning:** 고부하 설계로 인한 출력 제한")
                if score == 100: st.write("✨ 시노텍 설계 표준 가이드라인 충족")
            
            st.session_state.last_res = res
            if st.session_state.is_pro:
                if REPORTER_READY:
                    pdf_bytes = generate_expert_report(res, st.session_state.user_info['name'], st.session_state.user_info['company'])
                    st.download_button(T["pdf_btn"], pdf_bytes, "SynoCore_Report.pdf", use_container_width=True)
                    st.balloons()
            else:
                if st.button("🚀 Upgrade to Pro for Report"): st.session_state.show_upgrade = True
        except Exception as e:
            st.error(f"분석 중 오류: {e}")
    else:
        st.error("Free trial limit reached.")

# 전문가 등록 및 대시보드 (기존 로직 유지)
if st.session_state.show_upgrade and not st.session_state.is_pro:
    with st.form("enroll"):
        st.subheader("🚀 Join Expert Partnership")
        f_name = st.text_input("Name")
        f_comp = st.text_input("Company")
        if st.form_submit_button("Unlock Now"):
            save_lead(f_name, f_comp, "", "")
            st.session_state.user_info = {"name": f_name, "company": f_comp}
            st.session_state.is_pro = True
            st.session_state.show_upgrade = False
            st.rerun()

if st.session_state.admin_mode:
    st.markdown("---")
    st.header(f"🛡️ Intelligence Dashboard")
    tab1, tab2 = st.tabs(["📈 Analytics", "📜 Logs"])
    with tab1: st.bar_chart(get_leads()['company'].value_counts())
    with tab2: st.dataframe(get_audit_logs(), use_container_width=True)