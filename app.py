import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import hashlib
import io

# [PDF 라이브러리]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# [구글 시트 연결 라이브러리]
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
    .syno-title { color: #1A729A; font-size: 46px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 14px; }
    
    /* 결과 카드 디자인 */
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    
    /* 입력창 및 버튼 높이 40px 통일 */
    div[data-testid="stTextInput"] input { height: 40px !important; font-size: 16px !important; }
    
    /* 기본 블루 버튼 */
    div[data-testid="stButton"] > button {
        height: 40px !important; background-color: #1A729A !important; 
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important; margin-top: 0px !important;
    }
    
    /* PDF 오렌지 버튼 */
    div[data-testid="stDownloadButton"] > button {
        height: 40px !important; background-color: #FF8C00 !important; 
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
    .user-greeting { color: #1A729A; font-weight: bold; height: 40px; display: flex; align-items: center; justify-content: flex-end; font-size: 16px; padding-right: 15px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# https://play.google.com/store/apps/details?id=com.ironguard.vpn&hl=ko
# -----------------------------------------------------------------------------
URL_USERS = "https://docs.google.com/spreadsheets/d/1dvEymhMnVxYJH9m0DhyWdp0ydyML9dBFagsbntfropw/edit?usp=sharing"
URL_MATS  = "https://docs.google.com/spreadsheets/d/1_0PL3lJU5SvZYZXeF4sd5EYvAOormgDw/edit?usp=sharing"
URL_PARAM = "https://docs.google.com/spreadsheets/d/1mUGyFRHq-JIMcfl0NFeWknfu7hZYVzWU/edit?usp=sharing"

def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=60)
def load_cloud_data(url):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url) 
        df.columns = [str(c).split('(')[0].strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

def get_dqdv(cat_sel, v_tc):
    v_axis = np.linspace(2.0, 4.2, 150)
    dqdv = np.zeros_like(v_axis)
    pks = [3.05, 3.45] if "Prussian" in str(cat_sel) or "Altris" in str(cat_sel) else ([3.75] if "Polyanion" in str(cat_sel) or "NVPF" in str(cat_sel) else [3.15])
    for p in pks:
        dqdv += np.exp(-(v_axis - (p - float(v_tc)*0.015))**2 / (2 * 0.05**2)) * 15
    return v_axis, dqdv

def load_user_history(email):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        db_df = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
        my_logs = db_df[db_df['Email'] == email]
        hist = []
        for _, row in my_logs.iterrows():
            d = row.to_dict()
            vx, vy = get_dqdv(d.get('Cathode',''), d.get('C-rate',1.0))
            d.update({'dq_x': vx, 'dq_y': vy})
            hist.append(d)
        return hist[::-1]
    except: return []

def create_pdf(data_list, title="Simulation Report"):
    if not FPDF: return b""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated: {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="R")
    pdf.ln(5)
    headers = ["Time", "Cathode", "Cap(mAh)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life"]
    col_widths = [25, 55, 25, 20, 25, 20, 25, 25, 25]
    pdf.set_font("Arial", "B", 10)
    for i, h in enumerate(headers): pdf.cell(col_widths[i], 10, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for item in data_list:
        pdf.cell(col_widths[0], 10, str(item.get("Time", "")), border=1, align="C")
        pdf.cell(col_widths[1], 10, str(item.get("Cathode", ""))[:25], border=1, align="L")
        for i, k in enumerate(["Cap(mAh/g)", "Volt(V)", "Active(%)", "C-rate", "Wh/kg", "Cell_V", "Life(Cyc)"]):
            pdf.cell(col_widths[i+2], 10, str(item.get(k, "")), border=1, align="C")
        pdf.ln()
    return pdf.output(dest="S").encode("latin-1")

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화
# -----------------------------------------------------------------------------
default_vars = {'logged_in': False, 'show_reg': False, 'reg_stage': 0, 'v_code': "", 'temp_email': "", 'history': [], 'user_name': "", 'user_email': "", 'show_profile': False}
for k, v in default_vars.items():
    if k not in st.session_state: st.session_state[k] = v

# 클라우드 데이터 사전 로드
mat_df = load_cloud_data(URL_MATS)
param_df = load_cloud_data(URL_PARAM)

# -----------------------------------------------------------------------------
# 4. 상단 헤더 및 로그인 모듈 (2x2 그리드)
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        r1_c1, r1_c2 = st.columns(2)
        u_id = r1_c1.text_input("ID", placeholder="company email", key="l_id", label_visibility="collapsed")
        u_pw = r1_c2.text_input("PW", type="password", placeholder="password", key="l_pw", label_visibility="collapsed")
        r2_c1, r2_c2 = st.columns(2)
        if r2_c1.button("Login", use_container_width=True):
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_u = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1", ttl=5).astype(str)
            u_id_c = u_id.strip().lower()
            valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_c) & (df_u['Password'] == hash_password(u_pw))]
            if u_id_c == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.update({'logged_in': True, 'user_name': "최우석 대표", 'user_email': u_id_c, 'history': load_user_history(u_id_c)}); st.rerun()
            elif not valid.empty:
                st.session_state.update({'logged_in': True, 'user_name': valid.iloc[0]['Name'], 'user_email': u_id_c, 'history': load_user_history(u_id_c)}); st.rerun()
            else: st.error("정보 확인 필요")
        if r2_c2.button("계정생성 ㅣ Pro 회원가입", use_container_width=True):
            st.session_state.show_reg = not st.session_state.show_reg; st.rerun()
    else:
        rn, rm, ro = st.columns([2, 1, 1])
        rn.markdown(f'<div class="user-greeting">{st.session_state.user_name} (Pro)</div>', unsafe_allow_html=True)
        if rm.button("My 계정"): st.session_state.show_profile = not st.session_state.show_profile; st.rerun()
        if ro.button("Logout"): 
            for k in default_vars: st.session_state[k] = default_vars[k]
            st.rerun()

# [계정 신청/수정 패널]
if st.session_state.show_reg and not st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">📝 계정 신청 (Pro)</p>', unsafe_allow_html=True)
        if st.session_state.reg_stage == 0:
            e_in = st.text_input("회사 이메일")
            if st.button("인증번호 발송"): 
                st.session_state.update({'v_code': str(random.randint(100000, 999999)), 'temp_email': e_in, 'reg_stage': 1}); st.rerun()
        elif st.session_state.reg_stage == 1:
            st.info(f"🔑 [{st.session_state.temp_email}] 인증번호: {st.session_state.v_code}")
            if st.button("인증 확인"): st.session_state.reg_stage = 2; st.rerun()
        elif st.session_state.reg_stage == 2:
            c1, c2 = st.columns(2)
            p1 = c1.text_input("PW", type="password"); nm = c2.text_input("이름"); cp = c1.text_input("Company")
            if st.button("가입신청 완료"):
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(spreadsheet=URL_USERS, worksheet="Sheet1")
                new_u = pd.DataFrame([{"Email": st.session_state.temp_email, "Password": hash_password(p1), "Name": nm, "Company": cp, "RegDate": datetime.utcnow().strftime("%Y-%m-%d")}])
                conn.update(spreadsheet=URL_USERS, worksheet="Sheet1", data=pd.concat([df, new_u], ignore_index=True))
                st.success("회원가입 완료!"); st.session_state.update({'show_reg': False, 'reg_stage': 0}); st.rerun()

if st.session_state.show_profile and st.session_state.logged_in:
    with st.container(border=True):
        st.markdown('<p class="main-header">👤 My 계정 정보 수정</p>', unsafe_allow_html=True)
        if st.session_state.user_email == "wschoi@synotech.co.kr": st.info("마스터 계정은 수정 대상이 아닙니다.")
        else:
            new_n = st.text_input("이름 수정", value=st.session_state.user_name)
            if st.button("수정사항 저장"): st.session_state.user_name = new_n; st.session_state.show_profile = False; st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
is_pro = st.session_state.logged_in

# -----------------------------------------------------------------------------
# 5. 시뮬레이터 본문 (1~5번 들여쓰기 적용)
# -----------------------------------------------------------------------------

# [1] Material Selection
with st.container(border=True):
    st.markdown('<p class="main-header">1. Material Selection</p>', unsafe_allow_html=True)
    sp1, c1 = st.columns([0.03, 0.97])
    with c1:
        if not mat_df.empty:
            m1, m2, m3, m4 = st.columns(4)
            cat_sel = m1.selectbox("Cathode", mat_df[mat_df['Category']=='Cathode']['Name'].tolist())
            row = mat_df[mat_df['Name']==cat_sel].iloc[0]
            c_cap, c_vlt, c_den, c_lif, c_lod = float(row.get('Capacity',160)), float(row.get('Voltage',3.05)), float(row.get('Density',2.2)), int(row.get('Life',4000)), float(row.get('Rec_Loading',14.0))
            m2.selectbox("Anode", ["Hard Carbon (A)", "Hard Carbon (B)"])
            m3.selectbox("Electrolyte", ["NaPF6 Standard", "High-Stability"])
            m4.selectbox("Separator", ["PE 16um", "Ceramic 18um"])
        else:
            c_cap, c_vlt, c_den, c_lif, c_lod = 160, 3.05, 2.2, 4000, 14; cat_sel = "Sample"

# [2] Material Specs (로그인 시 자동 활성화)
with st.container(border=True):
    st.markdown('<p class="main-header">2. Material Specs Expert Mode</p>', unsafe_allow_html=True)
    sp2, c2 = st.columns([0.03, 0.97])
    with c2:
        expert = True if is_pro else st.checkbox("세부 사항 수정 활성화 :red[(Pro Mode 전용)]", disabled=True)
        s1, s2, s3, s4 = st.columns(4)
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 250.0, c_cap, key=f"c_{cat_sel}")
        v_vlt = s2.slider("Voltage (V)", 2.0, 4.5, c_vlt, key=f"v_{cat_sel}")
        v_den = s3.slider("Density (g/cc)", 1.0, 4.5, c_den, disabled=not expert)
        v_lif = s4.slider("Base Life (Cycles)", 500, 10000, c_lif, disabled=not expert)

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    sp3, c3 = st.columns([0.03, 0.97])
    with c3:
        adv = True if is_pro else st.checkbox("세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]", disabled=True)
        p1, p2, p3 = st.columns(3)
        v_lod = p1.slider("Loading (mg/cm2)", 5.0, 45.0, c_lod, key=f"l_{cat_sel}")
        p1.slider("Press Density", 1.5, 3.5, 2.5, disabled=not adv)
        v_np = p2.slider("N/P Ratio", 1.0, 1.5, 1.15)
        p2.slider("Anode Press", 0.8, 2.0, 1.1, disabled=not adv)
        v_act = p3.slider("Active Ratio (%)", 80.0, 99.0, 92.0)
        p3.slider("E/C Ratio", 1.0, 8.0, 3.5, disabled=not adv)

# [4] Target Settings
with st.container(border=True):
    st.markdown('<p class="main-header">4. Target Settings</p>', unsafe_allow_html=True)
    sp4, c4 = st.columns([0.03, 0.97])
    with c4:
        t1, t2 = st.columns(2)
        v_te = t1.slider("Energy Goal (Wh/kg)", 100, 250, 160)
        v_tc = t2.slider("Simulation C-rate", 0.1, 10.0, 1.0, 0.1)

# [5] Simulation & Analysis
with st.container(border=True):
    st.markdown('<p class="main-header">5. Simulation Control & Analysis</p>', unsafe_allow_html=True)
    sp5, c5 = st.columns([0.03, 0.97])
    with c5:
        if st.button("🚀 RUN DESIGN SIMULATION", use_container_width=True):
            cv = max(0.1, v_vlt - (0.1 + v_tc*0.02)); wh = round(((v_cap*(v_act/100)*cv)/2.5)*max(0.5, 1.0-(v_tc*0.015)), 1)
            ct = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S")
            vx, vy = get_dqdv(cat_sel, v_tc)
            st.session_state.history.insert(0, {"Time": ct, "Cathode": cat_sel, "Cap(mAh/g)": v_cap, "Volt(V)": v_vlt, "Load(mg)": v_lod, "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc, "Wh/kg": wh, "Cell_V": round(cv, 2), "Life(Cyc)": int(v_lif*(0.95**v_tc)), "dq_x": vx, "dq_y": vy})
            st.rerun()

        if st.session_state.history:
            st.markdown("---")
            opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg" for h in st.session_state.history]
            sel = st.selectbox("과거 기록 선택", range(len(opts)), format_func=lambda x: opts[x])
            res = st.session_state.history[sel]
            r1, r2, r3 = st.columns(3)
            r1.metric("Energy Density", f"{res['Wh/kg']} Wh/kg", delta=round(res['Wh/kg']-v_te, 1))
            r2.metric("Cell Voltage", f"{res['Cell_V']} V"); r3.metric("Expected Life", f"{res['Life(Cyc)']:,} Cyc")
            g1, g2 = st.columns(2)
            with g1:
                fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A', width=3)))
                fig1.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), template="plotly_white", xaxis_title="DOD (%)", yaxis_title="Voltage (V)")
                st.plotly_chart(fig1, use_container_width=True)
            with g2:
                fig2 = go.Figure(go.Scatter(x=res.get('dq_x', []), y=res.get('dq_y', []), fill='tozeroy', line=dict(color='#e63946', width=2)))
                fig2.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), template="plotly_white", xaxis_title="Voltage (V)", yaxis_title="dQ/dV")
                st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(pd.DataFrame(st.session_state.history).drop(columns=['dq_x','dq_y'], errors='ignore'), use_container_width=True)

# -----------------------------------------------------------------------------
# 6. Data Management & Export (들여쓰기 적용)
# -----------------------------------------------------------------------------
if is_pro and st.session_state.history:
    with st.container(border=True):
        st.markdown('<p class="main-header">6. Data Management & Export (Pro)</p>', unsafe_allow_html=True)
        sp6, c6 = st.columns([0.03, 0.97])
        with c6:
            b1, b2, b3, b4 = st.columns(4)
            if b1.button("💾 내 계정에 저장하기"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    db = conn.read(spreadsheet=URL_USERS, worksheet="myData", ttl=0)
                    if not db.empty and not db[(db['Email']==st.session_state.user_email) & (db['Time']==res['Time'])].empty:
                        st.warning("⚠️ 이미 동일한 데이터가 저장되어 있습니다.")
                    else:
                        s_rec = res.copy(); s_rec['Email'] = st.session_state.user_email
                        s_rec.pop('dq_x', None); s_rec.pop('dq_y', None)
                        conn.update(spreadsheet=URL_USERS, worksheet="myData", data=pd.concat([db, pd.DataFrame([s_rec])], ignore_index=True))
                        st.success("✅ myData에 안전하게 저장 되었습니다.")
                except: st.error("저장 실패")
            
            if b2.button("📂 저장된 기록 동기화"):
                st.session_state.history = load_user_history(st.session_state.user_email); st.rerun()

            if FPDF:
                b3.download_button("📄 선택 항목 PDF 출력", create_pdf([res]), f"Result_{res['Time']}.pdf")
                b4.download_button("📑 전체 이력 PDF 출력", create_pdf(st.session_state.history), "All_Logs.pdf")

st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)