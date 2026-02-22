import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import hashlib
import io
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [라이브러리 예외 처리 - 설치 환경에 따른 오류 방지]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (레이아웃 비율 및 스크롤바 제어)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore Pro Max 1.7 (beta)", layout="wide")

st.markdown("""
    <style>
    /* 기본 UI 요소 숨김 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* [핵심] 모든 스크롤바 트랙 투명화 (휠 스크롤은 유지) */
    ::-webkit-scrollbar { width: 0px !important; height: 0px !important; background: transparent !important; }
    * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
    
    /* 대시보드 최대폭 최적화 (10:65:25 비율 대응) */
    .main .block-container { 
        max-width: 1450px !important; 
        padding-top: 1.5rem; 
        padding-bottom: 2rem; 
        margin: auto; 
    }
            
    /* 헤더 텍스트 디자인 */
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 60px; }
    .syno-title { color: #1A729A; font-size: 42px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #D35400; font-size: 18px; font-weight: bold; padding-top: 14px; }
    
    /* 결과 지표(stMetric) 윗선 정렬 */
    div[data-testid="stMetric"] { 
        background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; 
        padding: 15px 15px 10px 15px; height: 120px; display: flex; flex-direction: column; justify-content: flex-start; 
    }
    div[data-testid="stMetricValue"] { font-size: 26px !important; color: #1A729A !important; margin-top: 5px; } 
    div[data-testid="stMetricDelta"] { font-size: 13px !important; margin-top: 3px; }
    
    /* 버튼 및 다운로드 버튼 스타일 */
    div[data-testid="stButton"] > button {
        height: 42px !important; background-color: #1A729A !important; color: white !important; 
        font-weight: bold !important; font-size: 15px !important; border-radius: 4px !important; width: 100%; border: none !important;
    }
    div[data-testid="stDownloadButton"] > button {
        height: 40px !important; background-color: #FFCA28 !important; color: #222 !important; 
        font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important; width: 100%; border: 1px solid #E4B526 !important;
    }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #FFB300 !important; border: 1px solid #DDA010 !important; }

    /* 섹션 구분 박스 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important; margin-bottom: 20px !important; 
    }
    
    .main-header { font-size: 24px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 15px; padding-right: 15px; }
    
    /* 챗봇 들여쓰기 제거 및 위아래 배치(Column) */
    div[data-testid="stChatMessage"] { 
        display: flex !important; flex-direction: column !important; align-items: flex-start !important; 
        padding: 12px 10px !important; background-color: #ffffff; border: 1px solid #eee; border-radius: 8px; margin-bottom: 8px; 
    }
    div[data-testid="stChatMessageContent"] { width: 100% !important; margin-left: 0px !important; padding-left: 0px !important; }
    
    /* 시노봇 입력창 스타일 */
    div[data-testid="stTextInput"] input { height: 45px !important; font-size: 15px !important; border: 2px solid #1A729A !important; border-radius: 6px; }
    
    /* 로고 중앙 정렬 및 여백 */
    .logo-wrapper { display: flex; justify-content: center; align-items: flex-start; padding-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 클라우드 DB 연동 및 유틸리티 함수
# -----------------------------------------------------------------------------
ADMIN_USERS = {"wschoi@synotech.co.kr": "최우석", "seoyeon@synotech.co.kr": "최서연"}
ADMIN_PW = "synotech0773!"

# 구글 시트 URL 설정
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
    except: pass
    return pd.DataFrame()

def get_vip_list_exact():
    df = load_cloud_data(URL_USERS, "VIPs")
    if not df.empty and 'Company' in df.columns:
        return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()]
    return []

def get_user_db():
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=URL_USERS, worksheet="Users", ttl=600)
    except:
        return pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Job", "Phone", "Purpose", "ProMax_Req", "RegDate"])

def safe_float(val, default):
    try: return float(val) if val != "" and not pd.isna(val) else default
    except: return default

def safe_int(val, default):
    try: return int(float(val)) if val != "" and not pd.isna(val) else default
    except: return default

def get_dqdv(cat_sel, v_tc, m_df=None):
    v_axis = np.linspace(2.0, 4.2, 150)
    dqdv = np.zeros_like(v_axis)
    p1, p2 = 3.15, 0.0 
    if m_df is not None and not m_df.empty and 'Name' in m_df.columns:
        mat_row = m_df[m_df['Name'] == cat_sel]
        if not mat_row.empty:
            p1 = float(mat_row.iloc[0].get('Peak1_V', 3.15))
            p2 = float(mat_row.iloc[0].get('Peak2_V', 0.0))
    peaks = [p for p in [p1, p2] if pd.notna(p) and float(p) > 0]
    for p in (peaks if peaks else [3.15]): 
        shifted_p = float(p) - (float(v_tc) * 0.015)
        dqdv += np.exp(-(v_axis - shifted_p)**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

# -----------------------------------------------------------------------------
# 3. 세션 초기화 및 헤더 모듈 (상하단 25% 폭 칼각 정렬)
# -----------------------------------------------------------------------------
for key, val in {'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'history': [], 'sim_result': None, 'user_name': "", 'user_email': "", 'show_profile': False, 'workspace': 'material_overall', 'chat_messages': [], 'show_bot': True, 'trigger_auto_bot': False, 'process_ai': False}.items():
    if key not in st.session_state: st.session_state[key] = val

# 상단 헤더: 왼쪽 75%, 오른쪽 25% (gap="large"로 하단 본문과 오차 없이 정렬)
h_l, h_r = st.columns([0.75, 0.25], gap="large")

with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore Pro Max</span><span class="syno-subtitle">1.7 (beta)</span></div>', unsafe_allow_html=True)

with h_r:
    # 계정 가입 버튼 및 로그인 로직
    if not st.session_state.logged_in:
        c1, c2 = st.columns([1, 1])
        with c1.popover("Login", use_container_width=True):
            with st.form("login_form", border=False):
                u_id = st.text_input("ID", placeholder="email", label_visibility="collapsed")
                u_pw = st.text_input("PW", type="password", placeholder="password", label_visibility="collapsed")
                if st.form_submit_button("로그인", use_container_width=True):
                    df_u = get_user_db()
                    u_id_clean = u_id.strip().lower()
                    if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                        st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_overall'})
                        st.rerun()
                    else:
                        valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hash_password(u_pw))] if not df_u.empty else pd.DataFrame()
                        if not valid.empty:
                            st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': str(valid['Email'].values[0]), 'workspace': 'material_list'})
                            st.rerun()
                        else: st.error("로그인 정보를 확인해 주세요.")
        
        # ✅ 계정 가입 버튼 (정상 작동)
        if c2.button("계정 가입 ㅣ Pro Mode", key="btn_reg_trigger", use_container_width=True):
            st.session_state.show_reg = not st.session_state.show_reg
            st.rerun()
    else:
        # 로그인 상태 표시
        r_info, r_btn = st.columns([2, 1])
        r_info.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if r_btn.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # 시노봇 토글 (우측 25% 라인 맞춤)
    st.columns([1, 1])[1].toggle("**💬 SynoBot 활성화**", value=st.session_state.show_bot, key="bot_toggle_ui")
    if st.session_state.bot_toggle_ui != st.session_state.show_bot:
        st.session_state.show_bot = st.session_state.bot_toggle_ui
        st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 시뮬레이터 본문 (✅ 10 : 65 : 25 레이아웃 - 로고 확대 및 상단과 일치)
# -----------------------------------------------------------------------------
if st.session_state.show_bot:
    col_logo, col_main, col_bot = st.columns([0.1, 0.65, 0.25], gap="large")
else:
    col_logo, col_main = st.columns([0.1, 0.9], gap="large")
    col_bot = None

# (A) 왼쪽 패널 - 로고 큼직하게 배치
with col_logo:
    st.markdown('<div class="logo-wrapper">', unsafe_allow_html=True)
    if os.path.exists("sc_logo.png"):
        st.image("sc_logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='color:#bbb; font-weight:900;'>SC</h1>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# (B) 중앙 패널 - 시뮬레이터 본문 (독립 스크롤)
with col_main:
    # 계정 가입 폼
    if st.session_state.show_reg:
        with st.container(border=True):
            st.markdown("### 📝 SynoCore 계정 가입신청")
            st.info("회사 이메일 정보를 입력하시면 검토 후 Pro Mode 권한을 부여해 드립니다.")
            col_reg1, col_reg2 = st.columns(2)
            reg_email = col_reg1.text_input("회사 이메일 주소")
            reg_name = col_reg2.text_input("성함")
            reg_company = col_reg1.text_input("회사명")
            reg_pw = col_reg2.text_input("비밀번호 설정", type="password")
            if st.button("가입 신청서 제출"):
                st.success("신청이 완료되었습니다. 담당자 승인 후 로그인 가능합니다."); st.session_state.show_reg = False; st.rerun()

    # 시뮬레이터 영역
    with st.container(height=900, border=False):
        # 1. Material Selection
        with st.container(border=True):
            st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            cat_sel = m1.selectbox("Cathode", ["Prussian Blue", "Layered Oxide", "Polyanionic"], index=0)
            ano_sel = m2.selectbox("Anode", ["Hard Carbon", "Soft Carbon"], index=0)
            m3.selectbox("Electrolyte", ["NaPF6 Standard"], index=0)
            m4.selectbox("Separator", ["PE Standard"], index=0)

        # 2. 결과 지표 (시뮬레이션 실행 후 노출)
        if st.session_state.history:
            res = st.session_state.history[0]
            st.markdown("---")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=f"{round(res['Wh/kg']-150, 1):+} (vs Ref)")
            r2.metric("Volumetric", f"{res['Wh/L']} Wh/L", delta="-")
            r3.metric("Cell Voltage", f"{res['Cell_V']} V", delta="-0.02V (IR Drop)", delta_color="inverse")
            r4.metric("Cycle Life", f"{res['Life(Cyc)']} Cyc", delta="+200 (vs Target)")
            
            # ✅ 결과값 하단 여유 공간 확보
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            g1, g2, g3 = st.columns(3)
            with g1: 
                fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                fig1.update_layout(height=240, margin=dict(l=10, r=10, t=30, b=10), template="plotly_white", title="Discharge Profile")
                st.plotly_chart(fig1, use_container_width=True)
            with g2:
                v_x, v_y = get_dqdv(cat_sel, 1.0)
                fig2 = go.Figure(go.Scatter(x=v_x, y=v_y, fill='tozeroy', line=dict(color='#e63946', width=2)))
                fig2.update_layout(height=240, margin=dict(l=10, r=10, t=30, b=10), template="plotly_white", title="dQ/dV Profile")
                st.plotly_chart(fig2, use_container_width=True)
            with g3:
                # ✅ Radar 글자 제거
                fig3 = go.Figure(go.Scatterpolar(r=[85, 70, 90, 80, 75], theta=['Energy', 'Power', 'Life', 'Voltage', 'Load'], fill='toself'))
                fig3.update_layout(height=240, margin=dict(l=30, r=30, t=30, b=30), title="Cell Performance")
                st.plotly_chart(fig3, use_container_width=True)

        # 3. Control Sliders
        with st.container(border=True):
            st.markdown('<p class="main-header">2. Parameter Control</p>', unsafe_allow_html=True)
            v_cap = st.slider("Capacity (mAh/g)", 100, 250, 160)
            v_volt = st.slider("Nominal Voltage (V)", 2.5, 4.5, 3.2)
            if st.button("🚀 RUN SIMULATION", key="run_sim_btn"):
                cell_v = round(v_volt - 0.12, 2)
                res_whkg = round((v_cap * 0.92 * cell_v) / 2.5, 1)
                new_res = {"Wh/kg": res_whkg, "Wh/L": round(res_whkg*2.2, 1), "Cell_V": cell_v, "Life(Cyc)": 3000, "dq_x": [], "dq_y": []}
                st.session_state.history.insert(0, new_res)
                st.session_state.sim_result = new_res
                st.session_state.trigger_auto_bot = True
                st.rerun()

# (C) 우측 패널 - 시노봇 (역방향 피드 + 상단 입력)
if col_bot:
    with col_bot:
        st.markdown("<div id='bot-fixed-anchor'></div>", unsafe_allow_html=True)
        st.markdown("#### 🤖 SynoBot (Beta)")
        
        # 1. 입력창 최상단 배치
        def bot_submit():
            prompt = st.session_state.bot_input_field.strip()
            if prompt:
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                st.session_state.process_ai = True
                st.session_state.bot_input_field = ""

        st.text_input("질문을 입력하세요 (Enter)", key="bot_input_field", on_change=bot_submit, placeholder="시뮬레이션 결과 분석해줘")

        # 2. AI 연산 로직 (OpenAI gpt-4o-mini 호출)
        if OpenAI and "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            sys_msg = "You are an SIB engineer. Be professional. Use dot bullets (- ) for technical data. Summarize logically."

            # 자동 분석 트리거
            if st.session_state.trigger_auto_bot and st.session_state.sim_result:
                st.session_state.trigger_auto_bot = False
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": f"Analyze: {st.session_state.sim_result}"}]
                )
                st.session_state.chat_messages.append({"role": "assistant", "content": "📊 **[AI 분석 브리핑]**\n\n" + resp.choices[0].message.content})

            # 일반 질문 처리
            elif st.session_state.process_ai:
                st.session_state.process_ai = False
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.chat_messages[-5:]
                )
                st.session_state.chat_messages.append({"role": "assistant", "content": resp.choices[0].message.content})

        # 3. 최근 대화가 위로 오는 독립 스크롤 대화창
        with st.container(height=750, border=True):
            if not st.session_state.chat_messages:
                st.info("안녕하세요! SIB 설계 전문 AI 시노봇입니다. 분석이 필요하시면 질문해 주세요.")
            for m in reversed(st.session_state.chat_messages):
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

# 7. 푸터 
st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 13px;'>ⓒ 2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)