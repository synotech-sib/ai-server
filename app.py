import streamlit as st
import time
import random
import os

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="SYNOTECH 배터리 시뮬레이터",
    page_icon="🔋",
    layout="centered"
)

# 2. 로그인 상태 관리 (세션 상태 초기화)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 3. 로그인 인증 함수
def login():
    # 업체별 부여할 비밀번호 리스트 (원하는 만큼 추가 가능)
    allowed_passwords = [
        "synotech0773",   # 기본 관리자용
        "client_a_7788",  # 업체 A용
        "client_b_1122"   # 업체 B용
    ]
    
    if st.session_state["password_input"] in allowed_passwords:
        st.session_state['logged_in'] = True
    else:
        st.error("❌ 비밀번호가 올바르지 않습니다. 다시 입력해주세요.")

# --- 화면 구성 시작 ---

# A. 로그인 전 화면
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 로고 파일(logo.jpg)이 서버에 있을 때만 표시하여 에러 방지
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=250)
    
    st.title("🔒 SYNOTECH 고객사 전용 접속")
    st.subheader("배터리 성능 시뮬레이션 시스템")
    
    # 비밀번호 입력창 (type="password"로 별표 표시)
    st.text_input(
        "부여받은 접속 코드를 입력하세요", 
        type="password", 
        key="password_input", 
        on_change=login,
        help="업체별로 할당된 12자리 이상의 코드를 입력하세요."
    )
    
    st.info("💡 비밀번호 입력 후 'Enter'키를 누르면 접속됩니다.")
    st.stop() # 로그인 성공 전까지 아래 코드는 실행되지 않음

# B. 로그인 성공 후 시뮬레이터 화면
# 상단 로고 (작은 사이즈)
if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=120)

st.title("🔋 SYNOTECH 배터리 성능 시뮬레이터")
st.success("✅ 인증되었습니다. 시뮬레이션을 시작할 수 있습니다.")

# --- 사이드바: 입력 조건 설정 ---
st.sidebar.header("🛠️ 시뮬레이션 조건 설정")
temp = st.sidebar.slider("🌡️ 작동 온도 (°C)", 0, 60, 25, help="배터리가 작동하는 외부 온도를 설정합니다.")
cycles = st.sidebar.number_input("🔄 목표 사이클 (Cycle)", min_value=100, max_value=5000, value=1000)

st.sidebar.divider()
if st.sidebar.button("🚪 로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 메인 화면: 시뮬레이션 실행 ---
if st.sidebar.button("🚀 시뮬레이션 시작"):
    # 로딩 애니메이션
    with st.status("배터리 데이터 분석 및 시뮬레이션 진행 중...", expanded=True) as status:
        st.write("알고리즘 최적화 중...")
        progress_bar = st.progress(0)
        
        for i in range(1, 101):
            time.sleep(0.01) # 시뮬레이션 속도 조절
            progress_bar.progress(i)
        
        # 가상의 결과 도출 로직 (온도와 사이클 기반)
        base_health = 100.0
        # 25도에서 멀어질수록 페널티 발생
        temp_effect = abs(temp - 25) * 0.4
        # 사이클이 많을수록 노화 진행
        cycle_effect = (cycles / 1000) * 1.5
        # 미세한 오차 반영
        random_error = random.uniform(0.1, 1.5)
        
        final_soh = max(0, base_health - temp_effect - cycle_effect - random_error)
        status.update(label="✅ 시뮬레이션 완료!", state="complete", expanded=False)

    # 결과 표시 영역
    st.divider()
    st.subheader("📊 예측 분석 결과")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("예상 잔존 수명(SOH)", f"{final_soh:.2f}%")
    c2.metric("작동 온도", f"{temp}°C")
    c3.metric("상태", "Good" if final_soh > 85 else "Caution" if final_soh > 75 else "Bad")

    # 결과 차트 (간단한 예시)
    st.line_chart([100, 98, 95, 92, final_soh])
    
    st.caption("※ 본 결과는 입력값에 기반한 가상 시뮬레이션 데이터입니다.")

else:
    # 초기 진입 시 안내문
    st.info("왼쪽 사이드바에서 조건을 입력하고 '시뮬레이션 시작' 버튼을 눌러주세요.")

# 푸터 (Footer)
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2026 SYNOTECH Co., Ltd. All rights reserved.</p>", unsafe_allow_html=True)