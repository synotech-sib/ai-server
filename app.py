import streamlit as st
import time
import random
import os

# 1. 페이지 설정
st.set_page_config(page_title="SYNOTECH 배터리 시뮬레이터", layout="centered")

# 2. 로그인 로직 (업체별 다중 비번 설정)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    # 업체별 비밀번호 리스트 정의
    allowed_passwords = [
        "synotech0773",  # 기본 비번
        "client_001", # 업체 A용
        "client_002"  # 업체 B용
    ]
    
    if st.session_state["password_input"] in allowed_passwords:
        st.session_state['logged_in'] = True
    else:
        st.error("비밀번호가 틀렸습니다. 업체 전용 번호를 확인하세요.")

# --- 로그인 화면 ---
if not st.session_state['logged_in']:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=200)
    
    st.title("🔒 SYNOTECH 고객사 전용 접속")
    st.text_input("부여받은 비밀번호를 입력하세요", type="password", 
                 key="password_input", on_change=login)
    st.info("비밀번호를 입력하고 Enter를 누르세요.")
    st.stop()

# --- 시뮬레이터 본문 (로그인 성공 시) ---
if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("🔋 SYNOTECH 배터리 성능 시뮬레이터")
st.success(f"인증되었습니다. 환영합니다!")

# ... (이하 시뮬레이션 로직 동일)