import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# [Step 1 & 2] 모듈화된 파일들로부터 기능 불러오기
from config.security_cfg import SECURITY_MODE, check_admin
from modules.engine import calculate_battery_specs
from modules.database import init_db, save_lead, get_leads, log_action
from modules.reporter import generate_expert_report

# --- [1. 시스템 초기화 및 보안 설정] ---
st.set_page_config(page_title="SynoCore V1.2 | SynoTech", layout="wide")

# 앱 시작 시 시스템 초기화 및 로그 기록
if 'initialized' not in st.session_state:
    init_db()
    log_action("System", "Application Global Startup")
    st.session_state.initialized = True

# 화이트 라벨링: 전문 소프트웨어 느낌을 위해 Streamlit 기본 UI 숨기기
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- [2. 다국어 사전 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: AI-Driven SIB Analysis",
        "subtitle": "Developed by Woosuk Choi & SeoYeon Choi",
        "input_h1": "📥 Material Parameters",
        "input_h2": "⚙️ Design Targets",
        "label_loading": "Cathode Loading (mg/cm²)",
        "label_cap": "Spec. Capacity (mAh/g)",
        "label_area": "Electrode Area (cm²)",
        "label_np": "Target N/P Ratio",
        "btn_run": "🚀 RUN STRATEGIC SIMULATION",
        "res_h": "📊 Basic Conversion Results",
        "pro_h": "🔬 Professional Predictive Report",
        "blur_msg": "💡 Full degradation curves and PDF reports are locked.",
        "upgrade_btn": "Upgrade to Professional to Unlock",
        "pdf_btn": "📥 Download Official Analysis Report (PDF)",
        "admin_label": f"Admin Access (Security: {SECURITY_MODE})",
        "quota_label": "Free Trials Remaining",
        "pro_active": "✅ PROFESSIONAL ACCESS ACTIVE"
    },
    "한국어": {
        "title": "SynoCore V1.2: AI 기반 SIB 분석 플랫폼",
        "subtitle": "Woosuk Choi & SeoYeon Choi 공동 개발",
        "input_h1": "📥 소재 파라미터 입력",
        "input_h2": "⚙️ 설계 목표 설정",
        "label_loading": "양극 로딩량 (mg/cm²)",
        "label_cap": "양극 비용량 (mAh/g)",
        "label_area": "전극 면적 (cm²)",
        "label_np": "목표 N/P Ratio",
        "btn_run": "🚀 전략적 시뮬레이션 실행",
        "res_h": "📊 기본 환산 결과",
        "pro_h": "🔬 전문가용 정밀 분석 리포트",
        "blur_msg": "💡 상세 열화 곡선 및 PDF 리포트는 잠겨 있습니다.",
        "upgrade_btn": "전문가 계정으로 업그레이드하여 잠금 해제",
        "pdf_btn": "📥 공식 분석 보고서 다운로드 (PDF)",
        "admin_label": f"관리자 접속 (보안 모드: {SECURITY_MODE})",
        "quota_label": "남은 무료 분석 횟수",
        "pro_active": "✅ 전문가 계정 활성화됨"
    }
}

# 세션 상태 초기화
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}

# --- [3. 시각화 컴포넌트] ---
def display_prediction_chart(is_blur=False):
    cycles = np.linspace(0, 2000, 100)
    retention = 100 - (cycles**1.18 / 650) 
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(cycles, retention, color='#1f77b4', linewidth=2.5, label='SOH Prediction')
    ax.axhline(y=80, color='red', linestyle='--', alpha=0.6)
    ax.set_ylim(60, 105)
    ax.set_ylabel("Retention (%)")
    ax.set_xlabel("Cycles")
    ax.grid(True, alpha=0.2)
    
    if is_blur:
        st.markdown("<div style='filter: blur(8px); pointer-events: none;'>", unsafe_allow_html=True)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.pyplot(fig)

# --- [4. 사이드바 관제 센터] ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=SynoTech", use_container_width=True)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    if not st.session_state.is_pro:
        st.metric(T["quota_label"], f"{st.session_state.trials} / 3")
    else:
        st.success(T["pro_active"])
    
    st.divider()
    with st.expander("⚖️ System & IP Info"):
        st.write(f"**{T['subtitle']}**")
        st.caption("Patent Pending: SIB-2026-SYNO-01")
        st.caption("© 2026 SynoTech Co., Ltd.")

    # 관리자 로그인 (보안 로직 적용)
    admin_pw = st.text_input(T["admin_label"], type="password")
    if check_admin(admin_pw):
        st.session_state.admin_mode = True
    else:
        st.session_state.admin_mode = False

# --- [5. 메인 레이아웃 및 분석 로직] ---
st.title(T["title"])
st.write(f"**{T['subtitle']}**")
st.markdown("---")

col_in1, col_in2 = st.columns(2)
with col_in1:
    st.subheader(T["input_h1"])
    loading = st.number_input(T["label_loading"], value=12.0)
    capacity = st.number_input(T["label_cap"], value=140.0)
with col_in2:
    st.subheader(T["input_h2"])
    area = st.number_input(T["label_area"], value=10.0)
    np_ratio = st.number_input(T["label_np"], value=1.1)

if st.button(T["btn_run"], use_container_width=True, type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        # 시뮬레이션 실행 및 로그 기록
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        log_action("User", f"Simulated: {loading}mg/cm2, {np_ratio}NP")
        
        # 기본 결과 표시
        st.divider()
        st.subheader(T["res_h"])
        res_c1, res_c2, res_c3 = st.columns(3)
        res_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        res_c2.metric("Total Design Cap.", f"{res['total_capacity']} mAh")
        res_c3.metric("Anode Load Target", f"{res['required_anode']} mg/cm²")
        
        # 전문가 리포트 섹션
        st.subheader(T["pro_h"])
        if not st.session_state.is_pro:
            display_prediction_chart(is_blur=True)
            st.warning(T["blur_msg"])
            if st.button(T["upgrade_btn"], use_container_width=True):
                st.session_state.show_upgrade = True
        else:
            display_prediction_chart(is_blur=False)
            
            # [Step 2 적용] 전문 보고서 생성 로직
            res['loading'] = loading
            res['np_ratio'] = np_ratio
            
            # 사용자 정보 세션에서 가져오기
            u_name = st.session_state.user_info.get("name", "Expert User")
            u_comp = st.session_state.user_info.get("company", "SynoTech Partner")
            
            pdf_bytes = generate_expert_report(res, u_name, u_comp)
            
            st.download_button(
                label=T["pdf_btn"],
                data=pdf_bytes,
                file_name=f"SynoCore_Expert_Report_{int(time.time())}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.balloons()
    else:
        st.error("Free trials exhausted. Please contact SynoTech for professional access.")

# --- [6. 전문가 등록 폼] ---
if st.session_state.show_upgrade and not st.session_state.is_pro:
    st.divider()
    with st.form("enroll_form"):
        st.subheader("🚀 Professional Account Upgrade (Open Partnership)")
        f_name = st.text_input("Full Name *")
        f_comp = st.text_input("Company/Institute *")
        f_mob  = st.text_input("Mobile Number *")
        f_email = st.text_input("Official Email *")
        
        if st.form_submit_button("Submit & Unlock Professional Features"):
            if f_name and f_comp and f_mob and f_email:
                save_lead(f_name, f_comp, f_mob, f_email)
                log_action(f_name, "Registered as Professional")
                st.session_state.user_info = {"name": f_name, "company": f_comp}
                st.session_state.is_pro = True
                st.session_state.show_upgrade = False
                st.success(f"Welcome {f_name}, your professional access is now active.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

# --- [7. 관리자 전용 커맨드 센터 (wschoi Only)] ---
if st.session_state.get('admin_mode', False):
    st.divider()
    st.subheader("🛡️ SynoCore Command Center")
    
    # 시스템 상태 요약
    c1, c2, c3 = st.columns(3)
    c1.success(f"Security: {SECURITY_MODE}")
    c2.info("User: wschoi (Root)")
    c3.warning("Audit Log: Active")

    # 가망 고객(Leads) 데이터 대시보드
    st.write("### 📊 Lead Management Dashboard")
    leads_df = get_leads()
    st.dataframe(leads_df, use_container_width=True)
    
    # 데이터 엑셀/CSV 추출 센터
    st.write("### 📂 Data Export Center")
    ex_c1, ex_c2, ex_c3 = st.columns(3)
    ex_c2.download_button("📥 Export Lead Data (CSV)", leads_df.to_csv(index=False), "synotech_leads.csv")
    if ex_c1.button("📥 Download Audit Logs"):
        st.info("Audit Log CSV export will be active in Step 3.")
    ex_c3.button("📥 Backup System Data")