import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image

# 1. 페이지 설정
st.set_page_config(page_title="SYNOTECH SIB Simulator", page_icon="🔋", layout="wide")

# 2. 로고 및 타이틀 표시부
try:
    # GitHub에 올린 로고 파일명이 정확히 logo.png여야 합니다
    img = Image.open("logo.jpg")
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image(img, width=120)
    with col2:
        st.title("SYNOTECH 나트륨 배터리 수명 시뮬레이터")
except Exception:
    # 로고를 못 찾을 경우 기본 타이틀 표시
    st.title("🔋 SYNOTECH 나트륨 배터리 수명 시뮬레이터")

st.write("나트륨이온(SIB) 배터리의 수명과 성능을 예측하는 전문가용 분석 도구입니다.")

# 3. 사이드바 설정 (기존 입력 기능)
st.sidebar.header("📋 시뮬레이션 조건 설정")
temp = st.sidebar.slider("작동 온도 (°C)", -20, 60, 25)
cycles = st.sidebar.number_input("목표 사이클 횟수", min_value=100, max_value=5000, value=1000)

# 4. 시뮬레이션 계산 및 결과 출력
if st.sidebar.button("🚀 시뮬레이션 시작"):
    st.subheader("📊 수명 예측 분석 결과")
    
    # 가상의 감쇠 데이터 생성
    x = np.arange(cycles)
    decay = 0.00005 * (temp + 20) / 40
    y = 100 * np.exp(-decay * x)
    
    # 그래프 시각화 (Plotly 활용)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='용량 유지율 (%)', line=dict(color='#0054A6', width=3)))
    fig.update_layout(xaxis_title="Cycles", yaxis_title="Capacity Retention (%)", height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.success(f"시뮬레이션 완료: {temp}°C 조건에서 {cycles}회 예측 결과입니다.")
else:
    st.info("왼쪽 사이드바에서 조건을 설정한 후 버튼을 눌러주세요.")