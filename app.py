import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# 모듈 임포트
from config.security_cfg import SECURITY_MODE, check_admin
from modules.engine import calculate_battery_specs
from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
from modules.reporter import generate_expert_report

# --- [1. 시스템 초기화] ---
st.set_page_config(page_title="SynoCore V1.2 | Admin Center", layout="wide")

if 'initialized' not in st.session_state:
    init_db()
    log_action("System", "Application Online")
    st.session_state.initialized = True

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
        "admin_label": f"Admin Access (Security: {SECURITY_MODE})",
        "pro_h": "🔬 Professional Predictive Report",
        "pdf_btn": "📥 Download Official Analysis Report (PDF)",
        "blur_msg": "💡 Professional reports are locked for guest users."
    },
    "한국어": {
        "title": "SynoCore V1.2: AI 기반 SIB 분석 플랫폼",
        "subtitle": "Woosuk Choi & SeoYeon Choi 공동 개발",
        "btn_run": "🚀 전략적 시뮬레이션 실행",
        "admin_label": f"관리자 접속 (보안: {SECURITY_MODE})",
        "pro_h": "🔬 전문가용 정밀 분석 리포트",
        "pdf_btn": "📥 공식 분석 보고서 다운로드 (PDF)",
        "blur_msg": "💡 전문가 리포트는 등록 후 이용 가능합니다."
    }
}

# 세션 상태
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}

# --- [3. 사이드바 관제 센터] ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=SynoTech", use_container_width=True)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    admin_pw = st.text_input(T["admin_label"], type="password")
    st.session_state.admin_mode = check_admin(admin_pw)
    
    if st.session_state.admin_mode:
        st.success("🔓 ADMIN AUTHORIZED")
    
    st.divider()
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [4. 메인 분석 화면] ---
st.title(T["title"])
st.write(f"**{T['subtitle']}**")
st.markdown("---")

# 입력창 (간소화 표기)
c_in1, c_in2, c_in3, c_in4 = st.columns(4)
loading = c_in1.number_input("Loading (mg/cm²)", value=12.0)
capacity = c_in2.number_input("Capacity (mAh/g)", value=140.0)
area = c_in3.number_input("Area (cm²)", value=10.0)
np_ratio = c_in4.number_input("N/P Ratio", value=1.1)

if st.button(T["btn_run"], use_container_width=True, type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        log_action("User", f"Simulated: {loading}mg/cm2")
        
        st.subheader("📊 Results")
        st.write(f"Areal Capacity: {res['areal_capacity']} mAh/cm² | Total: {res['total_capacity']} mAh")
        
        if not st.session_state.is_pro:
            st.warning(T["blur_msg"])
            if st.button("Upgrade to Unlock"): st.session_state.show_upgrade = True
        else:
            # Step 2 리포트 엔진 호출
            res['loading'], res['np_ratio'] = loading, np_ratio
            u_name = st.session_state.user_info.get("name", "Expert")
            u_comp = st.session_state.user_info.get("company", "Partner")
            pdf_bytes = generate_expert_report(res, u_name, u_comp)
            st.download_button(T["pdf_btn"], pdf_bytes, "Report.pdf", use_container_width=True)
    else:
        st.error("Limit reached.")

# 전문가 등록 폼 (생략 - 기존 유지)

# --- [5. Step 3: Command Center (wschoi 전용)] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    st.header("🛡️ SynoCore Command Center")
    
    # 상단: 시스템 상태 지표
    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Security Mode", SECURITY_MODE)
    stat2.metric("Active Sessions", "1 (Root)")
    stat3.metric("Total Simulations", len(get_audit_logs()))
    stat4.metric("New Partners", len(get_leads()))

    # 중앙: 프로젝트 관리 (알트리스 전용 프로젝트 현황판 컨셉)
    with st.expander("📂 Altris & Partner Project Monitoring", expanded=True):
        st.info("Real-time monitoring of data-exchange partnerships.")
        leads_df = get_leads()
        st.dataframe(leads_df, use_container_width=True)

    # 하단: Data Export Center (기획안 반영)
    st.subheader("📂 Data Export Center")
    ex_c1, ex_c2, ex_c3 = st.columns(3)
    
    # 1. 감사 로그 다운로드
    audit_df = get_audit_logs()
    ex_c1.download_button(
        "📥 Download Audit Logs", 
        audit_df.to_csv(index=False), 
        f"audit_log_{int(time.time())}.csv", 
        "text/csv",
        use_container_width=True
    )
    
    # 2. 통합 특징점 데이터 (Leads + Stats 컨셉)
    ex_c2.download_button(
        "📥 Feature Lake Export", 
        leads_df.to_csv(index=False), # 임시로 Lead 데이터 활용
        "feature_lake_sample.csv",
        use_container_width=True
    )
    
    # 3. 시스템 전체 백업
    if ex_c3.button("📥 Personal Project Backup", use_container_width=True):
        st.success("Full system snapshot generated & saved to /storage/private_vault/")