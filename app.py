import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# --- [1. 다국어 사전 정의] ---
LANG_DICT = {
    "KO": {
        "title": "SIB 설계 및 성능 분석 플랫폼",
        "login_sub": "🔐 마스터 권한 로그인",
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
        "auth_msg": "마스터 권한 승인됨",
        "master_features": "🛠️ 마스터 진단 정보 (Master Insights)",
        "graph_title": "에너지 밀도 시뮬레이션 그래프",
        "loading_label": "양극 로딩량"
    },
    "EN": {
        "title": "SIB Design & Performance Analysis Platform",
        "login_sub": "🔐 Master Access Login",
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
        "auth_msg": "Master Authorized",
        "master_features": "🛠️ Master Technical Insights",
        "graph_title": "Energy Density Simulation Graph",
        "loading_label": "Cathode Loading"
    }
}

# --- [2. 데이터 로드 엔진: XLSX 전용] ---
def load_external_data():
    files = os.listdir('.')
    mat_df, config_df = pd.DataFrame(), pd.DataFrame()
    # 요청대로 .xlsx 파일만 로딩
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

# CSS: 박스 레이아웃 및 서머리 줄간격 최적화
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .section-box { 
        border: 1px solid #e6e9ef; padding: 20px; border-radius: 12px; 
        background-color: #f8f9fa; margin-bottom: 15px; height: auto;
    }
    .summary-box { 
        border: 2px solid #1A729A; padding: 20px; border-radius: 12px; 
        background-color: #ffffff; margin-bottom: 20px; height: auto;
    }
    /* 서머리 아이템 줄간격 대폭 축소 */
    .summary-item { 
        font-size: 0.88rem; margin-bottom: 2px; color: #333; 
        border-bottom: 1px solid #f0f0f0; padding-bottom: 2px;
        display: inline-block; margin-right: 15px; line-height: 1.1;
    }
    .report-box { 
        background-color: #f0f4f8; border-top: 5px solid #1A729A; 
        padding: 25px; border-radius: 15px; margin-bottom: 30px; 
    }
    .stat-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; 
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); flex: 1; margin: 0 10px;
    }
    .master-insight-box {
        background-color: #fff4e6; border-left: 5px solid #fd7e14;
        padding: 15px; margin-bottom: 20px; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바: 로그인 및 언어] ---
with st.sidebar:
    st.markdown("<h2 style='color: #1A729A; text-align: center;'>SynoCore</h2>", unsafe_allow_html=True)
    lang_code = st.selectbox("🌐 Language / 언어", ["KO", "EN"])
    L = LANG_DICT[lang_code]
    st.divider()
    st.subheader(L["login_sub"])
    # ID 이메일 형식 및 placeholder 적용
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

# 상단 리포트 공간
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
                    selected_mats[cat] = st.selectbox(f"{cat}", m_list, key=f"mat_{cat}")
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
                        key=f"p_{p_name}"
                    )
    st.markdown('</div>', unsafe_allow_html=True)

# 5.3 목표 설정 (Box 3) - 슬라이더 방식, 초기값 160
st.markdown(f'<div class="section-box" style="background-color: #eef6fb;"><h3>{L["target_set"]}</h3>', unsafe_allow_html=True)
target_whkg = st.slider(L["target_label"], 100.0, 250.0, 160.0, 1.0)
st.markdown('</div>', unsafe_allow_html=True)

# 5.4 디자인 서머리 (Box 4) - 압축된 줄간격
st.markdown(f'<div class="summary-box"><h3>{L["design_sum"]}</h3>', unsafe_allow_html=True)
for cat, name in selected_mats.items():
    st.markdown(f'<span class="summary-item"><b>{cat}</b>: {name}</span>', unsafe_allow_html=True)
st.write("") 
for p_name, val in selected_params.items():
    st.markdown(f'<span class="summary-item"><b>{p_name}</b>: {val}</span>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5.5 마스터 전용 진단 정보 (관리자 전용)
if st.session_state.is_pro:
    st.markdown(f'<div class="master-insight-box"><h4>{L["master_features"]}</h4>', unsafe_allow_html=True)
    c_name = selected_mats.get('Cathode', '')
    if "프러시안" in c_name:
        st.warning("⚠️ [공정 알림] Prussian White 소재는 수분 관리가 생명입니다. 170°C 이상 진공 건조를 확인하십시오.")
    st.info("💡 [설계 팁] N/P Ratio 1.15 이상 설정 시 Sodium Plating 억제에 유리합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# 5.6 분석 실행 버튼
run_btn = st.button(L["run_btn"], use_container_width=True, type="primary")

# --- [6. 분석 로직 및 결과 리포트] ---
if run_btn and not mat_df.empty:
    try:
        c_name = selected_mats.get('Cathode', 'Default')
        c_cap = mat_df[mat_df['Name'] == c_name]['Base_Capacity'].values[0]
        ld = selected_params.get('Loading', 13.0)
        ice = selected_params.get('ICE', 85.0)
        
        # 에너지 밀도 연산 모델
        eff_cap = c_cap * (ice / 100.0) * 0.93
        whkg_res = (eff_cap * 3.1 * 0.38 * (ld / (ld + 4.9))) * 10
        
        st.session_state.history.append({"Time": time.strftime("%H:%M"), "Recipe": c_name, "Wh/kg": round(whkg_res, 1)})

        with report_placeholder.container():
            st.markdown(f'''<div class="report-box">
                <h3 style="text-align:center; color:#1A729A;">{L["report_title"]}</h3>
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                    <div class="stat-card"><h3>{whkg_res:.1f} Wh/kg</h3><small>{L["exp_energy"]}</small></div>
                    <div class="stat-card"><h3>{eff_cap:.1f} mAh/g</h3><small>{L["eff_cap"]}</small></div>
                    <div class="stat-card"><h3>{target_whkg}</h3><small>{L["target_label"]}</small></div>
                </div>
            </div>''', unsafe_allow_html=True)
            
            # --- 시뮬레이션 그래프 출력 ---
            st.subheader(L["graph_title"])
            l_range = np.linspace(5, 30, 50)
            w_range = (eff_cap * 3.1 * 0.38 * (l_range / (l_range + 4.9))) * 10
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(l_range, w_range, color='#1A729A', linewidth=2.5, label='Simulation Curve')
            ax.scatter(ld, whkg_res, color='#fd7e14', s=120, zorder=5, label='Current Point')
            ax.axvline(x=ld, color='#fd7e14', linestyle='--', alpha=0.5)
            ax.set_xlabel(f'{L["loading_label"]} (mg/cm2)')
            ax.set_ylabel('Energy Density (Wh/kg)')
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.legend()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Analysis Error: {e}")

# --- [7. 히스토리 로그] ---
if st.session_state.history:
    st.divider()
    st.subheader(L["history"])
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])