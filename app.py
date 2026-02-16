import streamlit as st
import time
import pandas as pd
import numpy as np
import os
from io import BytesIO

# 1. 페이지 및 보안 설정
st.set_page_config(page_title="SYNOTECH 소재 통합 시뮬레이터", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 마스터 비밀번호 설정
def login():
    if st.session_state["password_input"] == "synotech0773!":
        st.session_state['logged_in'] = True
    else:
        st.error("비밀번호가 틀렸습니다.")

# --- 접속 화면 ---
if not st.session_state['logged_in']:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=250)
    st.title("🔒 SYNOTECH 소재 시뮬레이션 시스템")
    st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=login)
    st.stop()

# --- 메인 본문 (인증 성공 시) ---
if os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width=150)

st.title("🔋 Altris 기반 Na-ion 4대 소재 시뮬레이터")
st.markdown("---")

# 2. 사이드바: 4대 재료 구성 및 조건 선택
st.sidebar.header("🛠️ Cell 설계 파라미터")

cathode_type = st.sidebar.selectbox("1. 양극재 선택", ["Altris Prussian White (PW)", "Custom Oxide"])
cathode_loading = st.sidebar.slider("양극 로딩량 (mg/cm²)", 5.0, 20.0, 10.0)

anode_type = st.sidebar.selectbox("2. 음극재 선택", ["Bio-based Hard Carbon", "Petroleum Coke HC"])
anode_loading = st.sidebar.slider("음극 로딩량 (mg/cm²)", 3.0, 15.0, 5.5)

electrolyte = st.sidebar.selectbox("3. 전해액 선택", ["Standard NaPF6/Carbonates", "High-Stability TEP based"])
separator = st.sidebar.selectbox("4. 분리막 선택", ["Polyolefin (PE/PP)", "Cellulose (Heat-Resistant)"])

st.sidebar.divider()
target_c_rate = st.sidebar.select_slider("충전 속도 (C-rate)", options=["0.1C", "0.33C", "0.5C", "1C"])
target_temp = st.sidebar.slider("운전 온도 (°C)", -20, 60, 25)

# 3. 시뮬레이션 계산 및 엑셀 변환 로직
if st.sidebar.button("🚀 시뮬레이션 실행"):
    with st.spinner('소재 계면 반응 및 수명 예측 분석 중...'):
        time.sleep(1)
        
        # [문서 기반 데이터 반영]
        cathode_cap = 162.0 if "Prussian" in cathode_type else 145.0
        anode_caps = {"0.1C": 340, "0.33C": 320, "0.5C": 314, "1C": 295}
        current_anode_cap = anode_caps[target_c_rate]
        
        # N/P Ratio 계산
        actual_np_ratio = (anode_loading * current_anode_cap) / (cathode_loading * cathode_cap)
        
        # 수명 예측 (Pathfinder 2026 데이터 기반)
        base_eol = 49061 if target_c_rate == "0.33C" else 44188
        
        # 환경 페널티 적용
        temp_penalty = 1.0 - (abs(target_temp - 25) * 0.015)
        np_penalty = 1.0 if actual_np_ratio >= 1.15 else (actual_np_ratio / 1.15)**2
        final_eol = int(base_eol * temp_penalty * np_penalty)
        
        # 에너지 밀도 추정 (3.0V 기준)
        energy_density = (cathode_cap * cathode_loading) * 3.0 / 100

        # 결과 화면 출력
        col1, col2, col3 = st.columns(3)
        col1.metric("실측 N/P Ratio", f"{actual_np_ratio:.2f}")
        col2.metric("예상 기대 수명", f"{final_eol:,} Cycles")
        col3.metric("에너지 밀도 (est.)", f"{energy_density:.1f} Wh/kg")

        # 시각화 데이터 생성
        cycles = np.linspace(0, final_eol, 50)
        soh_values = 100 - (20 * (cycles / final_eol)**1.5)
        chart_data = pd.DataFrame({'Cycles': cycles, 'SOH (%)': soh_values})
        st.line_chart(chart_data.set_index('Cycles'))

        # --- 엑셀 파일 생성 ---
        output_data = {
            "항목": ["양극재", "양극 로딩량", "음극재", "음극 로딩량", "전해질", "분리막", "C-rate", "온도", "N/P Ratio", "예상 수명(EOL)", "에너지밀도"],
            "설정치/결과": [cathode_type, cathode_loading, anode_type, anode_loading, electrolyte, separator, target_c_rate, target_temp, f"{actual_np_ratio:.2f}", f"{final_eol:,} Cycles", f"{energy_density:.1f} Wh/kg"]
        }
        df_result = pd.DataFrame(output_data)

        # 메모리에 엑셀 파일 생성
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False, sheet_name='Simulation_Result')
        excel_data = excel_buffer.getvalue()

        # 4. 다운로드 버튼 표시
        st.divider()
        st.subheader("💾 시뮬레이션 리포트 저장")
        st.download_button(
            label="📊 결과 Excel 파일 다운로드",
            data=excel_data,
            file_name=f"SYNOTECH_Sim_Result_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime