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
    .header-container { display: flex; align-items: center; justify-content: flex-start; }
    .syno-title { color: #003366; font-size: 38px; font-weight: 900; margin-right: 15px; }
    .syno-subtitle { color: #000; font-size: 22px; font-weight: normal; padding-top: 8px; }
    
    /* 메트릭(결과값) 카드 및 폰트 사이즈 조정 */
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #003366 !important; } /* 기본보다 한 단계 축소 및 색상 적용 */
    div[data-testid="stMetricDelta"] { font-size: 14px !important; }
    
    div[data-testid="stButton"] > button {
        height: 48px !important; background-color: #003366 !important;
        color: white !important; font-weight: bold !important; font-size: 16px !important; border-radius: 4px !important;
        width: 100%; border: none !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important;
        border-radius: 12px !important; padding: 25px 25px 15px 25px !important;
        margin-bottom: 40px !important; 
    }
    .main-header { font-size: 26px !important; font-weight: bold !important; color: #003366; margin-bottom: 20px; display: block; }
    .sub-header-bold { font-size: 20px !important; font-weight: bold !important; color: #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# [보안] 비밀번호 단방향 암호화
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화 (엔터 로그인 지원)
# -----------------------------------------------------------------------------
if 'init_master' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'show_reg': False, 'reg_stage': 0,
        'v_code': "", 'temp_email': "", 'history': [], 'sim_result': None,
        'init_master': True, 'trigger_login': False
    })

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
# 4. 상단 헤더 및 가입 모듈
# -----------------------------------------------------------------------------
h_l, h_r = st.columns([1, 1])
with h_l:
    st.markdown('<div class="header-container"><span class="syno-title">SynoCore</span><span class="syno-subtitle">V1.45 Pro</span></div>', unsafe_allow_html=True)

with h_r:
    if not st.session_state.logged_in:
        l_c1, l_c2, l_c3 = st.columns([2, 2, 1])
        u_id = l_c1.text_input("ID", placeholder="email", key="id_login_m", label_visibility="collapsed")
        u_pw = l_c2.text_input("PW", type="password", placeholder="password", key="pw_login_m", label_visibility="collapsed", on_change=process_login)
        login_btn = l_c3.button("Login", key="btn_login_m")
        
        if login_btn or st.session_state.pop('trigger_login', False):
            df_u = get_user_db()
            u_id_clean = u_id.strip().lower()
            hashed_pw = hash_password(u_pw) if u_pw else ""
            valid = df_u[(df_u['Email'].str.strip().str.lower() == u_id_clean) & (df_u['Password'] == hashed_pw)] if not df_u.empty else pd.DataFrame()
            
            if u_id_clean == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
                st.session_state.logged_in = True; st.rerun()
            elif not valid.empty:
                st.session_state.logged_in = True; st.rerun()
            else: st.error("정보 확인 필요")
        
        if st.button("계정생성 ㅣ Pro 회원가입", key="btn_go_reg_m"): 
            st.session_state.show_reg = not st.session_state.show_reg
    else:
        st.info("✅ 접속 중: Authorized Pro Member")
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
            if st.button("가입신청", disabled=not (pw1==pw2 and n_name), key="r_fin_m"):
                st.success("가입신청이 완료되었습니다."); st.session_state.show_reg = False; st.session_state.reg_stage = 0

st.markdown("<br>", unsafe_allow_html=True)

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
    
    exp_label = "🔓 밀도 및 수명 등 세부 물성 수정 활성화 :red[(Pro Mode 전용)]" if not is_pro else "🔓 세부 물성 수정 활성화"
    expert = st.checkbox(exp_label, key="chk_exp_m", disabled=not is_pro)
    
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

# [3] Process Parameters
with st.container(border=True):
    st.markdown('<p class="main-header">3. Process Parameters</p>', unsafe_allow_html=True)
    
    adv_label = "🔍 세부 파라미터 수정 활성화 :red[(Pro Mode 전용)]" if not is_pro else "🔍 세부 파라미터 수정 활성화"
    show_adv = st.checkbox(adv_label, key="chk_adv_m", disabled=not is_pro)
    
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
        # [요청 반영] C-rate 범위 0.1~10.0, 단위 0.1로 수정
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
        # C-rate에 따른 물리 현상 연산 엔진
        ir_drop = 0.1 + (v_tc * 0.02)
        cell_v = max(0.1, v_volt - ir_drop)
        efficiency = max(0.5, 1.0 - (v_tc * 0.015))
        res_whkg = ((v_cap * (v_act/100) * cell_v) / 2.5) * efficiency
        life_cyc = int(v_life * (0.95 ** v_tc))
        
        # [요청 반영] KST (한국 표준시) 적용
        kst_time = datetime.utcnow() + timedelta(hours=9)
        cur_time = kst_time.strftime("%H:%M:%S")
        
        # dQ/dV 데이터 계산
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

    # 과거 기록 복원 (드롭다운 자동 연동)
    if st.session_state.history:
        st.markdown("---")
        st.markdown('<p class="sub-header-bold">🔍 과거 기록 불러오기 (선택 시 아래 결과가 즉시 변경됩니다)</p>', unsafe_allow_html=True)
        
        # [요청 반영] 드롭다운에 핵심 수치 4가지 직관적 표시
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
            fig1 = go.Figure(go.Scatter(x=np.linspace(0,100,100), y=res['Cell_V']-(np.linspace(0,1,100)**1.5), line=dict(color='#003366', width=3)))
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