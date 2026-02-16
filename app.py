import streamlit as st
import time
import pandas as pd
import numpy as np
import os

# 1. 페이지 및 보안 설정
st.set_page_config(page_title="SYNOTECH 소재 통합 시뮬레이터", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    if st.session_state["password_input"] == "client_001":
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

# A. 양극재 (Cathode) 선택
cathode_type = st.sidebar.selectbox("1. 양극재 선택", ["Altris Prussian White (PW)", "Custom Oxide"])
cathode_loading = st.sidebar.slider("양극 로딩량 (mg/cm²)", 5.0, 20.0, 10.0)

# B. 음극재 (Anode) 선택
anode_type = st.sidebar.selectbox("2. 음극재 선택", ["Bio-based Hard Carbon", "Petroleum Coke HC"])
anode_loading = st.sidebar.slider("음극 로딩량 (mg/cm²)", 3.0, 15.0, 5.5)

# C. 전해액 (Electrolyte) 선택
electrolyte = st.sidebar.selectbox("3. 전해액 선택", ["Standard NaPF6/Carbonates", "High-Stability TEP based"])

# D. 분리막 (Separator) 선택
separator = st.sidebar.selectbox("4. 분리막 선택", ["Polyolefin (PE/PP)", "Cellulose (Heat-Resistant)"])

st.sidebar.divider()
target_c_rate = st.sidebar.select_slider("충전 속도 (C-rate)", options=["0.1C", "0.33C", "0.5C", "1C"])
target_temp = st.sidebar.slider("운전 온도 (°C)", -20, 60, 25)

# 3. 시뮬레이션 계산 로직 (문서 데이터 기반)
if st.sidebar.button("🚀 시뮬레이션 실행"):
    with st.spinner('소재 계면 반응 및 수명 예측 분석 중...'):
        time.sleep(1.5)
        
        # [데이터 반영] 소재별 고유 용량 (mAh/g)
        cathode_cap = 162.0 if "Prussian" in cathode_type else 145.0
        
        # C-rate별 음극 수용량 변화 (문서 Fig 12 참조)
        anode_caps = {"0.1C": 340, "0.33C": 320, "0.5C": 314, "1C": 295}
        current_anode_cap = anode_caps[target_c_rate]
        
        # N/P Ratio 계산: (음극로딩 * 음극용량) / (양극로딩 * 양극용량)
        actual_np_ratio = (anode_loading * current_anode_cap) / (cathode_loading * cathode_cap)
        
        # 수명 예측 베이스 (Altris Pathfinder 2026 데이터 기반)
        base_eol = 49000 if target_c_rate == "0.33C" else 44000
        
        # 온도 및 소재 조합에 따른 감쇄 계수
        temp_penalty = 1.0 - (abs(target_temp - 25) * 0.015)
        np_penalty = 1.0 if actual_np_ratio >= 1.1 else (actual_np_ratio / 1.1) ** 2 # N/P 1.1 미만 시 급격한 성능 저하
        
        # 전해액/분리막 보정
        elec_factor = 1.05 if "TEP" in electrolyte else 1.0
        sep_factor = 1.02 if "Cellulose" in separator and target_temp > 40 else 1.0
        
        final_eol = int(base_eol * temp_penalty * np_penalty * elec_factor * sep_factor)
        
        # 4. 결과 리포트 출력
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("실측 N/P Ratio", f"{actual_np_ratio:.2f}", 
                      delta="Safe" if actual_np_ratio >= 1.15 else "Danger (Plating Risk)",
                      delta_color="normal" if actual_np_ratio >= 1.15 else "inverse")
            st.caption("권장 Margin: 15% (1.15 이상)")

        with col2:
            st.metric("예상 기대 수명 (EOL)", f"{final_eol:,} Cycles")
            st.caption("80% SOH 유지 기준")

        with col3:
            energy_density = (cathode_cap * cathode_loading) * 3.0 / 100 # 가상 전압 3.0V
            st.metric("추정 에너지 밀도", f"{energy_density:.1f} Wh/kg")

        # 수명 저하 곡선 차트
        st.subheader("📍 수명 저하 예측 (SOH Curve)")
        cycles = np.linspace(0, final_eol, 50)
        soh_values = 100 - (20 * (cycles / final_eol)**1.5) # 비선형 열화 모델
        chart_data = pd.DataFrame({'Cycles': cycles, 'SOH (%)': soh_values}).set_index('Cycles')
        st.line_chart(chart_data)

        # 소재 구성 요약표
        st.subheader("📋 선택된 셀 구성 정보")
        spec_data = {
            "구분": ["양극", "음극", "전해질", "분리막"],
            "소재명": [cathode_type, anode_type, electrolyte, separator],
            "주요 설정": [f"{cathode_loading} mg/cm²", f"{anode_loading} mg/cm²", "Standard" if "Standard" in electrolyte else "High-Temp", "Cellulose" if "Cellulose" in separator else "PE/PP"]
        }
        st.table(pd.DataFrame(spec_data))

    st.success("✅ 시뮬레이션 완료. 결과가 구글 시트에 기록될 준비가 되었습니다.")

else:
    st.info("왼쪽 사이드바에서 4대 재료와 운전 조건을 선택한 후 '시뮬레이션 실행' 버튼을 눌러주세요.")

# 5. 하단 버튼 및 로그아웃
st.divider()
if st.button("🚪 로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown("<p style='text-align: center; color: gray;'>© 2026 SYNOTECH Co., Ltd. | Altris Technical Standard v1.2</p>", unsafe_allow_html=True)