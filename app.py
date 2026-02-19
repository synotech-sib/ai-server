import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime
import random

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# CSS: 헤더 50:50, 박스 수납, 버튼 높이 조정
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 8px; }
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    .trial-highlight {
        background-color: #003366; color: white; padding: 15px; border-radius: 8px;
        text-align: center; font-size: 24px; font-weight: bold; margin-top: 10px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 10px 25px !important;
        margin-bottom: 45px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. [에러 해결] 세션 상태 초기화 (AttributeError 방지)
# -----------------------------------------------------------------------------
session_keys = {
    'logged_in': False, 'trial_count': 0, 'show_reg': False, 
    'reg_stage': 0, 'v_code': "", 'temp_email': "", 
    'history': [], 'sim_result': None, 'loading_val': 14.0
}
for key, value in session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------------------------------------------------------
# 3. [에러 해결] 데이터 로드 및 DB 자동 생성 (KeyError & Mismatch 방지)
# -----------------------------------------------------------------------------
USER_DB = "users.xlsx"
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "RegDate"]).to_excel(USER_DB, index=False)

@st.cache_data
def load_mat_data():
    file = "material_list.xlsx"
    if not os.path.exists(file): return pd.DataFrame()
    df = pd.read_excel(file)
    # 컬럼명 표준화: 공백 제거 및 괄호(단위) 제거 (KeyError 방지)
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_mat_data()

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (50:50 배치 및 로그인)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="company email", key="login_id_input", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="login_pw_input", label_visibility="collapsed")
        if l_c3.button("Login", key="btn_main_login"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.rerun()
            else:
                users = pd.read_excel(USER_DB)
                if not users[(users['Email'] == u_id) & (users['Password'].astype(str) == u_pw)].empty:
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("로그인 정보를 확인하세요.")
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_show_reg"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            st.markdown(f'<div class="trial-highlight" style="font-size:16px; padding:5px; margin-top:0;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.write(f"✅ **{u_id if 'u_id' in locals() else 'User'}** 접속 중")
        if st.button("Logout", key="btn_logout"):
            st.session_state.logged_in = False
            st.rerun()

# 보안 가입 로직 (이메일 인증 포함)
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">계정 신청 및 보안 인증 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("회사 이메일 입력", key="reg_email_in")
            if st.button("인증번호 6자리 발송", key="btn_send_v"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in
                st.session_state.reg_stage = 1
                st.info(f"[{e_in}] 인증번호: {st.session_state.v_code} (테스트용 표시)"); st.rerun()
        elif st.session_state.reg_stage == 1:
            v_in = st.text_input("인증번호 6자리 입력", key="reg_v_in")
            if st.button("인증 확인", key="btn_v_confirm"):
                if v_in == st.session_state.v_code:
                    st.session_state.reg_stage = 2; st.rerun()
                else: st.error("번호가 일치하지 않습니다.")
        elif st.session_state.reg_stage == 2:
            with st.form("reg_form_final"):
                f_name = st.text_input("이름")
                f_comp = st.text_input("회사/부서")
                f_pw = st.text_input("비밀번호 설정", type="password")
                if st.form_submit_button("가입 완료"):
                    new_user = {"Email": st.session_state.temp_email, "Password": f_pw, "Name": f_name, "Company": f_comp, "RegDate": datetime.now().strftime("%Y-%m-%d")}
                    df_u = pd.read_excel(USER_DB)
                    pd.concat([df_u, pd.DataFrame([new_user])]).to_excel(USER_DB, index=False)
                    st.success("가입 완료! 로그인 해주세요."); st.session_state.show_reg = False; st.session_state.reg_stage = 0

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 시뮬레이터 (박스 수납)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    cat_names = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist() if not mat_df.empty else ["PW", "LO"]
    cat_sel = m1.selectbox("Cathode", cat_names, key="cat_sel_box")
    m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"], key="ano_sel_box")
    m3.selectbox("Electrolyte", ["Standard NaPF6"], key="ele_sel_box")
    m4.selectbox("Separator", ["PE 16um"], key="sep_sel_box")
    st.markdown("<br>", unsafe_allow_html=True)

# 소재 데이터 매핑 (KeyError 방지)
if not mat_df.empty:
    cat_row = mat_df[mat_df['Name'] == cat_sel].iloc[0]
    c_cap_base = cat_row.get('Base_Capacity', 162)
    c_volt_base = cat_row.get('Base_Avg_Voltage', 3.05)
    c_dens_base = cat_row.get('Base_True_Density', cat_row.get('Base_True Density', 2.2))
    c_life_base = cat_row.get('Base_Life', 4000)
    st.session_state.loading_val = float(cat_row.get('Rec_Loading', 14.0))

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert_spec = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert_spec")
    s1, s2, s3, s4 = st.columns(4)
    if expert_spec:
        c_cap = s1.slider("Capacity", 100, 220, int(c_cap_base), key="sld_cap_expert")
        c_volt = s2.slider("Voltage", 2.5, 4.5, float(c_volt_base), key="sld_volt_expert")
    else:
        c_cap, c_volt = c_cap_base, c_volt_base
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
    s3.markdown(f'<p class="sub-header-bold">Density</p>{c_dens_base} g/cc', unsafe_allow_html=True)
    s4.markdown(f'<p class="sub-header-bold">Base Life</p>{c_life_base} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (상세 보기 기능)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_show_adv")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        loading = st.slider("Loading", 5.0, 40.0, st.session_state.loading_val, key="sld_load_main")
        if show_adv:
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="sld_cat_dens_adv")
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0, key="sld_cond_adv")
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode Settings</p>', unsafe_allow_html=True)
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np_main")
        if show_adv: st.slider("Anode Press Density", 0.8, 2.0, 1.1, key="sld_ano_dens_adv")
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte Settings</p>', unsafe_allow_html=True)
        active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, 92.0, key="sld_act_main")
        if show_adv: st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="sld_ec_adv")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target & [5] Simulation
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target & 5. Run</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    t_en = t1.slider("Target Energy Density (Wh/kg)", 100, 250, 160, key="sld_target_e")
    t_cr = t2.slider("Target C-rate", 0.1, 20.0, 1.0, key="sld_target_c")
    
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_sim"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (c_cap * (active_ratio/100) * (c_volt - 0.1)) / 2.5
            sim_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.sim_result = {"whkg": res_whkg, "v": c_volt - 0.1, "life": c_life_base, "time": sim_time}
            st.session_state.history.insert(0, f"[{sim_time}] {cat_sel} | {res_whkg:.1f} Wh/kg")
        else: st.error("무료 횟수 초과!")

    # 이력 관리 (최근 순)
    if st.session_state.history:
        st.markdown('<p class="sub-header-bold">과거 시뮬레이션 기록 선택</p>', unsafe_allow_html=True)
        st.selectbox("History", st.session_state.history, label_visibility="collapsed", key="sel_sim_hist")

    # 결과 분석 리포트 (에러 수정)
    if st.session_state.sim_result:
        st.markdown("---")
        st.markdown(f'<p class="main-header">Engineering Analysis Result (Time: {st.session_state.sim_result["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"#### **Energy Density**\n## {st.session_state.sim_result['whkg']:.1f} Wh/kg")
        r2.markdown(f"#### **Cell Voltage**\n## {st.session_state.sim_result['v']:.2f} V")
        r3.markdown(f"#### **Life Expectancy**\n## {st.session_state.sim_result['life']} Cyc")
        
        st.markdown("---")
        g1, g2 = st.columns([3, 7])
        with g1:
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key="plot_res_main") # Duplicate ID 에러 해결 (key 부여)
            with st.expander("🔍 그래프 상세 확대"): st.plotly_chart(fig, use_container_width=True, key="plot_res_exp")
        with g2:
            st.table(pd.DataFrame({"Parameter": ["Loading", "N/P", "C-rate"], "Value": [loading, np_ratio, t_cr]}))
    st.markdown("<br>", unsafe_allow_html=True)