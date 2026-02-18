import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 시스템 설정] ---
st.set_page_config(page_title="SynoCore Master V1.3", layout="wide")

# --- [2. UI 제어 CSS: 박스 내부 정렬 및 버튼 중앙화] ---
st.markdown("""
    <style>
    /* 1. 헤더/툴바 완전 제거 */
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
    .block-container { padding-top: 1rem !important; }

    /* 2. 상단 컨트롤 바 */
    .top-nav {
        background-color: #f8f9fa;
        border-bottom: 2px solid #1A729A;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 25px;
    }
    
    .usage-badge { 
        background-color: #1A729A; color: white; padding: 5px 12px; 
        border-radius: 15px; font-size: 0.85rem; font-weight: bold;
    }

    /* 3. 섹션 박스 (모든 입력을 박스 안으로 강제 수용) */
    .section-card { 
        border: 1px solid #e6e9ef; 
        padding: 25px; 
        border-radius: 12px; 
        background-color: #f8f9fa; 
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .summary-card { 
        border: 2px solid #1A729A; 
        padding: 25px; 
        border-radius: 12px; 
        background-color: #ffffff; 
        margin-bottom: 20px;
        min-height: 250px;
    }

    .summary-item { font-size: 0.9rem; margin-bottom: 4px !important; color: #333; line-height: 1.4 !important; }
    
    /* 4. 분석 실행 버튼: 중앙 정렬 컨테이너 */
    .center-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px 0;
        width: 100%;
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important; 
        color: white !important;
        font-weight: bold !important;
        height: 65px !important;
        width: 400px !important; /* 버튼 크기 확대 */
        font-size: 1.25rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(26, 114, 154, 0.2) !important;
    }
    
    .footer-text { text-align: center; color: #888; font-size: 0.8rem; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 데이터 로드 및 사전 정의] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore Master V1.3 | SIB Design Platform",
        "login_sub": "Access", "usage_label": "Free Usage",
        "target_set": "3. Target Setting", "design_sum": "4. Design Summary",
        "mat_sel": "1. Material Selection", "proc_param": "2. Process Parameters",
        "run_btn": "RUN MASTER ANALYSIS", "history": "Design History Log",
        "report_title": "DESIGN ANALYSIS REPORT", "graph_title": "Energy Density Simulation",
        "target_label": "Target Energy Density (Wh/kg)", "exp_energy": "Expected Energy",
        "eff_cap": "Effective Capacity", "loading_label": "Cathode Loading", "auth_msg": "Master Activated"
    },
    "Korean": {
        "title": "SynoCore Master V1.3 | SIB 설계 플랫폼",
        "login_sub": "접속", "usage_label": "무료 이용",
        "target_set": "3. 목표 설정", "design_sum": "4. 디자인 서머리",
        "mat_sel": "1. 소재 레시피", "proc_param": "2. 공정 파라미터",
        "run_btn": "분석 실행", "history": "설계 이력 로그",
        "report_title": "DESIGN ANALYSIS REPORT", "graph_title": "에너지 밀도 시뮬레이션",
        "target_label": "목표 에너지 밀도 (Wh/kg)", "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량", "loading_label": "양극 로딩량", "auth_msg": "마스터 활성화"
    }
}

def load_data():
    try:
        m_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
        m_df['Base_Capacity'] = pd.to_numeric(m_df['Base_Capacity'], errors='coerce').fillna(0)
        c_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
        return m_df, c_df
    except: return pd.DataFrame(), pd.DataFrame()

mat_df, config_df = load_data()

# --- [4. 상단 컨트롤 바] ---
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'usage_count' not in st.session_state: st.session_state.usage_count = 0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_result' not in st.session_state: st.session_state.last_result = None

st.markdown('<div class="top-nav">', unsafe_allow_html=True)
t1, t2, t3, t4, t5 = st.columns([1.5, 0.8, 1.5, 1.5, 1])
with t1: st.markdown("<h3 style='color:#1A729A; margin:0;'>SynoCore</h3>", unsafe_allow_html=True)
with t2: lang_sel = st.selectbox("🌐", ["English", "Korean"], label_visibility="collapsed")
L = LANG_DICT[lang_sel]
with t3: u_email = st.text_input("Email", placeholder="Email", label_visibility="collapsed")
with t4: u_pw = st.text_input("Password", type="password", placeholder="PW", label_visibility="collapsed")
with t5: 
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(L["auth_msg"])
st.markdown('</div>', unsafe_allow_html=True)

# --- [5. 메인 UI] ---
st.title(L["title"])
st.caption("IP by Synotech | Energy11 Production Intelligence")

selected_mats, selected_params = {}, {}

# 1. 소재 선택 박스
st.markdown(f'<div class="section-card"><h3>{L["mat_sel"]}</h3>', unsafe_allow_html=True)
if not mat_df.empty:
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

# 2. 공정 파라미터 박스
st.markdown(f'<div class="section-card"><h3>{L["proc_param"]}</h3>', unsafe_allow_html=True)
if not config_df.empty:
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

# 3번/4번 좌우 대칭 배치
col_left, col_right = st.columns(2)

with col_left:
    st.markdown(f'<div class="section-card" style="background-color: #eef6fb; min-height: 250px;"><h3>{L["target_set"]}</h3>', unsafe_allow_html=True)
    target_whkg = st.slider(L["target_label"], 100.0, 250.0, 160.0, 1.0)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown(f'<div class="summary-card"><h3>{L["design_sum"]}</h3>', unsafe_allow_html=True)
    s_c1, s_c2 = st.columns(2)
    with s_c1:
        for k, v in list(selected_mats.items()):
            st.markdown(f'<p class="summary-item"><b>{k}</b>: {v}</p>', unsafe_allow_html=True)
    with s_c2:
        for k, v in list(selected_params.items()):
            st.markdown(f'<p class="summary-item"><b>{k}</b>: {v}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. 분석 실행 (화면 중앙 정렬)
st.markdown('<div class="center-container">', unsafe_allow_html=True)
if st.button(L["run_btn"], type="primary"):
    try:
        c_name = selected_mats.get('Cathode', '')
        c_cap = float(mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0])
        ld = float(selected_params.get('Loading', 13.0))
        ice = float(selected_params.get('ICE', 85.0))
        res_whkg = (c_cap * (ice/100) * 0.93 * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
        st.session_state.last_result = {"whkg": res_whkg, "eff": c_cap*(ice/100)*0.93, "target": target_whkg, "ld": ld}
        st.session_state.history.append({"Time": time.strftime("%H:%M"), "Wh/kg": round(res_whkg, 1)})
        st.rerun()
    except: st.error("Check Excel Data")
st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 결과 및 그래프] ---
if st.session_state.last_result:
    res = st.session_state.last_result
    st.markdown(f'''<div class="summary-card" style="background-color: #f0f4f8; min-height: auto;">
        <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
        <div style="display: flex; justify-content: space-around; text-align:center;">
            <div><h4>{res['whkg']:.1f} Wh/kg</h4><small>{L["exp_energy"]}</small></div>
            <div><h4>{res['eff']:.1f} mAh/g</h4><small>{L["eff_cap"]}</small></div>
            <div><h4>{res['target']}</h4><small>{L["target_label"]}</small></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    fig, ax = plt.subplots(figsize=(10, 3.5))
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    ax.plot(l_range, w_range, color='#1A729A', lw=2.5); ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=120)
    ax.set_xlabel('Loading (mg/cm2)'); ax.set_ylabel('Wh/kg'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)

st.markdown('<div class="footer-text">© Synotech Co., Ltd | All Rights Reserved</div>', unsafe_allow_html=True)