import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import hashlib
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [PDF 라이브러리 예외 처리]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# [구글 시트 라이브러리 예외 처리]
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="SynoCore V1.45 Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    /* 가로폭 컴팩트 제어 */
    .main .block-container {
        max-width: 1150px; 
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: auto; 
    }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    .syno-title { color: #1A729A; font-size: 46px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 14px; }
    
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    div[data-testid="stMetricDelta"] { font-size: 14px !important; }
    
    div[data-testid="stTextInput"] input { height: 40px !important; font-size: 16px !important; }
    
    div[data-testid="stButton"] > button {
        height: 40px !important; background-color: #1A729A !important; 
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important; margin-top: 0px !important;
    }
    
    /* PDF 및 다운로드 오렌지 색상 */
    div[data-testid="stDownloadButton"] > button {
        height: 40px !important; background-color: #FFCA28 !important; 
        color: #222 !important; 
        font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: 1px solid #E4B526 !important; margin-top: 0px !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #FFB300 !important;
        border: 1px solid #DDA010 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 40px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=60)
def load_cloud_data(url):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url)
        df.columns = [str(c).split('(')[0].strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

mat_df = load_cloud_data(URL_MATS)
param_df = load_cloud_data(URL_PARAM)

sys_params = {}
if not param_df.empty and 'Parameter_ID' in param_df.columns:
    sys_params = param_df.set_index('Parameter_ID').to_dict('index')

def get_p(pid, prop, fallback):
    try: return float(sys_params[pid][prop])
    except: return fallback

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5).astype(str)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# ✉️ [이메일 발송 시스템] 
# -----------------------------------------------------------------------------
def send_verification_email(to_email, code):
    # ⚠️ 보안 적용: Secrets에서 비밀번호를 불러옵니다.
    primary_email = "wschoi@synotech.co.kr"
    
    try:
        app_password = st.secrets["EMAIL_PASSWORD"]
    except KeyError:
        st.error("서버 설정 오류: EMAIL_PASSWORD가 Secrets에 등록되지 않았습니다.")
        return False
        
    alias_email = "synocore@synotech.co.kr"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = f"SynoCore 공식 센터 <{alias_email}>"
        msg['To'] = to_email
        msg['Subject'] = "[SynoCore Pro] 회원가입을 위한 인증번호가 발급되었습니다."

        body = f"""안녕하세요. 시노텍(SynoTech) 차세대 배터리 설계 플랫폼 SynoCore입니다.

SynoCore Pro 서비스 이용을 위한 회원가입 인증번호를 안내해 드립니다.

■ 인증번호 : {code}

본 메일은 발신 전용이며, 인증번호는 1회에 한해 유효합니다.
감사합니다.

ⓒ SynoTech All rights reserved.
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(primary_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"이메일 발송 에러: {e}")
        return False

# -----------------------------------------------------------------------------
def get_dqdv(cat_sel, v_tc):
    v_axis = np.linspace(2.0, 4.2, 150)
    dqdv = np.zeros_like(v_axis)
    
    p1, p2 = 3.15, 0.0 
    
    if not mat_df.empty and 'Name' in mat_df.columns:
        mat_row = mat_df[mat_df['Name'] == cat_sel]
        if not mat_row.empty:
            try:
                if 'Peak1_V' in mat_df.columns: p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15))
                if 'Peak2_V' in mat_df.columns: p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
            except: pass
            
    if 'Peak1_V' not in mat_df.columns:
        if "Prussian" in str(cat_sel) or "Altris" in str(cat_sel): p1, p2 = 3.05, 3.45
        elif "Polyanion" in str(cat_sel) or "NVPF" in str(cat_sel): p1, p2 = 3.75, 0.0
        else: p1, p2 = 3.15, 0.0

    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]
    if not peaks: peaks = [3.15]
    
    for p in peaks:
        shifted_p = float(p) - (float(v_tc) * 0.015) 
        dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
        
    return v_axis, dqdv

def load_user_history(email):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
        if db_df.empty or 'Email' not in db_df.columns: return []
        
        my_logs = db_df[db_df['Email'] == email]
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict()
            row_dict.pop('Email', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Cell_V']:
                    row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
            except: pass
            
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0))
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y
            hist.append(row_dict)
        return hist[::-1]
    except: return []

def create_pdf(data_list, title="Simulation Report"):
    if FPDF is None: return b""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C"); pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated: {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')} (KST)", ln=True, align="R"); pdf.ln(5)

    if not data_list:
        pdf.cell(0, 10, "No data available.", ln=True); return pdf.output(dest="S").encode("latin-1")

    headers = ["Time", "Cathode", "Cap(mAh)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life"]
    col_widths = [25, 60, 25, 20, 25, 20, 25, 25, 25]
    
    pdf.set_font("Arial", "B", 10)
    for i, head in enumerate(headers): pdf.cell(col_widths[i], 10, head, border=1, align="C")
    pdf.ln(); pdf.set_font("Arial", "", 10)
    for item in data_list:
        pdf.cell(col_widths[0], 10, str(item.get("Time", "")), border=1, align="C")
        pdf.cell(col_widths[1], 10, str(item.get("Cathode", ""))[:30], border=1, align="L")
        for i, k in enumerate(["Cap(mAh/g)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life(Cyc)"]):
            pdf.cell(col_widths[i+2], 10, str(item.get(k, "")), border=1, align="C")
        pdf.ln()
    return pdf.output(dest="S").encode("latin-1")

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화
# -----------------------------------------------------------------------------
default_session_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0,
    'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
    'trigger_login': False, 'user_name': "", 'user_email': "", 'show_profile': False
}
for key, value in default_session_vars.items():
    if key not in st.session_state: st.session_state[key] = value

def process_login(): st.session_state.trigger_login = True

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인 모듈 (비율 및 문구 수정)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        # ID/PW 입력창과 로그인/회원가입 버튼의 폭을 완벽하게 1:1로 맞춤
        r1_c1, r1_c2 = st.columns(2)
        u_id = r1_c1.text_input("ID", placeholder="company email", key="id_login_m", label_visibility="collapsed")
        u_pw = r1_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed", on_change=process_login)
        
        r2_c1, r2_c2 = st.columns(2)
        login_btn = r2_c1.button("Login", key="btn_login_m", use_container_width=True)
        # 문구를 요청하신대로 변경
        reg_btn = r2_c2.button("계정신청 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True) 
        
        if login_btn or st.session_state.pop('trigger_login', False):
            df_u = get_user_db()
            u_id_clean = u_id.strip().lower()
            hashed_pw = hash_password(u_pw) if u_pw else ""
            valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
            
            if u_id_clean == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.update({'logged_in': True, 'user_name': "최우석 대표", 'user_email': u_id_clean, 'history': load_user_history(u_id_clean)}); st.rerun()
            elif not valid.empty:
                st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'history': load_user_history(str(valid['Email'].values[0]))}); st.rerun()
            else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        
        if reg_btn: st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1])
        r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if r_my.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if r_out.button("Logout", key="btn_logout_m", use_container_width=True): 
            for k in default_session_vars: st.session_state[k] = default_session_vars[k]
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [가입 및 계정 관리]
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소", key="r_email_m")
            if st.button("인증번호 발송", key="r_v_send_m"):
                if not e_in or "@" not in e_in:
                    st.error("올바른 이메일 주소를 입력해주세요.")
                else:
                    v_code = str(random.randint(100000, 999999))
                    with st.spinner("📧 이메일을 발송 중입니다... (최대 10초 소요)"):
                        is_sent = send_verification_email(e_in, v_code)
                        
                    if is_sent:
                        st.session_state.v_code = v_code
                        st.session_state.temp_email = e_in
                        st.session_state.reg_stage = 1
                        st.rerun()
                    else:
                        st.error("이메일 발송에 실패했습니다. 관리자에게 문의하거나 발신 서버 설정을 확인해주세요.")
                        
        elif st.session_state.reg_stage == 1:
            st.info(f"📧 [{st.session_state.temp_email}]로 인증번호가 발송되었습니다. 메일함을 확인해주세요.")
            v_in = st.text_input("인증번호 6자리 입력", key="r_v_in_m")
            if st.button("인증 확인", key="r_v_chk_m"):
                if v_in == st.session_state.v_code: 
                    st.session_state.reg_stage = 2
                    st.rerun()
                else:
                    st.error("인증번호가 일치하지 않습니다.")
                    
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2); pw1 = p1.text_input("2. Password", type="password"); pw2 = p2.text_input("2-1. Password 확인", type="password")
            n_name = st.text_input("3. 이름"); n_comp = st.text_input("4. Company")
            if st.button("가입신청", disabled=not (pw1==pw2 and n_name)):
                conn = st.connection("gsheets", type=GSheetsConnection)
                df_u = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5)
                new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=pd.concat([df_u, new_user], ignore_index=True))
                st.success("가입신청 완료! 승인 후 이용 가능합니다."); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

if st.session_state.get('show_profile') and st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
        if st.session_state.user_email == "wschoi@synotech.co.kr": st.info("관리자(Admin) 마스터 계정은 시트 수정 대상이 아닙니다.")
        else:
            df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
            st.markdown(f"**이메일(ID):** {st.session_state.user_email} (변경 불가)")
            p1, p2 = st.columns(2)
            m_pw = p1.text_input("새 Password (변경 시에만 입력)", type="password"); m_name = p2.text_input("이름", value=u_row.get('Name', ''))
            m_comp = p1.text_input("Company", value=u_row.get('Company', '')); m_dept = p2.text_input("부서", value=u_row.get('Dept', ''))
            m_job = p1.text_input("담당업무", value=u_row.get('Job', '')); m_phone = p2.text_input("연락처", value=u_row.get('Phone', ''))
            if st.button("개인정보 수정 완료"):
                conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5)
                idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                df_update.at[idx, 'Name'] = m_name; df_update.at[idx, 'Company'] = m_comp; df_update.at[idx, 'Dept'] = m_dept
                df_update.at[idx, 'Job'] = m_job; df_update.at[idx, 'Phone'] = m_phone
                conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=df_update); st.session_state.user_name = m_name; st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()

is_pro = st.session_state.logged_in

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 (클라우드 데이터 지능형 연동)
# -----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    sp1, c_1 = st.columns([0.03, 0.97])
    with c_1:
        m1, m2, m3, m4 = st.columns(4)
        if not mat_df.empty and 'Category' in mat_df.columns:
            cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
            ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
            ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist()
            sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
            
            cat_sel = m1.selectbox("Cathode", cat_list if cat_list else ["Sample Cathode"], key="sel_cat_m")
            ano_sel = m2.selectbox("Anode", ano_list if ano_list else ["Sample Anode"], key="sel_ano_m")
            m3.selectbox("Electrolyte", ele_list if ele_list else ["Sample Elec"], key="sel_ele_m")
            m4.selectbox("Separator", sep_list if sep_list else ["Sample Sep"], key="sel_sep_m")
            
            row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
            
            def_cap_min, def_cap_max, def_cap_val = float(row.get('Cap_Min', 100)), float(row.get('Cap_Max', 250)), float(row.get('Cap_Def', 160))
            def_vlt_min, def_vlt_max, def_vlt_val = float(row.get('Volt_Min', 2.0)), float(row.get('Volt_Max', 4.5)), float(row.get('Volt_Def', 3.05))
            def_den_min, def_den_max, def_den_val = float(row.get('Den_Min', 1.0)), float(row.get('Den_Max', 4.5)), float(row.get('Den_Def', 2.2))
            def_lif_min, def_lif_max, def_lif_val = int(row.get('Life_Min', 500)), int(row.get('Life_Max', 10000)), int(row.get('Life_Def', 4000))
            def_lod_min, def_lod_max, def_lod_val = float(row.get('Load_Min', 5.0)), float(row.get('Load_Max', 45.0)), float(row.get('Load_Def', 14.0))
        else:
            st.warning("Cloud에서 소재 리스트를 불러오지 못했습니다. (기본값 작동)")
            cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
            def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, 160.0
            def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05
            def_den_min, def_den_max, def_den_val = 1.0, 4.0, 2.2
            def_lif_min, def_lif_max, def_lif_val = 500, 10000, 4000
            def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    sp2, c_2 = st.columns([0.03, 0.97])
    with c_2:
        expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True)
        
        s1, s2, s3, s4 = st.columns(4)
        v_cap_in = s1.slider("Capacity (mAh/g)", min_value=def_cap_min, max_value=def_cap_max, value=def_cap_val, key=f"cap_{cat_sel}")
        v_volt_in = s2.slider("Voltage (V)", min_value=def_vlt_min, max_value=def_vlt_max, value=def_vlt_val, key=f"volt_{cat_sel}")
        v_dens_in = s3.slider("Density (g/cc)", min_value=def_den_min, max_value=def_den_max, value=def_den_val, key=f"dens_{cat_sel}", disabled=not expert)
        v_life_in = s4.slider("Base Life (Cycles)", min_value=def_lif_min, max_value=def_lif_max, value=def_lif_val, key=f"life_{cat_sel}", disabled=not expert)
        
        v_cap, v_volt = v_cap_in, v_volt_in
        v_dens = v_dens_in if expert else def_den_val
        v_life = v_life_in if expert else def_lif_val
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    sp3, c_3 = st.columns([0.03, 0.97])
    with c_3:
        show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True)
        
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
            v_load_in = st.slider("Loading (mg/cm2)", min_value=def_lod_min, max_value=def_lod_max, value=def_lod_val, key=f"load_{cat_sel}")
            st.slider("Cathode Press Density", 1.5, 3.5, 2.5, key="ad_c_den_m", disabled=not show_adv)
            st.slider("Conductive Agent %", min_value=get_p('cat_conductive', 'Min', 0.5), max_value=get_p('cat_conductive', 'Max', 10.0), value=get_p('cat_conductive', 'Default', 2.0), step=get_p('cat_conductive', 'Step', 0.1), key="ad_c_con_m", disabled=not show_adv)
            st.slider("Binder %", min_value=get_p('cat_binder', 'Min', 0.5), max_value=get_p('cat_binder', 'Max', 10.0), value=get_p('cat_binder', 'Default', 3.0), step=get_p('cat_binder', 'Step', 0.1), key="ad_c_bin_m", disabled=not show_adv)
            v_load = v_load_in
        with p2:
            st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
            v_np_in = st.slider("N/P Ratio", 1.0, 1.5, 1.15, step=0.01, key="sl_np_m")
            st.slider("Anode Press Density", 0.8, 2.0, 1.1, key="ad_a_den_m", disabled=not show_adv)
            st.slider("Anode Active %", 80.0, 98.0, 95.0, key="ad_a_act_m", disabled=not show_adv)
            v_np = v_np_in
        with p3:
            st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
            v_act_in = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0, key="sl_act_m")
            st.slider("E/C Ratio (g/Ah)", min_value=get_p('ec_ratio', 'Min', 1.0), max_value=get_p('ec_ratio', 'Max', 8.0), value=get_p('ec_ratio', 'Default', 3.5), step=get_p('ec_ratio', 'Step', 0.1), key="ad_ec_m", disabled=not show_adv)
            st.slider("Separator Thick (μm)", min_value=int(get_p('sep_thick', 'Min', 5)), max_value=int(get_p('sep_thick', 'Max', 50)), value=int(get_p('sep_thick', 'Default', 16)), key="ad_sep_m", disabled=not show_adv)
            v_act = v_act_in
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    sp4, c_4 = st.columns([0.03, 0.97])
    with c_4:
        t1, t2 = st.columns(2)
        with t1:
            st.markdown('<p class="sub-header-bold">Energy Density Goal (Wh/kg)</p>', unsafe_allow_html=True)
            v_te = st.slider("Energy Goal", 100, 250, 160, key="sl_te_m", label_visibility="collapsed")
        with t2:
            st.markdown('<p class="sub-header-bold">Simulation C-rate</p>', unsafe_allow_html=True)
            v_tc = st.slider("C-rate", min_value=get_p('target_crate', 'Min', 0.1), max_value=get_p('target_crate', 'Max', 10.0), value=get_p('target_crate', 'Default', 1.0), step=get_p('target_crate', 'Step', 0.1), key="sl_tc_m", label_visibility="collapsed")
        # ✅ 4번 박스 하단 한 줄 여유 추가
        st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    sp5, c_5 = st.columns([0.03, 0.97])
    with c_5:
        col_btn, col_msg = st.columns([1, 3])
        with col_btn:
            run_clicked = st.button("🚀 RUN DESIGN SIMULATION", key="btn_run_m", use_container_width=True)
        with col_msg:
            if not st.session_state.history:
                st.markdown('<div style="padding-top: 12px; color: #666; font-weight: bold;">아직 시뮬레이션 이력이 없습니다. 좌측 실행 버튼을 눌러주세요.</div>', unsafe_allow_html=True)
        
        # ✅ 5번 박스 RUN 버튼 아래 한 줄 여유 추가
        st.markdown("<br>", unsafe_allow_html=True)
                
        if run_clicked:
            ir_drop = 0.1 + (v_tc * 0.02)
            cell_v = max(0.1, v_volt - ir_drop)
            efficiency = max(0.5, 1.0 - (v_tc * 0.015))
            res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
            life_cyc = int(v_life * (0.95 ** v_tc))
            
            cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S")
            v_axis, dqdv = get_dqdv(cat_sel, v_tc)
            
            log_data = {
                "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
                "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1),
                "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
                "Wh/kg": round(res_whkg, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc,
                "dq_x": v_axis, "dq_y": dqdv
            }
            st.session_state.history.insert(0, log_data)
            st.session_state.sim_result = log_data
            st.rerun()

        if st.session_state.history:
            st.markdown("---")
            st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록 (선택 시 아래 결과가 즉시 변경됩니다)</p>', unsafe_allow_html=True)
            
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
            st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
            df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
            st.dataframe(df_history, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 내 데이터 관리 (저장, 엑셀 다운로드, PDF 출력) - 로그인 유저 전용
# -----------------------------------------------------------------------------
if is_pro and st.session_state.history:
    with st.container(border=True):
        st.markdown('<p class="main-header">6. Data Management & Export (Pro)</p>', unsafe_allow_html=True)
        sp6, c_6 = st.columns([0.03, 0.97])
        with c_6:
            btn1, btn2, btn3, btn4 = st.columns(4)
            
            if btn1.button("💾 내 계정에 저장하기", key="btn_save_my"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
                    is_duplicate = False
                    
                    if not db_df.empty and 'Email' in db_df.columns and 'Time' in db_df.columns:
                        if not db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                            is_duplicate = True
                            
                    if not is_duplicate:
                        save_record = res.copy()
                        save_record['Email'] = st.session_state.user_email
                        save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                        conn.update(spreadsheet=URL_USERS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True))
                    
                    # ✅ 버그 픽스: if문을 풀어써서 DeltaGenerator 텍스트 출력 오류 방지
                    if is_duplicate:
                        st.warning("이미 저장된 시뮬레이션 결과와 중복되는 부분을 제외 하였습니다. 내 기록 다운로드를 실행해 주세요.") 
                    else:
                        st.success("내 계정에 저장하기가 완료되었습니다.")
                except Exception as e: 
                    st.error(f"저장 오류: {e}")

            df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
            buffer = io.BytesIO()
            try:
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Simulation_Logs')
                file_data = buffer.getvalue()
                file_name = f"SynoCore_Logs_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            except ImportError:
                file_data = df_export.to_csv(index=False).encode('utf-8-sig')
                file_name = f"SynoCore_Logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"
                mime_type = "text/csv"

            btn2.download_button(
                label="📥 내 기록 다운로드",
                data=file_data,
                file_name=file_name,
                mime=mime_type,
                key="btn_download_excel"
            )

            if FPDF is not None:
                btn3.download_button(label="📄 선택 항목 PDF 출력", data=create_pdf([res], f"Result - {res['Cathode']}"), file_name=f"SynoCore_Result_{res['Time'].replace(':','')}.pdf", mime="application/pdf")
                btn4.download_button(label="📑 전체 이력 PDF 출력", data=create_pdf(st.session_state.history, "SynoCore - All Logs"), file_name="SynoCore_All_Logs.pdf", mime="application/pdf")
            else:
                btn3.warning("PDF 모듈 설치 필요"); btn4.warning("PDF 모듈 설치 필요")

# 7. 푸터 (저작권 표시)
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)