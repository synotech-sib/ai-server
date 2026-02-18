import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 시스템 초기 설정] ---
st.set_page_config(
    page_title="SynoCore Master V1.3",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- [2. UI 제어 CSS: 헤더 박멸 및 사이드바 버튼 커스텀] ---
st.markdown("""
    <style>
    /* 1. 상단 툴바/헤더/푸터 강제 박멸 */
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer { visibility: hidden !important; height: 0px !important; }
    
    /* 2. 사이드바 접기/펴기 버튼(화살표) 커스텀: 크기 키우고 로고색 적용 */
    button[kind="headerNoPadding"] {
        visibility: visible !important;
        position: fixed !important;
        top: 20px !important;
        left: 20px !important;
        z-index: 1000001 !important;
        background-color: #ffffff !important;
        border: 2px solid #1A729A !important; /* 시노텍 블루 테두리 */
        border-radius: 8px !important;
        width: 45px !important;
        height: 45px !important;
        color: #1A729A !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* 3. 사이드바 내부 불필요한 메뉴 제거 */
    [data-testid="stSidebarNav"] { display: none !important; }

    .stApp { background-color: #ffffff; }
    .section-box { border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; background-color: #f8f9fa; margin-bottom: 15px; }
    
    /* 4. 무료 횟수 하이라이트 */
    .usage-badge { 
        background-color: #1A729A; 
        color: white; 
        padding: 8px 15px; 
        border-radius: 25px; 
        font-size: 0.9rem; 
        font-weight: bold;
    }
    
    .summary-box { border: 2px solid #1A729A; padding: 18px; border-radius: 12px; background-color: #ffffff; margin-bottom: 20px; }
    .summary-item { font-size: 0.9rem; margin-bottom: 3px !important; color: #333; line-height: 1.4 !important; }
    
    /* 5. 메인 분석 버튼 */
    div.stButton > button[kind="primary"] {
        background-color: #1A729A !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
        height: 50px;
    }
    .sidebar-footer { position: fixed; bottom: 20px; left: 20px; font-size: 0.8rem; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 다국어 사전 정의] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore Master V1.3 | SIB Design Platform",
        "login_sub": "Access Login",
        "usage_label": "Free Usage",
        "usage_limit_msg": "Free limit (3/3) reached. Please register for Pro.",
        "target_set": "3. Target Setting",
        "design_sum": "4. Design Summary",
        "mat_sel": "1. Material Selection",
        "proc_param": "2. Process Parameters",
        "run_btn": "5. Run Master Analysis",
        "history": "Design History Log",
        "report_title": "DESIGN ANALYSIS REPORT",
        "graph_title": "Energy Density Simulation Graph",
        "target_label": "Target Energy Density (Wh/kg)",
        "exp_energy": "Expected Energy Density",
        "eff_cap": "Effective Capacity",
        "loading_label": "Cathode Loading",
        "auth_msg": "Master Mode Activated"
    },
    "Korean": {
        "title": "SynoCore Master V1.3 | SIB 설계 플랫폼",
        "login_sub": "접속 로그인",
        "usage_label": "무료 이용 횟수",
        "usage_limit_msg": "무료 이용 횟수(3회)를 초과했습니다. Pro 등록이 필요합니다.",
        "target_set": "3. 목표 설정",
        "design_sum": "4. 디자인 서머리",
        "mat_sel": "1. 소재 레시피",
        "proc_param": "2. 공정 파라미터",
        "run_btn": "5. 분석 실행",
        "history": "설계 이력 로그",
        "report_title": "DESIGN ANALYSIS REPORT",
        "graph_title": "에너지 밀도 시뮬레이션 그래프",
        "target_label": "목표 에너지 밀도 (Wh/kg)",
        "exp_energy": "예상 에너지 밀도",
        "eff_cap": "실효 가역 용량",
        "loading_label": "양극 로딩량",
        "auth_msg": "마스터 모드 활성화됨"
    }
}

# --- [4. 데이터 로드 엔진: 데이터 타입 정제 강화] ---
def load_external_data():
    files = os.listdir('.')
    mat_df, config_df = pd.DataFrame(), pd.DataFrame()
    try:
        if 'material_list.xlsx' in files:
            mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
            # 텍스트가 섞여있거나 공백이 있는 경우 처리
            mat_df['Base_Capacity'] = pd.to_numeric(mat_df['Base_Capacity'].astype(str).str.strip(), errors='coerce').fillna(0)
        if 'param_config.xlsx' in files:
            config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
    except Exception as e:
        st.error(f"Excel Load Error: {e}")
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [5. 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'usage_count' not in st.session_state: st.session_state.usage_count = 0
if 'last_result' not in st.session_state: st.session_state.last_result = None

# --- [6. 사이드바] ---
with st.sidebar:
    st.markdown("<h2 style='color: #1A729A; text-align: center; margin-top: 20px;'>SynoCore</h2>", unsafe_allow_html=True)
    lang_sel = st.selectbox("Language", ["English", "Korean"])
    L = LANG_DICT[lang_sel]
    
    st.divider()
    usage_text = f"{L['usage_label']}: {st.session_state.usage_count}/3"
    st.markdown(f'<div style="text-align:center;"><span class="usage-badge">{usage_text}</span></div>', unsafe_allow_html=True)
    
    st.divider()
    st.subheader(L["login_sub"])
    u_email = st.text_input("Email", placeholder="your@email.com")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(L["auth_msg"])
    
    if st.button("Reset All"):
        st.session_state.history = []; st.session_state.usage_count = 0
        st.session_state.last_result = None; st.rerun()

    st.markdown('<div class="sidebar-footer">© Synotech Co., Ltd</div>', unsafe_allow_html=True)

# --- [7. 메인 패널] ---
st.title(L["title"])
st.caption("IP by Synotech | Energy11 Production Intelligence")

selected_mats, selected_params = {}, {}

# 1. 소재 선택
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
                    selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"mat_{cat}")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. 공정 파라미터
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
if st.button(L["run_btn"], use_container_width=True, type="primary"):
    if not st.session_state.is_pro and st.session_state.usage_count >= 3:
        st.error(L["usage_limit_msg"])
    else:
        try:
            c_name = selected_mats.get('Cathode', '')
            c_data = mat_df[mat_df['Name'] == c_name]
            if not c_data.empty:
                c_cap = float(c_data['Base_Capacity'].values[0])
                ld = float(selected_params.get('Loading', 13.0))
                ice = float(selected_params.get('ICE', 85.0))
                
                # 계산식 보호 로직
                if c_cap <= 0: raise ValueError("Capacity must be > 0")
                
                eff_cap = c_cap * (ice / 100.0) * 0.93
                whkg_res = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
                
                st.session_state.last_result = {"whkg": whkg_res, "eff_cap": eff_cap, "target": target_whkg, "ld": ld}
                st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg_res, 1)})
                if not st.session_state.is_pro: st.session_state.usage_count += 1
                st.rerun()
        except Exception as e:
            st.error(f"Computation Error: {e}. Check if Excel Base_Capacity has valid numbers.")

# --- [8. 하단 결과부] ---
if st.session_state.history:
    st.divider(); st.subheader(L["history"])
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])

if st.session_state.last_result:
    res = st.session_state.last_result
    st.markdown(f'''<div class="report-box">
        <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
        <div style="display: flex; justify-content: space-around;">
            <div class="stat-card"><h3>{res['whkg']:.1f} Wh/kg</h3><small>{L["exp_energy"]}</small></div>
            <div class="stat-card"><h3>{res['eff_cap']:.1f} mAh/g</h3><small>{L["eff_cap"]}</small></div>
            <div class="stat-card"><h3>{res['target']}</h3><small>{L["target_label"]}</small></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.subheader(L["graph_title"])
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff_cap'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(l_range, w_range, color='#1A729A', linewidth=2.5)
    ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=150, zorder=5)
    ax.set_xlabel('Cathode Loading (mg/cm2)'); ax.set_ylabel('Energy Density (Wh/kg)'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)