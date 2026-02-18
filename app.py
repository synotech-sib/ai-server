import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
from logic_engine import calculate_battery_specs
from database import init_db, save_lead, get_leads

# --- [1. 시스템 설정 및 UI 숨기기] ---
st.set_page_config(page_title="SynoCore V1.2 | SYNOTECH", layout="wide")
init_db()

# Streamlit 기본 헤더, 푸터, 메뉴 숨기기 (White Labeling)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- [2. 완벽한 다국어 사전] ---
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
        "admin_label": "Admin Access",
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
        "admin_label": "관리자 접속",
        "quota_label": "남은 무료 분석 횟수",
        "pro_active": "✅ 전문가 계정 활성화됨"
    }
}

# 세션 상태 관리
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False

# --- [3. 핵심 유틸리티 함수] ---

def generate_pdf(res, name, company):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt="SYNOTECH - SynoCore Strategic Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Client: {name} / {company}", ln=True)
    pdf.cell(200, 10, txt=f"Report Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="[Analysis Summary]", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Areal Capacity: {res['areal_capacity']} mAh/cm2", ln=True)
    pdf.cell(200, 10, txt=f"- Total Design Capacity: {res['total_capacity']} mAh", ln=True)
    pdf.cell(200, 10, txt=f"- Target Anode Loading: {res['required_anode']} mg/cm2", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, txt="This document is a confidential AI-generated report by SynoCore V1.2. All rights reserved by SYNOTECH Corp.")
    return pdf.output(dest='S').encode('latin-1')

def display_prediction_chart(is_blur=False):
    cycles = np.linspace(0, 2000, 100)
    retention = 100 - (cycles**1.18 / 650) 
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(cycles, retention, label='Capacity Retention', color='#1f77b4', linewidth=2.5)
    ax.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='EOL (80%)')
    ax.set_ylim(60, 105)
    ax.set_xlabel('Cycles')
    ax.set_ylabel('Retention (%)')
    ax.grid(True, alpha=0.3)
    
    if is_blur:
        st.markdown("<div style='filter: blur(8px); -webkit-filter: blur(8px); pointer-events: none;'>", unsafe_allow_html=True)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.pyplot(fig)

# --- [4. 사이드바 구성] ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=SYNOTECH", use_container_width=True)
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
        st.caption("© 2026 SYNOTECH Corp.")

    admin_pw = st.text_input(T["admin_label"], type="password")
    st.session_state.admin_mode = (admin_pw == "synotech0773!")

# --- [5. 메인 화면 구성] ---
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
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        
        st.divider()
        st.subheader(T["res_h"])
        res_c1, res_c2, res_c3 = st.columns(3)
        res_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        res_c2.metric("Total Design Cap.", f"{res['total_capacity']} mAh")
        res_c3.metric("Anode Load Target", f"{res['required_anode']} mg/cm²")
        
        st.subheader(T["pro_h"])
        if not st.session_state.is_pro:
            display_prediction_chart(is_blur=True)
            st.warning(T["blur_msg"])
            if st.button(T["upgrade_btn"], use_container_width=True):
                st.session_state.show_upgrade = True
        else:
            display_prediction_chart(is_blur=False)
            pdf_bytes = generate_pdf(res, "Professional User", "SYNOTECH Client")
            st.download_button(
                label=T["pdf_btn"],
                data=pdf_bytes,
                file_name=f"SynoCore_Report_{int(time.time())}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.balloons()
    else:
        st.error("Free trials exhausted. Please register for a Professional Account.")

# --- [6. 전문가 등록 폼] ---
if st.session_state.show_upgrade and not st.session_state.is_pro:
    st.divider()
    with st.form("enroll_form"):
        st.subheader("🚀 Professional Account Upgrade ($0 Promo)")
        f_name = st.text_input("Full Name *")
        f_comp = st.text_input("Company *")
        f_mob  = st.text_input("Mobile Number *")
        f_email = st.text_input("Official Email *")
        
        if st.form_submit_button("Submit & Unlock Immediate Access"):
            if f_name and f_comp and f_mob and f_email:
                save_lead(f_name, f_comp, f_mob, f_email)
                st.session_state.is_pro = True
                st.session_state.show_upgrade = False
                st.success(f"Welcome, {f_name}! Full access has been granted.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

# --- [7. 관리자 데이터 뷰어] ---
if st.session_state.get('admin_mode', False):
    st.divider()
    st.subheader("📊 Lead Management Dashboard (Admin Only)")
    leads_df = get_leads()
    st.dataframe(leads_df, use_container_width=True)
    st.download_button("Export to CSV", leads_df.to_csv(index=False), "synotech_leads.csv", "text/csv")