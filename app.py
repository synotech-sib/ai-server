import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 외부 데이터 로드 엔진: XLSX & CSV 지원] ---
def load_external_data():
    files = os.listdir('.')
    mat_df = None
    # 1.1 소재 리스트 로딩 (에러 핸들링 포함)
    try:
        if 'material_list.xlsx' in files:
            mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
        elif 'material_list.csv' in files:
            mat_df = pd.read_csv('material_list.csv')
        else:
            # 알트리스 실측 기준 기본값 (PW: 162mAh/g)
            mat_df = pd.DataFrame({
                'Category': ['Cathode', 'Anode', 'Electrolyte', 'Separator', 'Additive'],
                'Name': ['프러시안 화이트 (PW)', '쿠라레 A', 'G Type', 'PE', 'VC'],
                'Base_Capacity': [162.0, 340.0, 1.0, 1.0, 1.0]
            })
    except Exception as e:
        st.error(f"⚠️ 파일 로딩 오류: {e}. 'pip install openpyxl'을 확인하세요.")
        mat_df = pd.DataFrame({'Category':['Cathode'],'Name':['Default'],'Base_Capacity':[162.0]})

    # 1.2 공정 범위 설정 로딩
    config_df = None
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
    elif 'param_config.csv' in files:
        config_df = pd.read_csv('param_config.csv').set_index('Parameter')
    else:
        config_df = pd.DataFrame({
            'Min': [5.0, 70.0, 1.0, 0.1], 'Max': [40.0, 98.0, 1.5, 5.0],
            'Default': [13.0, 85.0, 1.15, 0.33], 'Step': [0.1, 0.5, 0.01, 0.1]
        }, index=['Loading', 'ICE', 'NP_Ratio', 'C-rate'])
        
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 시스템 초기화 및 테마 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech | Energy11 Production Intelligence"

st.set_page_config(page_title="SynoCore Master V1.2", layout="wide")

# CSS: 중괄호 충돌 방지를 위해 % 포맷팅 사용
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-section { border: 1px solid #e6e9ef; padding: 25px; border-radius: 15px; background-color: #f8f9fa; margin-bottom: 20px; }
    .summary-card { background-color: #ffffff; border: 2px solid #1A729A; padding: 20px; border-radius: 15px; min-height: 450px; }
    .report-box { background-color: #f0f4f8; border-top: 5px solid #1A729A; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 마스터 로그인] ---
with st.sidebar:
    st.markdown("<h1 style='color: #1A729A; text-align: center;'>SynoCore</h1>", unsafe_allow_html=True)
    st.divider()
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success("Master Authorized")
        else: st.error("Login Failed")
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [4. 메인 레이아웃 (7:3 분할)] ---
st.title("SIB 설계 및 성능 분석 플랫폼")
st.markdown(f"**{IP_MARK}**")

report_placeholder = st.empty()
col_left, col_right = st.columns([7, 3])

# --- [왼쪽 판: 그리드 기반 입력 섹션] ---
with col_left:
    # 4.1 소재 레시피 (한 줄에 4개씩)
    st.markdown('<div class="main-section">', unsafe_allow_html=True)
    st.subheader("🧪 소재 레시피 (Material Selection)")
    cats = mat_df['Category'].unique()
    selected_mats = {}
    
    for i in range(0, len(cats), 4):
        m_cols = st.columns(4)
        for j in range(4):
            if i + j < len(cats):
                cat = cats[i+j]
                with m_cols[j]:
                    m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
                    selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"mat_{cat}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.2 공정 파라미터 (한 줄에 4개씩)
    st.markdown('<div class="main-section">', unsafe_allow_html=True)
    st.subheader("⚙️ 공정 파라미터 (Process Params)")
    params = config_df.index.tolist()
    selected_params = {}
    
    for i in range(0, len(params), 4):
        p_cols = st.columns(4)
        for j in range(4):
            if i + j < len(params):
                p_name = params[i+j]
                with p_cols[j]:
                    cfg = config_df.loc[p_name]
                    selected_params[p_name] = st.slider(
                        f"{p_name}", 
                        float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step']),
                        key=f"p_{p_name}"
                    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- [오른쪽 판: 목표 설정 및 요약] ---
with col_right:
    # 4.3 목표 설정
    st.markdown('<div class="main-section" style="background-color: #eef6fb;">', unsafe_allow_html=True)
    st.subheader("🎯 목표 설정")
    target_whkg = st.number_input("Target Energy Density (Wh/kg)", value=160.0, step=1.0)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.4 디자인 서머리
    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
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

# --- [5. 분석 로직 및 결과 출력] ---
if run_btn:
    # 알트리스 실측 기반 연산 (PW: 162mAh/g)
    c_name = selected_mats.get('Cathode', 'Default')
    c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
    loading = selected_params.get('Loading', 13.0)
    ice = selected_params.get('ICE', 85.0)
    
    # 에너지11 하이브리드 보정 계수
    eff_cap = c_cap * (ice / 100.0) * 0.93
    whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 4.9))) * 10
    
    # 히스토리 저장
    st.session_state.history.append({
        "Date": time.strftime("%H:%M"), "Recipe": f"{c_name}", "Wh/kg": round(whkg, 1), "Target": target_whkg
    })

    # 상단 리포트 업데이트 (에러 수정된 포맷팅)
    with report_placeholder.container():
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align:center; color:#1A729A;">DESIGN ANALYSIS REPORT</h3>', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        diff = whkg - target_whkg
        res_color = "#28a745" if diff >= 0 else "#dc3545"
        
        # HTML 템플릿 분리하여 중괄호 에러 원천 차단
        card_html = '<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:%s;">%.1f Wh/kg</div><div>예상 에너지 밀도</div></div>'
        k1.markdown(card_html % (res_color, whkg), unsafe_allow_html=True)
        k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{target_whkg}</div><div>목표 에너지 밀도</div></div>', unsafe_allow_html=True)
        
        # 알트리스 기술 제언 (Page 4, 29 근거)
        if "프러시안" in c_name:
            st.warning("⚠️ **수분 관리 주의**: 알트리스 가이드에 따라 170°C 이상 진공 건조가 필수적입니다.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 히스토리 로그] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 로그 (History)")
    st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True)