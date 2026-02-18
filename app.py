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
    /* 1. 헤더/툴바 제거 */
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
    .block-container { padding-top: 1rem !important; }

    /* 2. 컨테이너(박스) 스타일링 */
    div[data-testid="stBorderContainer"] {
        background-color: #f8f9fa;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    /* 3번, 4번 박스 높이 동일하게 맞추기 위한 CSS (Marker 방식) */
    /* id="equal-height" 마커가 있는 컨테이너만 타겟팅하여 높이 고정 */
    div[data-testid="stBorderContainer"]:has(div#equal-height) {
        min-height: 380px !important; /* 높이 강제 통일 */
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    /* 4번 서머리 박스 강조 (파란 테두리) */
    div[data-testid="stBorderContainer"]:has(div#summary-marker) {
        border: 2px solid #1A729A !important;
        background-color: #ffffff;
    }
    
    /* 3. 분석 실행 버튼: 더 넓게, 중앙 정렬 */
    div.stButton {
        display: flex;
        justify-content: center; /* 버튼 컨테이너 중앙 정렬 */
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important; 
        color: white !important;
        font-weight: bold !important;
        height: 70px !important;    /* 높이 확대 */
        width: 500px !important;    /* 너비 대폭 확대 */
        font-size: 1.4rem !important;
        border-radius: 15px !important;
        border: none !important;
        box-shadow: 0 6px 12px rgba(26, 114, 154, 0.3);
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
    
    .footer-text { text-align: center; color: #888; font-size: 0.8rem; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 데이터 로드: 계산 오류 방지 강화] ---
def load_data():
    try:
        # 1. 엑셀 파일 읽기
        if os.path.exists('material_list.xlsx'):
            m_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
            # 2. 'Base_Capacity' 컬럼을 문자열로 변환 -> 공백 제거 -> 숫자로 변환 -> NaN은 0으로
            m_df['Base_Capacity'] = pd.to_numeric(m_df['Base_Capacity'].astype(str).str.strip(), errors='coerce').fillna(0)
        else:
            m_df = pd.DataFrame()

        if os.path.exists('param_config.xlsx'):
            c_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
        else:
            c_df = pd.DataFrame()
            
        return m_df, c_df
    except Exception as e:
        st.error(f"Excel File Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

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
with c2: st.selectbox("Language", ["English", "Korean"], label_visibility="collapsed")
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

# --- [6. 메인 설계 UI] ---

# 1. Material Selection
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

# 2. Process Parameters
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

# 3번 & 4번 좌우 분할 (높이 통일 적용)
col_left, col_right = st.columns(2)

with col_left:
    # 3. Target Setting (높이 고정)
    with st.container(border=True):
        # 높이 통일용 마커 삽입
        st.markdown('<div id="equal-height"></div>', unsafe_allow_html=True)
        st.markdown("### 3. Target Setting")
        st.write("") # 약간의 여백
        st.write("")
        target_whkg = st.slider("Target Energy Density (Wh/kg)", 100.0, 250.0, 160.0, 1.0)
        # 하단 여백 자동 조절을 위해 빈 공간 추가하지 않음 (CSS flex로 처리)

with col_right:
    # 4. Design Summary (높이 고정 + 파란 테두리)
    with st.container(border=True):
        # 높이 통일 + 파란 테두리용 마커 2개 삽입
        st.markdown('<div id="equal-height"></div><div id="summary-marker"></div>', unsafe_allow_html=True)
        st.markdown("### 4. Design Summary")
        
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            for k, v in list(selected_mats.items()):
                st.markdown(f'<div style="font-size:0.9rem; margin-bottom:5px;"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)
        with s_c2:
            for k, v in list(selected_params.items()):
                st.markdown(f'<div style="font-size:0.9rem; margin-bottom:5px;"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)

# 5. 분석 실행 버튼 (중앙 정렬 & 500px 너비)
st.write("")
if st.button("RUN MASTER ANALYSIS", type="primary"):
    try:
        # 데이터 안전 처리
        c_name = selected_mats.get('Cathode', '')
        if c_name:
            c_data = mat_df[mat_df['Name'] == c_name]
            if not c_data.empty:
                # 숫자형 변환 재확인
                c_cap = float(c_data['Base_Capacity'].values[0])
            else:
                c_cap = 0.0
        else:
            c_cap = 0.0

        ld = float(selected_params.get('Loading', 13.0))
        ice = float(selected_params.get('ICE', 85.0))
        
        # 0 나누기 방지
        denom = ld + 4.9
        if denom == 0: denom = 1.0 

        res_whkg = (c_cap * (ice/100) * 0.93 * 3.1 * 0.38 * (ld / denom)) * 10
        
        st.session_state.last_result = {"whkg": res_whkg, "eff": c_cap*(ice/100)*0.93, "target": target_whkg, "ld": ld}
        st.session_state.history.append({"Time": time.strftime("%H:%M"), "Wh/kg": round(res_whkg, 1)})
        
        if not st.session_state.is_pro: 
            st.session_state.usage_count += 1
        st.rerun()

    except Exception as e: 
        st.error(f"Calculation Error: {e}")

# --- [7. 결과 및 그래프] ---
if st.session_state.last_result:
    res = st.session_state.last_result
    
    # 결과 요약 박스
    with st.container(border=True):
        st.markdown('<div id="summary-marker"></div>', unsafe_allow_html=True)
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