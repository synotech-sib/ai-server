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

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.7 Pro", layout="wide")

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
# 2. 클라우드 DB 연동 설정 및 마스터 계정 세팅
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=5)
def load_cloud_data(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
    except Exception: pass
    return pd.DataFrame()

def get_vip_list_exact():
    df = load_cloud_data(URL_USERS, "VIPs")
    return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()] if not df.empty and 'Company' in df.columns else []

mat_df_public = load_cloud_data(URL_MATS, "material_list")
param_df = load_cloud_data(URL_PARAM, "Sheet1")

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
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=5).astype(str)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "RegDate"])

# -----------------------------------------------------------------------------
# ✉️ [이메일 발송 시스템] 
# -----------------------------------------------------------------------------
def send_verification_email(to_email, code):
    sender_email = "wschoi@synotech.co.kr"
    sender_password = "여기에_16자리_앱비밀번호를_입력하세요"
    try:
        if "EMAIL_PASSWORD" in st.secrets: sender_password = st.secrets["EMAIL_PASSWORD"]
    except: pass

    try:
        msg = MIMEMultipart()
        msg['From'] = f"SynoCore Admin <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "[SynoCore Pro] 회원가입 인증번호 안내"
        body = f"안녕하세요. SynoCore Pro 시뮬레이터 플랫폼 회원가입을 위한 인증번호 안내입니다.\n\n▶ 인증번호 : {code}\n\n위 인증번호 6자리를 회원가입 창에 입력해 주시기 바랍니다.\n감사합니다."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password.replace(" ", "")) 
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return False

# -----------------------------------------------------------------------------
# 유틸리티 (물리 엔진 및 PDF)
# -----------------------------------------------------------------------------
def get_dqdv(cat_sel, v_tc, m_df=None):
    v_axis = np.linspace(2.0, 4.2, 150); dqdv = np.zeros_like(v_axis); p1, p2 = 3.15, 0.0 
    if m_df is not None and not m_df.empty and 'Name' in m_df.columns:
        mat_row = m_df[m_df['Name'] == cat_sel]
        if not mat_row.empty:
            try: p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15)); p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
            except: pass
    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]
    if not peaks: peaks = [3.15]
    for p in peaks:
        shifted_p = float(p) - (float(v_tc) * 0.015); dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email, workspace="material_list"):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
        if db_df.empty or 'Email' not in db_df.columns: return []
        my_logs = db_df[(db_df['Email'] == email) & (db_df.get('Workspace', 'material_list') == workspace)]
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None); row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
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
# 4. 세션 초기화 및 헤더 모듈 (✅ 완벽한 정석 Dictionary 초기화 적용)
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "",
    'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'material_list', 'user_vip_name': None, 'show_guide': False, 'is_admin': False
}
for key, val in default_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

h_l, h_r = st.columns([1.2, 1]) 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.7 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        c1, c2 = st.columns([1, 1])
        with c1.popover("Login", use_container_width=True): # ✅ 버튼 폭 맞춤
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                submit_login = st.form_submit_button("로그인", use_container_width=True)
                
                if submit_login:
                    df_u = get_user_db()
                    u_id_clean = u_id.strip().lower()
                    hashed_pw = hash_password(u_pw) if u_pw else ""
                    
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_list'})
                        st.session_state.history = load_user_history(u_id_clean, 'material_list')
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                            st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list'});
                            st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                            st.rerun()
                        else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): 
            st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1])
        r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if r_my.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if r_out.button("Logout", key="btn_logout_m", use_container_width=True): 
            for key, val in default_vars.items(): st.session_state[key] = val
            st.rerun()

is_pro = st.session_state.logged_in

# ✅ 가이드 토글 버튼을 우측 (로그인 영역 아래쪽)으로 정렬 배치
if is_pro:
    t_spacer, t_tog = st.columns([0.83, 0.17])
    with t_tog:
        st.session_state.show_guide = st.toggle("💡 기술 가이드 보기", value=st.session_state.get('show_guide', False))

st.markdown("---")

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드] 최상단 배치
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    with st.container(border=True):
        st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
        a1, a2, a3, a4 = st.columns(4)
        a1.link_button("👥 유저 관리 DB (Users)", URL_USERS, use_container_width=True)
        a2.link_button("🔋 소재 DB (Materials)", URL_MATS, use_container_width=True)
        a3.link_button("⚙️ 파라미터 DB (Param)", URL_PARAM, use_container_width=True)
        a4.link_button("💾 시뮬레이션 로그 DB", URL_LOGS, use_container_width=True)
        
        st.markdown("---")
        vip_opts = ["material_list"] + get_vip_list_exact()
        sel_ws = st.selectbox("**🔒 관리자 접속 워크스페이스 선택**", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
        if sel_ws != st.session_state.workspace:
            st.session_state.workspace = sel_ws
            st.session_state.history = load_user_history(st.session_state.user_email, sel_ws)
            st.rerun()

# -----------------------------------------------------------------------------
# 계정 가입 및 My 계정 관리
# -----------------------------------------------------------------------------
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 가입 (Pro Mode)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("1. 회사 이메일 주소")
            if st.button("인증번호 발송"):
                if not e_in or "@" not in e_in: st.error("올바른 이메일 주소를 입력해주세요.")
                else:
                    v_code = str(random.randint(100000, 999999))
                    with st.spinner("📧 이메일을 발송 중입니다... (최대 10초 소요)"):
                        if send_verification_email(e_in, v_code):
                            st.session_state.update({'v_code': v_code, 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
                        else: st.error("이메일 발송 실패. 관리자에게 문의하세요.")
        elif st.session_state.reg_stage == 1:
            st.info(f"📧 [{st.session_state.temp_email}]로 인증번호가 발송되었습니다.")
            v_in = st.text_input("인증번호 6자리 입력")
            if st.button("인증 확인"):
                if v_in == st.session_state.v_code: st.session_state.reg_stage = 2; st.rerun()
                else: st.error("인증번호가 일치하지 않습니다.")
        elif st.session_state.reg_stage == 2:
            p1, p2 = st.columns(2); pw1 = p1.text_input("2. Password", type="password"); pw2 = p2.text_input("2-1. Password 확인", type="password")
            n_name = st.text_input("3. 이름"); n_comp = st.text_input("4. Company")
            if st.button("최종 가입신청", disabled=not (pw1==pw2 and n_name)):
                conn = st.connection("gsheets", type=GSheetsConnection); df_u = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=5)
                new_user = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(pw1), "Name": n_name, "Company": n_comp, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=pd.concat([df_u, new_user], ignore_index=True))
                st.success("가입신청 완료! 로그인 해주세요."); st.session_state.show_reg = False; st.session_state.reg_stage = 0; st.rerun()

if st.session_state.get('show_profile') and st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
        if st.session_state.get('is_admin', False): st.info("관리자 계정입니다.")
        else:
            df_u = get_user_db(); u_row = df_u[df_u['Email'] == st.session_state.user_email].iloc[0] if not df_u[df_u['Email'] == st.session_state.user_email].empty else {}
            st.markdown(f"**이메일(ID):** {st.session_state.user_email} (변경 불가)")
            p1, p2 = st.columns(2)
            m_pw = p1.text_input("새 Password (변경 시에만 입력)", type="password"); m_name = p2.text_input("이름", value=u_row.get('Name', ''))
            m_comp = p1.text_input("Company", value=u_row.get('Company', '')); m_dept = p2.text_input("부서", value=u_row.get('Dept', ''))
            m_job = p1.text_input("담당업무", value=u_row.get('Job', '')); m_phone = p2.text_input("연락처", value=u_row.get('Phone', ''))
            if st.button("개인정보 수정 완료"):
                conn = st.connection("gsheets", type=GSheetsConnection); df_update = conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=5)
                idx = df_update[df_update['Email'] == st.session_state.user_email].index[0]
                if m_pw: df_update.at[idx, 'Password'] = hash_password(m_pw)
                df_update.at[idx, 'Name'] = m_name; df_update.at[idx, 'Company'] = m_comp; df_update.at[idx, 'Dept'] = m_dept; df_update.at[idx, 'Job'] = m_job; df_update.at[idx, 'Phone'] = m_phone
                conn.update(spreadsheet=URL_USERS, worksheet="Users", data=df_update); st.session_state.user_name = m_name; st.session_state.show_profile = False; st.success("수정 완료!"); st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 (60:20:20 레이아웃)
# -----------------------------------------------------------------------------
if st.session_state.get('show_guide', False):
    col_main, col_glossary, col_deep = st.columns([0.6, 0.2, 0.2])
else:
    col_main = st.container()
    col_glossary, col_deep = None, None

with col_main:
    with st.container(border=True):
        ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
        st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
        sp1, c_1 = st.columns([0.03, 0.97])
        with c_1:
            df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame()
            mat_df = pd.concat([mat_df_public, df_vip]).drop_duplicates(subset=['Name'], keep='last') if not mat_df_public.empty else pd.DataFrame()

            m1, m2, m3, m4 = st.columns(4)
            if not mat_df.empty and 'Category' in mat_df.columns:
                cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist()
                ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist()
                ele_list = mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist()
                sep_list = mat_df[mat_df['Category']=='Separator']['Name'].tolist()
                
                # ✅ 1. 소재 선택 및 최적화된 소재 추가 폼
                with m1:
                    cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], key="sel_cat_m")
                    if is_pro and st.session_state.workspace != "material_list":
                        with st.expander("➕ 양극재 추가"):
                            n_cat = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Cat_01")
                            c_cat = st.number_input("용량 (mAh/g)", value=160.0, key="n_cat_c")
                            v_cat = st.number_input("전압 (V)", value=3.2, key="n_cat_v")
                            if st.button("저장", key="btn_save_cat"):
                                new_row = pd.DataFrame([{"Name": n_cat, "Category": "Cathode", "Cap_Def": c_cat, "Volt_Def": v_cat, "Den_Def": 2.2}])
                                st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, new_row], ignore_index=True))
                                st.rerun()

                with m2:
                    ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], key="sel_ano_m")
                    if is_pro and st.session_state.workspace != "material_list":
                        with st.expander("➕ 음극재 추가"):
                            n_ano = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Ano_01")
                            c_ano = st.number_input("용량 (mAh/g)", value=360.0, key="n_ano_c")
                            v_ano = st.number_input("전압 (V)", value=0.1, key="n_ano_v")
                            if st.button("저장", key="btn_save_ano"):
                                new_row = pd.DataFrame([{"Name": n_ano, "Category": "Anode", "Cap_Def": c_ano, "Volt_Def": v_ano, "Den_Def": 1.1}])
                                st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, new_row], ignore_index=True))
                                st.rerun()

                with m3:
                    st.selectbox("**Electrolyte**", ele_list if ele_list else ["Sample Elec"], key="sel_ele_m")
                    if is_pro and st.session_state.workspace != "material_list":
                        with st.expander("➕ 전해액 추가"):
                            n_ele = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Elec_01")
                            d_ele = st.number_input("밀도 (g/cc)", value=1.2, key="n_ele_d")
                            if st.button("저장", key="btn_save_ele"):
                                new_row = pd.DataFrame([{"Name": n_ele, "Category": "Electrolyte", "Den_Def": d_ele}])
                                st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, new_row], ignore_index=True))
                                st.rerun()

                with m4:
                    st.selectbox("**Separator**", sep_list if sep_list else ["Sample Sep"], key="sel_sep_m")
                    if is_pro and st.session_state.workspace != "material_list":
                        with st.expander("➕ 분리막 추가"):
                            n_sep = st.text_input("소재명", placeholder=f"{st.session_state.workspace}_Sep_01")
                            t_sep = st.number_input("두께 (μm)", value=16.0, key="n_sep_t") 
                            if st.button("저장", key="btn_save_sep"):
                                new_row = pd.DataFrame([{"Name": n_sep, "Category": "Separator", "Load_Def": t_sep}])
                                st.connection("gsheets", type=GSheetsConnection).update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, new_row], ignore_index=True))
                                st.rerun()
                
                row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
                def_cap_min, def_cap_max, def_cap_val = float(row.get('Cap_Min', 100)), float(row.get('Cap_Max', 250)), float(row.get('Cap_Def', 160))
                def_vlt_min, def_vlt_max, def_vlt_val = float(row.get('Volt_Min', 2.0)), float(row.get('Volt_Max', 4.5)), float(row.get('Volt_Def', 3.05))
                def_den_min, def_den_max, def_den_val = float(row.get('Den_Min', 1.0)), float(row.get('Den_Max', 5.0)), float(row.get('Den_Def', 4.5))
                def_lif_min, def_lif_max, def_lif_val = int(row.get('Life_Min', 500)), int(row.get('Life_Max', 10000)), int(row.get('Life_Def', 4000))
                def_lod_min, def_lod_max, def_lod_val = float(row.get('Load_Min', 5.0)), float(row.get('Load_Max', 45.0)), float(row.get('Load_Def', 14.0))
            else:
                st.warning("Cloud에서 소재 리스트를 불러오지 못했습니다. 앱이 기본값으로 작동합니다.")
                cat_sel, ano_sel = "Sample Cathode", "Sample Anode"
                def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, 160.0; def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, 3.05; def_den_min, def_den_max, def_den_val = 1.0, 5.0, 4.5; def_lif_min, def_lif_max, def_lif_val = 500, 10000, 4000; def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, 14.0
            st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
        sp2, c_2 = st.columns([0.03, 0.97])
        with c_2:
            expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True)
            
            s1, s2, s3, s4 = st.columns(4)
            v_cap = s1.slider("**Capacity (mAh/g)**", min_value=def_cap_min, max_value=def_cap_max, value=def_cap_val, key=f"cap_{cat_sel}")
            v_volt = s2.slider("**Voltage (V)**", min_value=def_vlt_min, max_value=def_vlt_max, value=def_vlt_val, key=f"volt_{cat_sel}")
            v_den = s3.slider("**True Density (g/cc)**", min_value=def_den_min, max_value=def_den_max, value=def_den_val, key=f"dens_{cat_sel}", disabled=not expert)
            v_life = s4.slider("**Base Life (Cycles)**", min_value=def_lif_min, max_value=def_lif_max, value=def_lif_val, key=f"life_{cat_sel}", disabled=not expert)
            st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
        sp3, c_3 = st.columns([0.03, 0.97])
        with c_3:
            show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True)
            
            p1, p2, p3 = st.columns(3)
            with p1:
                st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
                v_load = st.slider("**Loading (mg/cm2)**", min_value=def_lod_min, max_value=def_lod_max, value=def_lod_val, key=f"load_{cat_sel}")
                v_press = st.slider("**Cathode Press Density**", 1.5, 4.0, 2.5, key="ad_c_den_m", disabled=not show_adv)
                st.slider("**Conductive Agent %**", 0.5, 10.0, 2.0, key="ad_c_con_m", disabled=not show_adv)
                st.slider("**Binder %**", 0.5, 10.0, 3.0, key="ad_c_bin_m", disabled=not show_adv)
                
                porosity = max(0.0, (1 - (v_press / v_den)) * 100) if v_den > 0 else 0
                st.caption(f"**예상 공극률 (Porosity): {porosity:.1f}%**")
                if porosity < 20.0: st.error("⚠️ 공극률 부족: 전해액 침투 불량 위험!")
                    
            with p2:
                st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
                v_np = st.slider("**N/P Ratio**", 1.0, 1.5, 1.15, step=0.01, key="sl_np_m")
                st.slider("**Anode Press Density**", 0.8, 2.0, 1.1, key="ad_a_den_m", disabled=not show_adv)
                st.slider("**Anode Active %**", 80.0, 98.0, 95.0, key="ad_a_act_m", disabled=not show_adv)
            with p3:
                st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
                v_act = st.slider("**Active Ratio (%)**", 80.0, 99.0, 92.0, key="sl_act_m")
                st.slider("**E/C Ratio (g/Ah)**", 1.0, 8.0, 3.5, key="ad_ec_m", disabled=not show_adv)
                st.slider("**Separator Thick (μm)**", 5, 50, 16, key="ad_sep_m", disabled=not show_adv)
            st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
        sp4, c_4 = st.columns([0.03, 0.97])
        with c_4:
            t1, t2, t3 = st.columns(3)
            with t1:
                st.markdown('<p class="sub-header-bold">Energy Density Goal</p>', unsafe_allow_html=True)
                v_te = st.slider("Energy Goal (Wh/kg)", 100, 350, 250, label_visibility="collapsed")
            with t2:
                st.markdown('<p class="sub-header-bold">Simulation C-rate</p>', unsafe_allow_html=True)
                v_tc = st.slider("C-rate", 0.1, 10.0, 1.0, label_visibility="collapsed")
            with t3:
                st.markdown('<p class="sub-header-bold">Cycle Life Goal</p>', unsafe_allow_html=True)
                v_tl = st.slider("Cycle Goal", 500, 10000, 2000, label_visibility="collapsed")
        # ✅ 4번 박스 하단 여유 공간 축소
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
                    
            if run_clicked:
                ir_drop = 0.1 + (v_tc * 0.02)
                cell_v = max(0.1, v_volt - ir_drop)
                efficiency = max(0.5, 1.0 - (v_tc * 0.015))
                res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
                whl = res_whkg * v_press * 0.8  
                life_cyc = int(v_life * (0.95 ** v_tc))
                
                cur_time = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S")
                v_axis, dqdv = get_dqdv(cat_sel, v_tc, mat_df)
                
                log_data = {
                    "Time": cur_time, "Cathode": cat_sel, "Anode": ano_sel,
                    "Cap(mAh/g)": round(v_cap, 1), "Volt(V)": round(v_volt, 2), "Load(mg)": round(v_load, 1),
                    "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc,
                    "Wh/kg": round(res_whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life_cyc,
                    "dq_x": v_axis, "dq_y": dqdv
                }
                st.session_state.history.insert(0, log_data)
                st.session_state.sim_result = log_data
                st.rerun()

            if st.session_state.history:
                st.markdown("---")
                st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록</p>', unsafe_allow_html=True)
                
                log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Life(Cyc)']} Cyc" for h in st.session_state.history]
                sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")
                res = st.session_state.history[sel_idx]
                
                st.markdown("---")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=round(res['Wh/kg'] - v_te, 1))
                r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L")
                r3.metric("Cell Voltage", f"{res['Cell_V']} V")
                r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=res['Life(Cyc)'] - v_tl)
                
                g1, g2 = st.columns([1, 1])
                with g1:
                    st.markdown('<p class="sub-header-bold">Discharge Profile</p>', unsafe_allow_html=True)
                    fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                    fig1.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
                    st.plotly_chart(fig1, use_container_width=True)
                with g2:
                    st.markdown('<p class="sub-header-bold">dQ/dV Profile</p>', unsafe_allow_html=True)
                    fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                    fig2.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
                    st.plotly_chart(fig2, use_container_width=True)

                st.markdown("---")
                st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
                df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                st.dataframe(df_history, use_container_width=True)
        # ✅ 5번 박스 하단 여유 공간 축소
        st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # 6. 내 데이터 관리
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
                        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
                        is_duplicate = False
                        
                        if not db_df.empty and 'Email' in db_df.columns and 'Time' in db_df.columns:
                            if not db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                                is_duplicate = True
                                
                        if not is_duplicate:
                            save_record = res.copy()
                            save_record['Email'] = st.session_state.user_email
                            save_record['Workspace'] = st.session_state.workspace
                            save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                            conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True))
                        
                        st.warning("이미 저장된 시뮬레이션 결과입니다.") if is_duplicate else st.success("내 계정에 저장하기가 완료되었습니다.")
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

                btn2.download_button(label="📥 내 기록 다운로드", data=file_data, file_name=file_name, mime=mime_type)

                if FPDF is not None:
                    btn3.download_button(label="📄 선택 항목 PDF 출력", data=create_pdf([res], f"Result - {res['Cathode']}"), file_name=f"SynoCore_Result_{res['Time'].replace(':','')}.pdf", mime="application/pdf")
                    btn4.download_button(label="📑 전체 이력 PDF 출력", data=create_pdf(st.session_state.history, "SynoCore - All Logs"), file_name="SynoCore_All_Logs.pdf", mime="application/pdf")
                else:
                    btn3.warning("PDF 모듈 필요"); btn4.warning("PDF 모듈 필요")

# -----------------------------------------------------------------------------
# 📖 우측 가이드 패널 렌더링 (Toggle On 시 표출)
# -----------------------------------------------------------------------------
if col_glossary and col_deep:
    with col_glossary:
        st.markdown(f"#### 📖 Glossary (용어 사전)")
        with st.expander("N/P Ratio"): st.write("양극 대비 음극의 설계 용량 비율입니다. 리튬 석출 방지를 위해 통상 1.1~1.2 수준으로 세팅합니다.")
        with st.expander("C-rate"): st.write("배터리 충방전 속도입니다. 1C는 1시간 만에 배터리를 완전 충전/방전하는 속도입니다.")
        with st.expander("Porosity (공극률)"): st.write("전극 내 빈 공간의 비율입니다. 전해액이 침투할 수 있는 필수 공간입니다.")
            
    with col_deep:
        st.markdown(f"#### 🎓 Deep Dive Insight")
        st.info("**[Trade-off Insight]**\n합제 밀도(Press Density)를 과도하게 높이면 부피 에너지 밀도(Wh/L)는 좋아지지만, 공극률(Porosity)이 20% 이하로 떨어져 내부 저항이 급증하고 수명이 치명적으로 단축됩니다.")
        st.info("**[C-rate & Overpotential]**\n출력(C-rate)을 높일수록 배터리 내부 저항(IR Drop)으로 인해 실제 작동 전압이 낮아지며, 이는 곧 최종 에너지 밀도(Wh/kg)의 하락으로 직결됩니다.")

# 7. 푸터 (저작권 표시)
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)