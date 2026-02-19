import streamlit as st
import pandas as pd
import os

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="SynoCore V1.4", layout="wide")

# 2. 데이터 로드 함수 (이미지 4 파일명 및 컬럼 불일치 해결)
@st.cache_data
def load_data():
    try:
        mat_file = "material_list.xlsx"
        param_file = "param_config.xlsx"
        
        if not os.path.exists(mat_file) or not os.path.exists(param_file):
            st.error("❌ 엑셀 파일이 없습니다. 파일명을 확인해주세요.")
            return pd.DataFrame(), pd.DataFrame()

        # 데이터 로드
        mat_df = pd.read_excel(mat_file)
        param_df = pd.read_excel(param_file)

        # [Length mismatch 해결] 엑셀의 컬럼이 몇 개든 코드용 이름으로 강제 매핑
        # 엑셀의 첫 10개 컬럼을 아래 이름으로 고정합니다.
        new_cols = [
            "Category", "Name", "Base_Capacity", "Base_Avg_Voltage", 
            "Base_True_Density", "Base_Life", "Base_ICE", 
            "Rec_Loading", "Rec_Density", "Rec_Active"
        ]
        
        # 실제 엑셀 컬럼 개수와 맞지 않을 경우를 대비한 안전 로직
        if len(mat_df.columns) >= len(new_cols):
            mat_df = mat_df.iloc[:, :len(new_cols)] # 앞에서부터 10개만 슬라이싱
            mat_df.columns = new_cols
        else:
            st.error(f"❌ material_list.xlsx의 컬럼 개수가 부족합니다. (현재 {len(mat_df.columns)}개, 필요 10개)")
            return pd.DataFrame(), pd.DataFrame()

        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except Exception as e:
        st.error(f"❌ 데이터 로딩 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame()

mat_df, param_dict = load_data()

if mat_df.empty or param_dict.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 및 스마트 프리셋 로직
# -----------------------------------------------------------------------------
st.sidebar.header("1. Material Selection")
cathodes = mat_df[mat_df['Category'] == 'Cathode']
anodes = mat_df[mat_df['Category'] == 'Anode']

cat_name = st.sidebar.selectbox("Cathode Material", cathodes['Name'])
cat_row = cathodes[cathodes['Name'] == cat_name].iloc[0]

ano_name = st.sidebar.selectbox("Anode Material", anodes['Name'])
ano_row = anodes[anodes['Name'] == ano_name].iloc[0]

# 소재 변경 시 슬라이더 자동 동기화
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

if 'last_ano' not in st.session_state or st.session_state.last_ano != ano_name:
    st.session_state['ano_density'] = float(ano_row['Rec_Density'])
    st.session_state.last_ano = ano_name

# -----------------------------------------------------------------------------
# 4. 메인 화면 출력
# -----------------------------------------------------------------------------
st.title("🔋 SynoCore: Expert SIB Simulator")
st.markdown(f"### 2. Selected Material: **{cat_name}**")

# 이미지 4의 KeyError 해결: 표준화된 컬럼명 사용
col_i1, col_i2, col_i3, col_i4 = st.columns(4)
col_i1.metric("Capacity", f"{cat_row['Base_Capacity']} mAh/g")
col_i2.metric("Avg. Voltage", f"{cat_row['Base_Avg_Voltage']} V")
col_i3.metric("True Density", f"{cat_row['Base_True_Density']} g/cm³")
col_i4.metric("Base Life", f"{cat_row['Base_Life']} Cycles")

st.divider()

# 5. 공정 파라미터 슬라이더
st.markdown("### 3. Process Parameters")
use_custom = st.checkbox("🔓 Unlock Manual Adjustment", value=False)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🅰️ Cathode Settings")
    p_load = param_dict.loc['loading']
    loading = st.slider(label=p_load['Label_Name'], min_value=float(p_load['Min']), max_value=float(p_load['Max']), key='loading', step=float(p_load['Step']), disabled=not use_custom)
    
    p_c_den = param_dict.loc['cat_density']
    cat_density = st.slider(label=p_c_den['Label_Name'], min_value=float(p_c_den['Min']), max_value=float(p_c_den['Max']), key='cat_density', step=float(p_c_den['Step']), disabled=not use_custom)

with col_right:
    st.subheader("🅱️ Anode & Balance")
    p_np = param_dict.loc['np_ratio']
    np_ratio = st.slider(label=p_np['Label_Name'], min_value=float(p_np['Min']), max_value=float(p_np['Max']), value=float(p_np['Default']), step=float(p_np['Step']))

    # [SyntaxError 해결] 끊겼던 ano_density 코드 복구
    p_a_den = param_dict.loc['ano_density']
    ano_density = st.slider(label=p_a_den['Label_Name'], min_value=float(p_a_den['Min']), max_value=float(p_a_den['Max']), key='ano_density', step=float(p_a_den['Step']), disabled=not use_custom)

    p_act = param_dict.loc['active_ratio']
    active_ratio = st.slider(label=p_act['Label_Name'], min_value=float(p_act['Min']), max_value=float(p_act['Max']), key='active_ratio', step=float(p_act['Step']), disabled=not use_custom)

# 6. 결과 계산
if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
    cell_v = cat_row['Base_Avg_Voltage'] - ano_row['Base_Avg_Voltage']
    st.success("✅ 시뮬레이션 완료")
    res1, res2 = st.columns(2)
    res1.metric("Voltage Gap", f"{cell_v:.2f} V")
    res2.metric("Target Life", f"{cat_row['Base_Life']} Cycles")