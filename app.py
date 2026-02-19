import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. 페이지 레이아웃 및 스타일 설정
st.set_page_config(page_title="SynoCore V1.4 Pro", layout="wide")

# 버튼 색상 커스텀 (시노텍 로고색: #003366)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #003366;
        color: white;
        border-radius: 5px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("param_config.xlsx")
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 데이터 로딩 실패: {e}")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_data()

# -----------------------------------------------------------------------------
# [상단] 로그인 바 (이전 디자인 유지)
# -----------------------------------------------------------------------------
login_col1, login_col2, login_col3 = st.columns([3, 1, 1])
with login_col1:
    st.title("🔋 SynoCore V1.4 Pro")
with login_col2:
    st.text_input("User ID", value="Synotech_Admin")
with login_col3:
    st.text_input("Password", type="password", value="****")

st.markdown("---")

# -----------------------------------------------------------------------------
# [1번] Material Selection (전해질/분리막 분리)
# -----------------------------------------------------------------------------
st.header("1. Material Selection")
m1, m2, m3, m4 = st.columns(4)

with m1:
    cat_list = mat_df[mat_df['Category'] == 'Cathode']['Name']
    cat_name = st.selectbox("Cathode (양극)", cat_list)
    cat_row = mat_df[mat_df['Name'] == cat_name].iloc[0]
with m2:
    ano_list = mat_df[mat_df['Category'] == 'Anode']['Name']
    ano_name = st.selectbox("Anode (음극)", ano_list)
    ano_row = mat_df[mat_df['Name'] == ano_name].iloc[0]
with m3:
    elec_list = mat_df[mat_df['Category'] == 'Electrolyte']['Name']
    elec_name = st.selectbox("Electrolyte (전해질)", elec_list)
    elec_row = mat_df[mat_df['Name'] == elec_name].iloc[0]
with m4:
    sep_list = mat_df[mat_df['Category'] == 'Separator']['Name']
    sep_name = st.selectbox("Separator (분리막)", sep_list)
    sep_row = mat_df[mat_df['Name'] == sep_name].iloc[0]

# -----------------------------------------------------------------------------
# [2번] Material Specs (전문가 모드: 소재 스펙 수정)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("2. Material Specs & Expert Override")
expert_mode_spec = st.checkbox("🔓 Enable Expert Mode: Edit Material Properties")

# 기본값 로드
c_cap, c_volt, c_dens, c_life = cat_row['Base_Capacity'], cat_row['Base_Avg_Voltage'], cat_row['Base_True_Density'], cat_row['Base_Life']

if expert_mode_spec:
    sc1, sc2, sc3, sc4 = st.columns(4)
    c_cap = sc1.number_input("Cathode Capacity (mAh/g)", value=float(c_cap))
    c_volt = sc2.number_input("Avg. Voltage (V)", value=float(c_volt))
    c_dens = sc3.number_input("True Density (g/cc)", value=float(c_dens))
    c_life = sc4.number_input("Base Life (Cycles)", value=int(c_life))
else:
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Capacity", f"{c_cap} mAh/g")
    sc2.metric("Avg. Voltage", f"{c_volt} V")
    sc3.metric("True Density", f"{c_dens} g/cc")
    sc4.metric("Base Life", f"{c_life} Cycles")

# -----------------------------------------------------------------------------
# [3번] Process Parameters (전해질 섹션 추가)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("3. Process Parameters")
expert_mode_param = st.checkbox("🔓 Enable Expert Mode: Unlock Sliders")

# 스마트 프리셋 로직
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

p_col1, p_col2, p_col3 = st.columns(3)

with p_col1:
    st.subheader("(A) Cathode Settings")
    loading = st.slider("Loading Level (mg/cm2)", 5.0, 40.0, value=st.session_state['loading'], disabled=not expert_mode_param)
    cat_dens_val = st.slider("Cathode Density (g/cc)", 1.5, 3.5, value=st.session_state['cat_density'], disabled=not expert_mode_param)

with p_col2:
    st.subheader("(B) Anode & Balance")
    np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, 0.01)
    ano_dens_val = st.slider("Anode Density (g/cc)", 0.8, 2.0, value=float(ano_row['Rec_Density']), disabled=not expert_mode_param)

with p_col3:
    st.subheader("(C) Electrolyte & Additive")
    # 전해질 함량(E/C Ratio) 파라미터 추가
    ec_ratio = st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, help="용량 대비 전해질 투입량")
    active_material_ratio = st.slider("Active Material (%)", 85.0, 99.0, value=st.session_state['active_ratio'], disabled=not expert_mode_param)

# -----------------------------------------------------------------------------
# [4번] Target Setting (목표값 지정)
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("4. Target Goals")
tc1, tc2 = st.columns(2)
target_crate = tc1.slider("Simulation C-rate (출력 조건)", 0.1, 20.0, 1.0, 0.1)
target_energy = tc2.slider("Target Energy Density Goal (Wh/kg)", 100, 250, 160)

# -----------------------------------------------------------------------------
# [5번] Summary & Simulation Run
# -----------------------------------------------------------------------------
st.markdown("---")
st.header("5. Configuration Summary")
summary_data = {
    "Material": [cat_name, ano_name, elec_name, sep_name],
    "Key Spec": [f"{c_cap} mAh/g", f"{ano_row['Base_Capacity']} mAh/g", f"Density: {elec_row['Base_True_Density']}", f"Density: {sep_row['Base_True_Density']}"]
}
st.table(pd.DataFrame(summary_data, index=["Cathode", "Anode", "Electrolyte", "Separator"]))

if st.button("🚀 RUN DESIGN SIMULATION"):
    # 시뮬레이션 계산 로직
    # 1. 전압 및 면적당 용량
    cell_voltage = c_volt - ano_row['Base_Avg_Voltage']
    # C-rate에 따른 용량 감소 모델 (Peukert 효과 간이 적용)
    crate_factor = np.exp(-0.02 * (target_crate - 1)) if target_crate > 1 else 1.0
    effective_cap = c_cap * crate_factor
    
    cat_cap_area = loading * (active_material_ratio / 100) * effective_cap
    
    # 2. 무게 계산
    ano_loading = (cat_cap_area * np_ratio) / (ano_row['Base_Capacity'] * (ano_row['Base_ICE']/100) * (active_material_ratio/100))
    elec_weight = (cat_cap_area / 1000) * ec_ratio # Ah * g/Ah
    total_weight = (loading + ano_loading + elec_weight + 5) / 1000 # mg -> g (단위면적)
    
    # 3. 결과 도출
    wh_kg = (cat_cap_area / 1000 * cell_voltage) / total_weight
    
    # 결과 표시
    st.balloons()
    st.success("✅ Simulation Completed for Professional Engineers")
    
    # 엔지니어용 데이터 보드
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Energy Density", f"{wh_kg:.1f} Wh/kg", f"{wh_kg - target_energy:.1f} vs Goal")
    res2.metric("Effective Cap (at C-rate)", f"{effective_cap:.1f} mAh/g")
    res3.metric("Total Thickness", f"{(loading/cat_dens_val + ano_loading/ano_dens_val)*10 + 30:.1f} μm")
    res4.metric("Est. Cycle Life", f"{int(c_life * crate_factor):,} Cycles")

    # 그래프: C-rate별 용량 유지율 예측 (엔지니어 필수 관심사)
    st.subheader("📈 Engineering Analysis: Capacity Retention by C-rate")
    c_rates = np.linspace(0.1, 20, 50)
    retention = [np.exp(-0.02 * (c - 1)) * 100 if c > 1 else 100 for c in c_rates]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c_rates, y=retention, mode='lines', name='Retention', line=dict(color='#003366', width=3)))
    fig.add_hline(y=retention[int(target_crate*2.5)], line_dash="dot", annotation_text=f"Selected: {target_crate}C")
    fig.update_layout(title="Rate Capability Prediction", xaxis_title="C-rate", yaxis_title="Capacity Retention (%)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # 상세 설계 데이터 테이블
    st.subheader("📋 Detailed Design Parameters")
    detailed_df = pd.DataFrame({
        "Parameter": ["Cathode Loading", "Anode Loading", "Electrolyte Weight", "N/P Ratio", "Cell Voltage"],
        "Value": [f"{loading} mg/cm2", f"{ano_loading:.2f} mg/cm2", f"{elec_weight:.2f} mg/cm2", f"{np_ratio}", f"{cell_voltage:.2f} V"]
    })
    st.table(detailed_df)