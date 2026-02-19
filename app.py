import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4: Expert SIB Simulator", layout="wide")

# 2. 데이터 로드 함수
@st.cache_data
def load_db():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("process_parameters.xlsx")
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 엑셀 파일을 읽을 수 없습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_db()

if mat_df.empty or param_dict.empty:
    st.stop()

# 3. 사이드바: 소재 선택
st.sidebar.header("1. Material Selection")
st.sidebar.markdown("---")

cathodes = mat_df[mat_df['Category'] == 'Cathode']
anodes = mat_df[mat_df['Category'] == 'Anode']

cat_name = st.sidebar.selectbox("Cathode Material", cathodes['Name'])
cat_row = cathodes[cathodes['Name'] == cat_name].iloc[0]

ano_name = st.sidebar.selectbox("Anode Material", anodes['Name'])
ano_row = anodes[anodes['Name'] == ano_name].iloc[0]

# 4. 메인 화면: 소재 물성 자동 표시
st.title("🔋 SynoCore: Expert Na-ion Battery Simulator")
st.markdown(f"### 2. Material Specs: **{cat_name}**")

col_info1, col_info2, col_info3, col_info4 = st.columns(4)
col_info1.metric("Capacity", f"{cat_row['Capacity']} mAh/g")
col_info2.metric("Avg. Voltage", f"{cat_row['Voltage']} V")
col_info3.metric("Base ICE", f"{cat_row['Base_ICE']} %")
col_info4.metric("True Density", f"{cat_row['True_Density']} g/cc")

st.divider()

# 5. 스마트 프리셋 로직 (소재 변경 시 슬라이더 값 업데이트)
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

if 'last_ano' not in st.session_state or st.session_state.last_ano != ano_name:
    st.session_state['ano_density'] = float(ano_row['Rec_Density'])
    st.session_state.last_ano = ano_name

# 6. 공정 파라미터 슬라이더 구역
st.markdown("### 3. Process Parameters (Auto-Preset Applied)")
use_custom = st.checkbox("🔓 Unlock Manual Adjustment (전문가 모드)", value=False)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🅰️ Cathode Settings")
    p_load = param_dict.loc['loading']
    loading = st.slider(
        label=f"{p_load['Label_Name']} ({p_load['Unit']})",
        min_value=float(p_load['Min']),
        max_value=float(p_load['Max']),
        key='loading',
        step=float(p_load['Step']),
        disabled=not use_custom
    )

    p_c_den = param_dict.loc['cat_density']
    cat_density = st.slider(
        label=f"{p_c_den['Label_Name']} ({p_c_den['Unit']})",
        min_value=float(p_c_den['Min']),
        max_value=float(p_c_den['Max']),
        key='cat_density',
        step=float(p_c_den['Step']),
        disabled=not use_custom
    )

with col_right:
    st.subheader("🅱️ Anode & Balance")
    p_np = param_dict.loc['np_ratio']
    np_ratio = st.slider(
        label=p_np['Label_Name'],
        min_value=float(p_np['Min']),
        max_value=float(p_np['Max']),
        value=1.15,
        step=float(p_np['Step'])
    )

    p_a_den = param_dict.loc['ano_density']
    # 이전 오류 지점: 아래 코드가 잘리지 않도록 확인
    ano_density = st.slider(
        label=f"{p_a_den['Label_Name']} ({p_a_den['Unit']})",
        min_value=float(p_a_den['Min']),
        max_value=float(p_a_den['Max']),
        key='ano_density',
        step=float(p_a_den['Step']),
        disabled=not use_custom
    )

    p_act = param_dict.loc['active_ratio']
    active_ratio = st.slider(
        label=f"{p_act['Label_Name']} ({p_act['Unit']})",
        min_value=float(p_act['Min']),
        max_value=float(p_act['Max']),
        key='active_ratio',
        step=float(p_act['Step']),
        disabled=not use_custom
    )

# 7. 시뮬레이션 실행 및 결과
st.markdown("---")
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    # 정밀 계산 로직
    cell_v = cat_row['Voltage'] - ano_row['Voltage']
    cat_cap_area = loading * (active_ratio / 100) * cat_row['Capacity']
    ano_cap_req = cat_cap_area * np_ratio
    # 음극 로딩 역산 (효율 반영)
    ano_loading = ano_cap_req / (ano_row['Capacity'] * (ano_row['Base_ICE']/100) * (active_ratio/100))
    
    # 에너지 밀도 환산 (무게/부피)
    wh_kg = (cat_cap_area / 1000 * cell_v) / ((loading + ano_loading + 10) / 1000) # 간이 무게 팩터 포함
    wh_l = wh_kg * 1.6 # SIB 평균 밀도 보정
    
    st.success("✅ 시뮬레이션 완료")
    res1, res2, res3 = st.columns(3)
    res1.metric("무게 에너지 밀도", f"{wh_kg:.1f} Wh/kg")
    res2.metric("부피 에너지 밀도", f"{wh_l:.1f} Wh/L")
    res3.metric("예상 수명", f"{cat_row['Base_Life']} Cycles")