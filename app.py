import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import random
import os

# 1. 페이지 설정
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

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
# 2. [에러 해결] 세션 상태 초기화 (AttributeError 방지)
# -----------------------------------------------------------------------------
if 'init_v6' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.trial_count = 0
    st.session_state.show_reg = False
    st.session_state.reg_stage = 0
    st.session_state.v_code = ""
    st.session_state.temp_email = ""
    st.session_state.history = [] # 시뮬레이션 로그 저장
    st.session_state.sim_result = None # 현재 보여줄 결과
    st.session_state.init_v6 = True

# -----------------------------------------------------------------------------
# 3. [데이터 로드] 구글 시트 및 엑셀 (ValueError 방지)
# -----------------------------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

@st.cache_data
def load_mat_db():
    if not os.path.exists("material_list.xlsx"): return pd.DataFrame()
    df = pd.read_excel("material_list.xlsx")
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_mat_db()

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

def get_users():
    try:
        return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
    except:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (50:50)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="l_id_v6", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="l_pw_v6", label_visibility="collapsed")
        if l_c3.button("Login", key="btn_l_v6"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            else:
                df_u = get_users()
                valid = df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == u_pw)]
                if not valid.empty: st.session_state.logged_in = True; st.rerun()
                else: st.error("정보 확인 필요")
        
        reg_c1, reg_c2 = st.columns([1, 1])
        with reg_c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_reg_v6"):
                st.session_state.show_reg = not st.session_state.show_reg
        with reg_c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ 접속 중: Admin")
        if st.button("Logout", key="btn_logout_v6"): st.session_state.logged_in = False; st.rerun()

# 가입신청 섹션
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소 입력", key="r_e_v6")
            if st.button("인증번호 발송", key="btn_v_v6"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in
                st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력", key="r_v_v6")
            if st.button("인증 확인", key="btn_v_chk_v6"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2)
            pw1 = p1.text_input("2. Password 설정", type="password", key="r_p1_v6")
            pw2 = p2.text_input("2-1. Password 확인", type="password", key="r_p2_v6")
            n_name = st.text_input("3. 이름", key="r_n_v6")
            n_comp = st.text_input("4. Company", key="r_c_v6")
            n_dept = st.text_input("5. 부서", key="r_d_v6")
            n_job = st.text_input("6. 담당업무", key="r_j_v6")
            n_phone = st.text_input("7. 연락처", key="r_ph_v6")
            agree = st.checkbox("참조용 자료이며 결과에 책임지지 않음에 동의", key="r_a_v6")
            if st.button("가입신청", disabled=not (agree and pw1==pw2 and n_name), key="btn_fin_v6"):
                try:
                    df_u = get_users()
                    new_user = pd.DataFrame([{"Email":st.session_state.temp_email,"Password":pw1,"Name":n_name,"Company":n_comp,"Dept":n_dept,"Job":n_job,"Phone":n_phone,"RegDate":datetime.now().strftime("%Y-%m-%d")}])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    st.success("신청 완료!"); st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except: st.error("⚠️ 구글 시트 저장 실패: 서비스 계정 인증이 필요합니다.")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 본문 시뮬레이터 (슬라이더 및 로그 가시성 완전 복구)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        cat_sel = m1.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist(), key="s_cat_v6")
        row = mat_df[mat_df['Name']==cat_sel].iloc[0]
        # 소재 데이터 자동 연동
        c_cap_i = float(row.get('Capacity', 160))
        c_volt_i = float(row.get('Voltage', 3.05))
        c_dens_i = float(row.get('Density', 2.2))
        c_life_i = int(row.get('Life', 4000))
        c_load_i = float(row.get('Rec_Loading', 14.0))
        m2.selectbox("Anode", ["Hard Carbon (Standard)", "Hard Carbon (High-Cap)"], key="s_ano_v6")
        m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"], key="s_ele_v6")
        m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"], key="s_sep_v6")
    else: st.warning("material_list.xlsx 파일을 찾을 수 없습니다.")
    st.markdown("<br>", unsafe_allow_html=True)

# [2] Material Specs (4개 슬라이더 완전 가동)
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_exp_v6")
    s1, s2, s3, s4 = st.columns(4)
    if expert:
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i, key="sld_cap_v6")
        v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i, key="sld_volt_v6")
        v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i, key="sld_dens_v6")
        v_life = s4.slider("Base Life (Cycles)", 500, 10000, c_life_i, key="sld_life_v6")
    else:
        v_cap, v_volt, v_dens, v_life = c_cap_i, c_volt_i, c_dens_i, c_life_i
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{v_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{v_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{v_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{v_life:,} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (상세 파라미터 완전 복구)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv_v6")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, c_load_i, key="sld_load_v6")
        if show_adv:
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="adv_c_dens_v6")
            st.slider("Conductive Agent %", 0.5, 5.0, 2.0, key="adv_c_cond_v6")
            st.slider("Binder %", 0.5, 5.0, 3.0, key="adv_c_bind_v6")
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np_v6")
        if show_adv:
            st.slider("Anode Press Density", 0.8, 2.0, 1.1, key="adv_a_dens_v6")
            st.slider("Anode Active %", 90.0, 98.0, 95.0, key="adv_a_act_v6")
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Electrolyte & Cell</p>', unsafe_allow_html=True)
        v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sld_act_v6")
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="adv_ec_v6")
            st.slider("Separator Thick (μm)", 12, 30, 16, key="adv_sep_v6")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] & [5] 통합 박스 (로그 시스템 포함)
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target & 5. Run History</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160, key="sld_te_v6")
    v_tc = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0, key="sld_tc_v6")
    
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_v6"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
            cur_time = datetime.now().strftime("%H:%M:%S")
            # 로그 데이터 생성
            new_log = {"time": cur_time, "whkg": res_whkg, "v": v_volt-0.1, "life": v_life, "cat": cat_sel, "load": v_load, "np": v_np}
            st.session_state.history.insert(0, new_log)
            st.session_state.sim_result = new_log
        else: st.error("무료 횟수 초과!")

    # 로그 선택 및 데이터 복원 기능
    if st.session_state.history:
        st.markdown("---")
        st.markdown('<p class="sub-header-bold">📋 Simulation Logs (과거 기록 선택 시 데이터 복원)</p>', unsafe_allow_html=True)
        log_options = [f"[{h['time']}] {h['cat']} | {h['whkg']:.1f} Wh/kg" for h in st.session_state.history]
        selected_log_str = st.selectbox("불러올 기록 선택", log_options, key="log_sel_v6")
        
        # 선택된 로그 찾기
        idx = log_options.index(selected_log_str)
        st.session_state.sim_result = st.session_state.history[idx]

    # 결과 분석 리포트 (박스 5번 내부)
    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Analysis Result ({res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{res['v']:.2f} V")
        r3.metric("Expected Life", f"{res['life']:,} Cyc")
        
        g1, g2 = st.columns([4, 6])
        with g1:
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['v']-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key=f"fig_{res['time']}") # 시간 기반 고유 키로 ID 충돌 방지
        with g2:
            st.table(pd.DataFrame({"Parameter":["Cathode","Loading","N/P"],"Value":[res['cat'], f"{res['load']} mg", res['np']]}))
    st.markdown("<br>", unsafe_allow_html=True)