import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. 페이지 기본 설정
st.set_page_config(page_title="SYNOTECH SIB Simulator", page_icon="🔋", layout="wide")

# 2. 구글 시트 저장 함수 정의
def save_to_sheets(temp, cycles, result):
    try:
        # 서비스 계정 인증 정보 (Streamlit Secrets에서 불러옴)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # 구글 시트 열기 (시트 이름이 'SYNOTECH_Simulation_Log'여야 함)
        sheet = client.open("SYNOTECH_Simulation_Log").sheet1
        
        # 기록할 데이터 준비
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, temp, cycles, f"{result:.2f}%"])
        return True
    except Exception as e:
        st.error(f"데이터 기록 실패: {e}")
        return False

# 3. 상단 로고 및 타이틀
try:
    # GitHub에 업로드한 파일명이 logo.png인지 확인하세요
    img = Image.open("logo.png")
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image(img, width=120)
    with col2:
        st.title("SYNOTECH 나트륨 배터리 수명 시뮬레이터")
except Exception:
    st.title("🔋 SYNOTECH 나트륨 배터리 수명 시뮬레이터")

st.write("나트륨이온(SIB) 배터리의 수명과 성능을 예측하는 전문가용 분석 도구입니다.")

# 4. 사이드바 설정
st.sidebar.header("📋 시뮬레이션 조건 설정")
temp = st.sidebar.slider("작동 온도 (°C)", -20, 60, 25)
cycles = st.sidebar.number_input("목표 사이클 횟수", min_value=100, max_value=5000, value=1000)

# 5. 메인 로직 및 결과 출력
if st.sidebar.button("🚀 시뮬레이션 시작"):
    st.subheader("📊 수명 예측 분석 결과")
    
    # 가상의 수명 감쇠 계산
    x = np.arange(cycles)
    decay = 0.00005 * (temp + 20) / 40
    y = 100 * np.exp(-decay * x)
    final_retention = y[-1]
    
    # 시각화 그래프 (Plotly)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='용량 유지율 (%)', line=dict(color='#0054A6', width=3)))
    fig.update_layout(xaxis_title="Cycles", yaxis_title="Capacity Retention (%)")
    st.plotly_chart(fig, use_container_width=True)
    
    # 구글 시트에 데이터 저장 실행
    with st.spinner('