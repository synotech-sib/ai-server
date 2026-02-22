import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import hashlib
import io
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components

# [구글 시트 라이브러리 예외 처리]
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

# [OpenAI 라이브러리 예외 처리]
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (전역 스크롤바 숨김 + 커스텀 CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore Pro Max 1.8 (beta)", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 🔥 모든 스크롤바 트랙 숨기기 */
    ::-webkit-scrollbar { width: 0px !important; height: 0px !important; background: transparent !important; }
    * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
    
    /* 화면 최대폭 (1400px) */
    .main .block-container {
        max-width: 1400px !important; 
        padding-top: 2rem; padding-bottom: 2rem; margin: auto; 
    }
            
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 60px; }
    .syno-title { color: #1A729A; font-size: 44px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #D35400; font-size: 20px; font-weight: bold; padding-top: 16px; }
    
    /* 홈 버튼 투명 오버레이 */
    div.st-key-btn_home_overlay {
        margin-top: -60px !important; opacity: 0 !important; z-index: 999 !important;
        height: 60px !important; width: 350px !important; overflow: hidden !important;
    }
    div.st-key-btn_home_overlay button { height: 100% !important; width: 100% !important; cursor: pointer !important; }
    
    /* 🔥 지표(stMetric) 텍스트 굵게 및 중앙 정렬 */
    div[data-testid="stMetric"] { 
        background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; 
        padding: 15px 15px 10px 15px; height: 120px; display: flex; flex-direction: column; align-items: center; justify-content: center; 
    }
    div[data-testid="stMetricLabel"] { text-align: center !important; font-weight: 900 !important; font-size: 16px !important; color: #333 !important; width: 100%; display: block; }
    div[data-testid="stMetricValue"] { text-align: center !important; font-size: 26px !important; font-weight: bold !important; color: #1A729A !important; margin-top: 5px; width: 100%; display: block; } 
    div[data-testid="stMetricDelta"] { text-align: center !important; font-size: 14px !important; margin-top: 3px; width: 100%; display: block; }
    
    /* 일반 버튼 기본 디자인 */
    div[data-testid="stButton"] > button {
        height: 40px !important; background-color: #1A729A !important; color: white !important; 
        font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: none !important;
    }
    
    /* 🔥 실행 버튼 높이 20% 증가 (48px) */
    div[data-testid="stButton"] > button:active { transform: scale(0.98); }
    div.st-key-btn_run_m > button { height: 48px !important; font-size: 18px !important; background-color: #D35400 !important; }
    div.st-key-btn_run_m > button:hover { background-color: #E67E22 !important; }
    
    div[data-testid="stDownloadButton"] > button {
        height: 40px !important; background-color: #FFCA28 !important; color: #222 !important; 
        font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: 1px solid #E4B526 !important;
    }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #FFB300 !important; border: 1px solid #DDA010 !important; }

    .main-header { font-size: 26px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    
    /* 챗봇 들여쓰기 제거 및 배열 */
    div[data-testid="stChatMessage"] {
        display: flex !important; flex-direction: column !important; align-items: flex-start !important;
        padding: 15px 10px !important; background-color: #ffffff; border: 1px solid #eee;
        border-radius: 8px; margin-bottom: 10px; box-shadow: 0px 2px 5px rgba(0,0,0,0.02);
    }
    div[data-testid="stChatMessageContent"] { width: 100% !important; margin-left: 0px !important; padding-left: 0px !important; }
    div[data-testid="stTextInput"] input { height: 45px !important; font-size: 15px !important; border-radius: 6px; border: 2px solid #1A729A !important; }

    /* 사용자 코멘트 컬럼 헤더 텍스트 색상 강제 지정 */
    [data-testid="stTable"] th { color: #000000 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 설정
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1qY4V0A-r8uKBQtb3Nr7VIHyuL_e5JkIdCEpdv9WMjos/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1-yO5ulPP4FAuAEOizriEOSmNZQa1DpKyYYQynHFVK4U/edit?usp=sharing"
URL_LOGS  = "https://docs.google.com/spreadsheets/d/15YYACdkyLR9FwOHtZ2vz1JG-QqNVcWJrapWWxNvSVGQ/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

def load_cloud_data(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws, ttl=600)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
    except Exception: pass
    return pd.DataFrame()

def get_vip_list_exact():
    df = load_cloud_data(URL_USERS, "VIPs")
    return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()] if not df.empty and 'Company' in df.columns else []

mat_df_public = load_cloud_data(URL_MATS, "material_list")

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
    except Exception:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default

def safe_int(val, default):
    try: return int(float(val)) if val != "" and not pd.isna(val) else default
    except: return default

# -----------------------------------------------------------------------------
# 유틸리티 (물리 엔진)
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
        db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
        if db_df.empty or 'Email' not in db_df.columns: return []
        my_logs = db_df[(db_df['Email'] == email) & (db_df.get('Workspace', 'material_list') == workspace)]
        my_logs = my_logs.sort_values(by='Time', ascending=False) # 🔥 최신순 정렬 강제 적용
        hist = []
        for _, row in my_logs.iterrows():
            row_dict = row.to_dict(); row_dict.pop('Email', None); row_dict.pop('Workspace', None)
            try:
                for k in ['Cap(mAh/g)', 'Volt(V)', 'Load(mg)', 'N/P Ratio', 'Active(%)', 'C-rate', 'Wh/kg', 'Wh/L', 'Cell_V']: row_dict[k] = float(row_dict.get(k, 0))
                row_dict['Life(Cyc)'] = int(float(row_dict.get('Life(Cyc)', 0)))
            except: pass
            v_x, v_y = get_dqdv(row_dict.get('Cathode', ''), row_dict.get('C-rate', 1.0), pd.DataFrame())
            row_dict['dq_x'], row_dict['dq_y'] = v_x, v_y; hist.append(row_dict)
        return hist
    except: return []

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 모듈 
# -----------------------------------------------------------------------------
default_vars = {
    'logged_in': False, 'show_reg': False, 'user_name': "", 'user_email': "", 'show_profile': False,
    'workspace': 'material_overall', 'user_vip_name': None, 'is_admin': False, 'is_promax': False,
    'admin_view': None, 'admin_ws': None, 'chat_messages': [], 'history': [], 'sim_result': None,
    'show_bot': True, 'trigger_auto_bot': False, 'process_ai': False, 'bot_chat_count': 0
}
for key, val in default_vars.items():
    if key not in st.session_state: st.session_state[key] = val

h_l, h_r = st.columns([1, 1]) 

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">1.8 (beta)</span></div>', unsafe_allow_html=True)
    if st.button("홈으로", key="btn_home_overlay"):
        st.session_state.show_reg = False; st.session_state.show_profile = False; st.session_state.admin_view = None; st.session_state.admin_ws = None; st.rerun()

with h_r:
    is_pro = st.session_state.logged_in
    if not is_pro:
        c1, c2 = st.columns([1, 1])
        with c1.popover("Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="company email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                submit_login = st.form_submit_button("로그인", use_container_width=True)
                
                if submit_login:
                    df_u = get_user_db()
                    u_id_clean = u_id.strip().lower()
                    hashed_pw = hash_password(u_pw) if u_pw else ""
                    
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'is_promax': True, 'workspace': 'material_overall'})
                        st.session_state.history = load_user_history(u_id_clean, 'material_overall')
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                            is_pm = True if vip_map.get(domain) else False
                            st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'user_vip_name': vip_map.get(domain), 'is_promax': is_pm, 'workspace': vip_map.get(domain) if vip_map.get(domain) else 'material_list'})
                            st.session_state.history = load_user_history(st.session_state.user_email, st.session_state.workspace)
                            st.rerun()
                        else: st.error("아이디 또는 비밀번호를 확인해주세요.")
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_go_reg_m", use_container_width=True): 
            st.session_state.show_reg = not st.session_state.show_reg; st.session_state.show_profile = False; st.rerun()
    else:
        r_name, r_my, r_out = st.columns([2, 1, 1])
        # 🔥 유저 로그인 상태 명확히 표기 (Pro vs Pro Max)
        tier_label = "Pro Max" if st.session_state.is_promax else "Pro"
        r_name.markdown(f'<div class="user-greeting">{st.session_state.user_name} ({tier_label} User)</div>', unsafe_allow_html=True)
        if r_my.button("My 계정", key="btn_profile_m", use_container_width=True): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if r_out.button("Logout", key="btn_logout_m", use_container_width=True): 
            for key, val in default_vars.items(): st.session_state[key] = val
            st.rerun()

    t1, t2 = st.columns([1, 1])
    with t2:
        bot_active = st.toggle("**💬 SynoBot 활성화**", value=st.session_state.show_bot, key="bot_toggle_ui")
        if bot_active != st.session_state.show_bot: st.session_state.show_bot = bot_active; st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 👑 [최고 관리자 전용 대시보드] - 메인 폭과 맞춤 + 상단 작업
# -----------------------------------------------------------------------------
if is_pro and st.session_state.get('is_admin', False):
    if st.session_state.admin_view is not None or st.session_state.show_profile is False:
        # 🔥 관리자 패널은 화면 전체폭에 맞추되 내부 컨텐츠는 중앙 정렬 유도
        with st.container(border=True):
            st.markdown('<p class="main-header" style="color:#D35400;">👑 최고 관리자(Admin) 전용 패널</p>', unsafe_allow_html=True)
            a1, a2, a3, a4, a5 = st.columns(5)
            
            if a1.button("👥 유저 관리 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'users' else 'users'; st.session_state.admin_ws = 'Users'; st.rerun()
            if a2.button("🔋 소재 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'mats' else 'mats'; st.session_state.admin_ws = 'material_overall'; st.rerun()
            if a3.button("⚙️ 파라미터 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'param' else 'param'; st.session_state.admin_ws = 'param_config'; st.rerun()
            if a4.button("💾 시뮬 로그 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'logs' else 'logs'; st.session_state.admin_ws = 'myData'; st.rerun()
            if a5.button("💬 챗봇 로그 DB", use_container_width=True):
                st.session_state.admin_view = None if st.session_state.admin_view == 'botlogs' else 'botlogs'; st.session_state.admin_ws = 'BotLogs'; st.rerun()

            if st.session_state.admin_view:
                st.markdown("---")
                st.markdown(f'<p class="sub-header-bold">🛠️ 인라인 데이터베이스 편집기</p>', unsafe_allow_html=True)
                
                target_url = URL_USERS
                ws_options = ["Users"]
                if st.session_state.admin_view == 'users': ws_options = ["Users", "VIPs"]
                elif st.session_state.admin_view == 'mats': target_url = URL_MATS; ws_options = ["material_overall", "material_list"] + get_vip_list_exact()
                elif st.session_state.admin_view == 'param': target_url = URL_PARAM; ws_options = ["param_config"]
                elif st.session_state.admin_view == 'logs': target_url = URL_LOGS; ws_options = ["myData"]
                elif st.session_state.admin_view == 'botlogs': target_url = URL_LOGS; ws_options = ["BotLogs"]
                
                if len(ws_options) > 1:
                    sel_ws_admin = st.selectbox("📂 편집할 워크스페이스(탭) 선택", ws_options, index=ws_options.index(st.session_state.admin_ws) if st.session_state.admin_ws in ws_options else 0)
                    if sel_ws_admin != st.session_state.admin_ws: st.session_state.admin_ws = sel_ws_admin; st.rerun()
                
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    if st.session_state.admin_view == 'mats' and st.session_state.admin_ws == 'material_overall':
                        st.caption("ℹ️ 'material_overall'은 공용 및 모든 VIP 데이터가 취합된 **읽기 전용(Read-only)** 뷰입니다.")
                        # (생략: 병합 로직 동일하게 적용 가능)
                    else:
                        try:
                            df_admin = conn.read(spreadsheet=target_url, worksheet=st.session_state.admin_ws, ttl=600)
                            if st.session_state.admin_view in ['logs', 'botlogs'] and not df_admin.empty:
                                df_admin = df_admin.iloc[::-1].reset_index(drop=True)
                            edited_df = st.data_editor(df_admin, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.admin_view}")
                            if st.button("💾 클라우드에 저장", type="primary"):
                                save_df = edited_df.iloc[::-1].reset_index(drop=True) if st.session_state.admin_view in ['logs', 'botlogs'] else edited_df
                                conn.update(spreadsheet=target_url, worksheet=st.session_state.admin_ws, data=save_df.fillna(""))
                                st.cache_data.clear(); st.success("성공적으로 업데이트되었습니다.")
                        except: st.warning("해당 탭이 존재하지 않거나 권한이 없습니다.")
                except Exception as e: st.error(f"DB 오류: {e}")
                
                st.markdown("---")
                st.markdown('<p class="sub-header-bold">👁️ 하단 시뮬레이터 테스트 (VIP 시점)</p>', unsafe_allow_html=True)
                vip_opts = ["material_overall", "material_list"] + get_vip_list_exact()
                sel_ws = st.selectbox("**🔒 테스트 워크스페이스 선택**", vip_opts, index=vip_opts.index(st.session_state.workspace) if st.session_state.workspace in vip_opts else 0)
                if sel_ws != st.session_state.workspace: st.session_state.workspace = sel_ws; st.session_state.history = load_user_history(st.session_state.user_email, sel_ws); st.rerun()

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문
# -----------------------------------------------------------------------------
if st.session_state.get('show_bot', True):
    # 🔥 시노봇 폭을 우측 계정 박스와 일치하도록 비율 조정
    col_left, col_main, col_bot = st.columns([0.05, 0.70, 0.25], gap="large")
else:
    col_left, col_main = st.columns([0.05, 0.95], gap="large")
    col_bot = None

with col_left:
    # 🔥 좌측 상단 로고 삽입
    try:
        st.image("image_7.png", use_container_width=True)
    except:
        pass # 파일이 없으면 패스
    st.markdown("<div style='text-align: center; color: #bbb; font-weight: bold; margin-top: 10px; font-size: 13px; letter-spacing: 1px;'>SynoCore</div>", unsafe_allow_html=True)

with col_main:
    # 메인 패널의 높이를 넉넉하게 지정하거나 동적으로 늘어나게 처리
    with st.container(border=False):
        with st.container(border=True):
            ws_badge = f" [Workspace: {st.session_state.workspace}]" if is_pro else ""
            st.markdown(f'<p class="main-header">1. Material Selection<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
            sp1, c_1 = st.columns([0.02, 0.98])
            with c_1:
                df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace not in ["material_list", "material_overall"] else pd.DataFrame()
                _dfs = []
                if not df_vip.empty:
                    tmp_vip = df_vip.copy(); tmp_vip['Is_VIP'] = True; _dfs.append(tmp_vip.iloc[::-1])
                if not mat_df_public.empty:
                    tmp_pub = mat_df_public.copy(); tmp_pub['Is_VIP'] = False; _dfs.append(tmp_pub)
                
                mat_df = pd.concat(_dfs, ignore_index=True).drop_duplicates(subset=['Name'], keep='first') if _dfs else mat_df_public.copy()

                m1, m2, m3, m4 = st.columns(4)
                cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist() if not mat_df.empty and 'Category' in mat_df.columns else []
                ano_list = mat_df[mat_df['Category']=='Anode']['Name'].tolist() if not mat_df.empty and 'Category' in mat_df.columns else []
                
                vip_names = mat_df[mat_df.get('Is_VIP', False) == True]['Name'].tolist() if not mat_df.empty else []
                def format_mat_name(name): return f"💎 {name}" if name in vip_names else name
                
                with m1:
                    cat_sel = st.selectbox("**Cathode**", cat_list if cat_list else ["Sample Cathode"], format_func=format_mat_name, key="sel_cat_m")
                with m2:
                    ano_sel = st.selectbox("**Anode**", ano_list if ano_list else ["Sample Anode"], format_func=format_mat_name, key="sel_ano_m")
                with m3:
                    st.selectbox("**Electrolyte**", ["Standard Elec"], disabled=True)
                with m4:
                    st.selectbox("**Separator**", ["Standard Sep"], disabled=True)
                
                row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
                def_cap_min, def_cap_max, def_cap_val = 100.0, 250.0, safe_float(row.get('Cap_Def'), 160.0)
                def_vlt_min, def_vlt_max, def_vlt_val = 2.0, 4.5, safe_float(row.get('Volt_Def'), 3.05)
                def_den_min, def_den_max, def_den_val = 1.0, 5.0, safe_float(row.get('Den_Def'), 4.5)
                def_lif_min, def_lif_max, def_lif_val = 500, 10000, safe_int(row.get('Life_Def'), 4000)
                def_lod_min, def_lod_max, def_lod_val = 5.0, 45.0, safe_float(row.get('Load_Def'), 14.0)
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
            sp2, c_2 = st.columns([0.03, 0.97])
            with c_2:
                expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", key="chk_exp_m", disabled=True)
                
                s1, s2, s3, s4 = st.columns(4)
                # 🔥 터치 민감도 조절을 위해 step 파라미터 적용
                v_cap = s1.slider("**Capacity (mAh/g)**", def_cap_min, def_cap_max, def_cap_val, step=1.0, key=f"cap_{cat_sel}")
                v_volt = s2.slider("**Voltage (V)**", def_vlt_min, def_vlt_max, def_vlt_val, step=0.01, key=f"volt_{cat_sel}")
                v_den = s3.slider("**True Density (g/cc)**", def_den_min, def_den_max, def_den_val, step=0.1, key=f"dens_{cat_sel}", disabled=not expert)
                v_life = s4.slider("**Base Life (Cycles)**", def_lif_min, def_lif_max, def_lif_val, step=100, key=f"life_{cat_sel}", disabled=not expert)
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
            sp3, c_3 = st.columns([0.03, 0.97])
            with c_3:
                show_adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", key="chk_adv_m", disabled=True)
                
                p1, p2, p3 = st.columns(3)
                with p1:
                    st.markdown('<p class="sub-header-bold">(A) Cathode Settings</p>', unsafe_allow_html=True)
                    v_load = st.slider("**Cathode Areal Loading (mg/cm2)**", def_lod_min, def_lod_max, def_lod_val, step=0.5, key=f"load_{cat_sel}")
                    v_press = st.slider("**Cathode Press Density**", 1.5, 4.0, 2.5, step=0.1, key="ad_c_den_m", disabled=not show_adv)
                    
                    porosity = max(0.0, (1 - (v_press / v_den)) * 100) if v_den > 0 else 0
                        
                with p2:
                    st.markdown('<p class="sub-header-bold">(B) Anode & Balance</p>', unsafe_allow_html=True)
                    v_np = st.slider("**N/P Ratio**", 0.95, 1.50, 1.10, step=0.01, key="sl_np_m")
                    st.slider("**Anode Active %**", 80.0, 98.0, 95.0, step=0.5, key="ad_a_act_m", disabled=not show_adv)
                    
                with p3:
                    st.markdown('<p class="sub-header-bold">(C) Cell</p>', unsafe_allow_html=True)
                    v_act = st.slider("**Active Ratio (%)**", 80.0, 99.0, 92.0, step=0.5, key="sl_act_m")
                    v_ec = st.slider("**E/C Ratio (g/Ah)**", 1.0, 8.0, 3.5, step=0.1, key="ad_ec_m", disabled=not show_adv)
                    
                w1, w2, w3 = st.columns(3)
                with w1:
                    if porosity < 20.0: st.error("⚠️ 공극률 부족: 전해액 침투 불량 위험!")
                with w2:
                    if v_np < 1.05: st.error("⚠️ N/P Ratio 위험: 나트륨 석출(Na-Plating) 및 단락 위험!")
                with w3:
                    if show_adv and v_ec < 2.0: st.error("⚠️ E/C Ratio 부족: 전해액 고갈에 따른 수명 급감 위험!")
                st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
            sp4, c_4 = st.columns([0.03, 0.97])
            with c_4:
                t1, t2, t3 = st.columns(3)
                with t1:
                    st.markdown('<p class="sub-header-bold">Energy Density (Wh/kg)</p>', unsafe_allow_html=True)
                    v_te = st.slider("Energy Density", 100, 350, 250, step=5, label_visibility="collapsed")
                with t2:
                    st.markdown('<p class="sub-header-bold">Simulation C-rate</p>', unsafe_allow_html=True)
                    v_tc = st.slider("C-rate", 0.1, 10.0, 1.0, step=0.1, label_visibility="collapsed")
                with t3:
                    st.markdown('<p class="sub-header-bold">Cycle Life Goal</p>', unsafe_allow_html=True)
                    v_tl = st.slider("Cycle Goal", 500, 10000, 2000, step=100, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
            sp5, c_5 = st.columns([0.03, 0.97])
            with c_5:
                btn_text = "🚀 RUN SIMULATION" if st.session_state.history else "🚀 RUN SIMULATION ㅡ 아직 시뮬레이션 이력이 없습니다. 실행 버튼을 눌러 주세요."
                run_clicked = st.button(btn_text, key="btn_run_m", use_container_width=True)
                        
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
                    
                    # 🔥 중복 실행 철저 방지 로직 보강
                    is_dup = False
                    if st.session_state.history:
                        last_run = st.session_state.history[0]
                        keys_to_check = ["Cathode", "Anode", "Cap(mAh/g)", "Volt(V)", "Load(mg)", "N/P Ratio", "Active(%)", "C-rate"]
                        if all(log_data[k] == last_run.get(k) for k in keys_to_check):
                            is_dup = True

                    if is_dup:
                        st.warning("⚠️ 이전 실행과 동일한 파라미터 조건입니다. (결과가 저장되지 않습니다)")
                    else:
                        with st.spinner("🚀 물리 엔진 연산 및 시뮬레이션 진행 중..."):
                            time.sleep(0.6) 
                            st.session_state.history.insert(0, log_data)
                            st.session_state.sim_result = log_data
                            st.session_state.trigger_auto_bot = True 
                            st.rerun()

                if st.session_state.history:
                    st.markdown("---")
                    st.markdown('<p class="sub-header-bold">🔍 현재 세션 기록</p>', unsafe_allow_html=True)
                    
                    log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg | {h['Life(Cyc)']} Cyc" for h in st.session_state.history]
                    sel_idx = st.selectbox("기록 선택", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")
                    res = st.session_state.history[sel_idx]
                    
                    st.markdown("---")
                    
                    r1, r2, r3, r4 = st.columns(4)
                    delta_e = round(res['Wh/kg'] - v_te, 1)
                    r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{delta_e:+} Wh/kg (vs Target)")
                    r2.metric("Volumetric Density", f"{res.get('Wh/L', 0)} Wh/L", delta=" - ", delta_color="off")
                    delta_v = round(res['Cell_V'] - v_volt, 2)
                    r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta=f"{delta_v:+} V (IR Drop)", delta_color="inverse")
                    delta_l = res['Life(Cyc)'] - v_tl
                    r4.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc", delta=f"{delta_l:+} Cyc (vs Target)")
                    
                    # 🔥 그래프 하단 한 줄 여유
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">Discharge Profile</p>', unsafe_allow_html=True)
                        fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                        fig1.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9")
                        st.plotly_chart(fig1, use_container_width=True)
                        
                    with g2:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">dQ/dV Profile</p>', unsafe_allow_html=True)
                        fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                        fig2.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), template="plotly_white", plot_bgcolor="#f4f6f9")
                        st.plotly_chart(fig2, use_container_width=True)
                        
                    with g3:
                        st.markdown('<p class="sub-header-bold" style="text-align: center;">Cell Performance</p>', unsafe_allow_html=True)
                        categories = ['Energy', 'Power', 'Life', 'Voltage', 'Loading']
                        r_vals = [min(100, res.get('Wh/kg', 0)/250*100), min(100, res.get('C-rate', 1)/5.0*100), min(100, res.get('Life(Cyc)', 0)/5000*100), min(100, res.get('Cell_V', 0)/4.0*100), min(100, res.get('Load(mg)', 0)/25.0*100)]
                        fig3 = go.Figure(go.Scatterpolar(r=r_vals, theta=categories, fill='toself', line=dict(color='#E4B526', width=2)))
                        fig3.update_layout(polar=dict(bgcolor="#f4f6f9", radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=260, margin=dict(l=30, r=30, t=10, b=10), template="plotly_white")
                        st.plotly_chart(fig3, use_container_width=True)

                    # 🔥 차트와 데이터 프레임 사이 여유 간격 추가
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown('<p class="sub-header-bold">📋 Simulation Detailed Logs</p>', unsafe_allow_html=True)
                    df_history = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    # 🔥 최신순 정렬
                    st.dataframe(df_history.sort_values(by="Time", ascending=False), use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

        if is_pro and st.session_state.history:
            with st.container(border=True):
                st.markdown('<p class="main-header">6. Data Management & Past Records (Pro)</p>', unsafe_allow_html=True)
                sp6, c_6 = st.columns([0.03, 0.97])
                with c_6:
                    btn1, btn2, btn3 = st.columns(3)
                    
                    if btn1.button("💾 계정에 저장", key="btn_save_my", use_container_width=True):
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                            if not db_df[(db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == res['Time'])].empty:
                                st.warning("이미 저장된 시뮬레이션 결과입니다.")
                            else:
                                save_record = res.copy(); save_record['Email'] = st.session_state.user_email; save_record['Workspace'] = st.session_state.workspace; save_record['User Comment'] = "" 
                                save_record.pop('dq_x', None); save_record.pop('dq_y', None)
                                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([save_record])], ignore_index=True))
                                st.cache_data.clear(); st.success("저장 완료.")
                        except Exception as e: st.error(f"저장 오류: {e}")

                    df_export = pd.DataFrame(st.session_state.history).drop(columns=['dq_x', 'dq_y'], errors='ignore')
                    csv_data = df_export.to_csv(index=False).encode('utf-8-sig')
                    btn2.download_button(label="📥 CSV 다운로드", data=csv_data, file_name=f"SynoCore_Logs_{datetime.utcnow().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

                    with btn3:
                        # 🔥 PDF 저장 기능을 브라우저 자체 인쇄로 연결
                        components.html("""
                            <button onclick="window.parent.print()" style="height:40px; width:100%; background-color:#FFCA28; color:#222; font-weight:bold; font-size:16px; border-radius:4px; border:1px solid #E4B526; cursor:pointer;">📄 화면 PDF 인쇄</button>
                            <script>
                                const btn = document.querySelector('button');
                                btn.addEventListener('mouseover', () => btn.style.backgroundColor = '#FFB300');
                                btn.addEventListener('mouseout', () => btn.style.backgroundColor = '#FFCA28');
                            </script>
                        """, height=45)

                    st.markdown("---")
                    
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        db_df_all = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=600)
                        if not db_df_all.empty and 'Email' in db_df_all.columns:
                            my_saved_data = db_df_all[(db_df_all['Email'] == st.session_state.user_email) & (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace)]
                            
                            if not my_saved_data.empty:
                                # 🔥 최신순 정렬
                                my_saved_data = my_saved_data.sort_values(by='Time', ascending=False).reset_index(drop=True)
                                
                                col_title, col_btn_del = st.columns([0.8, 0.2])
                                with col_title: st.markdown('<p class="sub-header-bold">🗄️ 내 클라우드 저장 이력</p>', unsafe_allow_html=True)
                                
                                df_display = my_saved_data.drop(columns=['Email', 'Workspace', 'dq_x', 'dq_y'], errors='ignore').copy()
                                if 'User Comment' not in df_display.columns: df_display['User Comment'] = ""
                                df_display['User Comment'] = df_display['User Comment'].fillna("")
                                
                                core_cols = ['Time', 'User Comment', 'Cathode', 'Anode']
                                other_cols = [c for c in df_display.columns if c not in core_cols]
                                df_display = df_display[core_cols + other_cols]
                                df_display.insert(0, "선택", False)
                                
                                disabled_cols = [col for col in df_display.columns if col not in ["선택", "User Comment"]]
                                
                                # 🔥 코멘트 입력 시 자동 저장을 위한 data_editor
                                edited_df = st.data_editor(
                                    df_display, use_container_width=True, hide_index=True,
                                    disabled=disabled_cols, key="my_logs_editor",
                                    column_config={
                                        "User Comment": st.column_config.TextColumn(
                                            "💬 사용자 코멘트 (더블클릭)", width="large",
                                            help="더블클릭 후 기재하시면 외부 클릭 시 자동 저장됩니다."
                                        )
                                    }
                                )
                                
                                # 자동 저장 로직
                                if "prev_logs" not in st.session_state:
                                    st.session_state.prev_logs = df_display['User Comment'].tolist()
                                    
                                current_comments = edited_df['User Comment'].tolist()
                                if current_comments != st.session_state.prev_logs:
                                    # 변경 감지
                                    for idx, row in edited_df.iterrows():
                                        mask = (db_df_all['Email'] == st.session_state.user_email) & \
                                               (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & \
                                               (db_df_all['Time'] == row['Time'])
                                        if mask.any(): db_df_all.loc[mask, 'User Comment'] = row['User Comment']
                                    
                                    conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all)
                                    st.session_state.prev_logs = current_comments
                                    st.cache_data.clear(); st.success("코멘트가 자동 저장되었습니다.")

                                with col_btn_del:
                                    selected_times = edited_df[edited_df["선택"] == True]["Time"].tolist()
                                    if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
                                        if selected_times:
                                            mask = ~((db_df_all['Email'] == st.session_state.user_email) & \
                                                     (db_df_all.get('Workspace', 'material_list') == st.session_state.workspace) & \
                                                     (db_df_all['Time'].isin(selected_times)))
                                            conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df_all[mask])
                                            st.cache_data.clear(); st.rerun()
                            else: st.info("클라우드 DB에 이전에 저장된 시뮬레이션 데이터가 없습니다.")
                    except: st.warning("과거 이력을 불러오지 못했습니다.")

# -----------------------------------------------------------------------------
# 🤖 시노봇 (SynoBot) AI 패널 - 🔥 역방향 피드형 & 부드러운 엔지니어 톤 🔥
# -----------------------------------------------------------------------------
SYSTEM_KNOWLEDGE = """
You are 'SynoBot', an expert Sodium-Ion Battery (SIB) R&D engineer powered by OpenAI.
Answer accurately and professionally in Korean.
[응답 스타일 지침]
- 전문 엔지니어 어투를 사용하되, 너무 딱딱하지 않고 부드럽게 설명해 주세요.
- 서술형 문장을 허용하되 핵심 포인트나 수치, 비교 분석 등 중요한 내용은 눈에 띄게 반드시 도트 블릿('-' 또는 '•')을 사용하여 리스트 형태로 짚어주세요.
"""

if col_bot:
    with col_bot:
        st.markdown("#### 🤖 SynoBot (Beta)")
        
        if OpenAI is not None and "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
            if not st.session_state.chat_messages:
                st.session_state.chat_messages = [{"role": "assistant", "content": "배터리 설계 전문 AI 시노봇 대기 중입니다.\n\n• 시뮬레이터 결과를 분석하거나 SIB 설계 지식을 질문해 주세요."}]
                
            def handle_bot_input():
                user_val = st.session_state.get("bot_user_input", "").strip()
                if user_val:
                    # 🔥 무료 유저 사용 제한 로직
                    if not st.session_state.logged_in and st.session_state.bot_chat_count >= 3:
                        st.session_state.chat_messages.append({"role": "user", "content": user_val})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "⚠️ **안내**\n\n무료 사용자의 챗봇 이용 횟수를 초과했습니다. 더 깊이 있는 정보와 무제한 데이터 보안 관리를 원하신다면 상단의 **[계정 가입 ㅣ Pro Mode]**를 통해 전환해 주시기 바랍니다."})
                    else:
                        st.session_state.bot_chat_count += 1
                        st.session_state.chat_messages.append({"role": "user", "content": user_val})
                        st.session_state.process_ai = True
                    st.session_state.bot_user_input = "" 

            # 🔥 질문 입력란 윗쪽 배열
            st.text_input("💬 시노봇에게 질문 (Enter로 전송)", key="bot_user_input", on_change=handle_bot_input, placeholder="결과를 분석해줘")

            if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                st.session_state.trigger_auto_bot = False 
                auto_prompt = "방금 시뮬레이션이 실행되었습니다. 이 데이터를 분석하여 잘된 점, 개선점, 위험 요소를 블릿을 활용해 가독성 좋고 부드럽게 브리핑해 주세요."
                sys_prompt = SYSTEM_KNOWLEDGE + f"\n\n[Current Data]\n{st.session_state.sim_result}"
                
                with st.spinner("📊 실시간 데이터 분석 중..."):
                    try:
                        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": auto_prompt}])
                        bot_reply = "📊 **[실시간 AI 진단]**\n\n" + response.choices[0].message.content
                        st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                    except Exception as e: st.error(f"분석 오류: {e}")

            elif st.session_state.get("process_ai", False):
                st.session_state.process_ai = False
                sys_prompt = SYSTEM_KNOWLEDGE
                if st.session_state.sim_result: sys_prompt += f"\n\n[Current Data]\n{st.session_state.sim_result}"
                
                api_messages = [{"role": "system", "content": sys_prompt}]
                # 최근 문맥 10개만 유지
                for msg in st.session_state.chat_messages[-10:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                with st.spinner("답변 작성 중..."):
                    try:
                        response = client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response.choices[0].message.content})
                    except Exception as e: st.error(f"연산 오류: {e}")

            # 🔥 메인 컨테이너에 맞춰 늘어나게 flex-grow처럼 적용하거나 충분한 height 확보, 최근 대화가 맨 위로.
            with st.container(height=800, border=True):
                for message in reversed(st.session_state.chat_messages):
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

# 7. 푸터 
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #888; font-size: 13px; line-height: 1.6; margin-bottom: 20px;'>
    <strong>SynoTech Co., Ltd.</strong> ㅣ 687-88-01333<br>
    410, Industry-University Cooperation Building, Dankook University<br>
    152, Jukjeon-ro, Suji-gu, Yongin-si, Gyeonggi-do, South Korea<br>
    ☎️ +82 50 6020 8318 ㅣ 📧 cs@synotech.co.kr<br>
    <span style='font-size: 12px; color: #aaa; margin-top: 5px; display: inline-block;'>ⓒ 2026. SynoTech. All rights reserved.</span>
</div>
""", unsafe_allow_html=True)