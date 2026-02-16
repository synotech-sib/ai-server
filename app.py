import streamlit as st
import numpy as np
import pandas as pd

# 1. 페이지 및 제목 설정 (SYNOTECH 반영)
st.set_page_config(page_title="SYNOTECH SIB AI Simulator", layout="wide")
st.title("🔋 SYNOTECH 나트륨 배터리 수명 시뮬레이터")
st.write("나트륨이온(SIB) 배터리의 수명과 성능을 예측하는 전문가용 분석 도구입니다.")

# 2. 사이드바 - 조건 조절 장치
st.sidebar.header("📋 시뮬레이션 파라미터")
temp = st.sidebar.slider("작동 온도 (℃)", -20, 60, 25)
voltage = st.sidebar.number_input("충전 전압 (V)", 3.0, 4.5, 4.2)
c_rate = st.sidebar.slider("충방전 속도 (C-rate)", 0.1, 5.0, 1.0)
target_cycles = st.sidebar.number_input("예측 목표 사이클", 100, 2000, 1000)

# 3. 예측 수식 (물리 기반 간이 모델)
def run_simulation(t, v, c, cycles):
    # 온도, 전압, 충전속도에 따른 가중치 계산
    decay = 0.0001 * np.exp(0.02 * abs(t-25)) * (1 + (v-4.2)*5) * (1 + 0.05*c)
    x = np.arange(0, cycles + 1, 10)
    y = 100 * np.exp(-decay * x)
    return x, y

# 4. 결과 시각화
if st.sidebar.button("🚀 시뮬레이션 시작"):
    x, y = run_simulation(temp, voltage, c_rate, target_cycles)
    
    col1, col2 = st.columns(2)
    col1.metric("최종 예상 SOH (상태)", f"{y[-1]:.1f}%")
    col2.metric("판정", "✅ 안정적" if y[-1] > 80 else "⚠️ 성능 저하 주의")
    
    st.subheader("📊 사이클별 용량 유지율 예측 곡선")
    chart_data = pd.DataFrame({'Cycle': x, 'SOH(%)': y}).set_index('Cycle')
    st.line_chart(chart_data)
    
    st.success("시뮬레이션이 완료되었습니다.")
else:
    st.info("왼쪽 사이드바에서 조건을 설정한 후 '시뮬레이션 시작' 버튼을 눌러주세요.")