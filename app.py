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
st.set_page_config(
    page_title="SynoCore V1.2 | SynoTech Strategic Platform", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# CSS: 디자인 위계 및 사이드바 복구 완료
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* 메인 타이틀: 로고(2.2rem)보다 작은 1.1rem, 검정색 */
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
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { 
        background-color: #f1f6f9; 
        border-right: 2px solid #1A729A; 
    }
    
    /* 크레딧 폰트 설정 (Language 라벨과 동기화) */
    .streamlit-expanderHeader p { font-size: 0.9rem !important; color: #1A729A !important; }
    .streamlit-expanderContent { font-size: 0.75rem !important; color: #555555; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    try:
        init_db()
        log_action("System", "SynoCore V1.2.10 Optimization Engine Online")
        st.session_state.initialized = True
    except: pass

# --- [2. 다국어 사전 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence Report (PDF)",
        "chart_h": "📈 Design Sensitivity Analysis (Loading vs Wh/kg)"
    },
    "한국어": {
        "title": "SynoCore V1.2: 전략적 SIB 설계 인텔리전스",
        "btn_run": "🚀 전략적 분석 실행",
        "res_h": "📊 설계 성능 핵심 지표",
        "pdf_btn": "📥 전문가용 인텔리전스 리포트 다운로드 (PDF)",
        "chart_h": "📈 설계 민감도 분석 (로딩량 vs 에너지 밀도)"
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

if st.button(T["btn_run"], type="primary", use_container_width=True):
    if st.session_state.trials > 0 or st.session_state.is_pro:
        if not st.session_state.is_pro: st.session_state.trials -= 1
        
        try:
            # 4.1. 메인 결과 계산
            res = calculate_battery_specs(loading, capacity, area, np_ratio)
            log_action("User", f"Run: {res['specific_energy']} Wh/kg")
            
            # 4.2. 핵심 지표 렌더링
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

            # 4.3. [Step 10] 설계 민감도 분석 (곡선 그래프)
            st.subheader(T["chart_h"])
            
            # 로딩량 변화에 따른 데이터 생성 (5 ~ 35 mg/cm²)
            load_range = np.linspace(5, 35, 20)
            energy_trend = []
            for l in load_range:
                temp_res = calculate_battery_specs(l, capacity, area, np_ratio)
                energy_trend.append(temp_res['specific_energy'])
            
            chart_data = pd.DataFrame({
                'Loading (mg/cm²)': load_range,
                'Energy Density (Wh/kg)': energy_trend
            }).set_index('Loading (mg/cm²)')
            
            st.line_chart(chart_data)
            st.info("💡 위 그래프는 현재 고정된 N/P Ratio와 용량 조건에서 로딩량 변화에 따른 최적 에너지 밀도 추이를 보여줍니다.")

            st.divider()

            # 4.4. [Step 9] AI 디자인 인사이트
            st.subheader("🤖 SynoCore AI Design Insight")
            s_c1, s_c2 = st.columns([1, 2])
            
            with s_c1:
                score = 100
                if np_ratio < 1.05: score -= 30
                if loading > 22: score -= 20
                st.metric("Design Stability Score", f"{score} / 100")
                if score >= 80: st.success("✅ 안정적인 설계 범위입니다.")
                elif score >= 60: st.warning("⚠️ 공정 난이도가 예상됩니다.")
                else: st.error("🚨 실험 전 재검토가 필요합니다.")

            with s_c2:
                if np_ratio < 1.05: st.write("🚨 **Danger:** N/P Ratio가 너무 낮아 전극 표면 리튬 석출(Plating) 위험이 있습니다.")
                if loading > 22: st.write("⚠️ **Warning:** 고로딩 설계로 인해 급속 충전 시 성능 저하가 발생할 수 있습니다.")
                if score == 100: st.write("✨ 시노텍의 표준 권장 설계 가이드를 완벽히 충족합니다.")
            
            st.session_state.last_res = res

            # 4.5. 프로 전용 리포트
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
                if st.button("🚀 Upgrade to Pro for AI Expert Report"): 
                    st.session_state.show_upgrade = True
        except Exception as e:
            st.error(f"분석 엔진 처리 중 오류 발생: {e}")
    else:
        st.error("Free trial limit reached. Please contact SynoTech Admin.")

# 전문가 등록 폼
if st.session_state.show_upgrade and not st.session_state.is_pro:
    st.divider()
    with st.form("enroll"):
        st.subheader("🚀 Join SynoTech Expert Partnership")
        f_name = st.text_input("Name")
        f_comp = st.text_input("Company")
        f_mob = st.text_input("Mobile")
        f_email = st.text_input("Email")
        if st.form_submit_button("Unlock Professional Version"):
            save_lead(f_name, f_comp, f_mob, f_email)
            st.session_state.user_info = {"name": f_name, "company": f_comp}
            st.session_state.is_pro = True
            st.session_state.show_upgrade = False
            st.rerun()

# --- [5. Command Center] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    st.header(f"🛡️ SynoCore Intelligence Dashboard")
    leads_df = get_leads()
    audit_df = get_audit_logs()
    
    t1, t2, t3 = st.tabs(["📊 Analytics", "📜 Audit Logs", "👥 Partner Leads"])
    with t1:
        if not leads_df.empty: st.bar_chart(leads_df['company'].value_counts())
        else: st.info("No lead data yet.")
    with t2: st.dataframe(audit_df, use_container_width=True)
    with t3: st.dataframe(leads_df, use_container_width=True)