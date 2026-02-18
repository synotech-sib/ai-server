import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 데이터 로드 엔진] ---
@st.cache_data
def load_external_data():
    files = os.listdir('.')
    # 1.1 소재 리스트 로딩
    if 'material_list.xlsx' in files: mat_df = pd.read_excel('material_list.xlsx')
    elif 'material_list.csv' in files: mat_df = pd.read_csv('material_list.csv')
    else:
        mat_df = pd.DataFrame({
            'Category': ['Cathode', 'Anode', 'Electrolyte', 'Separator'],
            'Name': ['프러시안 화이트 (PW)', '쿠라레 A', '표준 전해질', 'PE 분리막'],
            'Base_Capacity': [162.0, 340.0, 1.0, 1.0]
        })
    # 1.2 파라미터 범위 로딩
    if 'param_config.xlsx' in files: config_df = pd.read_excel('param_config.xlsx').set_index('Parameter')
    elif 'param_config.csv' in files: config_df = pd.read_csv('param_config.csv').set_index('Parameter')
    else:
        config_df = pd.DataFrame({
            'Min': [5.0, 70.0, 1.0], 'Max': [40.0, 98.0, 1.5],
            'Default': [13.0, 85.0, 1.15], 'Step': [0.1, 0.5, 0.01]
        }, index=['Loading', 'ICE', 'NP_Ratio'])
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 세션 및 테마 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .report-box {{ border: 2px solid #1A729A; padding: 30px; border-radius: 15px; background-color: #fcfcfc; margin-bottom: 30px; }}
    .input-section {{ background-color: #f8f9fa; padding: 25px; border-radius: 15px; border: 1px solid #dee2e6; margin-top: 10px; }}
    .stat-card {{ background-color: #ffffff; border-top: 4px solid #1A729A; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{ color: #1A729A !important; font-weight: 800; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 로그인 전용] ---
with st.sidebar:
    st.markdown("<h1 style='color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.subheader("🔐 Master Login")
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(f"Authorized: {u_email.split('@')[0]}")
        else: st.error("Invalid Credentials")
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [4. 메인 판 상단: 분석 결과 리포트] ---
st.title(f"SIB 설계 및 기술 보고서")
st.markdown(f"**{IP_MARK}** | Energy11 Production Intelligence")

report_placeholder = st.empty() # 결과가 나타날 공간

# --- [5. 메인 판 하단: 4단 입력 시스템] ---
st.markdown("---")

# [1단: 타겟 및 주요 소재 선택]
st.subheader("🎯 1. Target & Main Materials")
t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
with t_col1: target_whkg = st.number_input("목표 에너지 (Wh/kg)", value=160.0, step=1.0)

# 파일의 카테고리 순서대로 배치
cats = ['Cathode', 'Anode', 'Electrolyte', 'Separator']
selected_mats = {}
cols = [t_col2, t_col3, t_col4, t_col5]

for i, cat in enumerate(cats):
    with cols[i]:
        m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
        selected_mats[cat] = st.selectbox(f"{cat} 선택", m_list)

# [2단: 추가 소재 레시피 (있을 경우)]
# material_list에 위 4가지 외 다른 카테고리가 있다면 여기서 표시
other_cats = [c for c in mat_df['Category'].unique() if c not in cats]
if other_cats:
    st.subheader("🧪 2. Additional Materials")
    o_cols = st.columns(len(other_cats))
    for i, cat in enumerate(other_cats):
        with o_cols[i]:
            m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
            selected_mats[cat] = st.selectbox(f"{cat} 선택", m_list)

# [3단: 파라미터 설정]
st.subheader("⚙️ 3. Process Parameters")
p_cols = st.columns(len(config_df))
selected_params = {}
for i, p_name in enumerate(config_df.index):
    with p_cols[i]:
        cfg = config_df.loc[p_name]
        selected_params[p_name] = st.slider(
            f"{p_name}", 
            float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step'])
        )

# [4단: 설계 요약 및 실행]
st.subheader("📋 4. Design Summary")
summary_box = st.container()
with summary_box:
    s_col1, s_col2 = st.columns([4, 1])
    with s_col1:
        # 가로로 요약 내용 표시
        summary_text = " / ".join([f"**{k}**: {v}" for k, v in selected_mats.items()])
        st.write(f"📝 **Recipe**: {summary_text}")
        param_text = " | ".join([f"{k}: {v}" for k, v in selected_params.items()])
        st.write(f"⚙️ **Params**: {param_text}")
    with s_col2:
        run_btn = st.button("🚀 분석 실행", use_container_width=True)

# --- [6. 연산 및 리포트 업데이트 로직] ---
if run_btn:
    # 계산 로직
    c_name = selected_mats.get('Cathode')
    c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
    loading = selected_params.get('Loading', 13.0)
    ice = selected_params.get('ICE', 85.0)
    
    eff_cap = c_cap * (ice / 100.0) * 0.9
    whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 5.0))) * 10
    
    # 히스토리 저장
    log_entry = {"Time": time.strftime("%H:%M:%S"), "Wh/kg": round(whkg, 1), "Target": target_whkg, "Cathode": c_name}
    st.session_state.history.append(log_entry)

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
        
        st.divider()
        if whkg < target_whkg:
            st.error(f"⚠️ 목표 미달: 로딩량을 {loading * (target_whkg/whkg):.1f}mg/cm² 이상으로 상향하거나 고용량 소재를 선정하십시오.")
        else:
            st.success("✅ 설계 만족: 현재 레시피로 목표 달성이 가능합니다.")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    with report_placeholder.container():
        st.info("하단에서 설계를 완료한 후 '분석 실행' 버튼을 눌러주세요.")

# --- [7. 최하단: 히스토리 로그] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 로그 (History Log)")
    st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True)