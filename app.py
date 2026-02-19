import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import random
import os

# 1. 페이지 설정 및 디자인
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
# 2. [에러 해결] 세션 상태 초기화 (AttributeError & NameError 방지)
# -----------------------------------------------------------------------------
# image_1fe9e4, image_2acab1 등 변수 미선언 에러 해결
if 'init_done' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.trial_count = 0
    st.session_state.show_reg = False
    st.session_state.reg_stage = 0
    st.session_state.v_code = ""
    st.session_state.temp_email = ""
    st.session_state.history = []
    st.session_state.sim_result = None
    st.session_state.c_cap = 160.0
    st.session_state.c_volt = 3.05
    st.session_state.loading_val = 14.0
    st.session_state.init_done = True

# -----------------------------------------------------------------------------
# 3. [에러 해결] 구글 시트 연결 (ValueError 방지)
# -----------------------------------------------------------------------------
# image_2acf68 에러 해결: 시트 주소를 명시적으로 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_db():
    return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)

# -----------------------------------------------------------------------------
# 4. [에러 해결] 엑셀 데이터 로드 (Hardcoding 제거)
# -----------------------------------------------------------------------------
@st.cache_data
def load_materials():
    file = "material_list.xlsx"
    if not os.path.exists(file): return pd.DataFrame()
    df = pd.read_excel(file)
    # image_1f62bf 에러 방지: 컬럼명 전처리
    df.columns = [c.split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_materials()

# -----------------------------------------------------------------------------
# 5. 상단 헤더 (50:50)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.4 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="top_id", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="top_pw", label_visibility="collapsed")
        if l_c3.button("Login", key="top_login"):
            df_u = get_db()
            valid = df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == u_pw)]
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            elif not valid.empty:
                st.session_state.logged_in = True; st.rerun()
            else: st.error("계정 정보를 확인하세요.")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_reg"):
                st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info(f"✅ 접속 중: Admin")
        if st.button("Logout", key="btn_logout"): st.session_state.logged_in = False; st.rerun()

# [기능 해결] 인증번호 보임 및 가입 신청 7개 항목
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 및 보안 인증 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소 입력", key="reg_email")
            if st.button("인증번호 6자리 발송", key="btn_v_send"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in
                st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            # 인증번호 노출 문제 해결
            st.info(f"[{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력", key="reg_v_in")
            if st.button("인증 확인", key="btn_v_chk"):
                if v_in == st.session_state.v_code:
                    st.session_state.reg_stage = 2; st.rerun()
                else: st.error("번호 불일치")
        elif st.session_state.reg_stage == 2:
            st.write(f"이메일: **{st.session_state.temp_email}**")
            p1, p2 = st.columns(2)
            new_pw = p1.text_input("2. Password 설정", type="password", key="reg_pw1")
            conf_pw = p2.text_input("2-1. Password 확인", type="password", key="reg_pw2")
            if new_pw and conf_pw and new_pw != conf_pw: st.error("비밀번호 불일치")
            
            n_name = st.text_input("3. 이름", key="reg_name")
            n_comp = st.text_input("4. Company", key="reg_comp")
            n_dept = st.text_input("5. 부서", key="reg_dept")
            n_job = st.text_input("6. 담당업무", key="reg_job")
            n_phone = st.text_input("7. 연락처", key="reg_phone")
            
            with st.expander("(동의) 내용보기"):
                st.markdown("참조용 자료이며 실제 결과에 대해 시노코어는 책임을 지지 않는다.")
            agree = st.checkbox("약관에 동의합니다.", key="reg_agree")
            
            can_sub = agree and (new_pw == conf_pw) and n_name and n_comp
            if st.button("가입신청", disabled=not can_sub, key="btn_reg_final"):
                df_u = get_db()
                new_user = pd.DataFrame([{
                    "Email": st.session_state.temp_email, "Password": new_pw, "Name": n_name,
                    "Company": n_comp, "Dept": n_dept, "Job": n_job, "Phone": n_phone,
                    "RegDate": datetime.now().strftime("%Y-%m-%d")
                }])
                updated = pd.concat([df_u, new_user], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
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
        cat_sel = m1.selectbox("Cathode", cat_list, key="sel_cat")
        
        # 2번 슬라이더 연동 로직
        sel_row = mat_df[mat_df['Name'] == cat_sel].iloc[0]
        st.session_state.c_cap = float(sel_row.get('Capacity', 160))
        st.session_state.c_volt = float(sel_row.get('Voltage', 3.05))
        st.session_state.loading_val = float(sel_row.get('Rec_Loading', 14.0))

        m2.selectbox("Anode", ["Aekyung Chemical", "Kuraray HC"], key="sel_ano")
        m3.selectbox("Electrolyte", ["Standard NaPF6"], key="sel_ele")
        m4.selectbox("Separator", ["PE 16um"], key="sel_sep")
    else: st.error("material_list.xlsx 없음")
    st.markdown("<br>", unsafe_allow_html=True)

# [2] Material Specs (슬라이더 작동 해결)
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_expert")
    s1, s2, s3, s4 = st.columns(4)
    if expert:
        c_cap = s1.slider("Capacity", 100.0, 220.0, st.session_state.c_cap, key="sld_cap")
        c_volt = s2.slider("Voltage", 2.5, 4.5, st.session_state.c_volt, key="sld_volt")
    else:
        c_cap, c_volt = st.session_state.c_cap, st.session_state.c_volt
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{c_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{c_volt} V', unsafe_allow_html=True)
    s3.markdown('<p class="sub-header-bold">Density</p>2.2 g/cc', unsafe_allow_html=True)
    s4.markdown('<p class="sub-header-bold">Base Life</p>4,000 Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (자세히 보기 해결)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv")
    p1, p2, p3 = st.columns(3)
    with p1:
        load = st.slider("Loading", 5.0, 45.0, st.session_state.loading_val, key="sld_load")
        if show_adv: 
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="sld_cat_dens")
            st.slider("Conductive Agent %", 0.5, 5.0, 2.0, key="sld_cond")
            st.slider("Binder %", 0.5, 5.0, 3.0, key="sld_bind")
    with p2:
        np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sld_np")
        if show_adv: st.slider("Anode Press Density", 0.8, 2.0, 1.1, key="sld_ano_dens")
    with p3:
        act_ratio = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sld_act")
        if show_adv: st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="sld_ec")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] & [5] 분리 및 Run
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Configuration</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    t_en = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160, key="sld_target_e")
    t_cr = t2.slider("Target C-rate", 0.1, 20.0, 1.0, key="sld_target_c")
    st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation History & Run</p>', unsafe_allow_html=True)
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (c_cap * (act_ratio/100) * (c_volt - 0.1)) / 2.5
            st.session_state.sim_result = {"whkg": res_whkg, "v": c_volt - 0.1, "time": datetime.now().strftime("%H:%M:%S")}
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
            # image_1f7163 에러 해결: 고유 key 부여
            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=c_volt-0.1-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key="plot_res_main")
        with g2:
            st.table(pd.DataFrame({"Param": ["Loading", "N/P", "C-rate"], "Value": [load, np_ratio, t_cr]}))
    st.markdown("<br>", unsafe_allow_html=True)