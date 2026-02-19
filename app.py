import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime

# 1. 페이지 레이아웃 및 스타일 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 시노텍 네이비 스타일 적용
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #003366;
        color: white;
        border-radius: 5px;
        height: 3.5em;
        width: 100%;
        font-weight: bold;
        font-size: 18px;
    }
    .reportview-container .main .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 및 세션 상태 초기화
@st.cache_data
def load_data():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("param_config.xlsx")
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except:
        st.error("❌ 엑셀 파일 로드 실패. 파일명과 경로를 확인하세요.")
        return pd.DataFrame(), pd.DataFrame()

if 'history' not in st.session_state:
    st.session_state.history = []
if 'sim_count' not in st.session_state:
    st.session_state.sim_count = 0
if 'current_result' not in st.session_state:
    st.session_state.current_result = None

mat_df, param_dict = load_data()

# -----------------------------------------------------------------------------
# [상단] 로그인 및 헤더
# -----------------------------------------------------------------------------
lcol1, lcol2, lcol3 = st.columns([3, 1, 1])
with lcol1:
    st.title("🔋 SynoCore V1.4 Pro Max")
with lcol2:
    st.text_input("User ID", value="Synotech_Admin")
with lcol3:
    st.text_input("Password", type="password", value="****")

st.markdown("---")

# -----------------------------------------------------------------------------
# [1번] Material Selection (소재 라인업 확정)
# -----------------------------------------------------------------------------
st.header("1. Material Selection")
m1, m2, m3, m4 = st.columns(4)

with m1:
    cat_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
    cat_name = st.selectbox("Cathode (양극재)", cat_list)
    cat_row = mat_df[mat_df['Name'] == cat_name].iloc[0]
with m2:
    ano_list = mat_df[mat_df['Category'] == 'Anode']['Name'].tolist()
    ano_name = st.selectbox("Anode (음극재)", ano_list)
    ano_row = mat_df[mat_df['Name'] == ano_name].iloc[0]
with m3:
    elec_list = mat_df[mat_df['Category'] == 'Electrolyte']['Name'].tolist()
    elec_name = st.selectbox("Electrolyte (전해질)", elec_list)
with m4:
    sep_list = mat_df[mat_df['Category'] == 'Separator']['Name'].tolist()
    sep_name = st.selectbox("Separator (분리막)", sep_list)

# -----------------------------------------------------------------------------
# [2번] Material Specs (슬라이더 방식 전문가 모드)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("2. Material Specs Expert Mode (Property Tuning)")
expert_spec = st.checkbox("🔓 소재 고유 물성 직접 수정 활성화")

if expert_spec:
    sc1, sc2, sc3, sc4 = st.columns(4)
    c_cap = sc1.slider("Capacity (mAh/g)", 80.0, 220.0, float(cat_row['Base_Capacity']))
    c_volt = sc2.slider("Avg. Voltage (V)", 2.0, 4.5, float(cat_row['Base_Avg_Voltage']))
    c_dens = sc3.slider("True Density (g/cc)", 1.5, 4.0, float(cat_row['Base_True_Density']))
    c_life = sc4.slider("Base Life (Cycles)", 500, 10000, int(cat_row['Base_Life']))
else:
    c_cap, c_volt, c_dens, c_life = cat_row['Base_Capacity'], cat_row['Base_Avg_Voltage'], cat_row['Base_True_Density'], cat_row['Base_Life']
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Capacity", f"{c_cap} mAh/g")
    sc2.metric("Voltage", f"{c_volt} V")
    sc3.metric("Density", f"{c_dens} g/cc")
    sc4.metric("Life", f"{c_life} Cyc")

# -----------------------------------------------------------------------------
# [3번] Process Parameters (전해질 추가 및 전문가 해제)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("3. Process Parameters & (C) Electrolyte")
expert_param = st.checkbox("🔓 공정 파라미터 직접 수정 활성화")

# 스마트 프리셋
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

p1, p2, p3 = st.columns(3)
with p1:
    st.subheader("(A) Cathode")
    loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, value=st.session_state['loading'], disabled=not expert_param)
    cat_dens = st.slider("Cathode Density (g/cc)", 1.5, 3.5, value=st.session_state['cat_density'], disabled=not expert_param)
with p2:
    st.subheader("(B) Anode")
    np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, 0.01)
    ano_dens = st.slider("Anode Density (g/cc)", 0.8, 2.0, value=float(ano_row['Rec_Density']), disabled=not expert_param)
with p3:
    st.subheader("(C) Electrolyte")
    ec_ratio = st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
    active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, value=st.session_state['active_ratio'], disabled=not expert_param)

# -----------------------------------------------------------------------------
# [4번] Target Setting (에너지 밀도 -> C-rate 순서 변경)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("4. Target Configuration")
t1, t2 = st.columns(2)
target_energy = t1.slider("Goal Energy Density (Wh/kg)", 100, 250, 160)
target_crate = t2.slider("Test C-rate (출력 조건)", 0.1, 20.0, 1.0, 0.1)

# -----------------------------------------------------------------------------
# [5번] Simulation History & Run
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("5. Simulation History & Execution")

# 버튼 실행 로직
if st.button("🚀 RUN DESIGN SIMULATION"):
    st.session_state.sim_count += 1
    sim_id = f"{st.session_state.sim_count:03d}"
    
    # 계산 로직
    cell_v = c_volt - ano_row['Base_Avg_Voltage']
    crate_factor = np.exp(-0.025 * (target_crate - 1)) if target_crate > 1 else 1.0
    eff_cap = c_cap * crate_factor
    cat_cap_area = loading * (active_ratio / 100) * eff_cap
    ano_loading = (cat_cap_area * np_ratio) / (ano_row['Base_Capacity'] * (ano_row['Base_ICE']/100) * (active_ratio/100))
    wh_kg = (cat_cap_area / 1000 * cell_v) / ((loading + ano_loading + (cat_cap_area/1000*ec_ratio*1000) + 5)/1000)
    
    # 기록 추가 (최근 것이 위로)
    history_entry = {
        "ID": sim_id,
        "Summary": f"[{cat_name}/{ano_name}] L:{loading}, NP:{np_ratio}, C:{target_crate}C, E:{target_energy}Wh",
        "Result_Whkg": round(wh_kg, 1),
        "Result_V": round(cell_v, 2),
        "Data": {"wh_kg": wh_kg, "cell_v": cell_v, "eff_cap": eff_cap, "loading": loading, "ano_loading": ano_loading, "c_life": c_life, "crate": target_crate}
    }
    st.session_state.history.insert(0, history_entry)
    st.session_state.current_result = history_entry

# 이력 선택창
if st.session_state.history:
    hist_options = [f"{h['ID']} | {h['Summary']}" for h in st.session_state.history]
    selected_hist = st.selectbox("과거 시뮬레이션 기록 선택 (상세 결과 복원)", hist_options)
    # 선택 시 데이터 복원 로직
    selected_id = selected_hist.split(" | ")[0]
    st.session_state.current_result = next(h for h in st.session_state.history if h['ID'] == selected_id)

# -----------------------------------------------------------------------------
# [결과 출력] 엔지니어용 대시보드 및 그래프
# -----------------------------------------------------------------------------
if st.session_state.current_result:
    res = st.session_state.current_result
    st.markdown("---")
    st.subheader(f"📊 Simulation Result (Record #{res['ID']})")
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Energy Density", f"{res['Data']['wh_kg']:.1f} Wh/kg")
    r2.metric("Cell Voltage", f"{res['Data']['cell_v']:.2f} V")
    r3.metric("Effective Capacity", f"{res['Data']['eff_cap']:.1f} mAh/g")
    r4.metric("Est. Life", f"{int(res['Data']['c_life'] * (res['Data']['wh_kg']/160)):,} Cycles")

    # 그래프
    c_rates = np.linspace(0.1, 20, 50)
    retention = [np.exp(-0.025 * (c - 1)) * 100 if c > 1 else 100 for c in c_rates]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c_rates, y=retention, mode='lines', name='Retention', line=dict(color='#003366', width=3)))
    fig.add_vline(x=res['Data']['crate'], line_dash="dot", line_color="red")
    fig.update_layout(title="C-rate Capability Prediction", xaxis_title="C-rate", yaxis_title="Retention (%)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # 상세 설계 표
    st.table(pd.DataFrame({
        "Parameter": ["Cathode Loading", "Anode Loading", "N/P Ratio", "Selected C-rate"],
        "Value": [f"{res['Data']['loading']} mg/cm2", f"{res['Data']['ano_loading']:.2f} mg/cm2", f"{np_ratio}", f"{res['Data']['crate']} C"]
    }))