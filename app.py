import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 시스템 설정] ---
st.set_page_config(page_title="SynoCore Master V1.3", layout="wide")

# --- [2. UI 제어 CSS: 헤더 완전 제거 및 상단바 스타일링] ---
st.markdown("""
    <style>
    /* 1. 상단 기본 헤더/툴바/푸터 완전 박멸 */
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
    
    /* 2. 메인 앱 상단 여백 제거 */
    .block-container { padding-top: 1rem !important; }

    /* 3. 상단 커스텀 컨트롤 바 스타일 */
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

    /* 4. 섹션 스타일링 */
    .section-box { border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; background-color: #f8f9fa; margin-bottom: 15px; }
    .summary-box { border: 2px solid #1A729A; padding: 18px; border-radius: 12px; background-color: #ffffff; margin-bottom: 20px; }
    .summary-item { font-size: 0.9rem; margin-bottom: 3px !important; color: #333; line-height: 1.4 !important; }
    
    /* 5. 실행 버튼 */
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important; color: white !important;
        font-weight: bold; height: 50px; width: 100%;
    }
    
    /* 6. 하단 카피라이트 */
    .footer-text { text-align: center; color: #888; font-size: 0.8rem; margin-top: 30px; padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 다국어 및 데이터 로드] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore Master V1.3 | SIB Design Platform",
        "login_sub": "Access", "usage_label": "Free Usage",
        "target_set": "3. Target Setting", "design_sum": "4. Design Summary",
        "mat_sel": "1. Material Selection", "proc_param": "2. Process Parameters",
        "run_btn": "5. Run Master Analysis", "history": "Design History Log",
        "report_title": "DESIGN ANALYSIS REPORT", "graph_title": "Energy Density Simulation Graph",
        "target_label": "Target Energy Density (Wh/kg)", "exp_energy": "Expected Energy",
        "eff_cap": "Effective Capacity", "loading_label": "Cathode Loading", "auth_msg": "Master Activated"
    },
    "Korean": {
        "title": "SynoCore Master V1.3 | SIB 설계 플랫폼",
        "login_sub": "접속", "usage_label": "무료 이용",
        "target_set": "3. 목표 설정", "design_sum": "4. 디자인 서머리",
        "mat_sel": "1. 소재 레시피", "proc_param": "2. 공정 파라미터",
        "run_btn": "5. 분석 실행", "history": "설계 이력 로그",
        "report_title": "DESIGN ANALYSIS REPORT", "graph_title": "에너지 밀도 시뮬레이션 그래프",
        "target_label": "목표 에너지 밀도 (Wh/kg)", "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량", "loading_label": "양극 로딩량", "auth_msg": "마스터 활성화"
    }
}

def load_external_data():
    try:
        mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
        mat_df['Base_Capacity'] = pd.to_numeric(mat_df['Base_Capacity'].astype(str).str.strip(), errors='coerce').fillna(0)
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
        return mat_df, config_df
    except:
        return pd.DataFrame(), pd.DataFrame()

mat_df, config_df = load_external_data()

# --- [4. 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'usage_count' not in st.session_state: st.session_state.usage_count = 0
if 'last_result' not in st.session_state: st.session_state.last_result = None

# --- [5. 상단 커스텀 컨트롤 바 (사이드바 대신)] ---
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([1.5, 1, 1.5, 1.5, 1])

with t_col1:
    st.markdown(f"<h3 style='color:#1A729A; margin:0;'>SynoCore</h3>", unsafe_allow_html=True)
with t_col2:
    lang_sel = st.selectbox("🌐", ["English", "Korean"], label_visibility="collapsed")
    L = LANG_DICT[lang_sel]
with t_col3:
    u_email = st.text_input("Email", placeholder="Email", label_visibility="collapsed")
with t_col4:
    u_pw = st.text_input("Password", type="password", placeholder="PW", label_visibility="collapsed")
with t_col5:
    if st.button("Login", use_container_width=True):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(L["auth_msg"])
st.markdown('</div>', unsafe_allow_html=True)

# 무료 이용 횟수 표시
st.markdown(f'<div style="text-align:right; margin-top:-15px;"><span class="usage-badge">{L["usage_label"]}: {st.session_state.usage_count}/3</span></div>', unsafe_allow_html=True)

# --- [6. 메인 설계 UI (1~5 수직)] ---
st.title(L["title"])
st.caption("IP by Synotech | Energy11 Production Intelligence")

selected_mats, selected_params = {}, {}

# 1. 소재 선택
st.markdown(f'<div class="section-box"><h3>{L["mat_sel"]}</h3>', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

# 2. 공정 파라미터
st.markdown(f'<div class="section-box"><h3>{L["proc_param"]}</h3>', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

# 3. 목표 설정
st.markdown(f'<div class="section-box" style="background-color: #eef6fb;"><h3>{L["target_set"]}</h3>', unsafe_allow_html=True)
target_whkg = st.slider(L["target_label"], 100.0, 250.0, 160.0, 1.0)
st.markdown('</div>', unsafe_allow_html=True)

# 4. 디자인 서머리 (2분할)
st.markdown(f'<div class="summary-box"><h3>{L["design_sum"]}</h3>', unsafe_allow_html=True)
col_sum1, col_sum2 = st.columns(2)
with col_sum1:
    for cat, name in selected_mats.items():
        st.markdown(f'<p class="summary-item"><b>{cat}</b>: {name}</p>', unsafe_allow_html=True)
with col_sum2:
    for p_name, val in selected_params.items():
        st.markdown(f'<p class="summary-item"><b>{p_name}</b>: {val}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5. 분석 실행
if st.button(L["run_btn"], type="primary"):
    if not st.session_state.is_pro and st.session_state.usage_count >= 3:
        st.error("Limit reached.")
    else:
        try:
            c_name = selected_mats.get('Cathode', '')
            c_cap = float(mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0])
            ld = float(selected_params.get('Loading', 13.0))
            ice = float(selected_params.get('ICE', 85.0))
            eff_cap = c_cap * (ice / 100.0) * 0.93
            whkg_res = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
            st.session_state.last_result = {"whkg": whkg_res, "eff_cap": eff_cap, "target": target_whkg, "ld": ld}
            st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg_res, 1)})
            if not st.session_state.is_pro: st.session_state.usage_count += 1
            st.rerun()
        except: st.error("Calc Error.")

# --- [7. 하단 결과 리포트 및 그래프] ---
if st.session_state.history:
    st.divider()
    st.subheader(L["history"])
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])

if st.session_state.last_result:
    res = st.session_state.last_result
    st.markdown(f'''<div class="summary-box" style="background-color: #f0f4f8;">
        <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
        <div style="display: flex; justify-content: space-around;">
            <div style="text-align:center;"><h4>{res['whkg']:.1f} Wh/kg</h4><small>{L["exp_energy"]}</small></div>
            <div style="text-align:center;"><h4>{res['eff_cap']:.1f} mAh/g</h4><small>{L["eff_cap"]}</small></div>
            <div style="text-align:center;"><h4>{res['target']}</h4><small>{L["target_label"]}</small></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.subheader(L["graph_title"])
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff_cap'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(l_range, w_range, color='#1A729A', linewidth=2); ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=100)
    ax.set_xlabel('Loading (mg/cm2)'); ax.set_ylabel('Wh/kg'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)

st.markdown('<div class="footer-text">© Synotech Co., Ltd | All Rights Reserved</div>', unsafe_allow_html=True)