import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 다국어 및 라벨 정의] ---
LANG_DICT = {
    "Korean": {
        "title": "SynoCore Master V1.3 | SIB 설계 플랫폼",
        "login_sub": "🔐 마스터 로그인",
        "pro_reg": "💎 Professional 등록",
        "usage_label": "무료 이용 횟수",
        "usage_limit_msg": "무료 이용 횟수(3회)를 초과했습니다. Pro 등록이 필요합니다.",
        "target_set": "🎯 3. 목표 설정",
        "design_sum": "📋 4. 디자인 서머리",
        "mat_sel": "🧪 1. 소재 레시피",
        "proc_param": "⚙️ 2. 공정 파라미터",
        "run_btn": "🚀 5. 분석 실행",
        "history": "🔄 설계 이력 로그 (History Log)",
        "report_title": "DESIGN ANALYSIS REPORT",
        "graph_title": "에너지 밀도 시뮬레이션 그래프",
        "master_features": "🛠️ 마스터 진단 정보",
        "reg_btn": "등록 신청하기"
    },
    "English": {
        "title": "SynoCore Master V1.3 | SIB Design Platform",
        "login_sub": "🔐 Master Login",
        "pro_reg": "💎 Pro Registration",
        "usage_label": "Free Usage",
        "usage_limit_msg": "Free limit (3/3) reached. Please register for Pro.",
        "target_set": "🎯 3. Target Setting",
        "design_sum": "📋 4. Design Summary",
        "mat_sel": "🧪 1. Material Selection",
        "proc_param": "⚙️ 2. Process Parameters",
        "run_btn": "🚀 5. Run Analysis",
        "history": "🔄 Design History Log",
        "report_title": "DESIGN ANALYSIS REPORT",
        "graph_title": "Energy Density Simulation Graph",
        "master_features": "🛠️ Master Technical Insights",
        "reg_btn": "Register Now"
    }
}

# --- [2. 데이터 로드] ---
def load_external_data():
    files = os.listdir('.')
    mat_df, config_df = pd.DataFrame(), pd.DataFrame()
    if 'material_list.xlsx' in files:
        mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [3. 시스템 초기화 및 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'usage_count' not in st.session_state: st.session_state.usage_count = 0
if 'last_result' not in st.session_state: st.session_state.last_result = None

IP_MARK = "IP by Synotech | Energy11 Production Intelligence"
st.set_page_config(page_title="SynoCore Master V1.3", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .section-box { border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; background-color: #f8f9fa; margin-bottom: 15px; }
    .summary-box { border: 2px solid #1A729A; padding: 20px; border-radius: 12px; background-color: #ffffff; margin-bottom: 20px; }
    .summary-item { font-size: 0.88rem; margin-bottom: 2px; color: #333; display: inline-block; margin-right: 15px; line-height: 1.1; }
    .report-box { background-color: #f0f4f8; border-top: 5px solid #1A729A; padding: 25px; border-radius: 15px; margin: 30px 0; }
    .stat-card { background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); flex: 1; margin: 0 10px; }
    .usage-badge { background-color: #1A729A; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바: 로그인, 언어, Pro 등록] ---
with st.sidebar:
    st.markdown("<h2 style='color: #1A729A; text-align: center;'>SynoCore</h2>", unsafe_allow_html=True)
    lang_sel = st.selectbox("🌐 Language", ["Korean", "English"])
    L = LANG_DICT[lang_sel]
    
    # 무료 횟수 표시
    st.divider()
    usage_text = f"{L['usage_label']}: {st.session_state.usage_count}/3"
    st.markdown(f'<div style="text-align:center;"><span class="usage-badge">{usage_text}</span></div>', unsafe_allow_html=True)
    
    # Pro 등록 섹션
    st.divider()
    st.subheader(L["pro_reg"])
    if not st.session_state.is_pro:
        reg_email = st.text_input("Email for Registration", placeholder="your@email.com")
        reg_company = st.text_input("Company", placeholder="Energy11")
        if st.button(L["reg_btn"]):
            st.info("Registration request sent to Master Admin.")
    
    # 마스터 로그인
    st.divider()
    st.subheader(L["login_sub"])
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success("Welcome, Master.")
    
    if st.button("🗑️ Clear Log"):
        st.session_state.history = []; st.session_state.usage_count = 0
        st.session_state.last_result = None; st.rerun()

# --- [5. 메인 UI (수직)] ---
st.title(L["title"])
st.caption(IP_MARK)

selected_mats, selected_params = {}, {}

# 5.1 소재 레시피
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

# 5.2 공정 파라미터
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
                    selected_params[p_name] = st.slider(f"{p_name}", float(cfg['Min']), float(cfg['Max']), float(cfg['Default']), float(cfg['Step']), key=f"v_p_{p_name}")
    st.markdown('</div>', unsafe_allow_html=True)

# 5.3 목표 설정 (슬라이더 초기값 160)
st.markdown(f'<div class="section-box" style="background-color: #eef6fb;"><h3>{L["target_set"]}</h3>', unsafe_allow_html=True)
target_whkg = st.slider(L["target_label"], 100.0, 250.0, 160.0, 1.0)
st.markdown('</div>', unsafe_allow_html=True)

# 5.4 디자인 서머리
st.markdown(f'<div class="summary-box"><h3>{L["design_sum"]}</h3>', unsafe_allow_html=True)
for cat, name in selected_mats.items():
    st.markdown(f'<span class="summary-item"><b>{cat}</b>: {name}</span>', unsafe_allow_html=True)
st.write("") 
for p_name, val in selected_params.items():
    st.markdown(f'<span class="summary-item"><b>{p_name}</b>: {val}</span>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5.5 마스터 진단 정보
if st.session_state.is_pro:
    st.info(f"💡 {L['master_features']}: Prussian White 소재는 고온 건조가 성능의 90%를 결정합니다.")

# 5.6 분석 실행 버튼 (횟수 제한 로직)
if st.button(L["run_btn"], use_container_width=True, type="primary"):
    if not st.session_state.is_pro and st.session_state.usage_count >= 3:
        st.error(L["usage_limit_msg"])
    else:
        try:
            c_name = selected_mats.get('Cathode', 'Default')
            c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
            ld = selected_params.get('Loading', 13.0)
            ice = selected_params.get('ICE', 85.0)
            eff_cap = c_cap * (ice / 100.0) * 0.93
            whkg_res = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
            
            st.session_state.last_result = {"whkg": whkg_res, "eff_cap": eff_cap, "target": target_whkg, "ld": ld}
            st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg_res, 1)})
            if not st.session_state.is_pro: st.session_state.usage_count += 1
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- [6. 하단 배치: 히스토리 -> 결과값 -> 그래프] ---
if st.session_state.history:
    st.divider()
    st.subheader(L["history"])
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
    
    # 그래프
    st.subheader(L["graph_title"])
    l_range = np.linspace(5, 30, 50)
    w_range = (res['eff_cap'] * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(l_range, w_range, color='#1A729A', linewidth=2); ax.scatter(res['ld'], res['whkg'], color='#fd7e14', s=100)
    ax.set_xlabel('Loading'); ax.set_ylabel('Wh/kg'); ax.grid(True, alpha=0.3)
    st.pyplot(fig)