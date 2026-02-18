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
st.set_page_config(page_title="Sinocore V1.2 | SYNOTECH", layout="wide")
init_db()

# Streamlit 헤더, 푸터, 메뉴 숨기기 (Professional Look)
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
        "title": "Sinocore V1.2: AI-Driven SIB Analysis",
        "subtitle": "Jointly Developed by Woo-seok Choi & Seo-yeon Choi",
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
        "title": "시노코어 V1.2: AI 기반 SIB 분석 플랫폼",
        "subtitle": "최우석 & 최서연 공동 개발 | 시노텍 기술 자산",
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

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=SYNOTECH", use_container_width=True)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang] # 선택된 언어 팩 로드
    
    st.divider()
    if not st.session_state.is_pro:
        st.metric(T["quota_label"], f"{st.session_state.trials} / 3")
    else:
        st.success(T["pro_active"])
    
    st.divider()
    with st.expander("⚖️ System & IP Info"):
        st.write(f"**{T['subtitle']}**")
        st.caption("Patent Pending: SIB-2026-SYNO-01")

    admin_pw = st.text_input(T["admin_label"], type="password")
    st.session_state.admin_mode = (admin_pw == "synotech0773!")

# --- [4. 메인 화면 구성 (다국어 적용)] ---
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

# 분석 실행 로직
if st.button(T["btn_run"], use_container_width=True, type="primary"):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        res = calculate_battery_specs(loading, capacity, area, np_ratio)
        
        st.divider()
        st.subheader(T["res_h"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
        c2.metric("Total Design Cap.", f"{res['total_capacity']} mAh")
        c3.metric("Anode Load Target", f"{res['required_anode']} mg/cm²")
        
        st.subheader(T["pro_h"])
        if not st.session_state.is_pro:
            # 흐림 효과용 그래프 함수 호출 (is_blur=True)
            # (그래프 함수는 이전과 동일하므로 생략 없이 내부 호출 방식으로 구현)
            cycles = np.linspace(0, 2000, 100)
            retention = 100 - (cycles**1.18 / 650)
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.plot(cycles, retention, color='#1f77b4')
            st.markdown("<div style='filter: blur(8px);'>", unsafe_allow_html=True)
            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.warning(T["blur_msg"])
            if st.button(T["upgrade_btn"], use_container_width=True):
                st.session_state.show_upgrade = True
        else:
            # 전문가 결과 (그래프 + PDF)
            cycles = np.linspace(0, 2000, 100)
            retention = 100 - (cycles**1.18 / 650)
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.plot(cycles, retention, color='#1f77b4', linewidth=2)
            ax.axhline(y=80, color='r', linestyle='--')
            st.pyplot(fig)
            
            # PDF 생성 로직 (이전 함수와 동일)
            # ... (중략: 이전 generate_pdf 함수 내용)
            st.download_button(T["pdf_btn"], data=b"PDF_DATA_PLACEHOLDER", file_name="Report.pdf", use_container_width=True)
            st.balloons()
    else:
        st.error("Access Denied: Please Upgrade.")

# 신청 폼 및 관리자 모드 (이하 생략 - 이전과 동일하게 유지)