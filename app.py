import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import random

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# 커스텀 CSS (헤더 50:50, 박스 수납, 버튼 높이, 텍스트 크기)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* 헤더 50:50 배치 */
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 8px; }
    
    /* 로그인 버튼 높이 및 스타일 */
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    
    /* 무료 시도 강조 박스 */
    .trial-highlight {
        background-color: #003366; color: white; padding: 10px; border-radius: 8px;
        text-align: center; font-size: 18px; font-weight: bold; margin-top: 5px;
    }
    
    /* [박스 수납] 제목과 내용이 모두 들어가는 회색 박스 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 45px !important; 
    }
    
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 구글 스프레드시트 연결 및 데이터베이스 설정
# -----------------------------------------------------------------------------
# 주소: https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing
conn = st.connection("gsheets", type=GSheetsConnection)

def get_db():
    return conn.read(ttl=5)

# -----------------------------------------------------------------------------
# 3. 세션 상태 초기화
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'show_reg' not in st.session_state: st.session_state.show_reg = False
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0 # 0:메일, 1:인증, 2:정보입력
if 'v_code' not in st.session_state: st.session_state.v_code = ""
if 'temp_email' not in st.session_state: st.session_state.temp_email = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'sim_result' not in st.session_state: st.session_state.sim_result = None

# 소재 DB
mat_db = {
    "Prussian White": {"cap": 162, "volt": 3.05, "dens": 2.2, "life": 4000, "load": 14.0, "active": 92.0},
    "Layered Oxide": {"cap": 140, "volt": 3.00, "dens": 2.4, "life": 3000, "load": 15.0, "active": 95.0},
    "Polyanion": {"cap": 115, "volt": 3.80, "dens": 2.2, "life": 8000, "load": 12.0, "active": 90.0}
}

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인/회원가입 (50:50 배치)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="login_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="login_pw", label_visibility="collapsed")
        if l_c3.button("Login"):
            # 관리자 및 구글 시트 대조
            df_u = get_db()
            valid_user = df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == u_pw)]
            if (u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!") or not valid_user.empty:
                st.session_state.logged_in = True; st.rerun()
            else: st.error("정보를 확인하세요.")
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            if st.button("계정생성 ㅣ Pro 회원가입"): st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            st.markdown(f'<div class="trial-highlight">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ 접속 중: {st.session_state.get('login_id', 'Admin')}")
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# -----------------------------------------------------------------------------
# 5. 계정 신청 프로세스 (보안 및 상세 정보 입력)
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 및 보안 인증 (Pro)</p>', unsafe_allow_html=True)
        
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소 입력")
            if st.button("인증번호 발송"):
                if "@" in e_in:
                    st.session_state.v_code = str(random.randint(100000, 999999))
                    st.session_state.temp_email = e_in
                    st.session_state.reg_stage = 1; st.rerun()
                else: st.error("이메일 형식을 확인하세요.")
        
        elif st.session_state.reg_stage == 1:
            st.write(f"이메일: **{st.session_state.temp_email}**")
            st.info(f"인증번호(테스트): {st.session_state.v_code}")
            v_in = st.text_input("인증번호 6자리 입력")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code:
                    st.session_state.reg_stage = 2; st.rerun()
                else: st.error("인증번호 불일치")
        
        elif st.session_state.reg_stage == 2:
            st.write(f"가입 이메일: **{st.session_state.temp_email}**")
            p1, p2 = st.columns(2)
            new_pw = p1.text_input("2. Password 설정", type="password")
            confirm_pw = p2.text_input("2-1. Password 확인", type="password")
            
            if new_pw and confirm_pw:
                if new_pw != confirm_pw: st.error("비밀번호가 일치하지 않습니다.")
                else: st.success("비밀번호가 일치합니다.")
            
            new_name = st.text_input("3. 이름")
            new_comp = st.text_input("4. Company (회사명)")
            new_dept = st.text_input("5. 부서")
            new_job = st.text_input("6. 담당업무")
            new_phone = st.text_input("7. 연락처 (전화번호)")
            
            st.markdown("---")
            with st.expander("(동의) 내용보기"):
                st.markdown("""
                **[시뮬레이션 이용 약관 및 면책 조항]**
                - 본 시뮬레이션 자료는 참조용으로만 사용해야 하며, 보고서의 내용과 다른 실제 결과가 나오는 것에 대해 **시노코어는 책임을 지지 않는다.**
                - 사용자는 본 서비스의 결과를 근거로 한 투자 및 제조 결정에 대한 모든 책임을 부담합니다.
                - 입력하신 정보는 서비스 승인 및 기술 지원 목적으로만 활용됩니다.
                """)
            agree = st.checkbox("위의 약관 내용을 확인하였으며, 이에 동의합니다.")
            
            # 모든 필수 조건 충족 시 가입신청 버튼 활성화
            can_submit = agree and (new_pw == confirm_pw) and new_pw and new_name and new_comp and new_phone
            
            if st.button("가입신청", disabled=not can_submit):
                try:
                    df_u = get_db()
                    new_user = pd.DataFrame([{
                        "Email": st.session_state.temp_email, "Password": new_pw, "Name": new_name,
                        "Company": new_comp, "Dept": new_dept, "Job": new_job, "Phone": new_phone,
                        "RegDate": datetime.now().strftime("%Y-%m-%d")
                    }])
                    updated_df = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("가입신청이 완료되었습니다! 관리자 승인 후 연락드리겠습니다.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except: st.error("구글 시트 저장 실패. 권한 설정을 확인하세요.")
        st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 시뮬레이터 본문 (1~5번 완전 수납 박스)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_type = m1.selectbox("Cathode", list(mat_db.keys()))
    m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"])
    m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"])
    m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"])
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 연동 로직
cur = mat_db[cat_type]
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_type:
    st.session_state.last_cat = cat_type
    st.session_state.c_cap, st.session_state.c_volt = float(cur['cap']), float(cur['volt'])
    st.session_state.c_dens, st.session_state.c_life = float(cur['dens']), int(cur['life'])
    st.session_state.loading, st.session_state.active = float(cur['load']), float(cur['active'])

# [2] Material Specs Expert Mode
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, st.session_state.c_cap)
        c_volt = s2.slider("Voltage (V)", 2.5, 4.5, st.session_state.c_volt)
        c_dens = s3.slider("Density (g/cc)", 1.5, 4.0, st.session_state.c_dens)
        c_life = s4.slider("Life (Cycles)", 500, 10000, st.session_state.c_life)
    else:
        c_cap, c_volt, c_dens, c_life = st.session_state.c_cap, st.session_state.c_volt, st.session_state.c_dens, st.session_state.c_life
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life} Cycles', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (상세 보기 기능)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        load = st.slider("Loading (mg/cm2)", 5.0, 45.0, st.session_state.loading)
        if show_adv:
            st.slider("Cathode Press Density (g/cc)", 1.5, 3.5, 2.5)
            st.slider("Conductive Agent %", 0.5, 5.0, 2.0)
            st.slider("Binder %", 0.5, 5.0, 3.0)
            st.caption(f"Estimated Thickness: {load/2.5*10:.1f} μm")
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        np = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
        if show_adv:
            st.slider("Anode Press Density (g/cc)", 0.8, 2.0, 1.1)
            st.slider("Anode Active Material %", 90.0, 98.0, 95.0)
            st.slider("Anode ICE (%)", 80.0, 98.0, 92.0)
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte & Cell</p>', unsafe_allow_html=True)
        act = st.slider("Active Ratio (%)", 80.0, 99.0, st.session_state.active)
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
            st.slider("Separator Thick (μm)", 12, 30, 16)
            st.slider("Tab/Can Weight Factor", 1.0, 1.5, 1.1)
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1: target_e = st.slider("Energy Density Goal (Wh/kg)", 100, 250, 160)
    with t2: target_c = st.slider("Simulation C-rate (출력 조건)", 0.1, 20.0, 1.0)
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run (PC 시간 기록)
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            # AI 계산 (에너지 밀도 추정)
            res_whkg = (c_cap * (act/100) * (c_volt - 0.1)) / (2.4 + (load/35))
            cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log = {"time": cur_time, "whkg": res_whkg, "v": c_volt - 0.1, "life": c_life, "cat": cat_type}
            st.session_state.history.insert(0, log)
            st.session_state.sim_result = log
        else: st.error("무료 횟수(10회)를 초과했습니다. Pro 로그인이 필요합니다.")

    if st.session_state.history:
        st.markdown('<p class="sub-header-bold">과거 시뮬레이션 기록 선택</p>', unsafe_allow_html=True)
        h_list = [f"[{h['time']}] {h['cat']} | {h['whkg']:.1f} Wh/kg" for h in st.session_state.history]
        st.selectbox("History History", h_list, label_visibility="collapsed")

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Engineering Analysis Result (Recorded: {res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{res['v']:.2f} V")
        r3.metric("Expected Life", f"{res['life']:,} Cycles")
        
        g1, g2 = st.columns([3, 7])
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            x = np.linspace(0, 100, 100); y = c_volt - 0.1 - (x/100)**1.5
            fig = go.Figure(go.Scatter(x=x, y=y, line=dict(color='#003366', width=3)))
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown('<p class="sub-header-bold">Design Parameters Summary</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Parameter": ["Loading", "N/P", "Active%", "C-rate"], "Value": [f"{load} mg", f"{np}", f"{act}%", f"{target_c}C"]}))
    st.markdown("<br>", unsafe_allow_html=True)