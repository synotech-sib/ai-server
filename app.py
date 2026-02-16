import streamlit as st
import time
import random

# 1. 페이지 설정
st.set_page_config(page_title="SYNOTECH 배터리 시뮬레이터", layout="centered")

# 2. 로그인 로직 (세션 상태 활용)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    if st.session_state["password_input"] == "synotech0773":  # ← 사용할 비밀번호 설정
        st.session_state['logged_in'] = True
    else:
        st.error("비밀번호가 틀렸습니다.")

# --- 로그인 화면 ---
if not st.session_state['logged_in']:
    st.title("🔒 시노텍 시뮬레이터 접속")
    st.text_input("접속 비밀번호를 입력하세요", type="password", 
                 key="password_input", on_change=login)
    st.info("비밀번호를 입력하고 Enter를 누르세요.")
    st.stop()  # 로그인 전까지 아래 코드를 실행하지 않음

# --- 시뮬레이터 본문 (로그인 성공 시에만 실행) ---
st.title("🔋 SYNOTECH 배터리 성능 시뮬레이터")
st.success("인증되었습니다. 시뮬레이션을 시작합니다.")

# 사이드바 입력
st.sidebar.header("🛠️ 시뮬레이션 설정")
temp = st.sidebar.slider("작동 온도 (°C)", 0, 60, 25)
cycles = st.sidebar.number_input("목표 사이클 (Cycle)", min_value=100, max_value=5000, value=1000)

if st.sidebar.button("🚀 시뮬레이션 시작"):
    progress_bar = st.progress(0)
    for i in range(101):
        time.sleep(0.01)
        progress_bar.progress(i)
    
    # 가상 결과 도출
    final_result = max(0, 100.0 - abs(temp - 25) * 0.5 - (cycles / 1000) * 2.0 - random.uniform(0, 2))
    
    st.divider()
    st.subheader("📊 시뮬레이션 결과")
    col1, col2 = st.columns(2)
    col1.metric("예상 배터리 수명 (SOH)", f"{final_result:.2f}%")
    col2.metric("상태", "양호" if final_result > 80 else "점검 필요")
    
    st.info("💡 본 시뮬레이터는 현재 '공개 모드'로 운영 중입니다.")

if st.button("로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()