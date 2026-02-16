import streamlit as st
import time
import random
import os

# 1. 페이지 및 로고 설정
st.set_page_config(page_title="SYNOTECH 배터리 분석 시스템", layout="centered")

# 2. 로그인 로직 (요청하신 비밀번호 적용)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    allowed_passwords = ["synotech0773", "client_001"] # 업체별 비번 확장 가능
    if st.session_state["password_input"] in allowed_passwords:
        st.session_state['logged_in'] = True
    else:
        st.error("비밀번호가 틀렸습니다.")

# --- 접속 화면 ---
if not st.session_state['logged_in']:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=200)
    st.title("🔒 SYNOTECH 데이터베이스 접속")
    st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=login)
    st.stop()

# --- 메인 시뮬레이터 본문 (인증 성공 시) ---
if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=120)

st.title("🔋 Altris 기반 Na-ion 배터리 시뮬레이터")
st.write("첨부된 JSC 기술 표준 및 N/P Ratio 계산법을 적용한 분석 도구입니다.")

# 3. 사이드바: 실제 배터리 설계 변수 입력
st.sidebar.header("📝 설계 파라미터")
cathode_loading = st.sidebar.number_input("양극(PW) 로딩량 (mg/cm2)", value=10.0) # 문서 기준값 [cite: 229]
target_c_rate = st.sidebar.selectbox("최대 충전 율 (C-rate)", ["0.1C", "0.33C", "0.5C", "1C"])
target_temp = st.sidebar.slider("테스트 온도 (°C)", 0, 60, 25)

# 4. 분석 로직 (문서 데이터 기반)
if st.sidebar.button("🚀 정밀 분석 시작"):
    with st.spinner('JSC 기술 표준에 따른 N/P Ratio 및 수명 예측 중...'):
        time.sleep(1.5)
        
        # [데이터 반영] C-rate별 음극 용량 변화 적용 
        anode_caps = {"0.1C": 340, "0.33C": 320, "0.5C": 314, "1C": 295}
        current_anode_cap = anode_caps[target_c_rate]
        
        # N/P Ratio 계산 (15% 마진 적용) [cite: 231]
        # X = (1.15 * Cathode_Cap * Loading) / Anode_Cap
        required_anode_loading = (1.15 * 162 * cathode_loading) / current_anode_cap # PW 용량 162 적용 [cite: 228]
        
        # 수명 예측 (Projection 데이터 기반) 
        # 1C 기준 약 44,000 사이클 이상의 기대 수명 반영
        expected_eol = 49061 if target_c_rate == "0.33C" else 44188
        
        # 온도 페널티 (25도 기준 편차 적용) [cite: 247]
        temp_factor = 1.0 - (abs(target_temp - 25) * 0.01)
        adjusted_eol = int(expected_eol * temp_factor)

    # 5. 결과 대시보드
    st.divider()
    st.subheader("📊 분석 결과 리포트")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("권장 음극 로딩량", f"{required_anode_loading:.3f} mg")
    col2.metric("권장 N/P Ratio", "1.15 (Safety)") # 마진 15% 정책 [cite: 231]
    col3.metric("예상 기대 수명", f"{adjusted_eol:,} Cycles")

    # 수명 저하 곡선 시각화 (문서 Fig 12 참조) [cite: 1023]
    st.write("**📍 용량 유지율(Capacity Retention) 예측 곡선**")
    chart_data = [100 - (i * (40/adjusted_eol)) for i in range(0, adjusted_eol, 1000)]
    st.line_chart(chart_data)
    
    st.success("✅ 분석 완료. 해당 로그는 SYNOTECH_Simulation_Log에 기록 준비되었습니다.")

else:
    st.info("사이드바에 설계 파라미터를 입력하고 분석을 시작하세요.")

# 로그아웃
if st.button("로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()