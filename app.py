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
# 고객이 처음 들어왔을 때 사이드바가 열려있도록 "expanded" 설정
st.set_page_config(
    page_title="SynoCore V1.2 | SynoTech Strategic Platform", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# 세션 상태 초기화
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'initialized' not in st.session_state:
    try:
        init_db()
        log_action("System", "SynoCore V1.2.11 UX Optimized Online")
        st.session_state.initialized = True
    except: pass

# CSS: 디자인 위계 및 사이드바 자동 제어 로직
# 관리자 모드일 경우 사이드바를 자동으로 닫는 CSS 인젝션 포함
sidebar_width = "0" if st.session_state.admin_mode else "21rem"
sidebar_opacity = "0" if st.session_state.admin_mode else "1"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    
    /* 메인 타이틀: 로고(2.2rem)보다 작은 1.1rem, 검정색 */
    .main h1 {{ 
        color: #000000 !important; 
        font-weight: 700 !important; 
        font-size: 1.1rem !important; 
        border-bottom: 2px solid #1A729A; 
        padding-bottom: 5px; 
        margin-bottom: 30px;
    }}
    
    h2, h3 {{ color: #1A729A !important; font-weight: 600 !important; }}
    
    /* 버튼 및 입력도구 스타일: 시노텍 블루 (#1A729A) */
    .stButton>button {{
        background-color: #1A729A; color: white; border-radius: 6px; border: none; font-weight: bold;
    }}
    
    /* 슬라이더 컬러 강조 */
    div[data-baseweb="slider"] div {{ background-color: #1A729A !important; }}

    /* 사이드바 스타일 및 로그인 시 자동 닫힘 시뮬레이션 */
    [data-testid="stSidebar"] {{ 
        background-color: #f1f6f9; 
        border-right: 2px solid #1A729A;
        transition: all 0.5s ease;
    }}
    
    /* 크레딧 폰트 설정 */
    .streamlit-expanderHeader p {{ font-size: 0.9rem !important; color: #1A729A !important; }}
    .streamlit-expanderContent {{ font-size: 0.75rem !important; color: #555555; }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

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

# 세션 데이터 관리
if 'trials' not in st.session_state: st.session_state.trials = 3
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'show_upgrade' not in st.session_state: st.session_state.show_upgrade = False
if 'user_info' not in st.session_state: st.session_state.user_info = {"name": "", "company": ""}
if 'last_res' not in st.session_state: st.session_state.last_res = None

# --- [3. 사이드바: 브랜드 로고 및 로그인] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A; font-weight: 800; font-size: 2.2rem; border-bottom: none;'>SynoCore</h1>", unsafe_allow_html=True)
    
    selected_lang = st.selectbox("🌐 Language", ["English", "한국어"])
    T = LANG_DICT[selected_lang]
    
    st.divider()
    u_id = st.text_input("Admin ID", key="admin_id")
    u_pw = st.text_input("Password", type="password", key="admin_pw")
    
    # 관리자 로그인 검증
    if verify_admin_access(u_id, u_pw):
        if not st.session_state.admin_mode:
            st.session_state.admin_mode = True
            st.rerun() # 로그인 성공 시 화면을 새로고침하여 사이드바 닫기 유도
        st.success("✅ MASTER AUTHORIZED")
    else:
        st.session_state.admin_mode = False
    
    st.divider()
    with st.expander("Developer Credits"):
        st.write("Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.")
    st.caption("© 2026 SynoTech Co., Ltd.")

# --- [4. 메인 화면: 시뮬레이션 인터페이스 (슬라이더 적용)] ---
st.title(T["title"])
st.markdown("---")

# [요청 반영] 슬라이더 방식으로 변경하여 직관적인 조절 가능하게 함
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    loading = c1.slider("Loading (mg/cm²)", 5.0, 35.0, 12.0, step=0.1)
    capacity = c2.slider("Cap. (mAh/g)", 100.0, 250.0, 140.0, step=1.0)
    area = c3.slider("Area (cm²)", 1.0, 50.0, 10.0, step=0.5)
    np_ratio = c4.slider("N/P Ratio", 0.8, 1.5, 1.1, step=0.01)

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
            load_range = np.linspace(5, 35, 30)
            energy_trend = [calculate_battery_specs(l, capacity, area, np_ratio)['specific_energy'] for l in load_range]
            chart_data = pd.DataFrame({'Loading': load_range, 'Energy Density': energy_trend}).set_index('Loading')
            st.line_chart(chart_data)

            st.divider()

            # 4.4. [Step 9] AI 디자인 인사이트
            st.subheader("🤖 SynoCore AI Design Insight")
            s_c1, s_c2 = st.columns([1, 2])
            with s_c1:
                score = 100
                if np_ratio < 1.05: score -= 30
                if loading > 22: score -= 20
                st.metric("Design Stability Score", f"{score} / 100")
                if score >= 80: st.success("✅ 안정적인 설계 범위")
                else: st.warning("⚠️ 보완 권장")
            with s_c2:
                if np_ratio < 1.05: st.write("🚨 **Danger:** 리튬 석출(Plating) 위험군")
                if loading > 22: st.write("⚠️ **Warning:** 고부하 설계로 인한 출력 저하 우려")
                if score == 100: st.write("✨ 시노텍 가이드라인 완벽 충족")
            
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
            st.error(f"분석 엔진 오류: {e}")
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
if st.session_state.admin_mode:
    st.markdown("---")
    st.header(f"🛡️ SynoCore Intelligence Dashboard")
    leads_df = get_leads()
    audit_df = get_audit_logs()
    t1, t2, t3 = st.tabs(["📊 Analytics", "📜 Audit Logs", "👥 Partner Leads"])
    with t1:
        if not leads_df.empty: st.bar_chart(leads_df['company'].value_counts())
    with t2: st.dataframe(audit_df, use_container_width=True)
    with t3: st.dataframe(leads_df, use_container_width=True)