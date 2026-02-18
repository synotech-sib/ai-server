import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 시스템 설정] ---
st.set_page_config(page_title="SynoCore Master V1.3", layout="wide")

# --- [2. UI 제어 CSS: 박스 내부 수용 및 버튼 중앙화] ---
st.markdown("""
    <style>
    /* 헤더/툴바 제거 */
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
    .block-container { padding-top: 1rem !important; }

    /* 커스텀 섹션 박스 (내용물 수용) */
    .section-card {
        border: 1px solid #e6e9ef;
        padding: 20px;
        border-radius: 12px;
        background-color: #f8f9fa;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .summary-card {
        border: 2px solid #1A729A;
        padding: 20px;
        border-radius: 12px;
        background-color: #ffffff;
        margin-bottom: 20px;
        min-height: 230px;
    }

    .summary-item { font-size: 0.9rem; margin-bottom: 4px !important; color: #333; line-height: 1.4; }

    /* 분석 실행 버튼 중앙 정렬 */
    .center-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 30px 0;
        width: 100%;
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important;
        color: white !important;
        font-weight: bold !important;
        height: 65px !important;
        width: 400px !important;
        font-size: 1.3rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(26, 114, 154, 0.3) !important;
        border: none !important;
    }

    /* 컨트롤 바 */
    .top-nav {
        background-color: #f8f9fa;
        border-bottom: 2px solid #1A729A;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 데이터 로드 로직] ---
def load_data():
    try:
        m_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
        m_df['Base_Capacity'] = pd.to_numeric(m_df['Base_Capacity'], errors='coerce').fillna(0)
        c_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
        return m_df, c_df
    except: return pd.DataFrame(), pd.DataFrame()

mat_df, config_df = load_data()

# --- [4. 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'last_result' not in st.session_state: st.session_state.last_result = None

# --- [5. 상단 커스텀 컨트롤 바] ---
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
t1, t2, t3, t4, t5 = st.columns([1.5, 0.8, 1.5, 1.5, 1])
with t1: st.markdown("<h3 style='color:#1A729A; margin:0;'>SynoCore</h3>", unsafe_allow_html=True)
with t2: lang_sel = st.selectbox("🌐", ["English", "Korean"], label_visibility="collapsed")
with t3: u_email = st.text_input("Email", placeholder="Email", label_visibility="collapsed")
with t4: u_pw = st.text_input("Password", type="password", placeholder="PW", label_visibility="collapsed")
with t5: 
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success("Master Mode")
st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 메인 설계 UI] ---
st.title("SynoCore Master V1.3 | SIB Design Platform")

selected_mats, selected_params = {}, {}

# 1. 소재 선택 (박스 내부에 가둠)
st.markdown('<div class="section-card"><h3>1. Material Selection</h3>', unsafe_allow_html=True)
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

# 2. 공정 파라미터 (박스 내부에 가둠)
st.markdown('<div class="section-card"><h3>2. Process Parameters</h3>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-card" style="background-color: #eef6fb; min-height: 250px;"><h3>3. Target Setting</h3>', unsafe_allow_html=True)
    target_whkg = st.slider("Target Energy Density (Wh/kg)", 100.0, 250.0, 160.0, 1.0)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="summary-card"><h3>4. Design Summary</h3>', unsafe_allow_html=True)
    s_c1, s_c2 = st.columns(2)
    with s_c1:
        for k, v in list(selected_mats.items()):
            st.markdown(f'<p class="summary-item"><b>{k}</b>: {v}</p>', unsafe_allow_html=True)
    with s_c2:
        for k, v in list(selected_params.items()):
            st.markdown(f'<p class="summary-item"><b>{k}</b>: {v}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. 분석 실행 (중앙 배치)
st.markdown('<div class="center-wrapper">', unsafe_allow_html=True)
if st.button("RUN MASTER ANALYSIS", type="primary"):
    try:
        c_name = selected_mats.get('Cathode', '')
        c_cap = float(mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0])
        ld = float(selected_params.get('Loading', 13.0))
        ice = float(selected_params.get('ICE', 85.0))
        # 에너지 밀도 계산식 (SIB 전용)
        res_whkg = (c_cap * (ice/100) * 0.93 * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
        st.session_state.last_result = {"whkg": res_whkg, "eff": c_cap*(ice/100)*0.93, "target": target_whkg, "ld": ld}
        st.session_state.history.append({"Time": time.strftime("%H:%M"), "Wh/kg": round(res_whkg, 1)})
        st.rerun()
    except: st.error("Calculation Error. Please check Excel data.")
st.markdown('</div>', unsafe_allow_html=True)

# --- [7. 결과 리포트 및 그래프] ---
if st.session_state.last_result:
    res = st.session_state.last_result
    st.markdown(f'''<div class="summary-card" style="background-color: #f0f4f8; min-height: auto;">
        <h3 style="text-align:center; color:#1A729A;">DESIGN ANALYSIS REPORT</h3>
        <div style="display: flex; justify-content: space-around; text-align:center;">
            <div><h4>{res['whkg']:.1f} Wh/kg</h4><small>Expected Energy</small></div>
            <div><h4>{res['eff']:.1f} mAh/g</h4><small>Effective Capacity</small></div>
            <div><h4>{res['target']}</h4><small>Target Wh/kg</small></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.subheader("Energy Density Simulation Curve")
    
    fig, ax = plt.subplots(figsize=(10, 3.5))
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    ax.plot(l_range, w_range, color='#1A729A', lw=2.5)
    ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=120)
    ax.set_xlabel('Loading (mg/cm2)'); ax.set_ylabel('Wh/kg'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)

st.markdown('<div style="text-align:center; color:#888; margin-top:50px;">© Synotech Co., Ltd | All Rights Reserved</div>', unsafe_allow_html=True)