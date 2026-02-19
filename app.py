import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 & 데이터 로드
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.4: Expert SIB Simulator", layout="wide")

@st.cache_data
def load_data():
    try:
        # 엑셀 파일 두 개 로드
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("process_parameters.xlsx")
        # 파라미터 ID를 인덱스로 설정하여 조회하기 쉽게 변환
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 데이터 파일을 찾을 수 없습니다. (Error: {e})")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_data()

# 데이터 로드 실패 시 중단
if mat_df.empty or param_dict.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 2. 사이드바: Material Selection (소재 선택)
# -----------------------------------------------------------------------------
st.sidebar.header("1. Material Selection")
st.sidebar.markdown("---")

# 카테고리별 데이터 필터링
cathodes = mat_df[mat_df['Category'] == 'Cathode']
anodes = mat_df[mat_df['Category'] == 'Anode']
elecs = mat_df[mat_df['Category'] == 'Electrolyte']
seps = mat_df[mat_df['Category'] == 'Separator']
foils = mat_df[mat_df['Category'] == 'Foil']

# [A] 양극재 선택 (핵심)
cat_name = st.sidebar.selectbox("Cathode Material (양극재)", cathodes['Name'])
cat_row = cathodes[cathodes['Name'] == cat_name].iloc[0]

# [B] 음극재 선택
ano_name = st.sidebar.selectbox("Anode Material (음극재)", anodes['Name'])
ano_row = anodes[anodes['Name'] == ano_name].iloc[0]

# [C] 기타 소재 선택
elec_name = st.sidebar.selectbox("Electrolyte (전해액)", elecs['Name'])
sep_name = st.sidebar.selectbox("Separator (분리막)", seps['Name'])
foil_name = st.sidebar.selectbox("Current Collector (집전체)", foils['Name'])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: 소재를 변경하면 권장 공정 조건(Recommended Settings)이 자동으로 적용됩니다.")

# -----------------------------------------------------------------------------
# 3. 메인 화면: Material Properties Info (자동 표시)
# -----------------------------------------------------------------------------
st.title("🔋 SynoCore: Na-ion Battery Design Simulator")
st.markdown(f"### 2. Material Specs : **{cat_name}** vs **{ano_name}**")

# 소재 물성 정보 카드 (Read-Only)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Cathode Capacity", f"{cat_row['Capacity']} mAh/g")
with c2:
    st.metric("Avg. Voltage", f"{cat_row['Voltage']} V")
with c3:
    st.metric("Base ICE (Efficiency)", f"{cat_row['Base_ICE']} %")
with c4:
    st.metric("True Density", f"{cat_row['True_Density']} g/cc")

st.divider()

# -----------------------------------------------------------------------------
# 4. 공정 파라미터 (Process Parameters) - Smart Preset Logic
# -----------------------------------------------------------------------------
st.markdown("### 3. Process Parameters (Auto-Optimized)")

# [핵심 로직] Session State를 활용한 '스마트 프리셋'
# 사용자가 소재를 바꿀 때만(onChange) 슬라이더 값을 엑셀의 '추천값'으로 업데이트
if 'last_cat_name' not in st.session_state or st.session_state.last_cat_name != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat_name = cat_name

if 'last_ano_name' not in st.session_state or st.session_state.last_ano_name != ano_name:
    st.session_state['ano_density'] = float(ano_row['Rec_Density'])
    st.session_state.last_ano_name = ano_name

# [UI 기능] 사용자 정의 모드 체크박스
use_custom = st.checkbox("🔓 **Unlock Manual Adjustment (전문가 모드)**", value=False)
st.caption("체크하면 추천값을 무시하고 슬라이더를 수동으로 정밀 조절할 수 있습니다.")

col_left, col_right = st.columns(2)

# --- 왼쪽 컬럼: 양극 공정 ---
with col_left:
    st.subheader("🅰️ Cathode Settings")
    
    # 1. Loading Level
    p_load = param_dict.loc['loading']
    loading = st.slider(
        label=f"1. {p_load['Label_Name']} ({p_load['Unit']})",
        min_value=float(p_load['Min']),
        max_value=float(p_load['Max']),
        # value는 session_state의 키('loading')와 연동됨
        key='loading', 
        step=float(p_load['Step']),
        disabled=not use_custom
    )

    # 2. Cathode Density
    p_c_den = param_dict.loc['cat_density']
    cat_density = st.slider(
        label=f"2. {p_c_den['Label_Name']} ({p_c_den['Unit']})",
        min_value=float(p_c_den['Min']),
        max_value=float(p_c_den['Max']),
        key='cat_density',
        step=float(p_c_den['Step']),
        disabled=not use_custom
    )

# --- 오른쪽 컬럼: 음극 및 밸런스 ---
with col_right:
    st.subheader("🅱️ Anode & Balance")

    # 3. N/P Ratio (항상 조절 가능)
    p_np = param_dict.loc['np_ratio']
    np_ratio = st.slider(
        label=f"3. {p_np['Label_Name']}",
        min_value=float(p_np['Min']),
        max_value=float(p_np['Max']),
        value=1.15, 
        step=float(p_np['Step'])
    )

    # 4. Anode Density
    p_a_den = param_dict.loc['ano_