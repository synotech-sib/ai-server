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
st.set_page_config(page_title="SynoCore V1.2 | SynoTech Strategic Platform", layout="wide")

# CSS 정밀 조정: 로고 강조(2.2rem), 메인 타이틀(1.1rem/Black), 크레딧 폰트 동기화
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* [수정] 메인 타이틀: 로고(2.2rem)보다 확실히 작은 1.1rem, 색상 검정 */
    .main h1 { 
        color: #000000 !important; 
        font-weight: 700 !important; 
        font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; 
        padding-bottom: 5px; 
        margin-bottom: 30px;
    }
    
    h2, h3 { color: #1A729A !important; font-weight: 600 !important; }
    
    /* 버튼 스타일: 시노텍 블루 (#1A729A) */
    .stButton>button {
        background-color: #1A729A;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #145d7d; color: #ffffff; }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #f1f6f9; border-right: 1px solid #1A729A; }
    
    /* Developer Credits 라벨: "Language" 라벨 크기와 동일하게 (0.8rem) */
    .streamlit-expanderHeader p {
        font-size: 0.8rem !important;
        color: #1A729A !important;
        font-weight: 400 !important;
    }
    
    /* Developer Credits 내용 크기: 더 작게 (0.7rem) */
    .streamlit-expanderContent {
        font-size: 0.7rem !important;
        line-height: 1.1 !important;
        color: #555555;
    }

    /* 하단 화이트 라벨링 제거 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    try:
        init_db()
        log_action("System", "SynoCore V1.2.9 AI Diagnostic Engine Online")
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

# 세션 상태 관리 (Step 9 비교 기능을 위한 last_res 추가)
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}
if 'last_res' not in st.session_state: st.session_state.last_res = None

# --- [3. 사이드바: 브랜드 로고 및 메뉴] ---
with st.sidebar:
    # 주인공 로고 (2.2rem, 시노텍 블루)
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    
    # Language 선택 (라벨 크기 기준점)
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    u_id = st.text_input("Admin ID", key="admin_id")
    u_pw = st.text_input("Password", type="password", key="admin_pw")
    st.session_state.admin_mode = verify_admin_access(u_id, u_pw)
    if st.session_state.admin_mode: st.success("✅ MASTER AUTHORIZED")
    
    st.divider()
    # 크레딧 섹션: Language 라벨과 크기 맞춤 (0.8rem)
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [4. 메인 화면: 분석 및 진단 인터페이스] ---
st.title(T["title"]) # 1.1rem / Black 적용
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
            # 4.1. 기본 엔진 호출
            res = calculate_battery_specs(loading, capacity, area, np_ratio)
            log_action("User", f"Run: {res['specific_energy']} Wh/kg")
            
            # 4.2. [Step 9] AI 안정성 진단 로직
            stability_score = 100
            alerts = []
            
            if np_ratio < 1.05:
                stability_score -= 30
                alerts.append("🚨 **N/P Ratio 위험:** 덴드라이트 형성 및 화재 위험이 매우 높습니다.")
            elif np_ratio > 1.25:
                stability_score -= 10
                alerts.append("ℹ️ **N/P Ratio 과다:** 불필요한 무게 증가로 에너지 밀도가 감소합니다.")
            
            if loading > 20:
                stability_score -= 15
                alerts.append("⚠️ **고로딩 경고:** 전해질 침투 저하 및 출력 특성 저하가 우려됩니다.")

            # 4.3. 결과 지표 표시
            st.subheader(T["res_h"])
            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            m_c1.metric("Areal Capacity", f"{res['areal_capacity']} mAh/cm²")
            
            # [Step 9] 비교 분석 연동 에너지 밀도
            delta_val = None
            if st.session_state.last_res:
                delta_val = f"{res['specific_energy'] - st.session_state.last_res['specific_energy']:+.1f} Wh/kg"
            m_c2.metric("Specific Energy", f"{res['specific_energy']} Wh/kg", delta=delta_val)
            
            m_c3.metric("Total Capacity", f"{res['total_capacity']} mAh")
            m_c4.metric("Anode Target", f"{res['required_anode']} mg/cm²")

            st.divider()

            # 4.4. [Step 9] AI 분석 섹션 표시
            st.subheader("🤖 SynoCore AI Design Insight")
            s_c1, s_c2 = st.columns([1, 2])
            
            with s_c1:
                st.metric("Design Stability Score", f"{stability_score} / 100")
                if stability_score >= 80: st.success("✅ 설계가 안정적입니다.")
                elif stability_score >= 60: st.warning("⚠️ 보완이 권장됩니다.")
                else: st.error("🚨 위험한 설계입니다.")

            with s_c2:
                if alerts:
                    for alert in alerts: st.write(alert)
                else:
                    st.write("✨ 현재 설계는 시노텍 표준 가이드라인을 완벽히 준수하고 있습니다.")
            
            # 결과 저장 (다음 시뮬레이션 비교용)
            st.session_state.last_res = res

            # 4.5. 리포트 및 전문가 전용 기능
            if st.session_state.is_pro:
                st.divider()
                if REPORTER_READY:
                    res.update({'loading': loading, 'np_ratio': np_ratio, 'stability': stability_score})
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
        st.error("Free trial limit reached. Please contact SynoTech admin.")

# 전문가 등록 폼
if st.session_state.show_upgrade and not st.session_state.is_pro:
    st.divider()
    with st.form("enroll"):
        st.subheader("🚀 Register for Professional Access")
        f_name = st.text_input("Name")
        f_comp = st.text_input("Company")
        f_mob = st.text_input("Mobile")
        f_email = st.text_input("Email")
        if st.form_submit_button("Submit & Unlock"):
            save_lead(f_name, f_comp, f_mob, f_email)
            st.session_state.user_info = {"name": f_name, "company": f_comp}
            st.session_state.is_pro = True
            st.session_state.show_upgrade = False
            st.rerun()

# --- [5. Command Center (Step 8: 시각화 대시보드 유지)] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    st.header(f"🛡️ SynoCore Intelligence Dashboard")
    
    leads_df = get_leads()
    audit_df = get_audit_logs()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Partners", f"{len(leads_df)} Leads")
    kpi2.metric("Total Sims", f"{len(audit_df[audit_df['action'].str.contains('Run', na=False)])} Hits")
    kpi3.metric("System Status", "Stable")
    kpi4.metric("Security Mode", "Whitelist")

    tab_chart, tab_log, tab_lead = st.tabs(["📈 Analytics", "📜 Audit Logs", "📊 Leads Data"])
    
    with tab_chart:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏢 Partner Company Stats")
            if not leads_df.empty: st.bar_chart(leads_df['company'].value_counts())
            else: st.info("데이터가 없습니다.")
        with c2:
            st.subheader("⚡ Energy Density Trends")
            sim_logs = audit_df[audit_df['action'].str.contains('Wh/kg', na=False)]
            if not sim_logs.empty:
                sim_logs['val'] = sim_logs['action'].str.extract(r'(\d+\.?\d*)').astype(float)
                st.line_chart(sim_logs['val'])
            else: st.info("시뮬레이션 기록이 없습니다.")

    with tab_log:
        show_human = st.checkbox("Human Activity Only", value=True)
        display_df = audit_df[audit_df['user'] != 'System'] if show_human else audit_df
        st.dataframe(display_df, use_container_width=True)
    
    with tab_lead:
        st.dataframe(leads_df, use_container_width=True)