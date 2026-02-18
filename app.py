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
        "target_set": "🎯 3. 목표 설정 (Target Setting)",
        "design_sum": "📋 4. 디자인 서머리 (Design Summary)",
        "mat_sel": "🧪 1. 소재 레시피 (Material Selection)",
        "proc_param": "⚙️ 2. 공정 파라미터 (Process Params)",
        "run_btn": "🚀 5. 분석 실행 (Run Master Analysis)",
        "history": "🔄 설계 이력 로그 (History Log)",
        "target_label": "목표 에너지 밀도 (Wh/kg)",
        "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량",
        "report_title": "DESIGN ANALYSIS REPORT",
        "auth_msg": "마스터 권한 승인됨"
    },
    "EN": {
        "title": "SIB Design & Performance Analysis Platform",
        "login_sub": "🔐 Master Login",
        "target_set": "🎯 3. Target Setting",
        "design_sum": "📋 4. Design Summary",
        "mat_sel": "🧪 1. Material Selection",
        "proc_param": "⚙️ 2. Process Parameters",
        "run_btn": "🚀 5. Run Master Analysis",
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

# CSS: 수직 배치 최적화 및 박스 자동 높이 조절
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* 공통 섹션 박스 스타일 */
    .section-box { 
        border: 1px solid #e6e9ef; 
        padding: 25px; 
        border-radius: 15px; 
        background-color: #f8f9fa; 
        margin-bottom: 25px;
        height: auto;
    }
    /* 서머리 전용 박스 (파란 테두리) */
    .summary-box { 
        border: 2px solid #1A729A; 
        padding: 25px; 
        border-radius: 15px; 
        background-color: #ffffff; 
        margin-bottom: 25px;
        height: auto;
    }
    .summary-item { 
        font-size: 0.95rem; 
        margin-bottom: 8px; 
        color: #333; 
        border-bottom: 1px solid #eee; 
        padding-bottom: 5px;
        display: inline-block;
        margin-right: 20px;
    }
    .report-box { 
        background-color: #f0f4f8; 
        border-top: 5px solid #1A729A; 
        padding: 25px; 
        border-radius: 15px; 
        margin-bottom: 30px; 
    }
    .stat-card { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        flex: 1;
        margin: 0 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바: 로그인 및 언어] ---
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

# --- [5. 메인 레이아웃 (수직 배치)] ---
st.title(L["title"])
st.caption(IP_MARK)

# 5.0 분석 결과 리포트 (버튼 클릭 시 상단에 노출)
report_placeholder = st.empty()

selected_mats, selected_params = {}, {}

# 5.1 소재 레시피 (Box 1)
if not mat_df.empty:
    st.markdown(f'<div class="section-box"><h3>{L["mat_sel"]}</h3>', unsafe_allow_html=True)
    cats = mat_df['Category'].unique()
    for i in range(0, len(cats), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(cats):
                cat = cats[i+j]
                with cols[j]:
                    m_list = mat_df[mat_df['Category'] == cat]['Name'].tolist()
                    selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"v_mat_{cat}")
    st.markdown('</div>', unsafe_allow_html=True)

# 5.2 공정 파라미터 (Box 2)
if not config_df.empty:
    st.markdown(f'<div class="section-box"><h3>{L["proc_param"]}</h3>', unsafe_allow_html=True)
    params = config_df.index.tolist()
    for i in range(0, len(params), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(params):
                p_name = params[i+j]
                with cols[j]:
                    cfg = config_df.loc[p_name]
                    selected_params[p_name] = st.slider(
                        f"{p_name}", float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step']),
                        key=f"v_p_{p_name}"
                    )
    st.markdown('</div>', unsafe_allow_html=True)

# 5.3 목표 설정 (Box 3)
st.markdown(f'<div class="section-box" style="background-color: #eef6fb;"><h3>{L["target_set"]}</h3>', unsafe_allow_html=True)
target_whkg = st.number_input(L["target_label"], value=160.0, step=1.0)
st.markdown('</div>', unsafe_allow_html=True)

# 5.4 디자인 서머리 (Box 4)
st.markdown(f'<div class="summary-box"><h3>{L["design_sum"]}</h3>', unsafe_allow_html=True)
sum_cols = st.columns([1])
with sum_cols[0]:
    # 가로로 나열하기 위해 태그 사용
    for cat, name in selected_mats.items():
        st.markdown(f'<span class="summary-item"><b>{cat}</b>: {name}</span>', unsafe_allow_html=True)
    st.write("") # 줄바꿈
    for p_name, val in selected_params.items():
        st.markdown(f'<span class="summary-item"><b>{p_name}</b>: {val}</span>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5.5 분석 실행 버튼
run_btn = st.button(L["run_btn"], use_container_width=True, type="primary")

# --- [6. 분석 로직 및 결과 리포트] ---
if run_btn and not mat_df.empty:
    try:
        c_name = selected_mats.get('Cathode', 'Default')
        c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
        ld = selected_params.get('Loading', 13.0)
        ice = selected_params.get('ICE', 85.0)
        
        # 예측 알고리즘 적용
        eff_cap = c_cap * (ice / 100.0) * 0.93
        whkg = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
        
        st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg, 1)})

        with report_placeholder.container():
            st.markdown(f'''<div class="report-box">
                <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                    <div class="stat-card"><h3>{whkg:.1f} Wh/kg</h3><small>{L["exp_energy"]}</small></div>
                    <div class="stat-card"><h3>{eff_cap:.1f} mAh/g</h3><small>{L["eff_cap"]}</small></div>
                    <div class="stat-card"><h3>{target_whkg}</h3><small>{L["target_label"]}</small></div>
                </div>
            </div>''', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Analysis Error: {e}")

# --- [7. 히스토리] ---
if st.session_state.history:
    st.divider()
    st.subheader(L["history"])
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])