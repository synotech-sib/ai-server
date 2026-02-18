import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 다국어 사전 정의] ---
LANG_DICT = {
    "KO": {
        "title": "SIB 설계 및 성능 분석 플랫폼",
        "login_sub": "🔐 마스터 로그인",
        "lang_sel": "🌐 언어 선택",
        "target_set": "🎯 목표 설정",
        "design_sum": "📋 디자인 서머리",
        "mat_sel": "🧪 소재 레시피 (Material Selection)",
        "proc_param": "⚙️ 공정 파라미터 (Process Params)",
        "run_btn": "🚀 분석 실행 (Run Analysis)",
        "history": "🔄 설계 이력 로그 (History)",
        "target_label": "목표 에너지 밀도",
        "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량",
        "report_title": "DESIGN ANALYSIS REPORT",
        "auth_msg": "마스터 권한 승인됨"
    },
    "EN": {
        "title": "SIB Design & Performance Analysis Platform",
        "login_sub": "🔐 Master Login",
        "lang_sel": "🌐 Language Select",
        "target_set": "🎯 Target Setting",
        "design_sum": "📋 Design Summary",
        "mat_sel": "🧪 Material Recipe Selection",
        "proc_param": "⚙️ Process Parameters",
        "run_btn": "🚀 Run Analysis",
        "history": "🔄 Design History Log",
        "target_label": "Target Energy Density",
        "exp_energy": "Expected Energy Density",
        "eff_cap": "Effective Capacity",
        "report_title": "DESIGN ANALYSIS REPORT",
        "auth_msg": "Master Authorized"
    }
}

# --- [2. 외부 데이터 로드 엔진: XLSX 전용] ---
def load_external_data():
    files = os.listdir('.')
    mat_df = pd.DataFrame()
    config_df = pd.DataFrame()
    if 'material_list.xlsx' in files:
        mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [3. 시스템 초기화 및 테마 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech | Energy11 Production Intelligence"

st.set_page_config(page_title="SynoCore Master V1.2", layout="wide")

# CSS: 우측 박스 및 레이아웃 스타일
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-section { border: 1px solid #e6e9ef; padding: 25px; border-radius: 12px; background-color: #f8f9fa; margin-bottom: 20px; }
    .unified-box { border: 2px solid #1A729A; padding: 25px; border-radius: 15px; background-color: #ffffff; min-height: 620px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .report-box { background-color: #f0f4f8; border-top: 5px solid #1A729A; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .summary-item { font-size: 0.92rem; margin-bottom: 6px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바: 로그인 및 언어 설정] ---
with st.sidebar:
    st.markdown("<h1 style='color: #1A729A; text-align: center;'>SynoCore</h1>", unsafe_allow_html=True)
    st.divider()
    
    # 언어 선택
    lang_code = st.selectbox("🌐 Language / 언어", ["KO", "EN"])
    L = LANG_DICT[lang_code]
    
    st.divider()
    st.subheader(L["login_sub"])
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(L["auth_msg"])
        else: st.error("Invalid Login")
    
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [5. 메인 레이아웃 (7:3 분할)] ---
st.title(L["title"])
st.markdown(f"**{IP_MARK}**")

report_placeholder = st.empty()
col_left, col_right = st.columns([7, 3])

# --- [왼쪽 판: 소재(4열) / 공정(4열) / 버튼] ---
with col_left:
    selected_mats = {}
    selected_params = {}

    if not mat_df.empty:
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.subheader(L["mat_sel"])
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

    if not config_df.empty:
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.subheader(L["proc_param"])
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

    st.write("") 
    run_btn = st.button(L["run_btn"], use_container_width=True)

# --- [오른쪽 판: 통합 제어 박스 (Target + Summary)] ---
with col_right:
    st.markdown('<div class="unified-box">', unsafe_allow_html=True)
    
    # 5.1 목표 설정
    st.subheader(L["target_set"])
    target_whkg = st.number_input(f"{L['target_label']} ($Wh/kg$)", value=160.0, step=1.0)
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    # 5.2 디자인 서머리
    st.subheader(L["design_sum"])
    for cat, name in selected_mats.items():
        st.markdown(f'<div class="summary-item"><b>{cat}</b>: {name}</div>', unsafe_allow_html=True)
    for p_name, val in selected_params.items():
        st.markdown(f'<div class="summary-item"><b>{p_name}</b>: {val}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 분석 로직 및 결과 리포트] ---
if run_btn and not mat_df.empty:
    c_name = selected_mats.get('Cathode', 'Default')
    try:
        c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
        loading = selected_params.get('Loading', 13.0)
        ice = selected_params.get('ICE', 85.0)
        
        # 예측 알고리즘
        eff_cap = c_cap * (ice / 100.0) * 0.93
        whkg = (eff_cap * 3.1 * 0.38 * (loading / (loading + 4.9))) * 10
        
        st.session_state.history.append({
            "Time": time.strftime("%H:%M"), "Recipe": f"{c_name}", "Wh/kg": round(whkg, 1), "Target": target_whkg
        })

        with report_placeholder.container():
            st.markdown('<div class="report-box">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>', unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            diff = whkg - target_whkg
            res_color = "#28a745" if diff >= 0 else "#dc3545"
            
            k1.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold; color:{res_color};">{whkg:.1f} Wh/kg</div><div>{L["exp_energy"]}</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>{L["eff_cap"]}</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="stat-card"><div style="font-size:1.6rem; font-weight:bold;">{target_whkg}</div><div>{L["target_label"]}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.error("Error in Analysis")

# --- [7. 히스토리 로그] ---
if st.session_state.history:
    st.divider()
    st.subheader(L["history"])
    st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True)