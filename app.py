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

# --- [1. 시스템 초기화] ---
st.set_page_config(page_title="SynoCore V1.2 | Security Enforced", layout="wide")

if 'initialized' not in st.session_state:
    init_db()
    log_action("System", f"Core Bootup (Mode: {SECURITY_MODE})")
    st.session_state.initialized = True

# UI 클리닝
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- [2. 다국어 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: AI-Driven SIB Analysis",
        "subtitle": "Developed by Woosuk Choi & SeoYeon Choi",
        "btn_run": "🚀 RUN STRATEGIC SIMULATION",
        "admin_id": "Admin ID",
        "admin_pw": "Security Password",
        "auth_success": "🔓 ACCESS GRANTED",
        "auth_fail": "🔒 UNAUTHORIZED ID",
        "pro_h": "🔬 Professional Predictive Report",
        "pdf_btn": "📥 Download Official Analysis Report (PDF)"
    },
    "한국어": {
        "title": "SynoCore V1.2: AI 기반 SIB 분석 플랫폼",
        "subtitle": "Woosuk Choi & SeoYeon Choi 공동 개발",
        "btn_run": "🚀 전략적 시뮬레이션 실행",
        "admin_id": "관리자 ID",
        "admin_pw": "보안 비밀번호",
        "auth_success": "🔓 관리자 권한 승인됨",
        "auth_fail": "🔒 미승인 ID 또는 비밀번호",
        "pro_h": "🔬 전문가용 정밀 분석 리포트",
        "pdf_btn": "📥 공식 분석 보고서 다운로드 (PDF)"
    }
}

# 세션 상태 관리
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}

# --- [3. 사이드바: Security Barrier 적용] ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=SynoTech", use_container_width=True)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    st.markdown(f"**🛡️ Security Barrier: {SECURITY_MODE}**")
    
    # [Step 4 핵심] ID 화이트리스트 대조 로그인
    input_id = st.text_input(T["admin_id"])
    input_pw = st.text_input(T["admin_pw"], type="password")
    
    if input_id and input_pw:
        if verify_admin_access(input_id, input_pw):
            st.session_state.admin_mode = True
            st.success(f"{T['auth_success']} ({input_id})")
            # 관리자 접속 로그 기록
            if 'last_admin_log' not in st.session_state or st.session_state.last_admin_log != input_id:
                log_action(input_id, "Admin Level Access Authenticated")
                st.session_state.last_admin_log = input_id
        else:
            st.session_state.admin_mode = False
            st.error(T["auth_fail"])
    else:
        st.session_state.admin_mode = False
    
    st.divider()
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [4. 메인 화면 및 분석 로직] ---
st.title(T["title"])
st.write(f"**{T['subtitle']}**")
st.markdown("---")

# 입력창 (4컬럼 배치)
in_c1, in_c2, in_c3, in_c4 = st.columns(4)
loading = in_c1.number_input("Loading (mg/cm²)", value=12.0)
capacity = in_c2.number_input("Capacity (mAh/g)", value=140.0)
area = in_c3.number_input("Area (cm²)", value=10.0)
np_ratio = in_c4.number_input("N/P Ratio", value=1.1)

if st.button(T["btn_run"], use_container_width=True, type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        
        st.subheader("📊 Analysis Results")
        res_c1, res_c2, res_c3 = st.columns(3)
        res_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        res_c2.metric("Total Design Cap.", f"{res['total_capacity']} mAh")
        res_c3.metric("Anode Load Target", f"{res['required_anode']} mg/cm²")
        
        if st.session_state.is_pro:
            st.divider()
            st.subheader(T["pro_h"])
            # 전문 보고서 생성 (Step 2 연동)
            res.update({'loading': loading, 'np_ratio': np_ratio})
            u_name = st.session_state.user_info.get("name", "Expert")
            u_comp = st.session_state.user_info.get("company", "Partner")
            pdf_bytes = generate_expert_report(res, u_name, u_comp)
            st.download_button(T["pdf_btn"], pdf_bytes, "Expert_Report.pdf", use_container_width=True)
            st.balloons()
        else:
            if st.button("Unlock Full Report"): st.session_state.show_upgrade = True
    else:
        st.error("Free trial limit reached. Please register.")

# 전문가 등록 폼 (생략 - 기존 유지)
if st.session_state.show_upgrade and not st.session_state.is_pro:
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

# --- [5. Step 4: Security Barrier Command Center] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    # 관리자 전용 UI (동적 분리)
    st.header(f"🛡️ Command Center: {input_id} (Master)")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Audit Status", "SECURE", delta="Live Monitoring")
    m2.metric("Partner Leads", len(get_leads()))
    m3.metric("System Uptime", "99.9%")

    tab1, tab2 = st.tabs(["📊 Data Monitoring", "📥 Export Center"])
    
    with tab1:
        st.write("### Real-time Partner Pipeline")
        st.dataframe(get_leads(), use_container_width=True)
    
    with tab2:
        st.write("### Sensitive Data Extraction")
        ex_c1, ex_c2 = st.columns(2)
        ex_c1.download_button("📥 Audit Log CSV", get_audit_logs().to_csv(index=False), f"audit_{int(time.time())}.csv")
        ex_c2.download_button("📥 Feature Lake (Leads)", get_leads().to_csv(index=False), "leads.csv")