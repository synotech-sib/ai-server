import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(page_title="SynoCore V1.4", layout="wide")

# -----------------------------------------------------------------------------
# 1. 데이터 로드 함수 (두 개의 엑셀 파일 읽기)
# -----------------------------------------------------------------------------
@st.cache_data
def load_db():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("process_parameters.xlsx")
        # Parameter_ID를 인덱스로 설정하여 찾기 쉽게 변환
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 데이터 파일을 읽을 수 없습니다. (Error: {e})")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_db()

if mat_df.empty or param_dict.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 2. 사이드바: 소재 선택
# -----------------------------------------------------------------------------
st.sidebar.header("1. Material Selection")

# 양극재 선택
cathodes = mat_df[mat_df['Category'] == 'Cathode']
cat_name = st.sidebar.selectbox("Cathode Material", cathodes['Name'])
cat_row = cathodes[cathodes['Name'] == cat_name].iloc[0]

# 음극재 및 기타 선택
anodes = mat_df[mat_df['Category'] == 'Anode']
ano_name = st.sidebar.selectbox("Anode Material", anodes['Name'])
ano_row = anodes[anodes['Name'] == ano_name].iloc[0]

# -----------------------------------------------------------------------------
# 3. 메인 화면: 소재 물성 정보 (자동 표시)
# -----------------------------------------------------------------------------
st.title("🔋 SynoCore: Expert SIB Simulator")
st.markdown(f"### 2. Selected Material Specs : **{cat_name}**")

# Info Card 디자인
c1, c2, c3, c4 = st.columns(4)
c1.metric("Capacity", f"{cat_row['Capacity']} mAh/g")
c2.metric("Avg. Voltage", f"{cat_row['Voltage']} V")
c3.metric("Base ICE", f"{cat_row['Base_ICE']} %")
c4.metric("True Density", f"{cat_row['True_Density']} g/cc")

st.divider()

# -----------------------------------------------------------------------------
# 4. 공정 파라미터 (Smart Preset 로직 적용)
# -----------------------------------------------------------------------------
st.markdown("### 3. Process Parameters (Auto-Optimized)")

# [핵심 로직] 소재가 변경되었는지 감지하여 Session State 업데이트
if 'last_cat_name' not in st.session_state or st.session_state.last_cat_name != cat_name:
    # 양극재가 바뀌면 -> 엑셀(mat_df)에 있는 '추천값'으로 슬라이더 값을 리셋
    st.session_state.loading_val = float(cat_row['Rec_Loading'])
    st.session_state.cat_den_val = float(cat_row['Rec_Density'])
    st.session_state.active_val = float(cat_row['Rec_Active'])
    st.session_state.last_cat_name = cat_name

if 'last_ano_name' not in st.session_state or st.session_state.last_ano_name != ano_name:
    # 음극재가 바뀌면 -> 음극 추천 밀도 리셋
    st.session_state.ano_den_val = float(ano_row['Rec_Density'])
    st.session_state.last_ano_name = ano_name

# [UI 기능] 사용자 정의 모드 (잠금 해제)
use_custom = st.checkbox("🔓 Unlock Manual Adjustment (전문가 모드)", value=False)
st.caption("체크하면 추천값을 무시하고 슬라이더를 수동으로 조절할 수 있습니다.")

col_left, col_right = st.columns(2)

# --- 왼쪽 컬럼: 양극 공정 ---
with col_left:
    st.subheader("🅰️ Cathode Settings")
    
    # 1. Loading Level (불러온 param_dict의 범위 적용)
    p_load = param_dict.loc['loading']
    loading = st.slider(
        label=f"{p_load['Label_Name']} ({p_load['Unit']})",
        min_value=float(p_load['Min']),
        max_value=float(p_load['Max']),
        value=st.session_state.loading_val, # 추천값 적용
        step=float(p_load['Step']),
        disabled=not use_custom, # 체크 안 하면 잠금
        key='slider_loading'
    )

    # 2. Cathode Density
    p_c_den = param_dict.loc['cat_density']
    cat_density = st.slider(
        label=f"{p_c_den['Label_Name']} ({p_c_den['Unit']})",
        min_value=float(p_c_den['Min']),
        max_value=float(p_c_den['Max']),
        value=st.session_state.cat_den_val,
        step=float(p_c_den['Step']),
        disabled=not use_custom,
        key='slider_c_den'
    )

# --- 오른쪽 컬럼: 음극 및 밸런스 ---
with col_right:
    st.subheader("🅱️ Anode & Balance")

    # 3. N/P Ratio (이건 항상 조절 가능하게 두는 것이 좋음, 필요시 잠금 가능)
    p_np = param_dict.loc['np_ratio']
    np_ratio = st.slider(
        label=p_np['Label_Name'],
        min_value=float(p_np['Min']),
        max_value=float(p_np['Max']),
        value=1.15, # N/P는 통상 1.15 고정이나, 원하면 이것도 DB화 가능
        step=float(p_np['Step'])
    )

    # 4. Anode Density
    p_a_den = param_dict.loc['ano_density']
    ano_density = st.slider(
        label=f"{p_a_den['Label_Name']} ({p_a_den['Unit']})",
        min_value=float(p_a_den['Min']),
        max_value=float(p_a_den['Max']),
        value=st.session_state.ano_den_val,
        step=float(p_a_den['Step']),
        disabled=not use_custom,
        key='slider_a_den'
    )

    # 5. Active Ratio
    p_act = param_dict.loc['active_ratio']
    active_ratio = st.slider(
        label=f"{p_act['Label_Name']} ({p_act['Unit']})",
        min_value=float(p_act['Min']),
        max_value=float(p_act['Max']),
        value=st.session_state.active_val,
        step=float(p_act['Step']),
        disabled=not use_custom,
        key='slider_active'
    )

# -----------------------------------------------------------------------------
# 5. 결과 시뮬레이션 (간략화된 예시)
# -----------------------------------------------------------------------------
if st.button("🚀 Calculate Performance", type="primary"):
    # (실제 복잡한 수식은 여기에 기존 로직 적용)
    
    # 1. 셀 전압 계산 (양극 - 음극)
    cell_voltage = cat_row['Voltage'] - ano_row['Voltage']
    
    # 2. 에너지 밀도 (Wh/kg) - 간이 수식
    # Capacity * Voltage / (Total Weight Factor)
    # 실제로는 집전체, 분리막, 전해액 무게 다 더해야 함
    energy_wh_kg = (cat_row['Capacity'] * cell_voltage) / 2.6  # 2.6은 대략적인 Cell Packaging Factor
    
    # 로딩량이 높으면(20 이상) 에너지 밀도 소폭 상승 보정
    if loading > 20.0:
        energy_wh_kg *= 1.02

    # 3. 결과 표시
    st.success("Simulation Completed!")
    m1, m2, m3 = st.columns(3)
    m1.metric("Gravimetric Energy", f"{energy_wh_kg:.1f} Wh/kg")
    m2.metric("Volumetric Energy", f"{energy_wh_kg * 1.8:.1f} Wh/L") # 대략적 환산
    m3.metric("Cell Price", f"${cat_row['Price'] * 1.3:.1f} / kWh")