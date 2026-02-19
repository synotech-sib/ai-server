import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection # requirements.txt에 st-gsheets-connection 필수
from datetime import datetime
import random
import os

# 1. 페이지 설정 및 디자인 (기본 틀 유지)
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
# image_1f5f1e, image_1fe9e4, image_2acab1 에러 해결을 위해 초기값 일괄 선언
if 'init' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.trial_count = 0
    st.session_state.show_reg = False
    st.session_state.reg_stage = 0
    st.session_state.v_code = ""
    st.session_state.temp_email = ""
    st.session_state.history = []
    st.session_state.sim_result = None
    st.session_state.loading_val = 14.0
    st.session_state.c_cap = 162.0
    st.session_state.c_volt = 3.05
    st.session_state.init = True

# -----------------------------------------------------------------------------
# 3. [에러 해결] 엑셀 데이터 로드 및 컬럼 표준화 (KeyError 방지)
# -----------------------------------------------------------------------------
@st.cache_data
def load_materials():
    file_path = "material_list.xlsx"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    df = pd.read_excel(file_path)
    # image_1f62bf 에러 해결을 위해 컬럼명 전처리 (공백 및 단위 제거)
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_materials()

# 구글 시트 연결 (가입자 DB용)
# image_2a5aac 에러 해결: requirements.txt의 라이브러리와 코드 싱크
conn = st.connection("gsheets", type=GSheetsConnection)

# -----------------------------------------------------------------------------
# 4. 상단 헤더 (50:50)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="top_login_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="top_login_pw", label_visibility="collapsed")
        if l_c3.button("Login", key="top_login_btn"):
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            else:
                try:
                    df_u = conn.read(worksheet="Sheet1")
                    if not df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == u_pw)].empty:
                        st.session_state.logged_in = True; st.rerun()
                    else: st.error("정보 확인 필요")
                except: st.error("DB 접근 오류")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="top_reg_btn"):
                st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ 접속 중: Admin")
        if st.button("Logout", key="top_logout_btn"): st.session_state.logged_in = False; st.rerun()

# -----------------------------------------------------------------------------
# 5. [기능 수정] 계정 신청 (번호 보임 문제 해결)
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 및 상세 정보 입력 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소 입력", key="reg_email_in")
            if st.button("인증번호 6자리 발송", key="btn_send_v"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in
                st.session_state.reg_stage = 1; st.rerun()
        
        elif st.session_state.reg_stage == 1:
            # 인증번호가 보이지 않던 문제 해결: 명시적 info 노출
            st.info(f"[{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력", key="reg_v_in")
            if st.button("인증 확인", key="btn_v_confirm"):
                if v_in == st.session_state.v_code:
                    st.session_state.reg_stage = 2; st.rerun()
                else: st.error("번호 불일치")
        
        elif st.session_state.reg_stage == 2:
            st.write(f"가입 이메일: **{st.session_state.temp_email}**")
            p_c1, p_c2 = st.columns(2)
            new_pw = p_c1.text_input("2. Password 설정", type="password", key="reg_pw_in")
            confirm_pw = p_c2.text_input("2-1. Password 확인", type="password", key="reg_pw_conf")
            
            if new_pw and confirm_pw and new_pw != confirm_pw:
                st.error("비밀번호가 일치하지 않습니다.")
            
            new_name = st.text_input("3. 이름", key="reg_name_in")
            new_comp = st.text_input("4. Company (회사명)", key="reg_comp_in")
            new_dept = st.text_input("5. 부서", key="reg_dept_in")
            new_job = st.text_input("6. 담당업무", key="reg_job_in")
            new_phone = st.text_input("7. 연락처 (전화번호)", key="reg_phone_in")
            
            with st.expander("(동의) 내용보기"):
                st.markdown("이 시뮬레이션 자료는 참조용이며 실제 결과에 대해 **시노코어는 책임을 지지 않는다.**")
            agree = st.checkbox("약관에 동의합니다.", key="reg_agree_chk")
            
            can_submit = agree and (new_pw == confirm_pw) and new_name and new_comp
            if st.button("가입신청", disabled=not can_submit, key="btn_reg_final"):
                df_u = conn.read(worksheet="Sheet1")
                new_user = pd.DataFrame([{
                    "Email": st.session_state.temp_email, "Password": new_pw, "Name": new_name,
                    "Company": new_comp, "Dept": new_dept, "Job": new_job, "Phone": new_phone,
                    "RegDate": datetime.now().strftime("%Y-%m-%d")
                }])
                updated_df = pd.concat([df_u, new_user], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("신청 완료!"); st.session_state.show_reg = False; st.session_state.reg_stage = 0

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 본문 시뮬레이터 (엑셀 연동 및 슬라이더 해결)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        cat_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
        cat_sel = m1.selectbox("Cathode", cat_list, key="sel_cat_box")
        
        # 2번 슬라이더 연동 오류 해결: 소재 변경 시 세션 강제 갱신
        sel_row = mat_df[mat_df['Name'] == cat_sel].iloc[0]
        st.session_state.c_cap = float(sel_row.get('Capacity', 160))
        st.session_state.c_volt = float(sel_row.get('Voltage', 3.05))
        st.session_state.loading_val = float(sel_row.get('Rec_Loading', 14.0))

        m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"], key="sel_ano_box")
        m3.selectbox("Electrolyte", ["Standard NaPF6"], key="sel_ele_box")
        m4.selectbox("Separator", ["PE 16um"], key="sel_sep_box")
    else: st.error("material_list.xlsx 없음")
    st.markdown("<br>", unsafe_allow_html=True)

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert_mode")
    s1, s2, s3, s4 = st.columns(4)
    # 슬라이더가 일부만 작동하던 문제 해결: key와 value 싱크 최적화
    if expert:
        c_cap_val = s1.slider("Capacity", 100.0, 220.0, st.session_state.c_cap, key="sld_cap_dyn")
        c_volt_val = s2.slider("Voltage", 2.5, 4.5, st.session_state.c_volt, key="sld_volt_dyn")
    else:
        c_cap_val, c_volt_val = st.session_state.c_cap, st.session_state.c_volt
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap_val} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt_val} V', unsafe_allow_html=True)
    s3.markdown('<p class="sub-header-bold">Density</p>2.2 g/cc', unsafe_allow_html=True)
    s4.markdown('<p class="sub-header-bold">Base Life</p>4000 Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv_show")
    p1, p2, p3 = st.columns(3)
    with p1:
        load = st.slider("Loading", 5.0, 45.0, st.session_state.loading_val, key="sld_load_dyn")
        if show_adv: 
            st.slider("Cathode Density", 1.5, 3.5, 2.5, key="sld_cat_dens_adv")
            st.slider("Conductive Agent %", 1.0, 5.0, 2.0, key="sld_cond_adv")
    with p2:
        np_r = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np_dyn")
    with p3:
        act_r = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sld_act_dyn")
        if show_adv: st.slider("E/C Ratio", 1.0, 8.0, 3.5, key="sld_ec_adv")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Configuration (박스 분리)
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    t_en = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160, key="sld_target_e")
    t_cr = t2.slider("Target C-rate", 0.1, 20.0, 1.0, key="sld_target_c")
    st.markdown("<br>", unsafe_allow_html=True)

# [5] Simulation History & Run (박스 분리)
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_main"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (c_cap_val * (act_r/100) * (c_volt_val - 0.1)) / 2.5
            st.session_state.sim_result = {"whkg": res_whkg, "v": c_volt_val - 0.1, "time": datetime.now().strftime("%H:%M:%S")}
        else: st.error("횟수 초과!")

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Analysis Result ({res["time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['whkg']:.1f} Wh/kg")
        r2.metric("Cell Voltage", f"{res['v']:.2f} V")
        r3.metric("Expected Life", "4,000 Cyc")
        
        g1, g2 = st.columns([3, 7])
        with g1:
            # image_1f7163, image_1f7d7d 에러 해결: 고유 key 부여
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt_val-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key="plot_res_final")
        with g2:
            st.table(pd.DataFrame({"Param": ["Loading", "N/P", "C-rate"], "Value": [load, np_r, t_cr]}))
    st.markdown("<br>", unsafe_allow_html=True)