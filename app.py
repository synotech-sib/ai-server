import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 외부 데이터 로드 엔진] ---
def load_external_data():
    files = os.listdir('.')
    # 1.1 소재 리스트 로드
    mat_df = None
    if 'material_list.xlsx' in files:
        mat_df = pd.read_excel('material_list.xlsx')
    elif 'material_list.csv' in files:
        mat_df = pd.read_csv('material_list.csv')
    else:
        # 기본값 설정 (파일 없을 시)
        mat_df = pd.DataFrame({
            'Category': ['Cathode', 'Anode', 'Electrolyte', 'Separator', 'Additive'],
            'Name': ['프러시안 화이트 (PW)', '쿠라레 A', 'G Type', 'PE', 'VC'],
            'Base_Capacity': [162.0, 340.0, 1.0, 1.0, 1.0]
        })

    # 1.2 공정 범위 설정 로드
    config_df = None
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx').set_index('Parameter')
    elif 'param_config.csv' in files:
        config_df = pd.read_csv('param_config.csv').set_index('Parameter')
    else:
        # 기본 파라미터 3종
        config_df = pd.DataFrame({
            'Min': [5.0, 70.0, 1.0], 'Max': [40.0, 98.0, 1.5], 
            'Default': [13.0, 85.0, 1.15], 'Step': [0.1, 0.5, 0.01]
        }, index=['Loading', 'ICE', 'NP_Ratio'])
        
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 시스템 초기화 및 테마] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

# CSS: 우측 입력창 배경색 및 리포트 디자인
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .report-container {{ border: 2px solid #1A729A; padding: 30px; border-radius: 15px; background-color: #ffffff; }}
    .stat-card {{ background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 15px; border-radius: 10px; text-align: center; }}
    /* 우측 입력 섹션 스타일 */
    [data-testid="stVerticalBlock"] > div:nth-child(2) {{ 
        background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #ddd;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 로그인 및 환경설정] ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption(f"Status: {IP_MARK}")
    
    st.divider()
    st.subheader("🔐 Professional Login")
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(f"Authorized: {u_email.split('@')[0]}")
        else:
            st.error("Invalid Credentials")
    
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [4. 메인 레이아웃 구성] ---
col_report, col_input = st.columns([2.2, 1])

# --- [5. 우측 칼럼: 모든 입력 컨트롤 (목표/소재/파라미터)] ---
with col_input:
    st.subheader("🎯 Target & Inputs")
    target_whkg = st.number_input("목표 에너지 밀도 (Wh/kg)", value=160.0, step=1.0)
    
    st.divider()
    # 5.1 소재 선택 (material_list 내 모든 카테고리 동적 생성)
    st.write("**🧪 소재 레시피 (Recipe)**")
    categories = mat_df['Category'].unique()
    selected_materials = {}
    
    for cat in categories:
        names = mat_df[mat_df['Category'] == cat]['Name'].tolist()
        selected_materials[cat] = st.selectbox(f"{cat} 선택", names)

    st.divider()
    # 5.2 파라미터 선택 (param_config 내 모든 항목 동적 생성)
    st.write("**⚙️ 설계 파라미터 (Params)**")
    params_values = {}
    for param_name in config_df.index:
        cfg = config_df.loc[param_name]
        params_values[param_name] = st.slider(
            f"{param_name}", 
            float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step'])
        )

    st.divider()
    # 5.3 설계 요약 (Snapshot)
    st.write("**📋 설계 요약 (Snapshot)**")
    for cat, name in selected_materials.items():
        st.caption(f"- {cat}: {name}")
    st.caption(f"- Target: {target_whkg} Wh/kg")
    
    run_btn = st.button("🚀 분석 실행", use_container_width=True)

# --- [6. 좌측 칼럼: 결과 리포트 및 히스토리] ---
with col_report:
    st.title(f"SIB 설계 분석 플랫폼")
    st.markdown(f"**{IP_MARK}** | Energy11 x Altris Hybrid Engine")
    
    if run_btn:
        # 연산 로직
        # 양극(Cathode) 용량 가져오기 (파일 기반)
        cathode_name = selected_materials.get('Cathode', list(selected_materials.values())[0])
        c_cap_base = mat_df[mat_df['Name'] == cathode_name]['Base_Capacity'].values[0]
        
        # 슬라이더 값 가져오기
        loading = params_values.get('Loading', 13.0)
        ice = params_values.get('ICE', 85.0)
        
        # 계산 공식 (Master V1.2 로직)
        eff_cap = c_cap_base * (ice / 100.0) * 0.9 # 0.9는 전압/속도 보정 계수
        whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 5.0))) * 10
        
        # 로그 저장
        log_entry = {"Time": time.strftime("%H:%M"), "Wh/kg": round(whkg, 1), "Target": target_whkg}
        log_entry.update(selected_materials) # 선택한 모든 소재 기록
        st.session_state.history.append(log_entry)

        # 리포트 출력
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="text-align:center; color:#1A729A;">DESIGN ANALYSIS REPORT</h2>', unsafe_allow_html=True)
        
        k1, k2, k3 = st.columns(3)
        diff = whkg - target_whkg
        color = "#28a745" if diff >= 0 else "#dc3545"
        
        k1.markdown(f'<div class="stat-card"><div style="font-size:1.5rem; font-weight:bold; color:{color};">{whkg:.1f} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="stat-card"><div style="font-size:1.5rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="stat-card"><div style="font-size:1.5rem; font-weight:bold;">{target_whkg}</div><div>목표 에너지 밀도</div></div>', unsafe_allow_html=True)
        
        st.divider()
        st.subheader("💡 기술 제언")
        if whkg < target_whkg:
            st.error(f"목표 달성을 위해 로딩량을 상향하거나 고용량 양극재 선정이 필요합니다.")
        else:
            st.success(f"현재 설계로 목표 달성이 가능합니다. 공정 안정성을 검토하십시오.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 히스토리 표시 (리포트 하단)
    if st.session_state.history:
        st.divider()
        st.subheader("🔄 설계 이력 로그 (History)")
        st.table(pd.DataFrame(st.session_state.history).iloc[::-1])