import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import hashlib
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# [라이브러리 예외 처리]
try: from fpdf import FPDF
except ImportError: FPDF = None
try: from streamlit_gsheets import GSheetsConnection
except ImportError: GSheetsConnection = None

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 다국어 사전 (English / Korean)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.46 Pro", layout="wide")

LANG = {
    "en": {
        "title": "SynoCore V1.46 Pro", "login": "Login", "logout": "Logout", "id": "Email", "pw": "Password", "reg": "Sign Up",
        "guide_on": "💡 Show Technical Guide", "guide_off": "Hide Guide",
        "sec1": "1. Material Selection", "sec2": "2. Material Specs Expert Mode",
        "sec3": "3. Process Parameters", "sec4": "4. Target Settings",
        "sec5": "5. Simulation Control & Analysis", "sec6": "6. Data Management",
        "add_custom": "➕ Add Custom Material", "run_sim": "🚀 RUN DESIGN SIMULATION",
        "energy_goal": "Energy Goal (Wh/kg)", "cycle_goal": "Cycle Life Goal", "crate": "C-rate",
        "sub_a": "(A) Cathode Settings", "sub_b": "(B) Anode & Balance", "sub_c": "(C) Cell",
        "porosity": "Porosity", "warn_porosity": "⚠️ Low Porosity: Risk of poor wetting!",
        "save_cloud": "💾 Save to Cloud", "del_cloud": "🗑️ Delete Record",
        "glossary": "📖 Glossary", "deep_dive": "🎓 Deep Dive Insight"
    },
    "ko": {
        "title": "시노코어 V1.46 프로", "login": "로그인", "logout": "로그아웃", "id": "이메일", "pw": "비밀번호", "reg": "계정 신청",
        "guide_on": "💡 기술 가이드 켜기", "guide_off": "가이드 숨기기",
        "sec1": "1. 소재 선택", "sec2": "2. 소재 스펙 정밀 설정",
        "sec3": "3. 공정 파라미터", "sec4": "4. 목표 수치 설정",
        "sec5": "5. 시뮬레이션 제어 및 분석", "sec6": "6. 데이터 관리 및 내보내기",
        "add_custom": "➕ 내 전용 소재 추가", "run_sim": "🚀 설계 시뮬레이션 실행",
        "energy_goal": "목표 에너지밀도 (Wh/kg)", "cycle_goal": "목표 수명(Cycle)", "crate": "충방전 속도(C-rate)",
        "sub_a": "(A) 양극재 설정", "sub_b": "(B) 음극재 및 밸런스", "sub_c": "(C) 셀 구성",
        "porosity": "예상 공극률", "warn_porosity": "⚠️ 공극률 부족: 전해액 함침 불량 위험!",
        "save_cloud": "💾 내 계정에 저장", "del_cloud": "🗑️ 선택 기록 삭제",
        "glossary": "📖 용어 사전", "deep_dive": "🎓 기술 인사이트"
    }
}

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stAppViewBlockContainer"] { max-width: 1400px; padding-top: 2rem; padding-bottom: 2rem; margin: auto; }
    .header-container { display: flex; align-items: center; justify-content: flex-start; height: 100%; }
    .syno-title { color: #1A729A; font-size: 40px; font-weight: 900; margin-right: 15px; letter-spacing: -1px; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1A729A !important; } 
    div[data-testid="stButton"] > button { height: 40px !important; background-color: #1A729A !important; color: white !important; font-weight: bold !important; width: 100%; border: none !important; }
    div[data-testid="stDownloadButton"] > button { height: 40px !important; background-color: #FFCA28 !important; color: #222 !important; font-weight: bold !important; width: 100%; border: 1px solid #E4B526 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 12px !important; padding: 25px !important; margin-bottom: 30px !important; }
    .main-header { font-size: 24px !important; font-weight: bold !important; color: #1A729A; margin-bottom: 20px; }
    .sub-header-bold { font-size: 18px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
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

def hash_password(password): return hashlib.sha256(password.strip().encode()).hexdigest()

@st.cache_data(ttl=60)
def load_cloud_data(url, ws="Sheet1"):
    if GSheetsConnection is None: return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=url, worksheet=ws)
        if df is not None and not df.empty:
            df.columns = [str(c).split('(')[0].strip() for c in df.columns]
            return df
    except: pass
    return pd.DataFrame()

def get_vip_list_exact():
    df = load_cloud_data(URL_USERS, "VIPs")
    return [str(x).strip() for x in df['Company'].dropna().tolist() if str(x).strip()] if not df.empty and 'Company' in df.columns else []

# -----------------------------------------------------------------------------
# 3. 유틸리티 엔진
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

def load_user_history(email, workspace):
    if GSheetsConnection is None: return []
    try:
        conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
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

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 헤더 UI
# -----------------------------------------------------------------------------
for k in ['logged_in', 'show_reg', 'history', 'lang', 'show_guide', 'user_email', 'user_name', 'is_admin', 'workspace', 'user_vip_name']:
    if k not in st.session_state: st.session_state[k] = "en" if k == 'lang' else False if isinstance(default:=False, bool) else [] if k == 'history' else "material_list" if k=='workspace' else ""

t1, t2, t3 = st.columns([5, 2, 3])
with t1: st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span style="font-size:20px; color:gray;">V1.46 Global Pro</span></div>', unsafe_allow_html=True)
with t2: st.session_state.lang = st.radio("Lang", ["en", "ko"], horizontal=True, label_visibility="collapsed")
t = LANG[st.session_state.lang]

with t3:
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([1,1,1])
        with c1.popover(t["login"]):
            u_id = st.text_input(t["id"]); u_pw = st.text_input(t["pw"], type="password")
            if st.button(t["login"], use_container_width=True):
                u_id_clean = u_id.strip().lower()
                if u_id_clean in ADMIN_USERS and u_pw == ADMIN_PW:
                    st.session_state.update({'logged_in': True, 'user_name': ADMIN_USERS[u_id_clean], 'user_email': u_id_clean, 'is_admin': True, 'workspace': 'material_list'}); st.rerun()
                else:
                    df_u = load_cloud_data(URL_USERS, "Users")
                    valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hash_password(u_pw))] if not df_u.empty else pd.DataFrame()
                    if not valid.empty:
                        domain = u_id_clean.split('@')[1].split('.')[0].lower(); vip_map = {v.lower(): v for v in get_vip_list_exact()}
                        st.session_state.update({'logged_in': True, 'user_name': str(valid['Name'].values[0]), 'user_email': u_id_clean, 'user_vip_name': vip_map.get(domain), 'workspace': 'material_list'}); st.rerun()
                    else: st.error("Fail")
        if c2.button(t["reg"]): st.session_state.show_reg = not st.session_state.show_reg; st.rerun()
    else:
        c1, c2 = st.columns([2, 1]); c1.markdown(f"**{st.session_state.user_name}** (Pro)")
        if c2.button(t["logout"]): 
            for k in ['logged_in', 'is_admin', 'history']: st.session_state[k] = False if type(st.session_state[k])==bool else []
            st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 어댑티브 레이아웃 (60:20:20 Toggle)
# -----------------------------------------------------------------------------
is_pro = st.session_state.logged_in
if is_pro: st.session_state.show_guide = st.toggle(t["guide_on"], value=st.session_state.show_guide)

if st.session_state.show_guide: col_main, col_glossary, col_deep = st.columns([0.6, 0.2, 0.2])
else: col_main = st.container(); col_glossary = None; col_deep = None

with col_main:
    # --- [섹션 1: 하이브리드 소재 선택] ---
    ws_badge = f" [{st.session_state.workspace}]" if is_pro else ""
    st.markdown(f'<p class="main-header">{t["sec1"]}<span style="font-size:16px; color:#888;">{ws_badge}</span></p>', unsafe_allow_html=True)
    
    df_pub = load_cloud_data(URL_MATS, "material_list")
    df_vip = load_cloud_data(URL_MATS, st.session_state.workspace) if is_pro and st.session_state.workspace != "material_list" else pd.DataFrame()
    mat_df = pd.concat([df_pub, df_vip]).drop_duplicates(subset=['Name'], keep='last') if not df_pub.empty else pd.DataFrame()

    if not mat_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        cat_list = mat_df[mat_df['Category']=='Cathode']['Name'].tolist(); cat_sel = c1.selectbox("Cathode", cat_list)
        ano_sel = c2.selectbox("Anode", mat_df[mat_df['Category']=='Anode']['Name'].tolist())
        ele_sel = c3.selectbox("Electrolyte", mat_df[mat_df['Category']=='Electrolyte']['Name'].tolist())
        sep_sel = c4.selectbox("Separator", mat_df[mat_df['Category']=='Separator']['Name'].tolist())
        
        if is_pro and st.session_state.workspace != "material_list":
            with st.expander(t["add_custom"]):
                new_cat = st.text_input("New Cathode Name"); new_cap = st.number_input("Capacity (mAh/g)", 160)
                if st.button("Save to My Workspace"):
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    new_row = pd.DataFrame([{"Name": new_cat, "Category": "Cathode", "Cap_Def": new_cap, "Volt_Def": 3.2, "Den_Def": 2.2}])
                    conn.update(spreadsheet=URL_MATS, worksheet=st.session_state.workspace, data=pd.concat([df_vip, new_row], ignore_index=True)); st.rerun()

        row = mat_df[mat_df['Name']==cat_sel].iloc[0] if cat_sel in cat_list else pd.Series()
        d_cap, d_vlt, d_den, d_lif, d_lod = float(row.get('Cap_Def', 160)), float(row.get('Volt_Def', 3.05)), float(row.get('Den_Def', 2.2)), int(row.get('Life_Def', 4000)), float(row.get('Load_Def', 14.0))
    else: st.error("DB Load Error"); d_cap, d_vlt, d_den, d_lif, d_lod = 160, 3.05, 2.2, 4000, 14

    # --- [섹션 2~4: 스펙, 파라미터, 목표] ---
    with st.container(border=True):
        st.markdown(f'<p class="main-header">{t["sec2"]}</p>', unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        v_cap = s1.slider("Capacity (mAh/g)", 100.0, 300.0, d_cap); v_vlt = s2.slider("Voltage (V)", 2.0, 5.0, d_vlt)
        v_den = s3.slider("Density (g/cc)", 1.0, 5.0, d_den, disabled=not is_pro); v_lif = s4.slider("Base Life", 500, 10000, d_lif, disabled=not is_pro)

    with st.container(border=True):
        st.markdown(f'<p class="main-header">{t["sec3"]}</p>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(f'<p class="sub-header-bold">{t["sub_a"]}</p>', unsafe_allow_html=True)
            v_load = st.slider("Loading (mg/cm2)", 5.0, 50.0, d_lod)
            v_press = st.slider("Press Density", 1.5, 4.0, 2.5, disabled=not is_pro)
            porosity = max(0.0, (1 - (v_press / v_den)) * 100) if v_den > 0 else 0
            st.caption(f"**{t['porosity']}: {porosity:.1f}%**")
            if porosity < 20.0: st.error(t["warn_porosity"])
        with p2:
            st.markdown(f'<p class="sub-header-bold">{t["sub_b"]}</p>', unsafe_allow_html=True)
            v_np = st.slider("N/P Ratio", 1.0, 1.5, 1.15, step=0.01)
        with p3:
            st.markdown(f'<p class="sub-header-bold">{t["sub_c"]}</p>', unsafe_allow_html=True)
            v_act = st.slider("Active Ratio (%)", 80.0, 99.0, 92.0)

    with st.container(border=True):
        st.markdown(f'<p class="main-header">{t["sec4"]}</p>', unsafe_allow_html=True)
        t1, t2, t3 = st.columns(3)
        v_te = t1.slider(t["energy_goal"], 100, 400, 250); v_tc = t2.slider(t["crate"], 0.1, 10.0, 1.0); v_tl = t3.slider(t["cycle_goal"], 500, 10000, 2000)

    # --- [섹션 5: 시뮬레이션 실행] ---
    with st.container(border=True):
        st.markdown(f'<p class="main-header">{t["sec5"]}</p>', unsafe_allow_html=True)
        if st.button(t["run_sim"], use_container_width=True):
            cell_v = max(0.1, v_vlt - (0.1 + v_tc*0.02)); whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * max(0.5, 1.0 - (v_tc*0.015))
            whl = whkg * v_press * 0.8  # 예상 부피 에너지 밀도
            life = int(v_lif * (0.95 ** v_tc))
            res = {"Time": (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M:%S"), "Cathode": cat_sel, "Wh/kg": round(whkg, 1), "Wh/L": round(whl, 1), "Cell_V": round(cell_v, 2), "Life(Cyc)": life}
            v_ax, dq = get_dqdv(cat_sel, v_tc, mat_df); res.update({"dq_x": v_ax, "dq_y": dq, "Anode": ano_sel, "Cap(mAh/g)": v_cap, "Volt(V)": v_vlt, "Load(mg)": v_load, "N/P Ratio": v_np, "Active(%)": v_act, "C-rate": v_tc})
            st.session_state.history.insert(0, res); st.rerun()

        if st.session_state.history:
            log_opts = [f"[{h['Time']}] {h['Cathode']} | {h['Wh/kg']} Wh/kg" for h in st.session_state.history]
            curr = st.session_state.history[st.selectbox("Select History", range(len(log_opts)), format_func=lambda x: log_opts[x], label_visibility="collapsed")]
            st.markdown("---")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Wh/kg", f"{curr['Wh/kg']}", delta=round(curr['Wh/kg']-v_te, 1)); r2.metric("Wh/L", f"{curr.get('Wh/L', 0)}")
            r3.metric("Cell V", f"{curr['Cell_V']} V"); r4.metric("Cycle Life", f"{curr['Life(Cyc)']:,}", delta=curr['Life(Cyc)']-v_tl)
            
            g1, g2 = st.columns(2)
            g1.plotly_chart(go.Figure(go.Scatter(x=np.linspace(0,100,100), y=curr['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#1A729A'))).update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="DOD (%)"), use_container_width=True)
            g2.plotly_chart(go.Figure(go.Scatter(x=curr['dq_x'], y=curr['dq_y'], fill='tozeroy', line=dict(color='#e63946'))).update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="Voltage"), use_container_width=True)

    # --- [섹션 6: 데이터 관리] ---
    if is_pro and st.session_state.history:
        with st.container(border=True):
            st.markdown(f'<p class="main-header">{t["sec6"]}</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button(t["save_cloud"]):
                conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
                sv = curr.copy(); sv.update({'Email': st.session_state.user_email, 'Workspace': st.session_state.workspace}); sv.pop('dq_x', None); sv.pop('dq_y', None)
                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=pd.concat([db_df, pd.DataFrame([sv])], ignore_index=True)); st.success("Saved!")
            if c2.button(t["del_cloud"]):
                conn = st.connection("gsheets", type=GSheetsConnection); db_df = conn.read(spreadsheet=URL_LOGS, worksheet="myData", ttl=0)
                conn.update(spreadsheet=URL_LOGS, worksheet="myData", data=db_df[~((db_df['Email'] == st.session_state.user_email) & (db_df['Time'] == curr['Time']))])
                st.session_state.history = [h for h in st.session_state.history if h['Time'] != curr['Time']]; st.rerun()

# --- [사이드 가이드 패널 렌더링] ---
if col_glossary and col_deep:
    with col_glossary:
        st.markdown(f"#### {t['glossary']}")
        with st.expander("N/P Ratio"): st.write("양극 대비 음극의 용량 비율. 리튬 석출 방지를 위해 1.1~1.2로 설계합니다." if st.session_state.lang=="ko" else "Anode to Cathode capacity ratio. >1.0 to prevent plating.")
        with st.expander("C-rate"): st.write("충방전 속도. 1C는 1시간 완충/완방을 의미합니다." if st.session_state.lang=="ko" else "Charge/Discharge rate.")
        with st.expander("Porosity"): st.write("전극 내 빈 공간. 전해액 함침에 필수적입니다." if st.session_state.lang=="ko" else "Empty space inside electrode, crucial for wetting.")
    with col_deep:
        st.markdown(f"#### {t['deep_dive']}")
        st.info("**[Trade-off Insight]**\n합제 밀도(Press Density)를 과하게 높이면 부피 에너지 밀도(Wh/L)는 상승하지만, 공극률(Porosity)이 20% 이하로 떨어져 저항이 급증하고 수명이 단축됩니다." if st.session_state.lang=="ko" else "High Press Density increases Wh/L but reduces Porosity. Below 20%, resistance spikes and cycle life drops.")

st.markdown("<br><hr><div style='text-align: center; color: #888; font-size: 14px;'>ⓒ 2019–2026. SynoTech. All rights reserved.</div>", unsafe_allow_html=True)