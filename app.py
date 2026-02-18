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
        "target_set": "🎯 목표 설정",
        "design_sum": "📋 디자인 서머리",
        "mat_sel": "🧪 소재 레시피 (Material Selection)",
        "proc_param": "⚙️ 공정 파라미터 (Process Params)",
        "run_btn": "🚀 분석 실행 (Run Analysis)",
        "history": "🔄 설계 이력 로그 (History)",
        "target_label": "목표 에너지 밀도 (Wh/kg)",
        "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량",
        "report_title": "DESIGN ANALYSIS REPORT",
        "auth_msg": "마스터 권한 승인됨"
    },
    "EN": {
        "title": "SIB Design & Performance Analysis Platform",
        "login_sub": "🔐 Master Login",
        "target_set": "🎯 Target Setting",
        "design_sum": "📋 Design Summary",
        "mat_sel": "🧪 Material Selection",
        "proc_param": "⚙️ Process Parameters",
        "run_btn": "🚀 Run Analysis",
        "history": "🔄 Design History Log",
        "target_label": "Target Energy Density (Wh/kg)",
        "exp_energy": "Expected Energy Density",
        "eff_cap": "Effective Capacity",
        "report_title": "DESIGN ANALYSIS REPORT",
        "auth_msg": "Master Authorized"
    }
}

# --- [2. 데이터 로드 엔진: XLSX 전용] ---
def load_external_data():
    files = os.listdir('.')
    mat_df, config_df = pd.DataFrame(), pd.DataFrame()
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

# [수정] 박스 이탈 방지 CSS (Auto-height & Word-wrap)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* 입력 박스: 높이 자동 조절 */
    .input-box { 
        border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; 
        background-color: #f8f9fa; margin-bottom: 20px;
        height: auto; overflow: hidden;
    }
    /* 우측 통합 박스: 내용에 따라 무한 확장, 글자 자동 줄바꿈 */
    .unified-right-box { 
        border: 2px solid #1A729A; padding: 25px; border-radius: 15px; 
        background-color: #ffffff; height: auto; min-height: 500px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        word-break: break-all;
    }
    .summary-item { 
        font-size: 0.85rem; margin-bottom: 8px; color: #333; 
        border-bottom: 1px solid #eee; padding-bottom: 4px;
        line-height: 1.4;
    }
    .report-box { background-color: #f0f4f8; border-top: 5px solid #1A729A; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바] ---
with st.sidebar:
    st.markdown("<h2 style='color: #1A729A; text-align: center;'>SynoCore</h2>", unsafe_allow_html=True)
    lang_code = st.selectbox("🌐 Language", ["KO", "EN"])
    L = LANG_DICT[lang_code]
    st.divider()
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(L["auth_msg"])
        else: st.error("Login Error")
    if st.button("🗑️ Clear Log"):
        st.session_state.history = []
        st.rerun()

# --- [5. 메인 레이아웃] ---
st.title(L["title"])
st.caption(IP_MARK)
report_placeholder = st.empty()

col_left, col_right = st.columns([7, 3])

with col_left:
    selected_mats, selected_params = {}, {}

    # 5.1 소재 레시피 박스
    if not mat_df.empty:
        st.markdown(f'<div class="input-box"><h4>{L["mat_sel"]}</h4>', unsafe_allow_html=True)
        cats = mat_df['Category'].unique()
        # 한 줄에 4개가 좁으면 자동으로 조절되도록 columns 생성
        for i in range(0, len(cats), 4):
            m_cols = st.columns(4)
            for j in range(4):
                if i + j < len(cats):
                    cat = cats[i+j]
                    with m_cols[j]:
                        m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
                        selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"mat_{cat}")
        st.markdown('</div>', unsafe_allow_html=True)

    # 5.2 공정 파라미터 박스
    if not config_df.empty:
        st.markdown(f'<div class="input-box"><h4>{L["proc_param"]}</h4>', unsafe_allow_html=True)
        params = config_df.index.tolist()
        for i in range(0, len(params), 4):
            p_cols = st.columns(4)
            for j in range(4):
                if i + j < len(params):
                    p_name = params[i+j]
                    with p_cols[j]:
                        cfg = config_df.loc[p_name]
                        selected_params[p_name] = st.slider(
                            f"{p_name}", float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step']),
                            key=f"p_{p_name}"
                        )
        st.markdown('</div>', unsafe_allow_html=True)

    run_btn = st.button(L["run_btn"], use_container_width=True)

with col_right:
    # 5.3 우측 통합 박스 (목표 + 서머리)
    st.markdown('<div class="unified-right-box">', unsafe_allow_html=True)
    st.subheader(L["target_set"])
    target_whkg = st.number_input(L["target_label"], value=160.0, step=1.0)
    
    st.markdown("<br><hr style='border:1px solid #eee;'><br>", unsafe_allow_html=True)
    
    st.subheader(L["design_sum"])
    # 소재 요약
    for cat, name in selected_mats.items():
        st.markdown(f'<div class="summary-item"><b>{cat}</b>: {name}</div>', unsafe_allow_html=True)
    # 파라미터 요약
    for p_name, val in selected_params.items():
        st.markdown(f'<div class="summary-item"><b>{p_name}</b>: {val}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 분석 및 리포트] ---
if run_btn and not mat_df.empty:
    try:
        c_name = selected_mats.get('Cathode', 'Default')
        c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
        ld = selected_params.get('Loading', 13.0)
        ice = selected_params.get('ICE', 85.0)
        
        eff_cap = c_cap * (ice / 100.0) * 0.93
        whkg = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
        
        st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg, 1)})

        with report_placeholder.container():
            st.markdown(f'''<div class="report-box">
                <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
                <div style="display: flex; justify-content: space-around;">
                    <div class="stat-card"><b>{whkg:.1f} Wh/kg</b><br><small>{L["exp_energy"]}</small></div>
                    <div class="stat-card"><b>{eff_cap:.1f} mAh/g</b><br><small>{L["eff_cap"]}</small></div>
                    <div class="stat-card"><b>{target_whkg}</b><br><small>{L["target_label"]}</small></div>
                </div>
            </div>''', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")

# --- [7. 히스토리] ---
if st.session_state.history:
    st.divider()
    st.subheader(L["history"])
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])