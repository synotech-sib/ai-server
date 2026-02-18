import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# 모듈 및 설정 임포트
from config.security_cfg import SECURITY_MODE, verify_admin_access
from modules.engine import calculate_battery_specs
from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
from modules.reporter import generate_expert_report

# --- [1. 시스템 초기화 & 브랜딩 테마 적용] ---
st.set_page_config(page_title="SynoCore V1.2 | SynoTech Solutions", layout="wide")

# [Step 6] SynoTech Corporate Identity 테마 적용
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .stApp { background-color: #f8f9fa; }
    h1 { color: #003366 !important; font-weight: 800 !important; }
    h2, h3 { color: #004080 !important; }
    
    /* 버튼 스타일 커스텀 */
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 8px;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #00509e;
        transform: translateY(-2px);
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    
    /* 화이트 라벨링 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    init_db()
    log_action("System", "Application Online (Branding Applied)")
    st.session_state.initialized = True

# --- [2. 다국어 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "subtitle": "SynoTech Co., Ltd. Proprietary Simulation Engine",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence Report (PDF)"
    },
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 설계 인텔리전스",
        "subtitle": "시노텍 주식회사 독자 개발 시뮬레이션 엔진",
        "btn_run": "🚀 전략적 분석 실행",
        "res_h": "📊 설계 성능 핵심 지표",
        "pdf_btn": "📥 전문가용 인텔리전스 리포트 다운로드 (PDF)"
    }
}

# 세션 관리 (기존 유지)
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}

# --- [3. 사이드바: 관리자 로그인 및 로고] ---
with st.sidebar:
    # 로고 영역 (나중에 실제 로고 파일 경로로 교체 가능)
    st.markdown("<h2 style='text-align: center; color: #003366;'>SynoTech</h2>", unsafe_allow_html=True)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    u_id = st.text_input("Admin ID", value="")
    u_pw = st.text_input("Password", type="password", value="")
    st.session_state.admin_mode = verify_admin_access(u_id, u_pw)
    
    if st.session_state.admin_mode: st.success("🔓 AUTHORIZED")
    
    st.divider()
    st.caption("© 2026 SynoTech Co., Ltd.")
    st.caption("Ver 1.2.5 (Standard Edition)")

# --- [4. 메인 화면: 설계 입력] ---
st.title(T["title"])
st.write(f"*{T['subtitle']}*")
st.markdown("---")

with st.container():
    in_c1, in_c2, in_c3, in_c4 = st.columns(4)
    loading = in_c1.number_input("Loading (mg/cm²)", value=12.0, help="Cathode active material loading")
    capacity = in_c2.number_input("Cap. (mAh/g)", value=140.0, help="Specific capacity of cathode")
    area = in_c3.number_input("Area (cm²)", value=10.0)
    np_ratio = in_c4.number_input("N/P Ratio", value=1.1, help="Anode/Cathode capacity ratio")

if st.button(T["btn_run"], use_container_width=True, type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        # [Step 7] 고도화된 엔진 호출
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        log_action("User", f"Run: {res['specific_energy']} Wh/kg")
        
        st.subheader(T["res_h"])
        # 결과값 메트릭 강조 배치
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        m_c2.metric("Specific Energy", f"{res['specific_energy']} Wh/kg", delta="Optimized")
        m_c3.metric("Total Capacity", f"{res['total_capacity']} mAh")
        m_c4.metric("Anode Target", f"{res['required_anode']} mg/cm²")
        
        if st.session_state.is_pro:
            st.divider()
            # 전문가 리포트 섹션 (Step 2 & 6 통합)
            res.update({'loading': loading, 'np_ratio': np_ratio})
            u_name = st.session_state.user_info.get("name", "Expert")
            u_comp = st.session_state.user_info.get("company", "Syno Partner")
            pdf_bytes = generate_expert_report(res, u_name, u_comp)
            st.download_button(T["pdf_btn"], pdf_bytes, f"SynoCore_Report_{u_name}.pdf", use_container_width=True)
            st.balloons()
        else:
            if st.button("🚀 Upgrade to Pro to see AI Insights"): st.session_state.show_upgrade = True
    else:
        st.error("Free trial limit reached.")

# 전문가 등록 폼 및 관리자 커맨드 센터 (기존 로직 유지)
if st.session_state.show_upgrade and not st.session_state.is_pro:
    # ... (기존 등록 폼 코드)
    with st.form("enroll"):
        st.subheader("🚀 Join SynoTech Professional Partnership")
        f_name = st.text_input("Name")
        f_comp = st.text_input("Company")
        f_mob = st.text_input("Mobile")
        f_email = st.text_input("Email")
        if st.form_submit_button("Request Full Access"):
            save_lead(f_name, f_comp, f_mob, f_email)
            st.session_state.user_info = {"name": f_name, "company": f_comp}
            st.session_state.is_pro = True
            st.session_state.show_upgrade = False
            st.rerun()

if st.session_state.get('admin_mode', False):
    # ... (기존 관리자 커맨드 센터 코드)
    st.markdown("---")
    st.header(f"🛡️ SynoCore Command Center (Admin: {u_id})")
    audit_df = get_audit_logs()
    show_human = st.checkbox("Human Activity Only", value=True)
    display_df = audit_df[audit_df['user'] != 'System'] if show_human else audit_df
    st.dataframe(display_df, use_container_width=True)
    st.download_button("📥 Download Filtered Logs", display_df.to_csv(index=False).encode('utf-8-sig'), "audit.csv")