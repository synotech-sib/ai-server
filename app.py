import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 외부 데이터 로드 엔진: XLSX 전용] ---
def load_external_data():
    files = os.listdir('.')
    mat_df = pd.DataFrame()
    config_df = pd.DataFrame()

    # 오직 .xlsx 파일만 확인하고 로드
    if 'material_list.xlsx' in files:
        mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
    
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
        
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 시스템 초기화 및 테마 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech | Energy11 Production Intelligence"

st.set_page_config(page_title="SynoCore Master V1.2", layout="wide")

# CSS: 중괄호 충돌 방지 및 레이아웃 스타일링
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-section { border: 1px solid #e6e9ef; padding: 25px; border-radius: 12px; background-color: #f8f9fa; margin-bottom: 20px; }
    .unified-box { border: 2px solid #1A729A; padding: 25px; border-radius: 15px; background-color: #ffffff; min-height: 600px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .report-box { background-color: #f0f4f8; border-top: 5px solid #1A729A; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .summary-item { font-size: 0.95rem; margin-bottom: 8px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }
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
st.title("SIB 설계 분석 플랫폼")
st.markdown(f"**{IP_MARK}**")

report_placeholder = st.empty()
col_left, col_right = st.columns([7, 3])

# --- [왼쪽 판: 소재(4열) / 공정(4열) / 버튼] ---
with col_left:
    selected_mats = {}
    selected_params = {}

    if not mat_df.empty:
        # 4.1 소재 레시피 그리드 (4개 한 줄)
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.subheader("🧪 소재 레시피 (Material Selection)")
        cats = mat_df['Category'].unique()
        for i in range(0, len(cats), 4):
            m_cols = st.columns(4)
            for j in range(4):
                if i + j < len(cats):
                    cat = cats[i+j]
                    with m_cols[j]:
                        m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
                        selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"mat_{cat}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ material_list.xlsx 파일을 찾을 수 없습니다.")

    if not config_df.empty:
        # 4.2 공정 파라미터 그리드 (4개 한 줄)
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.subheader("⚙️ 공정 파라미터 (Process Params)")
        params = config_df.index.tolist()
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
    else:
        st.warning("⚠️ param_config.xlsx 파일을 찾을 수 없습니다.")

    # 4.3 분석 실행 버튼
    st.write("") 
    run_btn = st.button("🚀 분석 실행 (Run Analysis)", use_container_width=True)

# --- [오른쪽 판: 통합 정보 박스 (Target + Summary)] ---
with col_right:
    st.markdown('<div class="unified-box">', unsafe_allow_html=True)
    
    # 4.4 목표 설정
    st.subheader("🎯 목표 설정")
    target_whkg = st.number_input("Target Energy Density (Wh/kg)", value=160.0, step=1.0)
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    # 4.5 디자인 서머리
    st.subheader("📋 Design Summary")
    st.write("")
    for cat, name in selected_mats.items():
        st.markdown(f'<div class="summary-item"><b>{cat}</b>: {name}</div>', unsafe_allow_html=True)
    for p_name, val in selected_params.items():
        st.markdown(f'<div class="summary-item"><b>{p_name}</b>: {val}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- [5. 분석 로직 및 결과 리포트] ---
if run_btn and not mat_df.empty:
    # 알트리스 실측 기반 연산 로직
    c_name = selected_mats.get('Cathode', 'Default')
    try:
        c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
        loading = selected_params.get('Loading', 13.0)
        ice = selected_params.get('ICE', 85.0)
        
        eff_cap = c_cap * (ice / 100.0) * 0.93
        whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 4.9))) * 10
        
        st.session_state.history.append({
            "Date": time.strftime("%H:%M"), "Recipe": f"{c_name}", "Wh/kg": round(whkg, 1), "Target": target_whkg
        })

        with report_placeholder.container():
            st.markdown('<div class="report-box">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align:center; color:#1A729A;">DESIGN ANALYSIS REPORT</h3>', unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            diff = whkg - target_whkg
            res_color = "#28a745" if diff >= 0 else "#dc3545"
            
            k1.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:{res_color};">{whkg:.1f} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{target_whkg}</div><div>목표 에너지 밀도</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.error("분석 중 오류가 발생했습니다. 소재 데이터를 확인해주세요.")

# --- [6. 히스토리 로그] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 로그 (History)")
    st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True)