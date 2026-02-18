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

# --- [1. 시스템 초기화 & 테마 적용] ---
# initial_sidebar_state="expanded"를 추가하여 메뉴가 항상 열려있게 설정했습니다.
st.set_page_config(
    page_title="SynoCore V1.2 | SynoTech Strategic Platform", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# CSS 수정: 헤더 숨김 해제 및 사이드바 토글 버튼 가시성 확보
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* 메인 타이틀 스타일 */
    .main h1 { 
        color: #000000 !important; 
        font-weight: 700 !important; 
        font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; 
        padding-bottom: 5px; 
        margin-bottom: 30px;
    }
    
    h2, h3 { color: #1A729A !important; font-weight: 600 !important; }
    
    /* 버튼 스타일: 시노텍 블루 */
    .stButton>button {
        background-color: #1A729A;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
    }
    
    /* 사이드바 스타일 및 경계선 강조 */
    [data-testid="stSidebar"] { 
        background-color: #f1f6f9; 
        border-right: 2px solid #1A729A; 
    }
    
    /* 크레딧 폰트 조절 */
    .streamlit-expanderHeader p { font-size: 0.9rem !important; color: #1A729A !important; }
    .streamlit-expanderContent { font-size: 0.75rem !important; color: #555555; }

    /* 불필요한 메뉴만 숨기고 헤더(토글버튼)는 유지 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;} <- 이 줄을 삭제하여 사이드바 버튼을 복구했습니다. */
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    try:
        init_db()
        log_action("System", "SynoCore V1.2.9 UI Restored")
        st.session_state.initialized = True
    except: pass

# --- [2. 다국어 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence Report (PDF)"
    },
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 설계 인텔리전스",
        "btn_run": "🚀 전략적 분석 실행",
        "res_h": "📊 설계 성능 핵심 지표",
        "pdf_btn": "📥 전문가용 인텔리전스 리포트 다운로드 (PDF)"
    }
}

if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}
if 'last_res' not in st.session_state: st.session_state.last_res = None

# --- [3. 사이드바: 브랜드 로고 및 메뉴] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    u_id = st.text_input("Admin ID", key="admin_id")
    u_pw = st.text_input("Password", type="password", key="admin_pw")
    st.session_state.admin_mode = verify_admin_access(u_id, u_pw)
    if st.session_state.admin_mode: st.success("✅ MASTER AUTHORIZED")
    
    st.divider()
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [4. 메인 화면: 분석 인터페이스] ---
st.title(T["title"])
st.markdown("---")

in_c1, in_c2, in_c3, in_c4 = st.columns(4)
loading = in_c1.number_input("Loading (mg/cm²)", value=12.0)
capacity = in_c2.number_input("Cap. (mAh/g)", value=140.0)
area = in_c3.number_input("Area (cm²)", value=10.0)
np_ratio = in_c4.number_input("N/P Ratio", value=1.1)

if st.button(T["btn_run"], type="primary"):
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

            # AI 분석 섹션
            st.subheader("🤖 SynoCore AI Design Insight")
            s_c1, s_c2 = st.columns([1, 2])
            
            with s_c1:
                # N/P Ratio와 Loading 기반의 간단한 점수 로직
                score = 100
                if np_ratio < 1.05: score -= 30
                if loading > 20: score -= 20
                st.metric("Design Stability Score", f"{score} / 100")
                if score >= 80: st.success("✅ 설계가 안정적입니다.")
                else: st.warning("⚠️ 보완이 권장됩니다.")

            with s_c2:
                if np_ratio < 1.05: st.write("🚨 **N/P Ratio 위험:** 덴드라이트 형성 위험이 있습니다.")
                else: st.write("✨ 설계 가이드라인을 준수하고 있습니다.")
            
            st.session_state.last_res = res

            if st.session_state.is_pro:
                st.divider()
                if REPORTER_READY:
                    res.update({'loading': loading, 'np_ratio': np_ratio})
                    u_name = st.session_state.user_info.get("name", "Expert")
                    u_comp = st.session_state.user_info.get("company", "Syno Partner")
                    pdf_bytes = generate_expert_report(res, u_name, u_comp)
                    st.download_button(T["pdf_btn"], pdf_bytes, f"SynoCore_Report_{u_name}.pdf", use_container_width=True)
                    st.balloons()
            else:
                if st.button("🚀 Unlock Pro for AI Detailed Report"): st.session_state.show_upgrade = True
        except Exception as e:
            st.error(f"분석 엔진 오류: {e}")
    else:
        st.error("Free trial limit reached.")

# 전문가 등록 폼
if st.session_state.show_upgrade and not st.session_state.is_pro:
    st.divider()
    with st.form("enroll"):
        st.subheader("🚀 Register for Professional Access")
        f_name = st.text_input("Name")
        f_comp = st.text_input("Company")
        f_mob = st.text_input("Mobile")
        f_email = st.text_input("Email")
        if st.form_submit_button("Submit"):
            save_lead(f_name, f_comp, f_mob, f_email)
            st.session_state.user_info = {"name": f_name, "company": f_comp}
            st.session_state.is_pro = True
            st.session_state.show_upgrade = False
            st.rerun()

# --- [5. Command Center (Dashboard)] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    st.header(f"🛡️ SynoCore Intelligence Dashboard")
    leads_df = get_leads()
    audit_df = get_audit_logs()
    
    tab_chart, tab_log, tab_lead = st.tabs(["📈 Analytics", "📜 Audit Logs", "📊 Leads Data"])
    with tab_chart:
        if not leads_df.empty: st.bar_chart(leads_df['company'].value_counts())
    with tab_log: st.dataframe(audit_df, use_container_width=True)
    with tab_lead: st.dataframe(leads_df, use_container_width=True)