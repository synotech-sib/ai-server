import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 다국어 사전 정의: English 기본] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore Master V1.3 | SIB Design Platform",
        "login_sub": "Access Login",
        "usage_label": "Free Usage",
        "usage_limit_msg": "Free limit (3/3) reached. Please register for Pro.",
        "target_set": "3. Target Setting",
        "design_sum": "4. Design Summary",
        "mat_sel": "1. Material Selection",
        "proc_param": "2. Process Parameters",
        "run_btn": "5. Run Master Analysis",
        "history": "Design History Log",
        "report_title": "DESIGN ANALYSIS REPORT",
        "graph_title": "Energy Density Simulation Graph",
        "master_features": "Master Technical Insights",
        "target_label": "Target Energy Density (Wh/kg)",
        "exp_energy": "Expected Energy Density",
        "eff_cap": "Effective Capacity",
        "loading_label": "Cathode Loading",
        "auth_msg": "Master Mode Activated"
    },
    "Korean": {
        "title": "SynoCore Master V1.3 | SIB 설계 플랫폼",
        "login_sub": "접속 로그인",
        "usage_label": "무료 이용 횟수",
        "usage_limit_msg": "무료 이용 횟수(3회)를 초과했습니다. Pro 등록이 필요합니다.",
        "target_set": "3. 목표 설정",
        "design_sum": "4. 디자인 서머리",
        "mat_sel": "1. 소재 레시피",
        "proc_param": "2. 공정 파라미터",
        "run_btn": "5. 분석 실행",
        "history": "설계 이력 로그",
        "report_title": "DESIGN ANALYSIS REPORT",
        "graph_title": "에너지 밀도 시뮬레이션 그래프",
        "master_features": "마스터 진단 정보",
        "target_label": "목표 에너지 밀도 (Wh/kg)",
        "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량",
        "loading_label": "양극 로딩량",
        "auth_msg": "마스터 모드 활성화됨"
    }
}

# --- [2. 데이터 로드 엔진: XLSX 전용] ---
def load_external_data():
    files = os.listdir('.')
    mat_df, config_df = pd.DataFrame(), pd.DataFrame()
    if 'material_list.xlsx' in files:
        mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [3. 시스템 초기화 및 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'usage_count' not in st.session_state: st.session_state.usage_count = 0
if 'last_result' not in st.session_state: st.session_state.last_result = None

st.set_page_config(page_title="SynoCore Master V1.3", layout="wide", initial_sidebar_state="expanded")

# --- [4. Master V1.2 스타일 복원: 헤더 숨김 및 버튼 노출 CSS] ---
st.markdown("""
    <style>
    /* 1. 상단 기본 메뉴 및 푸터 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. 헤더 전체를 숨기지 않고 배경만 투명화하여 접기/펴기 버튼 살리기 */
    header[data-testid="stHeader"] {
        background-color: rgba(0, 0, 0, 0) !important;
        border: none !important;
    }

    /* 3. 사이드바 접기/펴기 버튼 강조 및 위치 고정 */
    button[kind="headerNoPadding"] {
        visibility: visible !important;
        background-color: #f8f9fa !important;
        border: 1px solid #e6e9ef !important;
        border-radius: 5px !important;
        margin-top: 10px !important;
        margin-left: 10px !important;
    }

    /* 4. 무료 횟수 로고 컬러 하이라이트 (#1A729A) */
    .usage-badge { 
        background-color: #1A729A; 
        color: white; 
        padding: 8px 15px; 
        border-radius: 25px; 
        font-size: 0.9rem; 
        font-weight: bold;
    }

    .stApp { background-color: #ffffff; }
    .section-box { border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; background-color: #f8f9fa; margin-bottom: 15px; }
    .summary-box { border: 2px solid #1A729A; padding: 15px; border-radius: 12px; background-color: #ffffff; margin-bottom: 20px; }
    .summary-item { font-size: 0.88rem; margin-bottom: 2px; color: #333; display: inline-block; margin-right: 15px; line-height: 1.1; }
    
    /* 분석 실행 버튼: 로고 컬러 적용 */
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
        height: 50px;
    }
    .sidebar-footer { position: fixed; bottom: 20px; left: 20px; font-size: 0.8rem; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# --- [5. 사이드바 구성] ---
with st.sidebar:
    st.markdown("<h2 style='color: #1A729A; text-align: center;'>SynoCore</h2>", unsafe_allow_html=True)
    lang_sel = st.selectbox("Language", ["English", "Korean"])
    L = LANG_DICT[lang_sel]
    
    # 무료 횟수 하이라이트 표시
    st.divider()
    usage_text = f"{L['usage_label']}: {st.session_state.usage_count}/3"
    st.markdown(f'<div style="text-align:center; margin: 10px 0;"><span class="usage-badge">{usage_text}</span></div>', unsafe_allow_html=True)
    
    # 통합 로그인 (wschoi@synotech.co.kr 전용)
    st.divider()
    st.subheader(L["login_sub"])
    u_email = st.text_input("Email", placeholder="your@email.com")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(L["auth_msg"])
        else:
            st.info("User session recorded.")
    
    if st.button("Reset All"):
        st.session_state.history = []; st.session_state.usage_count = 0
        st.session_state.last_result = None; st.rerun()

    st.markdown('<div class="sidebar-footer">© Synotech Co., Ltd</div>', unsafe_allow_html=True)

# --- [6. 메인 UI: 수직 배치] ---
st.title(L["title"])
st.caption("IP by Synotech | Energy11 Production Intelligence")

selected_mats, selected_params = {}, {}

# 1. Material Selection (Grid 4)
if not mat_df.empty:
    st.markdown(f'<div class="section-box"><h3>{L["mat_sel"]}</h3>', unsafe_allow_html=True)
    cats = mat_df['Category'].unique()
    for i in range(0, len(cats), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(cats):
                cat = cats[i+j]
                with cols[j]:
                    m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
                    selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"mat_{cat}")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. Process Parameters
if not config_df.empty:
    st.markdown(f'<div class="section-box"><h3>{L["proc_param"]}</h3>', unsafe_allow_html=True)
    params = config_df.index.tolist()
    for i in range(0, len(params), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(params):
                p_name = params[i+j]
                with cols[j]:
                    cfg = config_df.loc[p_name]
                    selected_params[p_name] = st.slider(f"{p_name}", float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step']), key=f"p_{p_name}")
    st.markdown('</div>', unsafe_allow_html=True)

# 3. Target Setting (Slider)
st.markdown(f'<div class="section-box" style="background-color: #eef6fb;"><h3>{L["target_set"]}</h3>', unsafe_allow_html=True)
target_whkg = st.slider(L["target_label"], 100.0, 250.0, 160.0, 1.0)
st.markdown('</div>', unsafe_allow_html=True)

# 4. Design Summary
st.markdown(f'<div class="summary-box"><h3>{L["design_sum"]}</h3>', unsafe_allow_html=True)
for cat, name in selected_mats.items():
    st.markdown(f'<span class="summary-item"><b>{cat}</b>: {name}</span>', unsafe_allow_html=True)
st.write("") 
for p_name, val in selected_params.items():
    st.markdown(f'<span class="summary-item"><b>{p_name}</b>: {val}</span>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5. Run Analysis
if st.button(L["run_btn"], use_container_width=True, type="primary"):
    if not st.session_state.is_pro and st.session_state.usage_count >= 3:
        st.error(L["usage_limit_msg"])
    else:
        try:
            c_name = selected_mats.get('Cathode', '')
            c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
            ld = selected_params.get('Loading', 13.0); ice = selected_params.get('ICE', 85.0)
            eff_cap = c_cap * (ice / 100.0) * 0.93
            whkg_res = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
            st.session_state.last_result = {"whkg": whkg_res, "eff_cap": eff_cap, "target": target_whkg, "ld": ld}
            st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg_res, 1)})
            if not st.session_state.is_pro: st.session_state.usage_count += 1
            st.rerun()
        except: st.error("Error calculating results.")

# --- [7. 하단 출력부: 히스토리 -> 결과 리포트 -> 그래프] ---
if st.session_state.history:
    st.divider(); st.subheader(L["history"])
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])

if st.session_state.last_result:
    res = st.session_state.last_result
    st.markdown(f'''<div class="report-box" style="background-color: #f0f4f8; border-top: 5px solid #1A729A; padding: 25px; border-radius: 15px; margin: 30px 0;">
        <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); flex: 1; margin: 0 10px;"><h3>{res['whkg']:.1f} Wh/kg</h3><small>{L["exp_energy"]}</small></div>
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); flex: 1; margin: 0 10px;"><h3>{res['eff_cap']:.1f} mAh/g</h3><small>{L["eff_cap"]}</small></div>
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); flex: 1; margin: 0 10px;"><h3>{res['target']}</h3><small>{L["target_label"]}</small></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.subheader(L["graph_title"])
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff_cap'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(l_range, w_range, color='#1A729A', linewidth=2.5); ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=150, zorder=5)
    ax.set_xlabel('mg/cm2'); ax.set_ylabel('Wh/kg'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)