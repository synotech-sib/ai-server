import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import hashlib

# 구글 시트 라이브러리 예외 처리
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    
    /* SynoCore 타이틀 시노텍 로고컬러(#1A729A) 적용 */
    .syno-title { color: #1A729A; font-size: 46px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 14px; }
    
    /* 메트릭(결과값) 카드 및 폰트 사이즈 조정 */
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; }
    
    /* 입력창과 버튼의 높이를 40px로 통일 */
    div[data-testid="stTextInput"] input {
        height: 40px !important;
        font-size: 16px !important;
    }
    div[data-testid="stButton"] > button {
        height: 40px !important; 
        background-color: #1A729A !important; 
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important; margin-top: 0px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 40px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    
    /* 사용자 환영 메시지 텍스트 디자인 */
    .user-greeting {
        color: #1A729A; font-weight: bold; height: 40px; 
        display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px;
    }
    
    /* [요청 반영] 텍스트와 체크박스의 초밀착(한 칸 띄어쓰기)을 위한 CSS 엔진 */
    div[data-testid="column"]:has(.tight-text) {
        width: fit-content !important;
        flex: 0 0 auto !important;
        min-width: auto !important;
        padding-right: 5px !important;
    }
    div[data-testid="column"]:has(.tight-chk) {
        width: fit-content !important;
        flex: 0 0 auto !important;
        min-width: auto !important;
        padding-right: 8px !important;
    }
    div[data-testid="column"]:has(.tight-pro) {
        width: fit-content !important;
        flex: 1 1 auto !important;
        min-width: auto !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [보안] 비밀번호 단방향 암호화
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화
# -----------------------------------------------------------------------------
default_session_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0,
    'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
    'trigger_login': False, 'user_name': "", 'user_email': "", 'show_profile': False
}

for key, value in default_session_vars.items():
    if key not in st.session_state:
        st.session_state[key] = value

def process_login():
    st.session_state.trigger_login = True

# -----------------------------------------------------------------------------
# 3. 데이터 로드
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
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
        return df.astype(str)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인/마이페이지 모듈
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        r1_c1, r1_c2 = st.columns(2)
        u_id = r1_c1.text_input("ID", placeholder="company email", key="id_login_m", label_visibility="collapsed")
        u_pw = r1_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed", on_change=process_login)
        
        r2_c1, r2_c2 = st.columns(2)
        login_btn = r2_c1.button("Login", key="btn_login_m", use_container_width=True)
        reg_btn = r2_c2.button("계정생성 ㅣ Pro 회원가입", key="btn_go_reg_m", use_container_width=True)
        
        if login_btn or st.session_state.pop('trigger_login', False):
            df_u = get_user_db()
            u_id_clean = u_id.strip().lower()
            hashed_pw = hash_password(u_pw) if u_pw else ""
            valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
            
            if u_id_clean == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True
                st.session_state.user_name = "최우석 대표"
                st.session_state.user_email = u_id_clean
                st.rerun()
            elif not valid.empty:
                st.session_state.logged_in = True
                if 'Name' in valid.columns and str(valid['Name'].values[0]).strip() != "":
                    st.session_state.user_name = str(valid['Name'].values[0])
                else:
                    st.session_state.user_name = "회원"
                if 'Email' in valid.columns:
                    st.session_state.user_email = str(valid['Email'].values[0])
                else:
                    st.session_state.user_email = u_id_clean
                st.rerun()
            else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        
        if reg_btn:
            st.session_state.show_reg = not st.session_state.show_reg
            st.session_state.show_profile = False
            st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1])
        r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        
        if r_my.button("My 계정", key="btn_profile_m", use_container_width=True):
            st.session_state.show_profile = not st.session_state.show_profile
            st.rerun()
            
        if r_out.button("Logout", key="btn_logout_m", use_container_width=True): 
            st.session_state.logged_in = False
            st.session_state.user_name = ""
            st.session_state.user_email = ""
            st.session_state.show_profile = False
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [계정 관리] 가입신청 & My 계정 수정 섹션
# -----------------------------------------------------------------------------
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
            if st.button("가입신청", disabled=not (pw1==pw2 and n_name), key="r_fin_m"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df_u = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
                    hashed_pw_register = hash_password(pw1)
                    new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hashed_pw_register, "Name": n_name, "Company": n_comp, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                    updated = pd.concat([df_u, new_user], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated)
                    st.success("가입신청이 완료되었습니다."); st.session_state.show_reg = False; st.session_state.reg_stage = 0
                except:
                    st.error("가입 처리 중 오류가 발생했습니다.")

# My 계정 수정 폼
if st.session_state.get('show_profile') and st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
        if st.session_state.user_email == "wschoi@synotech.co.kr":
            st.info("관리자(Admin) 마스터 계정은 시트 수정 대상이 아닙니다.")
        else:
            df_u = get_user_db()
            user_data = df_u[df_u['Email'] == st.session_state.user_email]
            
            if not user_data.empty:
                u_row = user_data.iloc[0]
                st.markdown(f"**이메일(ID):** {st.session_state.user_email} (변경 불가)")
                
                p1, p2 = st.columns(2)
                m_pw = p1.text_input("새 Password (변경 시에만 입력)", type="password", key="m_pw")
                m_name = p2.text_input("이름", value=u_row.get('Name', ''), key="m_name")
                m_comp = p1.text_input("Company", value=u_row.get('Company', ''), key="m_comp")
                m_dept = p2.text_input("부서", value=u_row.get('Dept', ''), key="m_dept")
                m_job = p1.text_input("담당업무", value=u_row.get('Job', ''), key="m_job")
                m_phone = p2.text_input("연락처", value=u_row.get('Phone', ''), key="m_phone")
                
                if st.button("개인정보 수정 완료", key="m_save"):
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        df_update = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=5)
                        idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                        
                        if m_pw:  
                            df_update.at[idx, 'Password'] = hash_password(m_pw)
                        
                        df_update.at[idx, 'Name'] = m_name
                        df_update.at[idx, 'Company'] = m_comp
                        df_update.at[idx, 'Dept'] = m_dept
                        df_update.at[idx, 'Job'] = m_job
                        df_update.at[idx, 'Phone'] = m_phone
                        
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=df_update)
                        st.session_state.user_name = m_name  
                        st.session_state.show_profile = False
                        st.success("개인정보가 성공적으로 수정되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"정보 수정 중 오류가 발생했습니다: {e}")

# 권한 체크
is_pro = st.session_state.logged_in

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
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = float(row.get('Capacity', 160)), float(row.get('Voltage', 3.05)), float(row.get('Density', 2.2)), int(row.get('Life', 4000)), float(row.get('Rec_Loading', 14.0))
        
        ano_sel = m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"], key="sel_ano_m")
        m3.selectbox("Electrolyte", ["Standard NaPF6", "High-Stability"], key="sel_ele_m")
        m4.selectbox("Separator", ["PE 16um", "Ceramic Coated"], key="sel_sep_m")
    else:
        st.warning("material_list.xlsx 없음 (기본값 작동)")
        c_cap_i, c_volt_i, c_dens_i, c_life_i, c_load_i = 160.0, 3.05, 2.2, 4000, 14.0
        cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
    st.markdown("<br>", unsafe_allow_html=True)

# [2] Material Specs (체크박스 초밀착 레이아웃)
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    
    c2_1, c2_2, c2_3 = st.columns([3.2, 0.5, 6.3]) # 폴백 비율
    with c2_1:
        st.markdown('<div class="tight-text" style="margin-top: 6px; font-size: 16px; font-weight: bold; color: #333;">🔓 밀도 및 수명 등 세부 물성 수정 활성화</div>', unsafe_allow_html=True)
    with c2_2:
        st.markdown('<div class="tight-chk"></div>', unsafe_allow_html=True)
        # 체크박스 자체의 라벨을 감추어 간격을 최소화합니다
        expert = st.checkbox("expert_m", key="chk_exp_m", disabled=not is_pro, label_visibility="collapsed")
    with c2_3:
        if not is_pro:
            st.markdown('<div class="tight-pro" style="margin-top: 6px; font-size: 16px; font-weight: bold; color: #ff4b4b;">(Pro Mode 전용)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="tight-pro"></div>', unsafe_allow_html=True)
    
    s1, s2, s3, s4 = st.columns(4)
    v_cap_in = s1.slider("Capacity (mAh/g)", 100.0, 220.0, float(c_cap_i), key=f"cap_{cat_sel}")
    v_volt_in = s2.slider("Voltage (V)", 2.5, 4.5, float(c_volt_i), key=f"volt_{cat_sel}")
    
    v_dens_in = s3.slider("Density (g/cc)", 1.5, 4.0, float(c_dens_i), key=f"dens_{cat_sel}", disabled=not expert)
    v_life_in = s4.slider("Base Life (Cycles)", 500, 10000, int(c_life_i), key=f"life_{cat_sel}", disabled=not expert)
    
    v_cap = v_cap_in 
    v_volt = v_volt_in 
    v_dens = v_dens_in if expert else c_dens_i
    v_life = v_life_in if expert else c_life_i
    st.markdown("<br>", unsafe_allow_html=True)

# [3] Process Parameters (체크박스 초밀착 레이아웃 및 돋보기 -> 자물통 변경)
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    c3_1, c3_2, c3_3 = st.columns([2.5, 0.5, 7.0]) # 폴백 비율
    with c3_1:
        # [요청 반영] 돋보기 대신 자물통 이모티콘(🔓) 적용
        st.markdown('<div class="tight-text" style="margin-top: 6px; font-size: 16px; font-weight: bold; color: #333;">🔓 세부 파라미터 수정 활성화</div>', unsafe_allow_html=True)
    with c3_2:
        st.markdown('<div class="tight-chk"></div>', unsafe_allow_html=True)
        show_adv = st.checkbox("adv_m", key="chk_adv_m", disabled=not is_pro, label_visibility="collapsed")
    with c3_3:
        if not is_pro:
            st.markdown('<div class="tight-pro" style="margin-top: 6px; font-size: 16px; font-weight: bold; color: #ff4b4b;">(Pro Mode 전용)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="tight-pro"></div>', unsafe_allow_html=True)
    
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
        v_load_in = st.slider("Loading (mg/cm2)", 5.0, 45.0, float(c_load_i), key=f"load_{cat_sel}")
        st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="ad_c_den_m", disabled=not show_adv)
        st.slider("Conductive Agent %", 0.5, 5.0, 2.0, key="ad_c_con_m", disabled=not show_adv)
        st.slider("Binder %", 0.5, 5.0, 3.0, key="ad_c_bin_m", disabled=not show_adv)
        v_load = v_load_in

    with p2:
        st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
        v_np_in = st.slider("N/P Ratio", 1.0, 1.5, 1.15, key="sl_np_m")
        st.slider("Anode Press Density", 0.8, 2.0, 1.1, key="ad_a_den_m", disabled=not show_adv)
        st.slider("Anode Active %", 90.0, 98.0, 95.0, key="ad_a_act_m", disabled=not show_adv)
        v_np = v_np_in

    with p3:
        st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
        v_act_in = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sl_act_m")
        st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5, key="ad_ec_m", disabled=not show_adv)
        st.slider("Separator Thick (μm)", 12, 30, 16, key="ad_sep_m", disabled=not show_adv)
        v_act = v_act_in

    st.markdown("<br>", unsafe_allow_html=True)

# [4] Target Settings
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    
    t1, t2 = st.columns(2)
    with t1:
        st.markdown('<p class="sub-header-bold">Energy Density Goal (Wh/kg)</p>', unsafe_allow_html=True)
        v_te = st.slider("Energy Goal", 100, 250, 160, key="sl_te_m", label_visibility="collapsed")
    with t2:
        st.markdown('<p class="sub-header-bold">Simulation C-rate</p>', unsafe_allow_html=True)
        v_tc = st.slider("C-rate", 0.1, 10.0, 1.0, step=0.1, key="sl_tc_m", label_visibility="collapsed")

# [5] Simulation Control & Analysis
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    
    col_btn, col_msg = st.columns([1, 3])
    with col_btn:
        run_clicked = st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_m", use_container_width=True)
    with col_msg:
        if not st.session_state.history:
            st.markdown('<div style="padding-top: 12px; color: #666; font-weight: bold;">아직 시뮬레이션 이력이 없습니다. 좌측 실행 버튼을 눌러주세요.</div>', unsafe_allow_html=True)
            
    if run_clicked:
        ir_drop = 0.1 + (v_tc * 0.02)
        cell_v = max(0.1, v_volt - ir_drop)
        efficiency = max(0.5, 1.0 - (v_tc * 0.015))
        res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
        life_cyc = int(v_life * (0.95 ** v_tc))
        
        kst_time = datetime.utcnow() + timedelta(hours=9)
        cur_time = kst_time.strftime("%H:%M:%S")
        
        v_axis = np.linspace(2.0, 4.2, 150)
        dqdv = np.zeros_like(v_axis)
        peaks = [3.05, 3.45] if "Prussian" in cat_sel or "Altris" in cat_sel else ([3.75] if "Polyanion" in cat_sel or "NVPF" in cat_sel else [3.15])
        for p in peaks:
            shifted_p = p - (v_tc * 0.015) 
            dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
        
        log_data = {
            "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
            "Cap(mAh/g)": v_cap, "Volt(V)": v_volt, "Load(mg)": v_load,
            "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
            "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc,
            "dq_x": v_axis, "dq_y": dqdv
        }
        st.session_state.history.insert(0, log_data)
        st.session_state.sim_result = log_data
        st.rerun()

    # 과거 기록 복원
    if st.session_state.history:
        st.markdown("---")
        st.markdown('<p class="sub-header-bold">🔍 과거 기록 불러오기 (선택 시 아래 결과가 즉시 변경됩니다)</p>', unsafe_allow_html=True)
        
        log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Cell_V']} V | {h['Life(Cyc)']} Cyc" for h in st.session_state.history]
        
        sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], key="sel_hist_m", label_visibility="collapsed")
        res = st.session_state.history[sel_idx]
        
        st.markdown("---")
        r1, r2, r3 = st.columns(3)
        r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=round(res['Wh/kg'] - v_te, 1))
        r2.metric("Cell Voltage", f"{res['Cell_V']} V")
        r3.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc")
        
        g1, g2 = st.columns([1, 1])
        with g1:
            st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
            fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
            fig1.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
            st.plotly_chart(fig1, use_container_width=True, key=f"plot_v_{res['Time']}")
        with g2:
            st.markdown('<p class="sub-header-bold">dQ/dV Profile (Fingerprint)</p>', unsafe_allow_html=True)
            fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
            fig2.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
            st.plotly_chart(fig2, use_container_width=True, key=f"plot_dq_{res['Time']}")

        st.markdown("---")
        st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs (전체 이력)</p>', unsafe_allow_html=True)
        df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
        st.dataframe(df_history, use_container_width=True)

# 6. 푸터 (저작권 표시)
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)