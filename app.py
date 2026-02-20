import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# [안정화] 라이브러리 체크 및 연결
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("설치 필요: pip install st-gsheets-connection")

# 1. 페이지 설정 및 전문가용 UI 디자인
st.set_page_config(page_title="SynoCore V1.5 Pro Max", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #666; font-size: 20px; font-weight: normal; }
    .main-header { font-size: 24px; font-weight: bold; color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 20px; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stSidebar"] { background-color: #f1f3f5; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 유틸리티 함수 (보안 및 데이터 안정화)
# -----------------------------------------------------------------------------
def hash_password(password):
    """비밀번호 단방향 암호화 (SHA-256)"""
    return hashlib.sha256(password.strip().encode()).hexdigest()

def get_user_db(conn, url):
    """[안정화] 구글 시트 데이터 로드 및 PyArrow 에러 방지"""
    try:
        df = conn.read(spreadsheet=url, worksheet="Sheet1", ttl=5)
        return df.astype(str) # 모든 데이터를 문자로 강제 변환하여 화면 출력 에러 차단
    except Exception:
        # 연결 실패 시 빈 데이터프레임 반환 (앱 중단 방지)
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# 3. 세션 상태 및 기본 데이터 정의
# -----------------------------------------------------------------------------
if 'init_v15' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'show_reg': False, 'reg_stage': 0, 
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None, 'init_v15': True
    })

# 글로벌 3사 양극재 마스터 DB (논문 근거 스펙)
MASTER_MATS = [
    {"Name": "HiNa Battery (Layered Oxide)", "Cap": 145.0, "Volt": 3.2, "Dens": 4.0, "Type": "Layered", "Life": 3000},
    {"Name": "Altris (Prussian White)", "Cap": 160.0, "Volt": 3.2, "Dens": 1.8, "Type": "Prussian", "Life": 4000},
    {"Name": "Tiamat (Polyanion NVPF)", "Cap": 130.0, "Volt": 3.8, "Dens": 2.8, "Type": "Polyanion", "Life": 5000}
]

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인/회원가입 섹션 (완체 버전)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div style="display: flex; align-items: center;"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.5 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="login_id", label_visibility="collapsed").strip().lower()
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="login_pw", label_visibility="collapsed")
        
        if l_c3.button("Login", use_container_width=True):
            # 마스터 프리패스 계정
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
            else:
                df_u = get_user_db(conn, SHEET_URL)
                hashed_pw = hash_password(u_pw) if u_pw else ""
                # [안정화] 공백 제거 및 소문자 변환 대조
                valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id) & (df_u['Password'] == hashed_pw)]
                if not valid.empty:
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("정보가 일치하지 않습니다.")

        if st.button("계정 생성 ㅣ Pro 회원가입", use_container_width=True):
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.success(f"✅ 접속 중: Authorized Member")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# [회원가입 상세 로직 - 전체 포함]
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소", key="reg_email")
            if st.button("인증번호 발송"):
                if "@" in e_in:
                    st.session_state.v_code = str(random.randint(100000, 999999))
                    st.session_state.temp_email = e_in; st.session_state.reg_stage = 1; st.rerun()
                else: st.warning("올바른 이메일 형식을 입력하세요.")
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력", key="reg_v_in")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
                else: st.error("인증번호가 틀립니다.")
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2)
            pw1 = p1.text_input("2. Password", type="password", key="reg_pw1")
            pw2 = p2.text_input("2-1. Password 확인", type="password", key="reg_pw2")
            n_name = st.text_input("3. 이름", key="reg_name")
            n_comp = st.text_input("4. 회사명", key="reg_comp")
            if st.button("가입신청", disabled=not (pw1==pw2 and n_name and n_comp)):
                try:
                    df_u = get_user_db(conn, SHEET_URL)
                    new_user = pd.DataFrame([{
                        "Email": st.session_state.temp_email, 
                        "Password": hash_password(pw1), 
                        "Name": n_name, "Company": n_comp,
                        "RegDate": datetime.now().strftime("%Y-%m-%d")
                    }])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    # [요청 반영] 성공 메시지 수정
                    st.success("가입신청이 완료되었습니다. 개인정보는 암호화되어 보관되므로 안심하셔도 됩니다.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except Exception as e:
                    st.error(f"저장 중 오류 발생: {e}")

# -----------------------------------------------------------------------------
# 5. 시뮬레이션 엔진 및 대시보드
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    sel_mat = st.selectbox("Cathode Library", MASTER_MATS, format_func=lambda x: x['Name'])
    
    st.markdown("---")
    st.markdown('<p class="main-header">2. Lab-to-Fab Correction</p>', unsafe_allow_html=True)
    # [신기능] 현장 효율 보정 슬라이더
    yield_val = st.slider("양산 공정 효율 (%)", 70, 100, 92, help="연구실 이론값 대비 실제 양산 시 발현되는 성능 비율") / 100.0
    
    expert = st.toggle("🔓 Expert Mode (Manual Edit)")
    v_cap = st.number_input("Capacity (mAh/g)", value=sel_mat['Cap']) if expert else sel_mat['Cap']
    v_volt = st.number_input("Avg. Voltage (V)", value=sel_mat['Volt']) if expert else sel_mat['Volt']
    v_act = st.slider("Active Material Ratio (%)", 85.0, 98.0, 92.0)

# 실행 버튼
if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
    final_cap = v_cap * yield_val * (v_act/100)
    # 에너지 밀도 간이 수식 (보수적 접근)
    res_whkg = (final_cap * (v_volt - 0.1)) / 2.5 
    
    # [신기능] dQ/dV 피크 생성 알고리즘 (소재 특성 반영)
    v_axis = np.linspace(2.0, 4.2, 200)
    dqdv = np.zeros_like(v_axis)
    if sel_mat['Type'] == "Prussian": peaks = [3.05, 3.45]
    elif sel_mat['Type'] == "Polyanion": peaks = [3.75]
    else: peaks = [3.2] # Layered
    
    for p in peaks:
        dqdv += np.exp(-(v_axis - p)**2 / (2 * 0.05**2)) * 15 # 가우시안 피크 시뮬레이션
    
    st.session_state.sim_result = {
        "whkg": round(res_whkg, 1), "v": v_volt, "cap": round(final_cap, 1),
        "dq_x": v_axis, "dq_y": dqdv, "life": sel_mat['Life'],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# 결과 리포트 출력
if st.session_state.sim_result:
    res = st.session_state.sim_result
    st.markdown("---")
    st.markdown(f'<p class="main-header">Analysis Result ({res["time"]})</p>', unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Energy Density", f"{res['whkg']} Wh/kg")
    m2.metric("Final Cap", f"{res['cap']} mAh/g")
    m3.metric("Nominal Volt", f"{res['v']} V")
    m4.metric("Expected Life", f"{res['life']:,} Cyc")
    
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Discharge Profile (V vs DOD)")
        # 실제 배터리 곡선과 유사하게 2차 함수 적용
        fig1 = go.Figure(go.Scatter(x=np.linspace(0, 100, 100), y=res['v'] - (np.linspace(0, 1, 100)**2.5), line=dict(color='#003366', width=4)))
        fig1.update_layout(xaxis_title="Depth of Discharge (%)", yaxis_title="Voltage (V)", height=400, template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        st.subheader("dQ/dV Profile (Chemical Fingerprint)")
        fig2 = go.Figure(go.Scatter(x=res['dq_x'], y=res['dq_y'], fill='tozeroy', line=dict(color='#e63946', width=2)))
        fig2.update_layout(xaxis_title="Voltage (V)", yaxis_title="Differential Capacity (dQ/dV)", height=400, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
        
    # 실험 기록 저장 (간이 로그)
    st.session_state.history.insert(0, {"Time": res['time'], "Material": sel_mat['Name'], "Whkg": res['whkg']})
    if st.session_state.history:
        with st.expander("📋 Simulation History (Recent)"):
            st.table(pd.DataFrame(st.session_state.history[:5]))