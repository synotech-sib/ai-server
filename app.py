import streamlit as st
import pandas as pd
import os

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="SynoCore V1.4: Expert SIB Simulator", layout="wide")

# 2. 데이터 로드 함수 (파일명: 이미지 4 기준 반영)
@st.cache_data
def load_data():
    try:
        # 파일 경로 확인 (현재 폴더 기준)
        mat_file = "material_list.xlsx"
        param_file = "param_config.xlsx"
        
        if not os.path.exists(mat_file) or not os.path.exists(param_file):
            st.error(f"❌ 파일을 찾을 수 없습니다. (현재 폴더 확인 필수)")
            return pd.DataFrame(), pd.DataFrame()

        mat_df = pd.read_excel(mat_file)
        param_df = pd.read_excel(param_file)
        
        # 파라미터 ID를 인덱스로 설정하여 조회 최적화
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 엑셀 로드 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_data()

# 데이터 로드 실패 시 중단
if mat_df.empty or param_dict.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 소재 선택 (Material Selection)
# -----------------------------------------------------------------------------
st.sidebar.header("1. Material Selection")
st.sidebar.markdown("---")

cathodes = mat_df[mat_df['Category'] == 'Cathode']
anodes = mat_df[mat_df['Category'] == 'Anode']

# 양극재 선택
cat_name = st.sidebar.selectbox("Cathode Material", cathodes['Name'])
cat_row = cathodes[cathodes['Name'] == cat_name].iloc[0]

# 음극재 선택
ano_name = st.sidebar.selectbox("Anode Material", anodes['Name'])
ano_row = anodes[anodes['Name'] == ano_name].iloc[0]

# -----------------------------------------------------------------------------
# 4. 스마트 프리셋 (소재 변경 시 슬라이더 값 동기화)
# -----------------------------------------------------------------------------
# 양극재가 바뀌면 추천 공정값으로 슬라이더 위치를 초기화
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

# 음극재가 바뀌면 음극 추천 밀도로 초기화
if 'last_ano' not in st.session_state or st.session_state.last_ano != ano_name:
    st.session_state['ano_density'] = float(ano_row['Rec_Density'])
    st.session_state.last_ano = ano_name

# -----------------------------------------------------------------------------
# 5. 메인 화면: 소재 물성 자동 표시
# -----------------------------------------------------------------------------
st.title("🔋 SynoCore: Expert Na-ion Battery Simulator")
st.markdown(f"### 2. Selected Material Specs: **{cat_name}**")

# 이미지 2의 항목들 표시
col_i1, col_i2, col_i3, col_i4 = st.columns(4)
col_i1.metric("Capacity", f"{cat_row['Base_Capacity']} mAh/g")
col_i2.metric("Avg. Voltage", f"{cat_row['Base_Avg.Voltage']} V")
col_i3.metric("True Density", f"{cat_row['Base_True Density']} g/cm³")
col_i4.metric("Base Life", f"{cat_row['Base_Life']} Cycles")

st.divider()

# -----------------------------------------------------------------------------
# 6. 공정 파라미터 슬라이더 구역 (이미지 1 구성 반영)
# -----------------------------------------------------------------------------
st.markdown("### 3. Process Parameters (Smart Preset Applied)")
use_custom = st.checkbox("🔓 Unlock Manual Adjustment (전문가 모드)", value=False)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🅰️ Cathode Settings")
    
    # 1. Cathode Loading
    p_load = param_dict.loc['loading']
    loading = st.slider(
        label=p_load['Label_Name'],
        min_value=float(p_load['Min']),
        max_value=float(p_load['Max']),
        key='loading',
        step=float(p_load['Step']),
        disabled=not use_custom
    )

    # 2. Cathode Press Density
    p_c_den = param_dict.loc['cat_density']
    cat_density = st.slider(
        label=p_c_den['Label_Name'],
        min_value=float(p_c_den['Min']),
        max_value=float(p_c_den['Max']),
        key='cat_density',
        step=float(p_c_den['Step']),
        disabled=not use_custom
    )

with col_right:
    st.subheader("🅱️ Anode & Balance")
    
    # 3. NP_Ratio
    p_np = param_dict.loc['np_ratio']
    np_ratio = st.slider(
        label=p_np['Label_Name'],
        min_value=float(p_np['Min']),
        max_value=float(p_np['Max']),
        value=float(p_np['Default']), # 기본값 1.15
        step=float(p_np['Step'])
    )

    # 4. Anode Press Density (이미지 3의 SyntaxError 수정 지점)
    p_a_den = param_dict.loc['ano_density']
    ano_density = st.slider(
        label=p_a_den['Label_Name'],
        min_value=float(p_a_den['Min']),
        max_value=float(p_a_den['Max']),
        key='ano_density',
        step=float(p_a_den['Step']),
        disabled=not use_custom
    )

    # 5. Active Material Ratio
    p_act = param_dict.loc['active_ratio']
    active_ratio = st.slider(
        label=p_act['Label_Name'],
        min_value=float(p_act['Min']),
        max_value=float(p_act['Max']),
        key='active_ratio',
        step=float(p_act['Step']),
        disabled=not use_custom
    )

# -----------------------------------------------------------------------------
# 7. 시뮬레이션 결과 계산 (Simulation Logic)
# -----------------------------------------------------------------------------
st.markdown("---")
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    # (1) 셀 설계 계산
    cell_v = cat_row['Base_Avg.Voltage'] - ano_row['Base_Avg.Voltage']
    
    # 양극 용량 (mAh/cm2)
    cat_cap_area = loading * (active_ratio / 100) * cat_row['Base_Capacity']
    
    # 음극 로딩 역산 (N/P Ratio 및 ICE 반영)
    ano_cap_req = cat_cap_area * np_ratio
    # 음극은 효율(Base_ICE)을 고려하여 더 많은 양이 필요함
    ano_loading = ano_cap_req / (ano_row['Base_Capacity'] * (ano_row['Base_ICE']/100) * (active_ratio/100))
    
    # (2) 에너지 밀도 계산 (무게 기반 간이 모델)
    total_weight_mg = loading + ano_loading + 10 # 집전체 및 분리막 대략적 무게
    wh_kg = (cat_cap_area / 1000 * cell_v) / (total_weight_mg / 1000)
    
    # (3) 결과 표시
    st.success("✅ Simulation Completed!")
    r1, r2, r3 = st.columns(3)
    r1.metric("Energy Density", f"{wh_kg:.1f} Wh/kg")
    r2.metric("Total Thickness (Est.)", f"{(loading/cat_density + ano_loading/ano_density)*10 + 30:.1f} μm")
    r3.metric("Cycle Life (Base)", f"{cat_row['Base_Life']} Cycles")