import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random
import io
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 커스텀 CSS (디자인 고정)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

st.markdown("""
    <style>
    /* 메뉴 및 헤더 숨김 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 타이틀 디자인 */
    .syno-title { font-family: 'Helvetica', sans-serif; color: #003366; font-size: 40px; font-weight: 900; line-height: 1.0; }
    .syno-subtitle { font-family: 'Helvetica', sans-serif; color: #000000; font-size: 18px; font-weight: normal; }

    /* 섹션 제목 스타일 (글자 크기 크게 + 볼드) */
    .section-header { font-size: 26px !important; font-weight: bold !important; color: #333; margin-top: 25px; }
    .sub-header { font-size: 20px !important; font-weight: bold !important; color: #444; margin-bottom: 10px; }
    .expert-label { font-size: 22px !important; font-weight: bold !important; color: #003366; }

    /* 버튼 스타일 (시노텍 네이비) */
    div.stButton > button:first-child {
        background-color: #003366; color: white; border-radius: 5px; height: 3.5em; width: 100%; font-weight: bold; font-size: 18px;
    }
    
    /* 무료 체험 / 계정 관리 박스 */
    .info-box { background-color: #003366; color: white; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; margin-top: 5px; cursor: pointer; }
    
    /* 텍스트 크기 일관성 */
    .stMarkdown p { font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터베이스 엔진
# -----------------------------------------------------------------------------
def init_dbs():
    if not os.path.exists("users.xlsx"):
        df = pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Role", "Title", "Phone", "Is_Pro", "Is_Admin"])
        df.to_excel("users.xlsx", index=False)
    if not os.path.exists("simulation_logs.xlsx"):
        df = pd.DataFrame(columns=["Timestamp", "User", "ID", "Summary", "Result_Data"])
        df.to_excel("simulation_logs.xlsx", index=False)

def load_mat_db():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("param_config.xlsx")
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except:
        return pd.DataFrame(), pd.DataFrame()

init_dbs()
mat_df, param_dict = load_mat_db()

# -----------------------------------------------------------------------------
# 3. 세션 상태 관리
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'page' not in st.session_state: st.session_state.page = "Main" # Main or MyPage or Admin
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0
if 'history' not in st.session_state: st.session_state.history = []

# -----------------------------------------------------------------------------
# 4. 상단 레이아웃 (타이틀 & 로그인/계정생성)
# -----------------------------------------------------------------------------
top_left, top_right = st.columns([1.5, 1])

with top_left:
    st.markdown('<div class="syno-title">SynoCore</div>', unsafe_allow_html=True)
    st.markdown('<div class="syno-subtitle">V1.4 Pro</div>', unsafe_allow_html=True)

with top_right:
    if not st.session_state.logged_in:
        # 로그인 섹션
        with st.container():
            c1, c2, c3 = st.columns([2, 2, 1])
            login_id = c1.text_input("ID", placeholder="company email", label_visibility="collapsed")
            login_pw = c2.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
            login_btn = c3.button("Login")
            
            # 관리자 계정 체크
            if login_btn:
                if login_id == "wschoi@synotech.co.kr" and login_pw == "synotech0773!":
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"Email": login_id, "Name": "최우성", "Is_Admin": True, "Is_Pro": True}
                    st.rerun()
                else:
                    users = pd.read_excel("users.xlsx")
                    user = users[(users['Email'] == login_id) & (users['Password'] == str(login_pw))]
                    if not user.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("계정 정보를 확인하세요.")
            
            # 계정 생성 링크
            st.markdown('<div style="text-align:right; font-size:13px; color:#666;">계정생성 ㅣ Pro 회원가입</div>', unsafe_allow_html=True)
            
            # 무료 시도 표시
            st.markdown(f'<div class="info-box">무료 시도 {st.session_state.trial_count}/3</div>', unsafe_allow_html=True)
            
            # 계정 생성 익스팬더 (로그인 박스 하단 배치)
            with st.expander("계정 신청 및 인증"):
                if st.session_state.reg_stage == 0:
                    reg_email = st.text_input("회사 이메일 입력")
                    if st.button("인증메일 전송"):
                        st.session_state.temp_email = reg_email
                        st.session_state.v_code = str(random.randint(100000, 999999))
                        st.session_state.reg_stage = 1
                        st.info(f"인증번호: {st.session_state.v_code}") # 실제로는 메일 발송
                        st.rerun()
                elif st.session_state.reg_stage == 1:
                    v_input = st.text_input("6자리 인증번호")
                    if st.button("인증 확인"):
                        if v_input == st.session_state.v_code:
                            st.session_state.reg_stage = 2
                            st.rerun()
                elif st.session_state.reg_stage == 2:
                    with st.form("join"):
                        st.write(f"이메일: {st.session_state.temp_email}")
                        p1 = st.text_input("비밀번호", type="password")
                        p2 = st.text_input("비밀번호 확인", type="password")
                        nm = st.text_input("이름")
                        cp = st.text_input("회사")
                        dt = st.text_input("부서")
                        rl = st.text_input("담당업무")
                        tl = st.text_input("직함")
                        ph = st.text_input("전화 연락처")
                        if st.form_submit_button("가입 완료"):
                            new_u = {"Email": st.session_state.temp_email, "Password": p1, "Name": nm, "Company": cp, "Dept": dt, "Role": rl, "Title": tl, "Phone": ph, "Is_Pro": True, "Is_Admin": False}
                            users = pd.read_excel("users.xlsx")
                            pd.concat([users, pd.DataFrame([new_u])]).to_excel("users.xlsx", index=False)
                            st.success("가입 성공! 로그인 하세요.")
                            st.session_state.reg_stage = 0

    else:
        # 로그인 후 상태
        st.write(f"**{st.session_state.user_info['Name']}** 님 환영합니다.")
        btn_col1, btn_col2 = st.columns(2)
        if btn_col1.button("나의 계정 및 데이터 관리"):
            st.session_state.page = "MyPage"
            st.rerun()
        if st.session_state.user_info.get('Is_Admin'):
            if btn_col2.button("Admin Panel"):
                st.session_state.page = "Admin"
                st.rerun()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "Main"
            st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 페이지 라우팅
# -----------------------------------------------------------------------------

# (A) 관리자 페이지
if st.session_state.page == "Admin":
    st.header("🛡️ Admin Settings & Activity Logs")
    if st.button("⬅️ 메인으로"): st.session_state.page = "Main"; st.rerun()
    
    tab1, tab2 = st.tabs(["사용자 관리", "전체 로그 기록"])
    with tab1:
        st.dataframe(pd.read_excel("users.xlsx"), use_container_width=True)
    with tab2:
        st.dataframe(pd.read_excel("simulation_logs.xlsx"), use_container_width=True)

# (B) 마이 페이지
elif st.session_state.page == "MyPage":
    st.header("👤 나의 계정 및 데이터 관리")
    if st.button("⬅️ 메인으로"): st.session_state.page = "Main"; st.rerun()
    
    st.subheader("내 시뮬레이션 이력")
    all_logs = pd.read_excel("simulation_logs.xlsx")
    my_logs = all_logs[all_logs['User'] == st.session_state.user_info['Email']]
    st.dataframe(my_logs, use_container_width=True)
    
    st.subheader("회원 정보")
    st.json(st.session_state.user_info)

# (C) 메인 시뮬레이터 (핵심)
else:
    # [1번] 소재 선택 (전해질/분리막 분리)
    st.markdown('<div class="section-header">1. Material Selection</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        cat_name = st.selectbox("Cathode", mat_df[mat_df['Category'] == 'Cathode']['Name'])
        cat_row = mat_df[mat_df['Name'] == cat_name].iloc[0]
    with m2:
        ano_name = st.selectbox("Anode", mat_df[mat_df['Category'] == 'Anode']['Name'])
        ano_row = mat_df[mat_df['Name'] == ano_name].iloc[0]
    with m3:
        ele_name = st.selectbox("Electrolyte", mat_df[mat_df['Category'] == 'Electrolyte']['Name'])
    with m4:
        sep_name = st.selectbox("Separator", mat_df[mat_df['Category'] == 'Separator']['Name'])

    # [2번] 소재 스펙 (전문가 슬라이더)
    st.markdown('<div class="section-header">2. Material Specs Expert Mode</div>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 소재 고유 물성 직접 수정 활성화")
    
    if expert_spec:
        st.markdown('<div class="expert-label">Tuning Material Properties</div>', unsafe_allow_html=True)
        sc1, sc2, sc3, sc4 = st.columns(4)
        c_cap = sc1.slider("Capacity (mAh/g)", 100.0, 250.0, float(cat_row['Base_Capacity']))
        c_volt = sc2.slider("Voltage (V)", 2.0, 4.5, float(cat_row['Base_Avg_Voltage']))
        c_dens = sc3.slider("Density (g/cc)", 1.5, 4.0, float(cat_row['Base_True_Density']))
        c_life = sc4.slider("Base Life (Cycles)", 500, 10000, int(cat_row['Base_Life']))
    else:
        # 기본 보기 (글자 크게 + 볼드)
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.markdown(f"**Capacity**\n### {cat_row['Base_Capacity']} mAh/g")
        sc2.markdown(f"**Voltage**\n### {cat_row['Base_Avg_Voltage']} V")
        sc3.markdown(f"**Density**\n### {cat_row['Base_True_Density']} g/cc")
        sc4.markdown(f"**Life**\n### {cat_row['Base_Life']} Cyc")
        c_cap, c_volt, c_dens, c_life = cat_row['Base_Capacity'], cat_row['Base_Avg_Voltage'], cat_row['Base_True_Density'], cat_row['Base_Life']

    # [3번] 공정 파라미터
    st.markdown('<div class="section-header">3. Process Parameters</div>', unsafe_allow_html=True)
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        st.markdown('<div class="sub-header">(A) Cathode Settings</div>', unsafe_allow_html=True)
        loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, 14.0)
    with p_col2:
        st.markdown('<div class="sub-header">(B) Anode & Balance</div>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15)
    with p_col3:
        st.markdown('<div class="sub-header">(C) Electrolyte Change</div>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0)

    # [4번] 목표값 설정
    st.markdown('<div class="section-header">4. Target Design Goals</div>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown('<div class="sub-header">Target Energy Density (Wh/kg)</div>', unsafe_allow_html=True)
        target_e = st.slider("Energy Goal", 100, 250, 160, label_visibility="collapsed")
    with t2:
        st.markdown('<div class="sub-header">Target C-rate (C)</div>', unsafe_allow_html=True)
        target_c = st.slider("C-rate Goal", 0.1, 10.0, 1.0, label_visibility="collapsed")

    # [5번] 시뮬레이션 이력 및 실행
    st.markdown('<div class="section-header">5. Simulation Execution & History</div>', unsafe_allow_html=True)
    
    if st.button("🚀 RUN DESIGN SIMULATION"):
        if not st.session_state.user_info.get('Is_Pro') and st.session_state.trial_count >= 3:
            st.error("무료 체험 횟수 초과. Pro 가입이 필요합니다.")
        else:
            st.session_state.trial_count += 1
            # 시뮬레이션 계산 로직
            wh_kg = (c_cap * (active_ratio/100) * (c_volt - ano_row['Base_Avg_Voltage'])) / 2.5 # 간이 수식
            sim_id = f"SIM-{random.randint(1000,9999)}"
            summary = f"[{sim_id}] {cat_name}/{ano_name} | {target_c}C | {wh_kg:.1f}Wh/kg"
            
            # 로그 저장
            log_entry = {"Timestamp": datetime.now(), "User": st.session_state.user_info.get('Email', 'Guest'), "ID": sim_id, "Summary": summary, "Result_Data": wh_kg}
            pd.concat([pd.read_excel("simulation_logs.xlsx"), pd.DataFrame([log_entry])]).to_excel("simulation_logs.xlsx", index=False)
            st.session_state.history.insert(0, log_entry)
            st.session_state.current_res = log_entry

    if st.session_state.history:
        st.markdown('<div class="sub-header">과거 시뮬레이션 기록 선택 (최근 순)</div>', unsafe_allow_html=True)
        hist_sel = st.selectbox("이력 선택", [h['Summary'] for h in st.session_state.history], label_visibility="collapsed")

    # 결과 대시보드
    if 'current_res' in st.session_state:
        st.markdown("---")
        st.subheader("📊 Engineering Analysis Result")
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"#### **무게 에너지 밀도**\n## {st.session_state.current_res['Result_Data']:.1f} Wh/kg")
        r2.markdown(f"#### **예상 전압**\n## {c_volt - ano_row['Base_Avg_Voltage']:.2f} V")
        r3.markdown(f"#### **예상 수명**\n## {c_life} Cycles")

        # 그래프 (Half-cell / Full-cell 모사)
        x = np.linspace(0, 100, 100)
        y = np.exp(-x/50) * c_volt
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, name="Full-cell Discharge", line=dict(color='#003366', width=3)))
        fig.update_layout(title="Predicted Discharge Profile", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # 상세 설계 데이터 표
        detailed_data = pd.DataFrame({
            "설계 항목": ["Cathode Loading", "Anode Loading", "N/P Ratio", "Cell Voltage"],
            "수치": [f"{loading} mg/cm2", f"{loading*1.1:.2f} mg/cm2", f"{np_ratio}", f"{c_volt - ano_row['Base_Avg_Voltage']:.2f} V"]
        })
        st.table(detailed_data)
        
        # 다운로드
        csv = detailed_data.to_csv(index=False).encode('utf-8')
        st.download_button("📥 결과 데이터 다운로드 (CSV)", csv, "simulation_result.csv", "text/csv")