import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 데이터 로드 엔진] ---
@st.cache_data
def load_external_data():
    files = os.listdir('.')
    # 소재 리스트 로딩
    if 'material_list.xlsx' in files: mat_df = pd.read_excel('material_list.xlsx')
    elif 'material_list.csv' in files: mat_df = pd.read_csv('material_list.csv')
    else:
        mat_df = pd.DataFrame({
            'Category': ['Cathode', 'Anode', 'Electrolyte', 'Separator', 'Additive'],
            'Name': ['프러시안 화이트 (PW)', '쿠라레 A', '표준 전해질', 'PE 분리막', 'VC 첨가제'],
            'Base_Capacity': [162.0, 340.0, 1.0, 1.0, 1.0]
        })
    # 파라미터 범위 로딩
    if 'param_config.xlsx' in files: config_df = pd.read_excel('param_config.xlsx').set_index('Parameter')
    elif 'param_config.csv' in files: config_df = pd.read_csv('param_config.csv').set_index('Parameter')
    else:
        config_df = pd.DataFrame({
            'Min': [5.0, 70.0, 1.0, 3.8, 0.1], 'Max': [40.0, 98.0, 1.5, 4.3, 5.0],
            'Default': [13.0, 85.0, 1.15, 4.2, 0.33], 'Step': [0.1, 0.5, 0.01, 0.1, 0.1]
        }, index=['Loading', 'ICE', 'NP_Ratio', 'Voltage', 'C-rate'])
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 세션 및 테마 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

# CSS: 왼쪽 리포트와 오른쪽 제어판의 시각적 분리
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    /* 왼쪽 리포트 영역 스타일 */
    .main-report {{ border-radius: 20px; padding: 40px; background-color: #ffffff; border: 1px solid #eee; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
    /* 오른쪽 입력 영역 스타일 */
    .control-panel {{ background-color: #f8f9fa; padding: 25px; border-radius: 20px; border: 1px solid #dee2e6; }}
    .stat-card {{ background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{ color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 로그인 섹션] ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.subheader("🔐 Professional Login")
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

# --- [4. 전체 레이아웃 (좌: 리포트 / 우: 컨트롤)] ---
col_left, col_right = st.columns([2.2, 1])

# --- [5. 우측 칼럼: 모든 입력 컨트롤 (Target, Recipe, Params, Summary)] ---
with col_right:
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.subheader("🎯 Target Setting")
    target_whkg = st.number_input("목표 에너지 밀도 (Wh/kg)", value=160.0, step=1.0)
    
    st.divider()
    # 5.1 소재 레시피: 파일에 있는 모든 카테고리를 동적으로 생성
    st.write("**🧪 소재 레시피 (Material Recipe)**")
    selected_mats = {}
    categories = mat_df['Category'].unique()
    for cat in categories:
        m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
        selected_mats[cat] = st.selectbox(f"{cat} 선택", m_list)

    st.divider()
    # 5.2 파라미터 슬라이더: 파일에 있는 모든 파라미터를 동적으로 생성
    st.write("**⚙️ 공정 파라미터 (Process Params)**")
    selected_params = {}
    for p_name in config_df.index:
        cfg = config_df.loc[p_name]
        selected_params[p_name] = st.slider(
            f"{p_name}", 
            float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step'])
        )

    st.divider()
    # 5.3 설계 요약 (Snapshot)
    st.write("**📋 설계 요약 (Summary)**")
    for cat, name in selected_mats.items():
        st.caption(f"• {cat}: {name}")
    for p_name, val in selected_params.items():
        st.caption(f"• {p_name}: {val}")
    
    run_btn = st.button("🚀 분석 실행", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 좌측 칼럼: 분석 리포트 및 이력 출력] ---
with col_left:
    st.markdown('<div class="main-report">', unsafe_allow_html=True)
    st.title("SIB 설계 분석 및 기술 보고서")
    st.markdown(f"**{IP_MARK}** | Energy11 Production Intelligence")
    st.divider()

    if run_btn:
        # 연산 로직 (Selected Mats & Params 기반)
        # 예시 연산: Cathode의 Base_Capacity와 Loading, ICE를 활용
        c_name = selected_mats.get('Cathode', list(selected_mats.values())[0])
        c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
        
        loading = selected_params.get('Loading', 13.0)
        ice = selected_params.get('ICE', 85.0)
        v_win = selected_params.get('Voltage', 4.2)
        
        # 간이 예측 모델 적용
        eff_cap = c_cap * (ice / 100.0) * (v_win / 4.2)
        whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 5.0))) * 10
        
        # 로그 저장
        log_entry = {"Time": time.strftime("%H:%M:%S"), "Wh/kg": round(whkg, 1), "Target": target_whkg}
        log_entry.update(selected_mats)
        log_entry.update(selected_params)
        st.session_state.history.append(log_entry)

        # 리포트 렌더링
        k1, k2, k3 = st.columns(3)
        diff = whkg - target_whkg
        color = "#28a745" if diff >= 0 else "#dc3545"
        
        k1.markdown(f'<div class="stat-card"><div style="font-size:1.5rem; font-weight:bold; color:{color};">{whkg:.1f} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="stat-card"><div style="font-size:1.5rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="stat-card"><div style="font-size:1.5rem; font-weight:bold;">{target_whkg}</div><div>목표 에너지 밀도</div></div>', unsafe_allow_html=True)
        
        st.divider()
        st.subheader("💡 엔지니어 기술 제언")
        if whkg < target_whkg:
            st.error(f"목표치 달성을 위해 로딩량을 상향하거나, {c_name} 대신 고용량 양극재 선정이 필요합니다.")
        else:
            st.success(f"현재 설계 레시피로 목표 달성이 가능합니다. 공정 안정성(수분 제어)을 확인하십시오.")
    else:
        st.info("우측 패널에서 레시피를 설정한 후 '분석 실행' 버튼을 눌러주세요.")
    st.markdown('</div>', unsafe_allow_html=True)

    # 7. 설계 이력 로그 (리포트 하단)
    if st.session_state.history:
        st.divider()
        st.subheader("🔄 설계 이력 로그 (History Log)")
        st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True)