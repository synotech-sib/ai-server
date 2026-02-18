import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 데이터 로드 엔진] ---
@st.cache_data
def load_external_data():
    files = os.listdir('.')
    if 'material_list.xlsx' in files: mat_df = pd.read_excel('material_list.xlsx')
    elif 'material_list.csv' in files: mat_df = pd.read_csv('material_list.csv')
    else:
        mat_df = pd.DataFrame({
            'Category': ['Cathode', 'Anode', 'Electrolyte', 'Separator', 'Additive'],
            'Name': ['프러시안 화이트 (PW)', '쿠라레 A', '표준 전해질', 'PE 분리막', 'VC'],
            'Base_Capacity': [162.0, 340.0, 1.0, 1.0, 1.0]
        })
    if 'param_config.xlsx' in files: config_df = pd.read_excel('param_config.xlsx').set_index('Parameter')
    elif 'param_config.csv' in files: config_df = pd.read_csv('param_config.csv').set_index('Parameter')
    else:
        config_df = pd.DataFrame({
            'Min': [5.0, 70.0, 1.0], 'Max': [40.0, 98.0, 1.5],
            'Default': [13.0, 85.0, 1.15], 'Step': [0.1, 0.5, 0.01]
        }, index=['Loading', 'ICE', 'NP_Ratio'])
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 테마 및 세션 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

# 레이아웃 커스텀 CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .section-container {{ 
        border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; 
        background-color: #f8f9fa; margin-bottom: 20px;
    }}
    .summary-box {{ 
        background-color: #ffffff; border: 2px solid #1A729A; 
        padding: 20px; border-radius: 12px; min-height: 300px;
    }}
    .report-box {{ 
        background-color: #f0f4f8; border-top: 5px solid #1A729A; 
        padding: 25px; border-radius: 15px; margin-bottom: 25px;
    }}
    .stat-card {{ background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{ color: #1A729A !important; font-weight: 800; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 로그인 전 전용] ---
with st.sidebar:
    st.markdown("<h1 style='color: #1A729A; text-align: center;'>SynoCore</h1>", unsafe_allow_html=True)
    st.divider()
    st.subheader("🔐 Master Access")
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(f"Welcome, {u_email.split('@')[0]}")
        else: st.error("Login Failed")
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [4. 메인 판 레이아웃 (7:3 분할)] ---
st.title(f"SIB 설계 분석 플랫폼")
st.markdown(f"**{IP_MARK}** | Energy11 Production Intelligence")

# 상단 리포트 출력 영역 (결과 발생 시 표시)
report_placeholder = st.empty()

# 입력 및 요약 판
col_left, col_right = st.columns([7, 3])

# --- [왼쪽 판: 상단 머트리얼 / 하단 파라미터] ---
with col_left:
    # 4.1 소재 레시피 (왼쪽 상단)
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("🧪 소재 레시피 (Material Selection)")
    m_cols = st.columns(3)
    selected_mats = {}
    categories = mat_df['Category'].unique()
    
    for i, cat in enumerate(categories):
        with m_cols[i % 3]:
            m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
            selected_mats[cat] = st.selectbox(f"{cat}", m_list)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.2 공정 파라미터 (왼쪽 하단)
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("⚙️ 공정 파라미터 (Process Params)")
    p_cols = st.columns(3)
    selected_params = {}
    for i, p_name in enumerate(config_df.index):
        with p_cols[i % 3]:
            cfg = config_df.loc[p_name]
            selected_params[p_name] = st.slider(
                f"{p_name}", 
                float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step'])
            )
    st.markdown('</div>', unsafe_allow_html=True)

# --- [오른쪽 판: 상단 목표 / 하단 디자인 서머리] ---
with col_right:
    # 4.3 목표 에너지 밀도 (오른쪽 상단)
    st.markdown('<div class="section-container" style="background-color: #eef6fb;">', unsafe_allow_html=True)
    st.subheader("🎯 목표 설정")
    target_whkg = st.number_input("Target Energy Density (Wh/kg)", value=160.0, step=1.0)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.4 디자인 서머리 (오른쪽 하단)
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.subheader("📋 Design Summary")
    st.write("---")
    for cat, name in selected_mats.items():
        st.write(f"**{cat}**: {name}")
    st.write("---")
    for p_name, val in selected_params.items():
        st.write(f"**{p_name}**: {val}")
    
    st.write("")
    run_btn = st.button("🚀 분석 실행", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [5. 연산 로직 및 결과 리포트] ---
if run_btn:
    # 예시 연산 로직 (Selected Mats & Params 활용)
    c_name = selected_mats.get('Cathode', 'Default')
    c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
    loading = selected_params.get('Loading', 13.0)
    ice = selected_params.get('ICE', 85.0)
    
    # 알트리스 하이이브리드 모델 예측치
    eff_cap = c_cap * (ice / 100.0) * 0.92 
    whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 4.9))) * 10
    
    # 히스토리 저장
    st.session_state.history.append({
        "Date": time.strftime("%Y-%m-%d %H:%M"),
        "Recipe": f"{c_name}", "Wh/kg": round(whkg, 1), "Target": target_whkg
    })

    # 상단 리포트 업데이트
    with report_placeholder.container():
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.markdown(f'<h3 style="text-align:center; color:#1A729A;">DESIGN ANALYSIS REPORT</h3>', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        diff = whkg - target_whkg
        color = "#28a745" if diff >= 0 else "#dc3545"
        
        k1.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:{color};">{whkg:.1f} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{target_whkg}</div><div>목표 에너지 밀도</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 히스토리 로그] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 로그 (History)")
    st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True)