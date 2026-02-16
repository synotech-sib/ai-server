import streamlit as st
import time
import random

# 1. 페이지 설정 (심플하게 제목만 표시)
st.set_page_config(page_title="SYNOTECH 배터리 시뮬레이터", layout="centered")

st.title("🔋 SYNOTECH 배터리 성능 시뮬레이터")
st.write("작동 조건에 따른 배터리 예상 수명을 시뮬레이션합니다.")

# 2. 사이드바: 시뮬레이션 조건 입력
st.sidebar.header("🛠️ 시뮬레이션 설정")
temp = st.sidebar.slider("작동 온도 (°C)", 0, 60, 25)
cycles = st.sidebar.number_input("목표 사이클 (Cycle)", min_value=100, max_value=5000, value=1000)

# 3. 시뮬레이션 실행 버튼
if st.sidebar.button("🚀 시뮬레이션 시작"):
    # 진행 상황 표시 (Progress Bar)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(101):
        time.sleep(0.01)  # 시뮬레이션 느낌을 주기 위한 지연
        progress_bar.progress(i)
        status_text.text(f"시뮬레이션 진행 중... {i}%")
    
    # 4. 가상의 예측 결과 계산 (단순 수식 적용)
    # 온도가 높을수록, 사이클이 많을수록 성능이 낮아지는 가상의 로직
    base_health = 100.0
    temp_penalty = abs(temp - 25) * 0.5  # 25도에서 멀어질수록 페널티
    cycle_penalty = (cycles / 1000) * 2.0
    
    final_result = max(0, base_health - temp_penalty - cycle_penalty - random.uniform(0, 2))
    
    # 5. 결과 화면 표시
    st.divider()
    st.subheader("📊 시뮬레이션 결과")
    
    col1, col2 = st.columns(2)
    col1.metric("예상 배터리 수명 (SOH)", f"{final_result:.2f}%")
    col2.metric("상태", "양호" if final_result > 80 else "점검 필요")

    # 참고: 데이터 저장 로직(Google Sheets)은 현재 비활성화되어 있습니다.
    st.info("💡 현재 '공개 모드'로 실행 중이며, 외부 데이터베이스에 기록되지 않습니다.")

else:
    st.info("사이드바에서 조건을 설정한 후 '시뮬레이션 시작' 버튼을 눌러주세요.")