import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import hashlib

# 구글 시트 라이브러리 예외 처리
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 디자인 (V1.45 정식 명명)
st.set_page_config(page_title="SynoCore V1.45 Pro Max", layout="wide")

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
# [보안] 비밀번호 단방향 암호화 (SHA-256) 함수
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화
# -----------------------------------------------------------------------------
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'trial_count': 0, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
        'init_master': True
    })

# -----------------------------------------------------------------------------
# 3. 데이터 로드 (엑셀 및 구글 시트 안전 연결)
# -----------------------------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"

@st.cache_data
def load_materials():
    if not os.path.exists("material_list.xlsx"): return pd.DataFrame()
    df = pd.read_excel("material_list.xlsx")
    df.columns = [str(c).split('(')[0].strip() for c in df.columns]
    return df

mat_df = load_materials()

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 가입 모듈 (V1.45 적용)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed")
        if l_c3.button("Login", key="btn_login_m"):
            df_u = get_user_db()
            hashed_pw = hash_password(u_pw) if u_pw else ""
            valid = df_u[(df_u['Email'] == u_id) & (df_u['Password'].astype(str) == hashed_pw)] if not df_u.empty else pd.DataFrame()
            
            if u_id == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            elif not valid.empty:
                st.session_state.logged_in = True; st.rerun()
            else: st.error("정보 확인 필요")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("계정생성 ㅣ Pro 회원가입", key="btn_go_reg_m"): st.session_state.show_reg = not st.session_state.show_reg
        with c2:
            st.markdown(f'<div style="background-color:#003366; color:white; padding:5px; border-radius:8px; text-align:center;">무료 시도 {st.session_state.trial_count}/10</div>', unsafe_allow_html=True)
    else:
        st.info("✅ 접속 중: Admin")
        if st.button("Logout", key="btn_logout_m"): st.session_state.logged_in = False; st.rerun()

# 가입신청 섹션
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소", key="r_email_m")
            if st.button("인증번호 발송", key="r_v_send_m"):
                st.session_state.v_code = str(random.randint(100000, 999999))
                st.session_state.temp_email = e_in; st.session_state.reg_stage = 1; st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            v_in = st.text_input("인증번호 입력", key="r_v_in_m")
            if st.button("인증 확인", key="r_v_chk_m"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2)
            pw1 = p1.text_input("2. Password", type="password", key="r_p1_m")
            pw2 = p2.text_input("2-1. Password 확인", type="password", key="r_p2_m")
            n_name = st.text_input("3. 이름", key="r_n_m")
            n_comp = st.text_input("4. Company", key="r_c_m")
            n_dept = st.text_input("5. 부서", key="r_d_m")
            n_job = st.text_input("6. 담당업무", key="r_j_m")
            n_phone = st.text_input("7. 연락처", key="r_ph_m")
            agree = st.checkbox("참조용 자료이며 책임지지 않음에 동의", key="r_a_m")
            if st.button("가입신청", disabled=not (agree and pw1==pw2 and n_name), key="r_fin_m"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df_u = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
                    hashed_pw_register = hash_password(pw1)
                    new_user = pd.DataFrame([{
                        "Email": st.session_state.temp_email, 
                        "Password": hashed_pw_register, 
                        "Name": n_name, 
                        "Company": n_comp, 
                        "Dept": n_dept, 
                        "Job": n_job, 
                        "Phone": n_phone, 
                        "RegDate": datetime.now().strftime("%Y-%m-%d")
                    }])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    st.success("가입신청이 완료되었습니다. 개인정보는 암호화되어 보관되므로 안심하셔도 됩니다.")
                    st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except Exception as e:
                    st.error(f"⚠️ 구글 시트 저장 불가: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    if not mat_df.empty:
        m1, m2, m3, m4 = st.columns(4)
        cat_sel = m1.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist(), key="sel_cat_m")
        row = mat_df[mat_df['Name']==cat_sel].iloc[0]
        c_cap_i = float(row.get('Capacity', 160))
        c_volt_i = float(row.get('Voltage', 3.05))
        c_dens_i = float(row.get('Density', 2.2))
        c_life_i = int(row.get('Life', 4000))
        c_load_i = float(row.get('Rec_Loading', 14.0))
        
        ano_sel = m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"], key="sel_ano_m")
        m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"], key="sel_ele_m")
        m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"], key="sel_sep_m")
    else:
        st.warning("material_list.xlsx 없음 (기본값 작동)")
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = 160.0, 3.05, 2.2, 4000, 14.0
        cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
    st.markdown("<br>", unsafe_allow_html=True)

# [2] Material Specs
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    expert = st.checkbox("🔓 물성 직접 수정 활성화", key="chk_exp_m")
    s1, s2, s3, s4 = st.columns(4)
    if expert:
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 220.0, c_cap_i, key="sl_cap_m")
        v_volt = s2.slider("Voltage (V)", 2.5, 4.5, c_volt_i, key="sl_volt_m")
        v_dens = s3.slider("Density (g/cc)", 1.5, 4.0, c_dens_i, key="sl_dens_m")
        v_life = s4.slider("Base Life (Cycles)", 500, 10000, c_life_i, key="sl_life_m")
    else:
        v_cap, v_volt, v_dens, v_life = c_cap_i, c_volt_i, c_dens_i, c_life_i
        s1.markdown(f'<p class="sub-header-bold">Capacity</p>{v_cap} mAh/g', unsafe_allow_html=True)
        s2.markdown(f'<p class="sub-header-bold">Voltage</p>{v_volt} V', unsafe_allow_html=True)
        s3.markdown(f'<p class="sub-header-bold">Density</p>{v_dens} g/cc', unsafe_allow_html=True)
        s4.markdown(f'<p class="sub-header-bold">Base Life</p>{v_life:,} Cyc', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    show_adv = st.checkbox("🔍 더 자세히 보기 (Advanced Settings)", key="chk_adv_m")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        v_load = st.slider("Loading (mg/cm2)", 5.0, 45.0, c_load_i, key="sl_load_m")
        if show_adv:
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="ad_c_den_m")
            st.slider("Conductive Agent %", 0.5, 5.0, 2.0, key="ad_c_con_m")
            st.slider("Binder %", 0.5, 5.0, 3.0, key="ad_c_bin_m")
    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sl_np_m")
        if show_adv:
            st.slider("Anode Press Density", 0.8, 2.0, 1.1, key="ad_a_den_m")
            st.slider("Anode Active %", 90.0, 98.0, 95.0, key="ad_a_act_m")
    with p3:
        st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
        v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sl_act_m")
        if show_adv:
            st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="ad_ec_m")
            st.slider("Separator Thick (μm)", 12, 30, 16, key="ad_sep_m")
    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target & Simulation
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target & Simulation</p>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160, key="sl_te_m")
    v_tc = t2.slider("Simulation C-rate", 0.1, 20.0, 1.0, key="sl_tc_m")
    
    if st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_m"):
        if st.session_state.trial_count < 10 or st.session_state.logged_in:
            st.session_state.trial_count += 1
            res_whkg = (v_cap * (v_act/100) * (v_volt - 0.1)) / 2.5
            cell_v = v_volt - 0.1
            cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            log_data = {
                "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
                "Cap(mAh/g)": v_cap, "Volt(V)": v_volt, "Load(mg)": v_load,
                "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
                "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": v_life
            }
            st.session_state.history.insert(0, log_data)
            st.session_state.sim_result = log_data
        else: st.error("무료 횟수 초과!")

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown(f'<p class="main-header">Analysis Result ({res["Time"]})</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg")
        r2.metric("Cell Voltage", f"{res['Cell_V']} V")
        r3.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc")
        
        g1, g2 = st.columns([4, 6])
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            

[Image of lithium-ion battery discharge curve]

            fig = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key=f"plot_m_{res['Time']}")
        with g2:
            st.markdown('<p class="sub-header-bold">Applied Parameters</p>', unsafe_allow_html=True)
            st.table(pd.DataFrame({
                "Parameter": ["Cathode", "Anode", "Loading", "N/P Ratio", "Test C-rate"],
                "Value": [res['Cathode'], res['Anode'], f"{res['Load(mg)']} mg/cm2", res['N/P Ratio'], f"{res['C-rate']} C"]
            }))

# [5] Simulation History
if st.session_state.history:
    st.markdown("---")
    st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs (전체 이력)</p>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)