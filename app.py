import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 시스템 설정] ---
st.set_page_config(page_title="SynoCore Master V1.3", layout="wide")

# --- [2. UI 제어 CSS] ---
st.markdown("""
    <style>
    /* 1. 헤더/툴바 완전 제거 */
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
    .block-container { padding-top: 1rem !important; }

    /* 2. 컨테이너(박스) 스타일링 오버라이드 */
    /* 기본 섹션 박스 (회색 테두리) */
    div[data-testid="stBorderContainer"] {
        background-color: #f8f9fa;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    /* 디자인 서머리 박스 전용 스타일 (파란색 테두리 강조) 
       :has() 선택자를 사용하여 특정 마커가 있는 컨테이너만 타겟팅 */
    div[data-testid="stBorderContainer"]:has(div#summary-marker) {
        background-color: #ffffff;
        border: 2px solid #1A729A;
    }
    
    /* 제목 스타일 */
    h3 { color: #333; font-size: 1.3rem; margin-bottom: 20px; }
    
    /* 3. 분석 실행 버튼 스타일 */
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important; 
        color: white !important;
        font-weight: bold !important;
        height: 60px !important;
        width: 100% !important;
        font-size: 1.2rem !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(26, 114, 154, 0.3);
    }
    
    /* 4. 상단 네비게이션 스타일 */
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
    
    .summary-item { font-size: 0.95rem; margin-bottom: 5px; color: #333; line-height: 1.5; }
    .footer-text { text-align: center; color: #888; font-size: 0.8rem; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 데이터 로드] ---
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
if 'usage_count' not in st.session_state: st.session_state.usage_count = 0

# --- [5. 상단 컨트롤 바] ---
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([1.5, 0.8, 1.5, 1.5, 1])
with c1: st.markdown("<h3 style='color:#1A729A; margin:0;'>SynoCore</h3>", unsafe_allow_html=True)
with c2: lang = st.selectbox("Language", ["English", "Korean"], label_visibility="collapsed")
with c3: st.text_input("Email", placeholder="Email", label_visibility="collapsed")
with c4: st.text_input("PW", type="password", placeholder="PW", label_visibility="collapsed")
with c5: 
    if st.button("Login"):
        st.session_state.is_pro = True
        st.success("Master Mode")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:right; margin-top:-10px; margin-bottom:20px;"><span class="usage-badge">Free Usage: {st.session_state.usage_count}/3</span></div>', unsafe_allow_html=True)

st.title("SynoCore Master V1.3 | SIB Design Platform")

selected_mats, selected_params = {}, {}

# --- [6. 메인 설계 UI (컨테이너 방식 적용)] ---

# 1. Material Selection (회색 박스)
with st.container(border=True):
    st.markdown("### 1. Material Selection")
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

# 2. Process Parameters (회색 박스)
with st.container(border=True):
    st.markdown("### 2. Process Parameters")
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

# 3번 & 4번 좌우 분할
col_left, col_right = st.columns(2)

with col_left:
    # 3. Target Setting (회색 박스)
    with st.container(border=True):
        st.markdown("### 3. Target Setting")
        # 높이 균형을 위한 빈 공간 확보
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        target_whkg = st.slider("Target Energy Density (Wh/kg)", 100.0, 250.0, 160.0, 1.0)
        st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True) # 박스 높이 맞춤용

with col_right:
    # 4. Design Summary (파란색 테두리 박스)
    with st.container(border=True):
        # CSS 타겟팅을 위한 마커 삽입 (화면엔 안 보임)
        st.markdown('<div id="summary-marker"></div>', unsafe_allow_html=True)
        st.markdown("### 4. Design Summary")
        
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            for k, v in list(selected_mats.items()):
                st.markdown(f'<div class="summary-item"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)
        with s_c2:
            for k, v in list(selected_params.items()):
                st.markdown(f'<div class="summary-item"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)

# 5. 분석 실행 버튼 (중앙 정렬)
st.write("") # 여백
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1]) # 1:2:1 비율로 중앙 집중
with btn_col2:
    if st.button("RUN MASTER ANALYSIS", type="primary"):
        try:
            c_name = selected_mats.get('Cathode', '')
            c_cap = float(mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0])
            ld = float(selected_params.get('Loading', 13.0))
            ice = float(selected_params.get('ICE', 85.0))
            
            res_whkg = (c_cap * (ice/100) * 0.93 * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
            st.session_state.last_result = {"whkg": res_whkg, "eff": c_cap*(ice/100)*0.93, "target": target_whkg, "ld": ld}
            st.session_state.history.append({"Time": time.strftime("%H:%M"), "Wh/kg": round(res_whkg, 1)})
            st.rerun()
        except: st.error("Calculation Error")

# --- [7. 결과 및 그래프] ---
if st.session_state.last_result:
    res = st.session_state.last_result
    
    # 결과 요약 박스 (파란 테두리 적용)
    with st.container(border=True):
        st.markdown('<div id="summary-marker"></div>', unsafe_allow_html=True) # 파란 테두리 적용
        st.markdown("<h3 style='text-align:center; color:#1A729A;'>DESIGN ANALYSIS REPORT</h3>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        with r1: st.metric("Expected Energy", f"{res['whkg']:.1f} Wh/kg")
        with r2: st.metric("Effective Capacity", f"{res['eff']:.1f} mAh/g")
        with r3: st.metric("Target", f"{res['target']} Wh/kg")

    st.subheader("Energy Density Simulation")
    fig, ax = plt.subplots(figsize=(10, 3.5))
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    ax.plot(l_range, w_range, color='#1A729A', lw=2.5)
    ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=120, zorder=5)
    ax.set_xlabel('Loading (mg/cm2)'); ax.set_ylabel('Wh/kg'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)

st.markdown('<div class="footer-text">© Synotech Co., Ltd | All Rights Reserved</div>', unsafe_allow_html=True)