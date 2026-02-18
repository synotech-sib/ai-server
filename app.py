import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# 모듈 및 설정 임포트 (왼쪽 벽에 밀착!)
from config.security_cfg import SECURITY_MODE, verify_admin_access
from modules.engine import calculate_battery_specs
from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
from modules.reporter import generate_expert_report

# --- [1. 시스템 초기화 & Syno Blue 테마 적용] ---
st.set_page_config(page_title="SynoCore V1.2 | SynoTech Strategic Platform", layout="wide")

# 시노텍 로고 칼라 #1A729A 및 타이틀 크기 최적화 CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* 타이틀 크기 축소 및 컬러 적용 */
    h1 { 
        color: #1A729A !important; 
        font-weight: 700 !important; 
        font-size: 1.6rem !important; /* 대표님 요청에 따라 더 슬림하게 조정 */
        border-bottom: 2px solid #1A729A; 
        padding-bottom: 8px; 
    }
    
    h2, h3 { color: #1A729A !important; font-weight: 600 !important; }
    
    /* 버튼 스타일 커스텀: #1A729A */
    .stButton>button {
        background-color: #1A729A;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #145d7d;
        color: #ffffff;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #f1f6f9; border-right: 1px solid #1A729A; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    init_db()
    log_action("System", "SynoBlue Production Version Online")
    st.session_state.initialized = True

# --- [2. 다국어 사전 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "subtitle": "Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence Report (PDF)"
    },
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 설계 인텔리전스",
        "subtitle": "Woosuk Choi & SeoYeon Choi 공동 개발 | 시노텍 주식회사",
        "btn_run": "🚀 전략적 분석 실행",
        "res_h": "📊 설계 성능 핵심 지표",
        "pdf_btn": "📥 전문가용 인텔리전스 리포트 다운로드 (PDF)"
    }
}

if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}

# --- [3. 사이드바: 관리자 로그인] ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: #1A729A;'>SynoTech</h2>", unsafe_allow_html=True)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    st.divider()
    u_id = st.text_input("Admin ID", key="admin_id")
    u_pw = st.text_input("Password", type="password", key="admin_pw")
    st.session_state.admin_mode = verify_admin_access(u_id, u_pw)
    if st.session_state.admin_mode: st.success("✅ MASTER AUTHORIZED")
    st.divider()
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [4. 메인 화면: 설계 입력 및 분석] ---
st.title(T["title"])
st.write(f"*{T['subtitle']}*")
st.markdown("---")

in_c1, in_c2, in_c3, in_c4 = st.columns(4)
loading = in_c1.number_input("Loading (mg/cm²)", value=12.0)
capacity = in_c2.number_input("Cap. (mAh/g)", value=140.0)
area = in_c3.number_input("Area (cm²)", value=10.0)
np_ratio = in_c4.number_input("N/P Ratio", value=1.1)

if st.button(T["btn_run"], type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        log_action("User", f"Run: {res['specific_energy']} Wh/kg")
        
        st.subheader(T["res_h"])
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        m_c2.metric("Specific Energy", f"{res['specific_energy']} Wh/kg")
        m_c3.metric("Total Capacity", f"{res['total_capacity']} mAh")
        m_c4.metric("Anode Target", f"{res['required_anode']} mg/cm²")
        
        if st.session_state.is_pro:
            st.divider()
            res.update({'loading': loading, 'np_ratio': np_ratio})
            u_name = st.session_state.user_info.get("name", "Expert")
            u_comp = st.session_state.user_info.get("company", "Syno Partner")
            pdf_bytes = generate_expert_report(res, u_name, u_comp)
            st.download_button(T["pdf_btn"], pdf_bytes, f"SynoCore_{u_name}.pdf", use_container_width=True)
            st.balloons()
        else:
            if st.button("🚀 Unlock Pro for PDF Report"): st.session_state.show_upgrade = True
    else:
        st.error("Free trial limit reached.")

# 전문가 등록 폼
if st.session_state.show_upgrade and not st.session_state.is_pro:
    with st.form("enroll"):
        st.subheader("🚀 Register Professional Access")
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

# --- [5. Command Center] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    st.header(f"🛡️ Command Center")
    audit_df = get_audit_logs()
    st.dataframe(audit_df[audit_df['user'] != 'System'], use_container_width=True)
    st.dataframe(get_leads(), use_container_width=True)