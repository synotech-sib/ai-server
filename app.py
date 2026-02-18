import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
from logic_engine import calculate_battery_specs
from database import init_db, save_lead, get_leads

# --- [1. 시스템 초기화] ---
st.set_page_config(page_title="Sinocore V1.2 | SYNOTECH", layout="wide")
init_db()

if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False

# --- [2. PDF 및 그래프 유틸리티] ---

def generate_pdf(res, name, company):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt="SYNOTECH - Sinocore Strategic Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Client: {name} / {company}", ln=True)
    pdf.cell(200, 10, txt=f"Report Date: {time.strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="[Key Analysis Results]", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Areal Capacity: {res['areal_capacity']} mAh/cm2", ln=True)
    pdf.cell(200, 10, txt=f"- Total Design Capacity: {res['total_capacity']} mAh", ln=True)
    pdf.cell(200, 10, txt=f"- Target Anode Loading: {res['required_anode']} mg/cm2", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, txt="This document is confidential. All rights reserved by SYNOTECH Corp.")
    return pdf.output(dest='S').encode('latin-1')

def display_prediction_chart(is_blur=False):
    cycles = np.linspace(0, 2000, 100)
    retention = 100 - (cycles**1.18 / 650) 
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(cycles, retention, label='Capacity Retention', color='#1f77b4', linewidth=2.5)
    ax.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='EOL (80%)')
    ax.set_ylim(60, 105)
    ax.set_xlabel('Cycles')
    ax.set_ylabel('Retention (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if is_blur:
        st.markdown("<div style='filter: blur(8px); pointer-events: none;'>", unsafe_allow_html=True)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.pyplot(fig)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    # use_container_width로 경고 해결
    st.image("https://via.placeholder.com/200x60?text=SYNOTECH", use_container_width=True)
    lang = st.selectbox("🌐 Language", ["한국어", "English"])
    
    st.divider()
    if not st.session_state.is_pro:
        st.metric("Free Trials Remaining", f"{st.session_state.trials} / 3")
    else:
        st.success("✅ PROFESSIONAL ACCESS ACTIVE")
    
    st.divider()
    with st.expander("⚖️ System & IP Information"):
        st.write("**Woo-seok Choi** (CEO / Battery Logic)")
        st.write("**Seo-yeon Choi** (Marketing / Implementation)")
        st.caption("Patent Pending: SIB-2026-SYNO-01")

    # 관리자 비밀번호 적용
    st.divider()
    admin_pw = st.text_input("Admin Access", type="password")
    if admin_pw == "synotech0773!":
        st.session_state.admin_mode = True
    else:
        st.session_state.admin_mode = False

# --- [4. 메인 화면 구성] ---
st.title("Sinocore V1.2: AI-Driven SIB Analysis")
st.markdown("---")

col_in1, col_in2 = st.columns(2)
with col_in1:
    loading = st.number_input("Cathode Loading (mg/cm²)", value=12.0)
    capacity = st.number_input("Spec. Capacity (mAh/g)", value=140.0)
with col_in2:
    area = st.number_input("Electrode Area (cm²)", value=10.0)
    np_ratio = st.number_input("Target N/P Ratio", value=1.1)

if st.button("🚀 RUN STRATEGIC SIMULATION", use_container_width=True, type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        
        st.success("Analysis Complete!")
        c1, c2, c3 = st.columns(3)
        c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        c2.metric("Total Design Cap.", f"{res['total_capacity']} mAh")
        c3.metric("Anode Load Target", f"{res['required_anode']} mg/cm²")
        
        st.markdown("### 🔬 Professional Predictive Report")
        if not st.session_state.is_pro:
            display_prediction_chart(is_blur=True)
            if st.button("Upgrade to Professional to Unlock PDF Report", use_container_width=True):
                st.session_state.show_upgrade = True
        else:
            display_prediction_chart(is_blur=False)
            # PDF 다운로드 활성화
            pdf_bytes = generate_pdf(res, "Professional User", "SYNOTECH Client")
            st.download_button(
                label="📥 Download Official Analysis Report (PDF)",
                data=pdf_bytes,
                file_name="Sinocore_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.balloons()
    else:
        st.error("Free trials exhausted.")

# --- [5. 전문가 등록 및 관리자 모드] ---
if st.session_state.show_upgrade and not st.session_state.is_pro:
    with st.form("enroll_form"):
        st.subheader("🚀 Professional Account Upgrade")
        f_name = st.text_input("Name *")
        f_comp = st.text_input("Company *")
        f_mob  = st.text_input("Mobile *")
        f_email = st.text_input("Email *")
        if st.form_submit_button("Submit & Unlock Access"):
            if f_name and f_comp and f_mob and f_email:
                save_lead(f_name, f_comp, f_mob, f_email)
                st.session_state.is_pro = True
                st.session_state.show_upgrade = False
                st.rerun()

if st.session_state.get('admin_mode', False):
    st.divider()
    st.subheader("📊 Lead Management (Admin Only)")
    leads_df = get_leads()
    st.dataframe(leads_df, use_container_width=True)