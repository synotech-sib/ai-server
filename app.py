import streamlit as st
import time
import pandas as pd
import numpy as np
import os
from io import BytesIO

# 1. 페이지 및 보안 설정
st.set_page_config(page_title="SYNOTECH 배터리 통합 시뮬레이터", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    if st.session_state.get("password_input") == "synotech0773!":
        st.session_state['logged_in'] = True
    else:
        st.error("비밀번호가 틀렸습니다.")

# --- 접속 화면 ---
if not st.session_state['logged_in']:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=250)
    st.title("🔒 SYNOTECH 배터리 분석 시스템")
    st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=login)
    st.stop()

# --- 메인 대시보드 ---
if os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width=150)

st.title("🔋 LIB vs SIB 통합 성능 시뮬레이터")
st.markdown("---")

# 2. 사이드바: 배터리 타입 및 파라미터 선택
st.sidebar.header("⚙️ 시뮬레이션 설정")
battery_type = st.sidebar.radio("배터리 기술 선택", ["SIB (Na-ion, Altris Base)", "LIB (Li-ion, NASA Base)"])

st.sidebar.divider()
st.sidebar.subheader("🛠️ 상세 설계값")

if battery_type == "SIB (Na-ion, Altris Base)":
    cathode_material = "Altris Prussian White (PW)"
    cathode_cap = 162.0 #
    anode_caps = {"0.1C": 340, "0.33C": 320, "0.5C": 314, "1C": 295} #
    base_eol_val = 49061 #
else:
    cathode_material = "LiNiMnCoO2 (NMC)"
    cathode_cap = 180.0 # NASA LIB Standard
    anode_caps = {"0.1C": 360, "0.33C": 355, "0.5C": 350, "1C": 330} # NASA LIB Standard
    base_eol_val = 2500 # 일반적인 고성능 LIB 기준

cathode_loading = st.sidebar.slider("양극 로딩량 (mg/cm²)", 5.0, 20.0, 10.0)
anode_loading = st.sidebar.slider("음극 로딩량 (mg/cm²)", 3.0, 15.0, 5.5)
target_c_rate = st.sidebar.select_slider("테스트 속도 (C-rate)", options=["0.1C", "0.33C", "0.5C", "1C"])
target_temp = st.sidebar.slider("운전 온도 (°C)", -20, 60, 25)

# 3. 시뮬레이션 계산 로직
if st.sidebar.button("🚀 시뮬레이션 실행"):
    with st.spinner(f'{battery_type} 데이터 분석 중...'):
        time.sleep(1)
        
        # N/P Ratio 계산
        current_anode_cap = anode_caps[target_c_rate]
        actual_np_ratio = (anode_loading * current_anode_cap) / (cathode_loading * cathode_cap)
        
        # 수명 및 성능 감쇄 모델
        # SIB: Altris 15% 마진 정책 및 고온 특성 반영
        # LIB: NASA 기계학습 모델 기반 열화 계수 반영
        temp_factor = 1.0 - (abs(target_temp - 25) * 0.02)
        np_margin_standard = 1.15 if battery_type.startswith("SIB") else 1.10
        np_penalty = 1.0 if actual_np_ratio >= np_margin_standard else (actual_np_ratio / np_margin_standard)**2
        
        final_eol = int(base_eol_val * temp_factor * np_penalty)
        avg_voltage = 3.0 if battery_type.startswith("SIB") else 3.7 #
        energy_density = (cathode_cap * cathode_loading) * avg_voltage / 100

        # 결과 대시보드
        st.subheader(f"📊 {battery_type} 시뮬레이션 리포트")
        col1, col2, col3 = st.columns(3)
        col1.metric("실측 N/P Ratio", f"{actual_np_ratio:.2f}", 
                  delta="Safe" if actual_np_ratio >= np_margin_standard else "Warning")
        col2.metric("예상 수명 (EOL)", f"{final_eol:,} Cycles")
        col3.metric("에너지 밀도 (est.)", f"{energy_density:.1f} Wh/kg")

        # 📈 수명 곡선 시각화
        cycles_axis = np.linspace(0, final_eol, 50)
        # SIB는 제어된 감쇄를 보임, LIB는 후반부 가파른 감쇄
        decay_power = 1.3 if battery_type.startswith("SIB") else 1.8 
        soh_curve = 100 - (20 * (cycles_axis / final_eol)**decay_power)
        
        chart_df = pd.DataFrame({'Cycles': cycles_axis, 'SOH (%)': soh_curve}).set_index('Cycles')
        st.line_chart(chart_df)

        # 엑셀 데이터 준비
        excel_df = pd.DataFrame({
            "항목": ["배터리 타입", "양극재", "양극 로딩", "음극 로딩", "C-rate", "온도", "N/P Ratio", "예상수명", "에너지밀도"],
            "결과": [battery_type, cathode_material, cathode_loading, anode_loading, target_c_rate, target_temp, f"{actual_np_ratio:.2f}", f"{final_eol:,}", f"{energy_density:.1f}"]
        })

        # 엑셀 다운로드 버튼
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            excel_df.to_excel(writer, index=False, sheet_name='Result')
        
        st.divider()
        st.download_button(
            label="💾 결과 Excel 다운로드",
            data=output.getvalue(),
            file_name=f"SYNOTECH_{battery_type[:3]}_{time.strftime('%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("사이드바에서 배터리 종류와 조건을 선택한 후 '시뮬레이션 실행'을 눌러주세요.")

# 로그아웃
if st.button("🚪 로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown("<p style='text-align: center; color: gray;'>© 2026 SYNOTECH | Data: Altris Technical Standard & NASA Ames PCoE</p>", unsafe_allow_html=True)