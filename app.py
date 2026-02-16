import streamlit as st
import time
import pandas as pd
import numpy as np
import os
from io import BytesIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="SYNOTECH 소재 통합 시뮬레이터", layout="wide")

# 2. 보안 로그인 시스템
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    # 마스터 비밀번호 설정
    if st.session_state.get("password_input") == "synotech0773!":
        st.session_state['logged_in'] = True
    else:
        st.error("비밀번호가 올바르지 않습니다.")

# --- 접속 화면 처리 ---
if not st.session_state['logged_in']:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=250)
    st.title("🔒 SYNOTECH 소재 시뮬레이션 시스템")
    st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=login)
    st.stop()

# --- 메인 대시보드 (인증 성공 시) ---
if os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width=150)

st.title("🔋 Altris 기반 Na-ion 4대 소재 시뮬레이터")
st.markdown("---")

# 3. 사이드바 설계 파라미터
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

# 4. 시뮬레이션 엔진 및 결과 처리
if st.sidebar.button("🚀 시뮬레이션 실행"):
    with st.spinner('데이터 알고리즘 분석 중...'):
        time.sleep(1)
        
        # [문서 기반 데이터 수식]
        cathode_cap = 162.0 if "Prussian" in cathode_type else 145.0
        anode_caps = {"0.1C": 340, "0.33C": 320, "0.5C": 314, "1C": 295}
        current_anode_cap = anode_caps[target_c_rate]
        
        actual_np_ratio = (anode_loading * current_anode_cap) / (cathode_loading * cathode_cap)
        base_eol = 49061 if target_c_rate == "0.33C" else 44188
        temp_penalty = 1.0 - (abs(target_temp - 25) * 0.015)
        np_penalty = 1.0 if actual_np_ratio >= 1.15 else (actual_np_ratio / 1.15)**2
        final_eol = int(base_eol * temp_penalty * np_penalty)
        energy_density = (cathode_cap * cathode_loading) * 3.0 / 100

        # 결과 대시보드 출력
        col1, col2, col3 = st.columns(3)
        col1.metric("실측 N/P Ratio", f"{actual_np_ratio:.2f}")
        col2.metric("예상 수명", f"{final_eol:,} Cycles")
        col3.metric("에너지 밀도 (est.)", f"{energy_density:.1f} Wh/kg")

        # 📊 SOH 그래프 시각화
        cycles_axis = np.linspace(0, final_eol, 50)
        soh_curve = 100 - (20 * (cycles_axis / final_eol)**1.5)
        st.line_chart(pd.DataFrame({'Cycles': cycles_axis, 'SOH (%)': soh_curve}).set_index('Cycles'))

        # --- Excel 파일 생성 로직 (image_6c2370 해결책) ---
        excel_df = pd.DataFrame({
            "설계 항목": ["양극재 종류", "양극 로딩량", "음극재 종류", "음극 로딩량", "전해질 종류", "분리막 종류", "C-rate 설정", "운전 온도", "N/P 비율 결과", "예상 수명 결과", "추정 에너지밀도"],
            "수치 및 데이터": [cathode_type, cathode_loading, anode_type, anode_loading, electrolyte, separator, target_c_rate, target_temp, f"{actual_np_ratio:.2f}", f"{final_eol:,} Cycles", f"{energy_density:.1f} Wh/kg"]
        })

        output = BytesIO()
        # xlsxwriter 엔진 사용 - 반드시 requirements.txt에 등록되어야 함
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            excel_df.to_excel(writer, index=False, sheet_name='Simulation_Log')
        
        excel_binary = output.getvalue()

        # 5. 다운로드 버튼 (image_6c1f8a 해결책)
        st.divider()
        st.subheader("💾 리포트 데이터 저장")
        st.download_button(
            label="📊 분석 결과 Excel 다운로드",
            data=excel_binary,
            file_name=f"SYNOTECH_Report_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("분석이 완료되었습니다. 결과 파일을 다운로드할 수 있습니다.")

else:
    st.info("왼쪽 사이드바에서 설계 조건을 설정하고 시뮬레이션 버튼을 눌러주세요.")

# 로그아웃 기능
if st.button("🚪 시스템 로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown("<p style='text-align: center; color: gray;'>© 2026 SYNOTECH Co., Ltd. | Powered by Altris Technical Data</p>", unsafe_allow_html=True)