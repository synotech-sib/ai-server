import streamlit as st
import pandas as pd
import os

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="SynoCore V1.4", layout="wide")

# -----------------------------------------------------------------------------
# [디자인 복구] 상단 로그인 섹션
# -----------------------------------------------------------------------------
login_col1, login_col2, login_col3 = st.columns([3, 1, 1])
with login_col1:
    st.title("🔋 SynoCore: Expert SIB Simulator")
with login_col2:
    st.text_input("User ID", value="Synotech_Admin", key="user_id")
with login_col3:
    st.text_input("Password", type="password", value="****", key="user_pw")

st.markdown("---")

# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        mat_file = "material_list.xlsx"
        param_file = "param_config.xlsx"
        
        if not os.path.exists(mat_file) or not os.path.exists(param_file):
            st.error("❌ 엑셀 파일이 없습니다. 파일명을 확인해주세요.")
            return pd.DataFrame(), pd.DataFrame()

        mat_df = pd.read_excel(mat_file)
        param_df = pd.read_excel(param_file)

        # 컬럼명 표준화 (KeyError 방지)
        new_cols = [
            "Category", "Name", "Base_Capacity", "Base_Avg_Voltage", 
            "Base_True_Density", "Base_Life", "Base_ICE", 
            "Rec_Loading", "Rec_Density", "Rec_Active"
        ]
        if len(mat_df.columns) >= len(new_cols):
            mat_df = mat_df.iloc[:, :len(new_cols)]
            mat_df.columns = new_cols
        
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 데이터 로딩 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_data()

if mat_df.empty or param_dict.empty:
    st.stop()

# -----------------------------------------------------------------------------
# [복구] 1. Material Selection (메인 화면 상단 배치)
# -----------------------------------------------------------------------------
st.header("1. Material Selection")
m_col1, m_col2, m_col3 = st.columns(3)

cathodes = mat_df[mat_df['Category'] == 'Cathode']
anodes = mat_df[mat_df['Category'] == 'Anode']

with m_col1:
    cat_name = st.selectbox("Cathode (양극재 선택)", cathodes['Name'])
    cat_row = cathodes[cathodes['Name'] == cat_name].iloc[0]

with m_col2:
    ano_name = st.selectbox("Anode (음극재 선택)", anodes['Name'])
    ano_row = anodes[anodes['Name'] == ano_name].iloc[0]

with m_col3:
    st.selectbox("Electrolyte/Separator", ["Standard SIB Set", "High-Temp Set", "Low-Cost Set"])

# 스마트 프리셋 로직 (소재 변경 시 슬라이더 값 동기화)
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

if 'last_ano' not in st.session_state or st.session_state.last_ano != ano_name:
    st.session_state['ano_density'] = float(ano_row['Rec_Density'])
    st.session_state.last_ano = ano_name

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. Material Specs (자동 표시 섹션)
# -----------------------------------------------------------------------------
st.header(f"2. Material Specs: {cat_name}")
col_i1, col_i2, col_i3, col_i4 = st.columns(4)
col_i1.metric("Capacity", f"{cat_row['Base_Capacity']} mAh/g")
col_i2.metric("Avg. Voltage", f"{cat_row['Base_Avg_Voltage']} V")
col_i3.metric("True Density", f"{cat_row['Base_True_Density']} g/cm³")
col_i4.metric("Base Life", f"{cat_row['Base_Life']} Cycles")

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. Process Parameters (슬라이더 섹션)
# -----------------------------------------------------------------------------
st.header("3. Process Parameters")
use_custom = st.checkbox("🔓 Unlock Manual Adjustment (전문가 모드)", value=False)

p_col1, p_col2 = st.columns(2)

with p_col1:
    st.subheader("🅰️ Cathode Settings")
    p_load = param_dict.loc['loading']
    loading = st.slider(label=p_load['Label_Name'], min_value=float(p_load['Min']), max_value=float(p_load['Max']), key='loading', step=float(p_load['Step']), disabled=not use_custom)
    
    p_c_den = param_dict.loc['cat_density']
    cat_density = st.slider(label=p_c_den['Label_Name'], min_value=float(p_c_den['Min']), max_value=float(p_c_den['Max']), key='cat_density', step=float(p_c_den['Step']), disabled=not use_custom)

with p_col2:
    st.subheader("🅱️ Anode & Balance")
    p_np = param_dict.loc['np_ratio']
    np_ratio = st.slider(label=p_np['Label_Name'], min_value=float(p_np['Min']), max_value=float(p_np['Max']), value=float(p_np['Default']), step=float(p_np['Step']))

    p_a_den = param_dict.loc['ano_density']
    ano_density = st.slider(label=p_a_den['Label_Name'], min_value=float(p_a_den['Min']), max_value=float(p_a_den['Max']), key='ano_density', step=float(p_a_den['Step']), disabled=not use_custom)

    p_act = param_dict.loc['active_ratio']
    active_ratio = st.slider(label=p_act['Label_Name'], min_value=float(p_act['Min']), max_value=float(p_act['Max']), key='active_ratio', step=float(p_act['Step']), disabled=not use_custom)

# -----------------------------------------------------------------------------
# 4. 시뮬레이션 결과
# -----------------------------------------------------------------------------
st.markdown("---")
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    # 설계 로직 계산
    cell_v = cat_row['Base_Avg_Voltage'] - ano_row['Base_Avg_Voltage']
    cat_cap_area = loading * (active_ratio / 100) * cat_row['Base_Capacity']
    ano_cap_req = cat_cap_area * np_ratio
    ano_loading = ano_cap_req / (ano_row['Base_Capacity'] * (ano_row['Base_ICE']/100) * (active_ratio/100))
    
    # 에너지 밀도 계산
    total_weight_mg = loading + ano_loading + 10 
    wh_kg = (cat_cap_area / 1000 * cell_v) / (total_weight_mg / 1000)
    
    st.success("✅ 시뮬레이션이 완료되었습니다.")
    res1, res2, res3 = st.columns(3)
    res1.metric("Gravimetric Energy Density", f"{wh_kg:.1f} Wh/kg")
    res2.metric("Volumetric Energy Density", f"{wh_kg * 1.6:.1f} Wh/L")
    res3.metric("Estimated Cycle Life", f"{cat_row['Base_Life']} Cycles")